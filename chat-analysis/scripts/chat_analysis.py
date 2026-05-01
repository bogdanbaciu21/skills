#!/usr/bin/env python3
"""
Claude chat transcript analyzer — recursive self-improvement pipeline.

Four-stage pipeline:
  1. Parse   — read JSONL session files from ~/.claude/projects/<project>/
  2. Filter  — regex pre-filter, drop sessions with no friction signals
  3. Label   — send survivors to Sonnet with strict JSON schema
  4. Compile — aggregate into top failure modes, high-cost patterns, rule candidates

Usage:
    python3 scripts/chat_analysis.py                      # current project, last 50
    python3 scripts/chat_analysis.py --n 100              # last 100 sessions
    python3 scripts/chat_analysis.py --all                # every project under ~/.claude/projects/
    python3 scripts/chat_analysis.py --dry-run            # filter only, no API calls
    python3 scripts/chat_analysis.py --output review.md   # custom output path
    python3 scripts/chat_analysis.py --project /path/to/project

Requires ANTHROPIC_API_KEY in environment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"
DEFAULT_N = 50
DEFAULT_OUTPUT = "chat-analysis-review.md"
DEFAULT_MODEL = "claude-sonnet-4-6"
SLEEP_BETWEEN_CALLS = 1.0  # seconds between API calls

# ---------------------------------------------------------------------------
# Redaction — strip secrets/PII before any data leaves the local machine
# ---------------------------------------------------------------------------

REDACTION_RULES: list[tuple[re.Pattern[str], str]] = [
    # API keys / tokens (Anthropic, OpenAI, GitHub, generic sk- / ghp_ / etc.)
    (re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"), "[REDACTED_ANTHROPIC_KEY]"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bgho_[A-Za-z0-9]{20,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bghs_[A-Za-z0-9]{20,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    # JWTs
    (re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b"), "[REDACTED_JWT]"),
    # Bearer tokens in headers
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.=]{16,}"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)authorization:\s*\S+"), "authorization: [REDACTED]"),
    # Generic secret/password/token assignments
    (re.compile(r"(?i)(password|passwd|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?[^\s'\"]+"),
     r"\1=[REDACTED]"),
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    # Absolute home paths (leak username + project structure)
    (re.compile(r"/Users/[^/\s]+"), "/Users/[REDACTED]"),
    (re.compile(r"/home/[^/\s]+"), "/home/[REDACTED]"),
    # Credit-card-shaped numbers
    (re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"), "[REDACTED_CARD]"),
    # Private IPs are usually fine; public ones can identify infra — leave as-is.
]


def redact(text: str) -> str:
    """Apply all redaction rules to a string. Idempotent."""
    if not text:
        return text
    for pattern, replacement in REDACTION_RULES:
        text = pattern.sub(replacement, text)
    return text


FRICTION_PATTERNS = re.compile(
    r"\b(no[,.]|nope|wrong|stop|don'?t|incorrect|not right|wait[,.]|"
    r"undo|revert|that'?s not|you missed|you forgot|you ignored|"
    r"again|re-?do|re-?try|re-?run|still broken|still failing|"
    r"that'?s wrong|please don'?t|i said|i told you|as i said|"
    r"actually[,. ]|but you|you didn'?t|didn'?t ask|didn'?t say)\b",
    re.IGNORECASE,
)

LABEL_SCHEMA = """\
{
  "taskSummary": "string (1-2 sentences, what the user asked for)",
  "taskType": "debug|feature|refactor|research|config|content|deploy|other",
  "domain": "string (e.g. frontend, backend, content, infra, styling, data)",
  "outcome": "completed|partial|failed|abandoned",
  "reworkCycles": "integer (how many times did the user have to correct course)",
  "rootCauseArchetype": "trusted-stale-data|wrong-abstraction-level|missed-existing-work|incomplete-verification|wrong-diagnosis|overexplained|other|none",
  "corrections": [
    {"text": "verbatim or close paraphrase of user correction", "severity": "low|medium|high"}
  ],
  "positiveSignals": ["verbatim or close paraphrase of user praise / 'exactly right' signals"],
  "communicationAntipatterns": ["explained-before-fixing", "too-verbose", "hedged-unnecessarily", "asked-unnecessary-question", "narrated-thought-process"],
  "whichRulesViolated": ["rule name or short description, e.g. fix-first-explain-later"],
  "verificationLevel": "ran-tests-and-checked-output|ran-tests|verbal-claim-only|none",
  "codebbaseAwareness": "strong|adequate|weak|oblivious"
}"""

LABEL_PROMPT = """\
You are analyzing a Claude Code session transcript for failure patterns and friction signals.

Your job: produce a structured JSON label for this session so it can be aggregated
across hundreds of sessions to identify systemic improvement opportunities.

Be precise. If no corrections occurred, say so. If the outcome was good, say so.
Do not over-label — a clean session with no friction should get reworkCycles: 0 and
rootCauseArchetype: "none".

Schema (respond ONLY with valid JSON matching this shape, no markdown, no fences):
{schema}

--- SESSION TRANSCRIPT ---
{transcript}
--- END TRANSCRIPT ---

Respond with a single JSON object only. No prose, no explanation, no code fences."""


# ---------------------------------------------------------------------------
# Stage 1 — Parse
# ---------------------------------------------------------------------------

def detect_project_dir(cwd: Path) -> Path | None:
    """Map a filesystem path to its ~/.claude/projects/<hashed> directory."""
    if not CLAUDE_PROJECTS.exists():
        return None
    # Claude hashes the project path by replacing / with - (leading slash dropped)
    candidate = CLAUDE_PROJECTS / cwd.as_posix().replace("/", "-").lstrip("-")
    if candidate.exists():
        return candidate
    # Also try with the leading dash kept
    candidate2 = CLAUDE_PROJECTS / ("-" + cwd.as_posix().replace("/", "-").lstrip("-"))
    if candidate2.exists():
        return candidate2
    return None


def list_project_dirs() -> list[Path]:
    if not CLAUDE_PROJECTS.exists():
        return []
    return sorted(p for p in CLAUDE_PROJECTS.iterdir() if p.is_dir())


def extract_text(content: Any) -> str:
    """Pull plain text out of a message content field (string or content-block array)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                btype = block.get("type", "")
                if btype == "text":
                    parts.append(block.get("text", ""))
                elif btype == "tool_result":
                    # Flatten nested tool result content (first 120 chars only)
                    inner = block.get("content", "")
                    snippet = extract_text(inner)[:120]
                    if snippet:
                        parts.append(f"[tool_result: {snippet}]")
        return "\n".join(parts)
    return ""


def parse_session(path: Path) -> dict:
    """Parse a single .jsonl session file into a structured session dict."""
    turns: list[dict] = []
    first_ts = last_ts = None

    for raw_line in path.read_text(errors="replace").splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            obj = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        ts_str = obj.get("timestamp")
        if ts_str:
            ts = ts_str
            if first_ts is None:
                first_ts = ts
            last_ts = ts

        obj_type = obj.get("type")

        if obj_type == "user":
            msg = obj.get("message", {})
            content = msg.get("content", "")
            text = extract_text(content)
            # Filter out pure tool-result-only turns (they have no user text)
            if text and not text.startswith("[tool_result:"):
                turns.append({"role": "user", "text": text, "ts": ts_str})

        elif obj_type == "assistant":
            msg = obj.get("message", {})
            content = msg.get("content", [])
            text_parts = []
            tool_calls = []
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type", "")
                    if btype == "text":
                        text_parts.append(block.get("text", ""))
                    elif btype == "tool_use":
                        tool_calls.append(block.get("name", "unknown"))
            text = "\n".join(text_parts).strip()
            if text or tool_calls:
                turns.append({
                    "role": "assistant",
                    "text": text,
                    "tools": tool_calls,
                    "ts": ts_str,
                })

    return {
        "session_id": path.stem,
        "path": str(path),
        "first_ts": first_ts,
        "last_ts": last_ts,
        "turns": turns,
        "user_turns": [t for t in turns if t["role"] == "user"],
        "assistant_turns": [t for t in turns if t["role"] == "assistant"],
    }


def load_sessions(project_dir: Path, n: int) -> list[dict]:
    """Load the most recent N sessions from a project directory."""
    jsonl_files = sorted(project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    selected = jsonl_files[-n:]
    sessions = []
    for p in selected:
        try:
            s = parse_session(p)
            if s["turns"]:
                sessions.append(s)
        except Exception as e:
            print(f"  warn: could not parse {p.name}: {e}", file=sys.stderr)
    return sessions


# ---------------------------------------------------------------------------
# Stage 2 — Filter
# ---------------------------------------------------------------------------

def has_friction(session: dict) -> bool:
    """Return True if the session has any correction/friction signals."""
    user_texts = [t["text"] for t in session["user_turns"]]
    combined = " ".join(user_texts)
    if FRICTION_PATTERNS.search(combined):
        return True
    # Also flag repeated identical tool calls (retry loops)
    all_tools: list[str] = []
    for t in session["assistant_turns"]:
        all_tools.extend(t.get("tools", []))
    if len(all_tools) != len(set(all_tools)) and len(all_tools) > 3:
        counts = Counter(all_tools)
        if any(v >= 3 for v in counts.values()):
            return True
    return False


def pre_filter(sessions: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split sessions into (friction, clean)."""
    friction, clean = [], []
    for s in sessions:
        (friction if has_friction(s) else clean).append(s)
    return friction, clean


# ---------------------------------------------------------------------------
# Stage 3 — Label
# ---------------------------------------------------------------------------

def build_transcript_text(session: dict, max_chars: int = 6000) -> str:
    """Render a session as a compact, redacted text transcript for the labeler."""
    lines = []
    for turn in session["turns"]:
        role = turn["role"].upper()
        text = redact(turn.get("text", "").strip())
        tools = turn.get("tools", [])
        if tools:
            lines.append(f"{role} [tools: {', '.join(tools)}]: {text[:300]}")
        elif text:
            lines.append(f"{role}: {text[:500]}")
    full = "\n\n".join(lines)
    if len(full) > max_chars:
        full = full[:max_chars] + "\n[... truncated ...]"
    return full


def label_session(session: dict, client: Any) -> dict | None:
    """Send a session to the LLM labeler; return parsed JSON or None."""
    transcript = build_transcript_text(session)
    prompt = LABEL_PROMPT.format(schema=LABEL_SCHEMA, transcript=transcript)
    try:
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Strip accidental markdown fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        label = json.loads(raw)
        label["_session_id"] = session["session_id"]
        label["_first_ts"] = session.get("first_ts")
        return label
    except json.JSONDecodeError as e:
        print(f"  warn: label parse error for {session['session_id']}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  warn: label API error for {session['session_id']}: {e}", file=sys.stderr)
        return None


def label_batch(sessions: list[dict], client: Any) -> list[dict]:
    """Label all sessions sequentially with progress."""
    labels = []
    for i, s in enumerate(sessions, 1):
        sid = s["session_id"][:8]
        print(f"  labeling {i}/{len(sessions)}  {sid}…", end="\r")
        label = label_session(s, client)
        if label:
            labels.append(label)
        if i < len(sessions):
            time.sleep(SLEEP_BETWEEN_CALLS)
    print(f"  labeled {len(labels)}/{len(sessions)} sessions        ")
    return labels


# ---------------------------------------------------------------------------
# Stage 4 — Compile
# ---------------------------------------------------------------------------

def aggregate(labels: list[dict]) -> dict:
    """Aggregate labels into ranked tables and candidate rules."""
    root_causes: Counter = Counter()
    root_cause_rework: defaultdict[str, list[int]] = defaultdict(list)
    antipatterns: Counter = Counter()
    rule_violations: Counter = Counter()
    corrections_all: list[str] = []
    positive_signals: list[str] = []
    verification_counts: Counter = Counter()
    awareness_counts: Counter = Counter()
    outcomes: Counter = Counter()

    for lb in labels:
        rc = lb.get("rootCauseArchetype", "other") or "other"
        rework = lb.get("reworkCycles", 0) or 0
        root_causes[rc] += 1
        root_cause_rework[rc].append(rework)

        for ap in lb.get("communicationAntipatterns", []) or []:
            antipatterns[ap] += 1

        for rv in lb.get("whichRulesViolated", []) or []:
            rule_violations[rv] += 1

        for c in lb.get("corrections", []) or []:
            if isinstance(c, dict):
                corrections_all.append(c.get("text", ""))

        positive_signals.extend(lb.get("positiveSignals", []) or [])

        vl = lb.get("verificationLevel", "none") or "none"
        verification_counts[vl] += 1

        aw = lb.get("codebbaseAwareness", "unknown") or "unknown"
        awareness_counts[aw] += 1

        oc = lb.get("outcome", "unknown") or "unknown"
        outcomes[oc] += 1

    def avg_rework(rc: str) -> float:
        vals = root_cause_rework[rc]
        return sum(vals) / len(vals) if vals else 0.0

    top_by_count = root_causes.most_common(10)
    top_by_cost = sorted(root_causes.keys(), key=lambda rc: avg_rework(rc), reverse=True)

    return {
        "total_labeled": len(labels),
        "outcomes": outcomes,
        "top_by_count": top_by_count,
        "top_by_cost": [(rc, avg_rework(rc), root_causes[rc]) for rc in top_by_cost if rc != "none"],
        "antipatterns": antipatterns.most_common(10),
        "rule_violations": rule_violations.most_common(10),
        "verification_counts": verification_counts,
        "awareness_counts": awareness_counts,
        "sample_corrections": corrections_all[:20],
        "sample_positives": positive_signals[:10],
    }


# ---------------------------------------------------------------------------
# Stage 5 — Write report
# ---------------------------------------------------------------------------

def write_report(
    agg: dict,
    labels: list[dict],
    friction: list[dict],
    clean: list[dict],
    output_path: Path,
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(friction) + len(clean)
    lines = [
        f"# Chat Analysis Review — {now}",
        "",
        "> **Review required.** This file was generated by `scripts/chat_analysis.py`.",
        "> Accept, reject, or edit each proposed delta before touching `CLAUDE.md`.",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Sessions parsed | {total} |",
        f"| Passed friction filter | {len(friction)} ({100*len(friction)//max(total,1)}%) |",
        f"| Labeled by LLM | {agg['total_labeled']} |",
    ]

    oc = agg["outcomes"]
    for outcome, count in sorted(oc.items()):
        lines.append(f"| Outcome: {outcome} | {count} |")

    lines += ["", "---", "", "## Top Failure Modes (by count)", ""]
    if agg["top_by_count"]:
        lines.append("| Root Cause | Count |")
        lines.append("|------------|-------|")
        for rc, cnt in agg["top_by_count"]:
            if rc and rc != "none":
                lines.append(f"| {rc} | {cnt} |")
    else:
        lines.append("_No friction sessions found._")

    lines += ["", "## Highest-Cost Failure Modes (avg rework cycles)", ""]
    if agg["top_by_cost"]:
        lines.append("| Root Cause | Avg Rework | Count |")
        lines.append("|------------|-----------|-------|")
        for rc, avg, cnt in agg["top_by_cost"][:8]:
            lines.append(f"| {rc} | {avg:.1f} | {cnt} |")
    else:
        lines.append("_No data._")

    lines += ["", "## Communication Antipatterns", ""]
    if agg["antipatterns"]:
        lines.append("| Antipattern | Sessions |")
        lines.append("|-------------|---------|")
        for ap, cnt in agg["antipatterns"]:
            lines.append(f"| {ap} | {cnt} |")
    else:
        lines.append("_None detected._")

    lines += ["", "## Rule Violations", ""]
    if agg["rule_violations"]:
        lines.append("| Rule | Violations |")
        lines.append("|------|-----------|")
        for rv, cnt in agg["rule_violations"]:
            lines.append(f"| {rv} | {cnt} |")
    else:
        lines.append("_None detected._")

    lines += ["", "## Verification Levels", ""]
    vl_order = ["ran-tests-and-checked-output", "ran-tests", "verbal-claim-only", "none"]
    vc = agg["verification_counts"]
    total_labeled = agg["total_labeled"] or 1
    lines.append("| Level | Count | % |")
    lines.append("|-------|-------|---|")
    for vl in vl_order:
        cnt = vc.get(vl, 0)
        lines.append(f"| {vl} | {cnt} | {100*cnt//total_labeled}% |")

    lines += ["", "## Codebase Awareness", ""]
    aw_order = ["strong", "adequate", "weak", "oblivious"]
    ac = agg["awareness_counts"]
    lines.append("| Level | Count | % |")
    lines.append("|-------|-------|---|")
    for aw in aw_order:
        cnt = ac.get(aw, 0)
        lines.append(f"| {aw} | {cnt} | {100*cnt//total_labeled}% |")

    lines += ["", "---", "", "## Proposed CLAUDE.md Deltas", ""]
    lines.append(
        "> These are *candidates* based on the analysis above.\n"
        "> Each one needs a human decision: accept / reject / reword.\n"
    )

    # Auto-generate candidates from top findings
    candidates = []
    for rc, cnt in agg["top_by_count"][:3]:
        if rc and rc != "none" and cnt >= 3:
            candidates.append(f"- [ ] **{rc}** ({cnt} sessions) — add or sharpen a rule targeting this failure mode.")
    for ap, cnt in agg["antipatterns"][:3]:
        if cnt >= 3:
            candidates.append(f"- [ ] **{ap}** ({cnt} sessions) — add an anti-pattern rule to CLAUDE.md.")
    for rv, cnt in agg["rule_violations"][:3]:
        if cnt >= 2:
            candidates.append(f"- [ ] **{rv}** ({cnt} violations) — review whether the existing rule is clear enough or needs strengthening.")

    if candidates:
        lines.extend(candidates)
    else:
        lines.append("_No high-frequency patterns reached the threshold for a rule proposal._")

    if agg["sample_corrections"]:
        lines += ["", "### Sample corrections (redacted, truncated)", ""]
        for c in agg["sample_corrections"][:10]:
            if c:
                lines.append(f"- {redact(c)[:160]}")

    if agg["sample_positives"]:
        lines += ["", "### Positive signals (redacted, truncated)", ""]
        for p in agg["sample_positives"][:10]:
            if p:
                lines.append(f"- {redact(p)[:160]}")

    lines += ["", "---", "", "## Per-Session Detail", ""]
    lines.append("| Session | Outcome | Root Cause | Rework | Verified |")
    lines.append("|---------|---------|-----------|--------|---------|")
    for lb in sorted(labels, key=lambda x: -(x.get("reworkCycles") or 0)):
        raw_sid = lb.get("_session_id", "?")
        sid = hashlib.sha256(raw_sid.encode()).hexdigest()[:8]
        outcome = lb.get("outcome", "?")
        rc = lb.get("rootCauseArchetype", "?")
        rework = lb.get("reworkCycles", 0)
        vl = lb.get("verificationLevel", "?")
        lines.append(f"| `{sid}` | {outcome} | {rc} | {rework} | {vl} |")

    lines.append("")
    output_path.write_text("\n".join(lines))
    print(f"\nReport written to: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--project", metavar="PATH",
                    help="Path to the Claude project directory (auto-detected from CWD if omitted)")
    ap.add_argument("--all", action="store_true",
                    help="Analyze every project under ~/.claude/projects/")
    ap.add_argument("--n", type=int, default=DEFAULT_N, metavar="N",
                    help=f"Last N sessions per project (default: {DEFAULT_N})")
    ap.add_argument("--output", metavar="FILE", default=DEFAULT_OUTPUT,
                    help=f"Output report path (default: {DEFAULT_OUTPUT})")
    ap.add_argument("--dry-run", action="store_true",
                    help="Parse and filter only — no API calls, no report written")
    ap.add_argument("--no-label", action="store_true",
                    help="Skip the LLM labeling step entirely. Produces a heuristic-only report with no data leaving the machine.")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help=f"Anthropic model for labeling (default: {DEFAULT_MODEL})")
    args = ap.parse_args()

    # Resolve project dirs
    if args.all:
        project_dirs = list_project_dirs()
        if not project_dirs:
            print(f"error: no project dirs found under {CLAUDE_PROJECTS}", file=sys.stderr)
            return 2
    elif args.project:
        project_dirs = [Path(args.project)]
    else:
        detected = detect_project_dir(ROOT)
        if not detected:
            # Fallback: let user know
            print("Could not auto-detect project dir. Specify --project or --all.", file=sys.stderr)
            print(f"Expected something under {CLAUDE_PROJECTS}", file=sys.stderr)
            return 2
        project_dirs = [detected]

    # Load sessions
    all_sessions: list[dict] = []
    for pdir in project_dirs:
        print(f"Loading sessions from {pdir.name}…")
        sessions = load_sessions(pdir, args.n)
        print(f"  {len(sessions)} sessions loaded")
        all_sessions.extend(sessions)

    if not all_sessions:
        print("No sessions found.")
        return 0

    # Pre-filter
    friction, clean = pre_filter(all_sessions)
    print(f"\nPre-filter: {len(friction)} friction sessions, {len(clean)} clean (dropped)")

    if args.dry_run:
        print("\nDry-run mode — stopping before API calls.")
        print("Friction sessions:")
        for s in friction:
            sid = hashlib.sha256(s["session_id"].encode()).hexdigest()[:8]
            user_texts = " | ".join(redact(t["text"])[:80] for t in s["user_turns"][:2])
            print(f"  {sid}  {user_texts}")
        return 0

    if not friction:
        print("No friction sessions — nothing to label. All sessions look clean.")
        return 0

    if args.no_label:
        print("\n--no-label mode: skipping API calls. Writing heuristic-only report.")
        output_path = Path(args.output)
        empty_agg = aggregate([])
        write_report(empty_agg, [], friction, clean, output_path)
        return 0

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("error: ANTHROPIC_API_KEY not set in environment", file=sys.stderr)
        return 2

    # Import anthropic (checked at runtime so --dry-run works without it)
    try:
        import anthropic as anthropic_sdk
    except ImportError:
        print("error: anthropic package not installed. Run: pip install anthropic", file=sys.stderr)
        return 2

    client = anthropic_sdk.Anthropic(api_key=api_key)

    # Label
    print(f"\nLabeling {len(friction)} sessions with {args.model}…")
    labels = label_batch(friction, client)

    if not labels:
        print("No labels produced.")
        return 1

    # Aggregate
    agg = aggregate(labels)

    # Write report
    output_path = Path(args.output)
    write_report(agg, labels, friction, clean, output_path)

    # Quick summary to stdout
    print("\nTop failure modes:")
    for rc, cnt in agg["top_by_count"][:5]:
        if rc and rc != "none":
            print(f"  {rc}: {cnt}")
    print("\nTop rule violations:")
    for rv, cnt in agg["rule_violations"][:5]:
        print(f"  {rv}: {cnt}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
