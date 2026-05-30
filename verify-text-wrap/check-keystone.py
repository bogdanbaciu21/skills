#!/usr/bin/env python3
"""check-keystone.py — deterministic root-cause guard for the wrap-safe keystone.

The wrap-safe contract: any page that uses flex or grid layout MUST include the
universal min-width:0 reset:

    *, *::before, *::after { min-width: 0; }   /* wrap-safe keystone */

This is the single most important rule for preventing container-collapse /
"caterpillar text" wrap bugs. The default min-width of a flex/grid item is
`auto`, not 0 — so one unbreakable child (a long word, a URL, an image) can
force a *sibling* wider than its budget, and the browser collapses the other
children to make room. The paragraph in the collapsed child then wraps one or
two words per line: text "wrapping when it shouldn't."

runner.py catches that symptom *after* it renders, and only at the viewports it
happens to test. This script catches the *cause* before anything renders:
deterministic, no browser, no flake. Wire it into pre-commit / CI so a repo can
never ship flex/grid layout without the keystone again.

A repo satisfies the contract if EITHER:
  (a) a scanned stylesheet (or inline <style>) contains a universal-selector
      min-width:0 rule, OR
  (b) any HTML references wrap-safe.css (local path or the jsDelivr CDN), which
      ships the keystone.

Exit codes:
    0 — keystone present, OR no flex/grid found (so the keystone isn't required)
    1 — flex/grid used but keystone missing  (the failure class this guards)
    2 — operational error (path missing, no CSS/HTML found)

Usage:
    python3 check-keystone.py --portal <static-html-dir>
    python3 check-keystone.py --css assets/app.css assets/extra.css
    python3 check-keystone.py --portal site/ --quiet
"""
import argparse
import glob
import os
import re
import sys

_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)
_STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_MINWIDTH0 = re.compile(r"min-width\s*:\s*0(px)?\b", re.IGNORECASE)
_FLEXGRID = re.compile(r"display\s*:\s*(inline-)?(flex|grid)\b", re.IGNORECASE)
_GRIDTPL = re.compile(r"\b(grid-template|flex-direction|flex-flow)\b", re.IGNORECASE)
_IGNORE_DIRS = {"node_modules", ".git", "vendor", "dist", "build", "__pycache__"}


def _strip_comments(css):
    return _COMMENT.sub(" ", css)


def _iter_rules(css):
    """Yield (selector, body) for every rule block, including those nested in
    @media (the innermost-block regex matches them too)."""
    for m in _RULE.finditer(css):
        yield m.group(1).strip(), m.group(2)


def _is_universal(selector):
    for part in selector.split(","):
        p = part.strip()
        if p in ("*", ":where(*)"):
            return True
        if re.match(r"^\*(\s|$)", p):          # `* ` universal + combinator
            return True
        if re.match(r"^:where\(\s*\*\s*\)", p):  # :where(*) ...
            return True
    return False


def has_keystone(css):
    css = _strip_comments(css)
    for selector, body in _iter_rules(css):
        if _MINWIDTH0.search(body) and _is_universal(selector):
            return True
    return False


def uses_flex_grid(css):
    css = _strip_comments(css)
    return bool(_FLEXGRID.search(css) or _GRIDTPL.search(css))


def references_wrapsafe(html):
    return "wrap-safe.css" in html


def _walk(portal, ext):
    for root, dirs, files in os.walk(portal):
        dirs[:] = [d for d in dirs if d not in _IGNORE_DIRS]
        for fn in files:
            if fn.endswith(ext):
                yield os.path.join(root, fn)


def gather(portal, css_paths):
    css_texts, html_texts, scanned = [], [], {"css": 0, "html": 0, "inline": 0}
    if css_paths:
        for pat in css_paths:
            for path in glob.glob(pat, recursive=True):
                try:
                    css_texts.append(open(path, encoding="utf-8", errors="ignore").read())
                    scanned["css"] += 1
                except OSError:
                    pass
    if portal:
        for path in _walk(portal, ".css"):
            try:
                css_texts.append(open(path, encoding="utf-8", errors="ignore").read())
                scanned["css"] += 1
            except OSError:
                pass
        for path in _walk(portal, ".html"):
            try:
                html = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            html_texts.append(html)
            scanned["html"] += 1
            for block in _STYLE_BLOCK.findall(html):
                css_texts.append(block)
                scanned["inline"] += 1
    return css_texts, html_texts, scanned


def main():
    ap = argparse.ArgumentParser(description="Deterministic wrap-safe keystone guard.")
    ap.add_argument("--portal", help="Static-HTML dir to scan recursively (.css + inline <style> + .html links).")
    ap.add_argument("--css", nargs="+", help="Explicit CSS files/globs to scan (in addition to --portal).")
    ap.add_argument("--quiet", action="store_true", help="Only print on failure.")
    args = ap.parse_args()

    if not args.portal and not args.css:
        print("[check-keystone] ERROR: pass --portal DIR and/or --css FILE...", file=sys.stderr)
        return 2
    if args.portal and not os.path.isdir(args.portal):
        print(f"[check-keystone] ERROR: --portal not a directory: {args.portal}", file=sys.stderr)
        return 2

    css_texts, html_texts, scanned = gather(args.portal, args.css)
    if not css_texts and not html_texts:
        print("[check-keystone] ERROR: no CSS or HTML found to scan.", file=sys.stderr)
        return 2

    combined = "\n".join(css_texts)
    flexgrid = uses_flex_grid(combined)
    keystone = has_keystone(combined) or any(references_wrapsafe(h) for h in html_texts)

    where = args.portal or ", ".join(args.css)
    summary = f"{scanned['css']} css, {scanned['inline']} inline <style>, {scanned['html']} html"

    if flexgrid and not keystone:
        print(f"[check-keystone] FAIL — flex/grid layout found but the wrap-safe keystone is missing.")
        print(f"  scanned: {summary}  under: {where}")
        print(f"  This is the #1 cause of caterpillar / container-collapse text wrap.")
        print(f"  Add to your GLOBAL stylesheet (not per-page):")
        print(f"\n      *, *::before, *::after {{ min-width: 0; }}   /* wrap-safe keystone */\n")
        print(f"  …or install wrap-safe.css, which ships it:")
        print(f"      <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/gh/bogdanbaciu21/skills@main/verify-text-wrap/wrap-safe.css\">")
        return 1

    if not args.quiet:
        if not flexgrid:
            print(f"[check-keystone] PASS — no flex/grid layout found; keystone not required. ({summary})")
        else:
            print(f"[check-keystone] PASS — flex/grid present and the wrap-safe keystone is in place. ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
