#!/usr/bin/env python3
"""table-ratchet.py - no-new-debt guard for HTML table migrations.

This script lets a repo keep known legacy table debt while blocking new debt.
It scans source files for:

  * table elements without an approved table class
  * table elements outside an approved wrapper class
  * inline <style> blocks that contain table-specific CSS
  * canonical_override: a page-local selector that out-specifies the canonical
    table component and re-paints its header/cells. This is the silent failure
    mode of a class-only migration -- the table HAS the canonical class (so the
    other checks pass) but a leftover per-page rule like
    `table.legacy thead th { background: #1a2330 }` ties the canonical
    `table.<canonical> thead th` selector (both specificity 0,1,3) and WINS on
    source order, because a page <style> block follows the linked stylesheet.
    The table renders off-brand even though every other check is green.

Baseline workflow:

  python3 table-ratchet.py --root . --write-baseline
  python3 table-ratchet.py --root .

Exit codes:
  0 - no table debt increased beyond the baseline
  1 - one or more files regressed
  2 - operational/configuration error
"""

import argparse
import fnmatch
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_BASELINE = ".table-ratchet-baseline.json"
DEFAULT_INCLUDE = [
    "**/*.html",
    "**/*.htm",
    "**/*.md",
    "**/*.mdx",
    "**/*.njk",
    "**/*.liquid",
    "**/*.astro",
    "**/*.jsx",
    "**/*.tsx",
    "**/*.vue",
    "**/*.svelte",
    "**/*.php",
]
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".vercel",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "vendor",
}
KINDS = ("naked_table", "unsanctioned_table_class", "unwrapped_table", "inline_table_css", "canonical_override")

CLASS_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_:-]*")
TABLE_CSS = re.compile(
    r"(^|[\s,{])table\b|"
    r"\b(border-collapse|border-spacing|caption-side|empty-cells|table-layout)\s*:|"
    r"\.[A-Za-z0-9_:-]*table[A-Za-z0-9_:-]*\b",
    re.IGNORECASE,
)
FENCED_CODE = re.compile(r"(```.*?```|~~~.*?~~~)", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")

# --- canonical_override detection ---------------------------------------------
# A naive split of `selector { declarations }` rules inside a <style> block.
# Good enough for hand-authored page CSS; we only need the selector text and
# whether the declaration paints a canonical-owned property.
CSS_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
# The declaration paints a property the canonical component owns (so an override
# here visibly defeats the migration). background/color are the high-signal ones.
PAINT_PROP = re.compile(r"(?:^|;|\s)(background(?:-color)?|color)\s*:", re.IGNORECASE)
# Values that are NOT a real override (resets / inheritance) -> ignore.
PAINT_NOOP = re.compile(r":\s*(transparent|inherit|initial|unset|none|currentcolor)\b", re.IGNORECASE)
# Selector targets the table HEADER (thead ... th). The header background is the
# dominant "off-brand" signal and the actual failure this guard exists to catch;
# body zebra/hover tints are low-signal and pervasive, so we deliberately do not
# flag them here (keep the gate high-signal, not noisy).
SEL_TARGETS_HEADER = re.compile(r"\bthead\b[^,{}]*\bth\b", re.IGNORECASE)
# Selector specificity ties-or-beats the canonical `table.<c> thead th` (0,1,3):
#   an element-prefixed table class (table.x ...), OR two+ class tokens, OR an id.
SEL_HIGH_SPEC = re.compile(r"\btable\s*\.[A-Za-z_][\w:-]*|\.[A-Za-z_][\w:-]*\s*\.[A-Za-z_][\w:-]*|#[A-Za-z_][\w:-]*")


def find_canonical_overrides(css, canonical_classes):
    """Yield (selector, prop) for page-local rules that out-specify and re-paint
    the canonical table component. `canonical_classes` are the approved table
    classes whose own rules are exempt (they ARE the component)."""
    canon = {c for c in canonical_classes if c}
    for rule in CSS_RULE.finditer(css):
        decl = rule.group(2)
        paint = PAINT_PROP.search(decl)
        if not paint:
            continue
        bang = "!important" in decl.lower()
        for selector in rule.group(1).split(","):
            sel = " ".join(selector.split())
            if not sel or sel.startswith("@"):
                continue
            # The canonical component's own rules are allowed.
            if any(re.search(r"(^|[\s.>+~])" + re.escape(c) + r"(\b|[\s.>+~:])", sel) for c in canon):
                continue
            if not SEL_TARGETS_HEADER.search(sel):
                continue
            # Wins if it out-specifies canonical OR carries !important.
            if not (SEL_HIGH_SPEC.search(sel) or bang):
                continue
            # Skip pure resets (background:transparent etc.) unless !important.
            seg = decl[paint.start():]
            if PAINT_NOOP.search(seg[:40]) and not bang:
                continue
            yield sel[:90], paint.group(1).lower()


def split_classes(value):
    if not value:
        return set()
    return set(CLASS_TOKEN.findall(str(value)))


def scrub_markdown_code(path, text):
    if path.suffix.lower() not in {".md", ".mdx", ".markdown"}:
        return text
    text = FENCED_CODE.sub("", text)
    return INLINE_CODE.sub("", text)


def should_skip(path, root, exclude_dirs, allow_files):
    rel = path.relative_to(root).as_posix()
    if any(part in exclude_dirs for part in path.relative_to(root).parts[:-1]):
        return True
    return any(fnmatch.fnmatch(rel, pattern) or rel == pattern for pattern in allow_files)


def find_files(root, includes, exclude_dirs, allow_files):
    files = []
    for pattern in includes:
        for path in root.glob(pattern):
            if path.is_file() and not should_skip(path, root, exclude_dirs, allow_files):
                files.append(path)
    return sorted(set(files))


class TableDebtParser(HTMLParser):
    def __init__(self, allowed_table, allowed_wrapper, wrapper_exempt):
        super().__init__(convert_charrefs=True)
        self.allowed_table = allowed_table
        self.allowed_wrapper = allowed_wrapper
        self.wrapper_exempt = wrapper_exempt
        self.stack = []
        self.findings = []
        self._style_line = None
        self._style_chunks = []

    def handle_starttag(self, tag, attrs):
        attrs_by_name = {name.lower(): value for name, value in attrs}
        classes = split_classes(attrs_by_name.get("class") or attrs_by_name.get("classname"))
        line, col = self.getpos()
        tag = tag.lower()

        if tag == "style":
            self._style_line = line
            self._style_chunks = []

        self.stack.append({"tag": tag, "classes": classes})

        if tag == "table":
            self._check_table(classes, line, col)

    def handle_startendtag(self, tag, attrs):
        attrs_by_name = {name.lower(): value for name, value in attrs}
        classes = split_classes(attrs_by_name.get("class") or attrs_by_name.get("classname"))
        if tag.lower() == "table":
            line, col = self.getpos()
            self._check_table(classes, line, col)

    def handle_data(self, data):
        if self._style_line is not None:
            self._style_chunks.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "style" and self._style_line is not None:
            css = "".join(self._style_chunks)
            if TABLE_CSS.search(css):
                self._add("inline_table_css", self._style_line, 0, "inline <style> contains table-specific CSS")
            for sel, prop in find_canonical_overrides(css, self.allowed_table):
                self._add(
                    "canonical_override",
                    self._style_line,
                    0,
                    f"selector [{sel}] re-paints '{prop}' on the table header and out-specifies the canonical component (will win on source order)",
                )
            self._style_line = None
            self._style_chunks = []

        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break

    def _check_table(self, classes, line, col):
        if not classes:
            self._add("naked_table", line, col, "table has no class/className")
        elif not (classes & self.allowed_table):
            found = " ".join(sorted(classes))
            allowed = ", ".join(sorted(self.allowed_table))
            self._add("unsanctioned_table_class", line, col, f"table classes [{found}] do not include approved class [{allowed}]")

        if classes & self.wrapper_exempt:
            return
        if not any(frame["classes"] & self.allowed_wrapper for frame in self.stack[:-1]):
            allowed = ", ".join(sorted(self.allowed_wrapper))
            self._add("unwrapped_table", line, col, f"table is not inside approved wrapper [{allowed}]")

    def _add(self, kind, line, col, message):
        self.findings.append({"kind": kind, "line": line, "column": col + 1, "message": message})


def scan_file(path, allowed_table, allowed_wrapper, wrapper_exempt):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        raise RuntimeError(f"could not read {path}: {exc}") from exc

    parser = TableDebtParser(allowed_table, allowed_wrapper, wrapper_exempt)
    try:
        parser.feed(scrub_markdown_code(path, text))
        parser.close()
    except Exception as exc:
        raise RuntimeError(f"could not parse {path}: {exc}") from exc
    return parser.findings


def scan(root, includes, exclude_dirs, allow_files, allowed_table, allowed_wrapper, wrapper_exempt):
    findings_by_file = {}
    for path in find_files(root, includes, exclude_dirs, allow_files):
        findings = scan_file(path, allowed_table, allowed_wrapper, wrapper_exempt)
        if findings:
            findings_by_file[path.relative_to(root).as_posix()] = findings
    return findings_by_file


def counts_from_findings(findings_by_file):
    counts = {}
    for rel, findings in findings_by_file.items():
        by_kind = Counter(item["kind"] for item in findings)
        counts[rel] = {kind: by_kind.get(kind, 0) for kind in KINDS if by_kind.get(kind, 0)}
    return counts


def load_baseline(path):
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"could not read baseline {path}: {exc}") from exc
    return data.get("counts", {})


def write_baseline(path, root, args, counts):
    data = {
        "version": 1,
        "generated_by": "table-ratchet.py",
        "root": ".",
        "canonical_table_class": args.canonical_table_class,
        "canonical_wrapper_class": args.canonical_wrapper_class,
        "allow_table_class": sorted(set(args.allow_table_class or [])),
        "allow_wrapper_class": sorted(set(args.allow_wrapper_class or [])),
        "allow_unwrapped_table_class": sorted(set(args.allow_unwrapped_table_class or [])),
        "counts": counts,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compare_counts(current, baseline):
    regressions = []
    for rel in sorted(set(current) | set(baseline)):
        for kind in KINDS:
            now = current.get(rel, {}).get(kind, 0)
            before = baseline.get(rel, {}).get(kind, 0)
            if now > before:
                regressions.append({"file": rel, "kind": kind, "before": before, "now": now})
    return regressions


def format_count_summary(counts):
    total = Counter()
    for by_kind in counts.values():
        total.update(by_kind)
    if not total:
        return "0 findings"
    return ", ".join(f"{total[k]} {k}" for k in KINDS if total.get(k))


def print_regressions(regressions, findings_by_file, sample_limit):
    print("[table-ratchet] FAIL - table debt increased beyond baseline.")
    for item in regressions:
        print(f"  {item['file']}: {item['kind']} {item['before']} -> {item['now']} (+{item['now'] - item['before']})")
        samples = [f for f in findings_by_file.get(item["file"], []) if f["kind"] == item["kind"]]
        for finding in samples[:sample_limit]:
            print(f"    line {finding['line']}:{finding['column']} - {finding['message']}")
        if len(samples) > sample_limit:
            print(f"    ... {len(samples) - sample_limit} more")
    print("\nRemediation:")
    print("  - Use the canonical table class on prose/content tables.")
    print("  - Put wide/content tables inside the canonical wrapper.")
    print("  - Move table-specific inline CSS into the shared table stylesheet.")
    print("  - canonical_override: a page-local rule out-specifies the canonical")
    print("    component and re-paints it (e.g. `table.legacy thead th{background}`).")
    print("    Adding the class is not enough -- remove the competing background/color")
    print("    so the canonical styling wins; KEEP structural rules (min-width/scroll,")
    print("    position:sticky, @media card-mode, hidden columns, numeric text-align).")
    print("    Genuine data-viz (heatmaps, color-encoded matrices, frozen-corner pivots,")
    print("    JS-rendered tables) are not overrides -- allowlist the class + re-baseline.")
    print("  - If a legacy/admin grid is intentional, add a narrow allowlist flag and refresh the baseline.")


def parse_args(argv):
    ap = argparse.ArgumentParser(description="No-new-debt ratchet for HTML table migrations.")
    ap.add_argument("--root", default=".", help="Repository or site root to scan. Default: current directory.")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE, help=f"Baseline JSON path. Default: {DEFAULT_BASELINE}")
    ap.add_argument("--include", action="append", help="Glob to scan, relative to --root. May be repeated.")
    ap.add_argument("--exclude-dir", action="append", help="Directory name to exclude. May be repeated.")
    ap.add_argument("--allow-file", action="append", default=[], help="File glob/path to ignore entirely. May be repeated.")
    ap.add_argument("--canonical-table-class", default="content-table", help="Approved prose/content table class.")
    ap.add_argument("--canonical-wrapper-class", default="table-scroll", help="Approved table wrapper class.")
    ap.add_argument("--allow-table-class", action="append", default=[], help="Additional approved table class, such as an admin grid class.")
    ap.add_argument("--allow-wrapper-class", action="append", default=[], help="Additional approved wrapper class.")
    ap.add_argument("--allow-unwrapped-table-class", action="append", default=[], help="Approved table class that does not require a wrapper.")
    ap.add_argument("--write-baseline", action="store_true", help="Write/replace the baseline with current counts instead of comparing.")
    ap.add_argument("--sample-limit", type=int, default=3, help="Number of sample findings to print per regression.")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"[table-ratchet] ERROR - --root is not a directory: {root}", file=sys.stderr)
        return 2

    includes = args.include or DEFAULT_INCLUDE
    exclude_dirs = DEFAULT_EXCLUDE_DIRS | set(args.exclude_dir or [])
    allowed_table = {args.canonical_table_class} | set(args.allow_table_class or [])
    allowed_wrapper = {args.canonical_wrapper_class} | set(args.allow_wrapper_class or [])
    wrapper_exempt = set(args.allow_unwrapped_table_class or [])
    baseline_path = Path(args.baseline)
    if not baseline_path.is_absolute():
        baseline_path = root / baseline_path

    try:
        findings_by_file = scan(root, includes, exclude_dirs, args.allow_file, allowed_table, allowed_wrapper, wrapper_exempt)
        current_counts = counts_from_findings(findings_by_file)
    except RuntimeError as exc:
        print(f"[table-ratchet] ERROR - {exc}", file=sys.stderr)
        return 2

    if args.write_baseline:
        try:
            write_baseline(baseline_path, root, args, current_counts)
        except OSError as exc:
            print(f"[table-ratchet] ERROR - could not write baseline {baseline_path}: {exc}", file=sys.stderr)
            return 2
        print(f"[table-ratchet] baseline written: {baseline_path}")
        print(f"[table-ratchet] current debt: {format_count_summary(current_counts)} across {len(current_counts)} files")
        return 0

    try:
        baseline_counts = load_baseline(baseline_path)
    except RuntimeError as exc:
        print(f"[table-ratchet] ERROR - {exc}", file=sys.stderr)
        return 2
    if baseline_counts is None:
        print(f"[table-ratchet] ERROR - missing baseline: {baseline_path}", file=sys.stderr)
        print("Create one after reviewing current legacy debt:", file=sys.stderr)
        print(f"  python3 {Path(__file__).name} --root {root} --write-baseline", file=sys.stderr)
        return 2

    regressions = compare_counts(current_counts, baseline_counts)
    if regressions:
        print_regressions(regressions, findings_by_file, args.sample_limit)
        return 1

    print(f"[table-ratchet] PASS - no table debt increased. Current debt: {format_count_summary(current_counts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
