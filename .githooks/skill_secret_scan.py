#!/usr/bin/env python3
"""skill_secret_scan.py — fail-closed secret/client-confidential gate for skill propagation.

WHY: the codex-skill-sync sweep propagates skills source -> install roots on a
TIMER, unattended, and skills get seeded/promoted ACROSS repos — including into
and out of client repos (LJB). A skill that carries a live credential or a
client-confidential marker would be spread everywhere. Nothing checked for that.
This is the gate: scan a skill tree before it is copied into another repo, before
it is promoted into the canonical source, and (as a standing check) across all
skills via skill_coverage_audit.py.

Two severities, both block by default (exit 1):
  SECRET     a live-looking credential VALUE (Anthropic/OpenAI/AWS/GitHub/Google/
             Slack/GitLab keys, private keys, JWTs, live access links).
  SENSITIVE  a client-confidential MARKER — not necessarily a value, but auth
             internals / identity headers / client invite links that must not
             leave the client repo even as a reference. Seeded from LJB's
             .claude/security-patterns.yaml and best-effort re-read from it at
             runtime so this gate inherits LJB's evolving client-secret list.
  SCOPE      a repo-owned orchestration marker that must not be promoted into
             the shared/global skills source and then propagated into client repos.

Pure stdlib; safe from bare cron / git hooks. Placeholder-guarded to avoid
flagging YOUR-KEY-HERE / EXAMPLE / REDACTED docs.

Usage:
  python3 bin/skill_secret_scan.py <path> [<path> ...]   # scan dirs/files
  python3 bin/skill_secret_scan.py --json <path>
  # exit 0 clean, 1 if any SECRET/SENSITIVE finding, 2 on usage error
Importable:
  from skill_secret_scan import scan_tree   # -> list[dict] findings
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LJB_PATTERNS_YAML = Path.home() / "Desktop" / "LJB" / ".claude" / "security-patterns.yaml"

# --- SECRET: live credential VALUE shapes. Length-guarded to clear placeholders. -
SECRET_PATTERNS = [
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_-]{24,}")),
    ("openai_proj_key", re.compile(r"sk-proj-[A-Za-z0-9_-]{24,}")),
    ("openai_legacy_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    ("resend_key", re.compile(r"\bre_[A-Za-z0-9]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_pat_classic", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    ("github_pat_fine", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("gitlab_pat", re.compile(r"\bglpat-[A-Za-z0-9_-]{20}")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("live_qbo_invite", re.compile(r"accounts\.intuit\.com/app/invite/accept")),
    ("generic_assignment", re.compile(
        r"(?i)(?:api[_-]?key|secret|passwd|password|access[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*['\"][A-Za-z0-9/+_-]{20,}['\"]")),
]

# --- SENSITIVE: client-confidential markers (seeded from LJB security-patterns.yaml). -
SENSITIVE_SUBSTRINGS = {
    "PORTAL_WRITE_KEY", "x-portal-key", "x-slg-admin-id", "x-slg-verified-user",
    "ANTHROPIC_ADMIN_KEY", "GITHUB_TOKEN",
}

SCOPE_SUBSTRINGS = {
    "builder-pagecraft-html",
    "Builder Pagecraft HTML",
    ".builder/skills/builder-pagecraft-html",
    ".builderrules",
}

SCOPE_DOC_ALLOWLIST = {"README.md", "CONTRIBUTING.md", "SECURITY.md"}

# Lines that are clearly placeholders/docs, not live material.
PLACEHOLDER = re.compile(r"(?i)YOUR[_-]?|EXAMPLE|REDACTED|PLACEHOLDER|XXXX|\.\.\.|<[a-z_]+>|FAKE|DUMMY|TEST[_-]?KEY")
_KEY_PREFIX = re.compile(r"(?i)^(sk-ant-|sk-proj-|sk-|re_|AKIA|ghp_|github_pat_|AIza|glpat-|xox[baprs]-)")
_SEQ_ALPHA = "abcdefghijklmnopqrstuvwxyz" * 2
_SEQ_NUM = "0123456789" * 4


def _looks_fake(matched: str) -> bool:
    """True for low-entropy fixtures (sequential alphabet, runs, repeated chars)
    so test fixtures like 'sk-ant-abcdefghijklmnopqrstuvwxyz' don't trip the gate
    while real high-entropy keys still do."""
    body = _KEY_PREFIX.sub("", matched).strip("'\"").lower()
    if len(set(body)) <= 4:                      # e.g. AAAA…, xxxx…
        return True
    if body and (body in _SEQ_ALPHA or body in _SEQ_NUM):   # the literal alphabet/digits
        return True
    if "abcdefghij" in body or "0123456789" in body:        # embedded sequential run
        return True
    return False
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".mp4", ".woff", ".woff2", ".ico", ".webp"}
MAX_BYTES = 1_000_000


def _load_ljb_sensitive() -> set[str]:
    """Best-effort: re-read LJB's security-patterns.yaml substrings so the gate
    inherits its evolving client-secret list. No yaml dependency — line regex."""
    extra: set[str] = set()
    if not LJB_PATTERNS_YAML.exists():
        return extra
    try:
        text = LJB_PATTERNS_YAML.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"substrings:\s*\[([^\]]*)\]", text):
            for tok in re.findall(r"['\"]([^'\"]+)['\"]", m.group(1)):
                if len(tok) >= 6 and not tok.startswith("sk-ant") and tok != "AKIA":
                    extra.add(tok)  # key shapes already covered by SECRET_PATTERNS
    except Exception:
        pass
    return extra


def scan_text(path: Path, text: str, sensitive: set[str]) -> list[dict]:
    findings: list[dict] = []
    allow_scope_docs = path.name in SCOPE_DOC_ALLOWLIST
    for i, line in enumerate(text.splitlines(), 1):
        if PLACEHOLDER.search(line):
            continue
        for name, rx in SECRET_PATTERNS:
            m = rx.search(line)
            if m and not _looks_fake(m.group(0)):
                findings.append({"severity": "SECRET", "rule": name, "file": str(path), "line": i})
        for sub in sensitive:
            if sub in line:
                findings.append({"severity": "SENSITIVE", "rule": sub, "file": str(path), "line": i})
        for sub in SCOPE_SUBSTRINGS:
            if sub in line and not allow_scope_docs:
                findings.append({"severity": "SCOPE", "rule": sub, "file": str(path), "line": i})
    return findings


def scan_tree(root: Path, sensitive: set[str] | None = None) -> list[dict]:
    """Scan a file or directory tree; return list of findings."""
    if sensitive is None:
        sensitive = SENSITIVE_SUBSTRINGS | _load_ljb_sensitive()
    root = Path(root)
    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]
    out: list[dict] = []
    for f in files:
        if f.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            if f.stat().st_size > MAX_BYTES:
                continue
            text = f.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable -> skip
        out.extend(scan_text(f, text, sensitive))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan skill trees for secrets / client-confidential markers.")
    ap.add_argument("paths", nargs="+", help="files or directories to scan")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    sensitive = SENSITIVE_SUBSTRINGS | _load_ljb_sensitive()
    all_findings: list[dict] = []
    for p in args.paths:
        all_findings.extend(scan_tree(Path(p), sensitive))

    if args.json:
        print(json.dumps(all_findings, indent=2))
    elif not all_findings:
        print("✅ clean — no secrets or client-confidential markers")
    else:
        for f in all_findings:
            print(f"{f['severity']:9} {f['rule']:24} {f['file']}:{f['line']}")
        secrets = sum(1 for f in all_findings if f["severity"] == "SECRET")
        sensitive_count = sum(1 for f in all_findings if f["severity"] == "SENSITIVE")
        scope_count = sum(1 for f in all_findings if f["severity"] == "SCOPE")
        print(f"\n⛔ {len(all_findings)} finding(s): {secrets} SECRET, {sensitive_count} SENSITIVE, {scope_count} SCOPE")
    return 1 if all_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
