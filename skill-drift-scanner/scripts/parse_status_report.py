#!/usr/bin/env python3
"""Parse a codex-skill-sync status report into a compact JSON summary."""

import argparse
import json
import re
import sys
from pathlib import Path


SECTION_NAMES = {
    "missing installed skills": "missing_installed_skills",
    "content drift": "content_drift",
    "unmanaged custom skills": "unmanaged_custom_skills",
}


def parse_report(text):
    summary = {
        "missing_installed_skills": 0,
        "content_drift": 0,
        "unmanaged_custom_skills": 0,
        "codex_restart_recommended": None,
        "report_path": None,
    }
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        key = SECTION_NAMES.get(line.lower().rstrip(":"))
        if key:
            current = key
            continue
        if current and re.match(r"^[-*]\s+\S", line):
            summary[current] += 1
        if "codex restart recommended" in line.lower():
            summary["codex_restart_recommended"] = "yes" in line.lower()
        if "report" in line.lower() and "/" in line:
            match = re.search(r"(/[^ ]+)", line)
            if match:
                summary["report_path"] = match.group(1)
    return summary


def parse_sync_dry_run(text):
    summary = {
        "dry_run": "(dry-run" in text or "[dry-run]" in text,
        "canonical": None,
        "targets": [],
        "skills": [],
        "planned_copies": 0,
    }
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("canonical"):
            summary["canonical"] = line.split(":", 1)[1].strip()
        elif line.startswith("targets"):
            summary["targets"] = line.split(":", 1)[1].split()
        elif line.startswith("skills"):
            summary["skills"] = line.split(":", 1)[1].split()
        elif line.startswith("==>"):
            summary["planned_copies"] += 1
    return summary


def main():
    ap = argparse.ArgumentParser(description="Parse codex-skill-sync status or sync-skills dry-run output.")
    ap.add_argument("report", help="Path to a text report, or '-' for stdin")
    ap.add_argument("--sync-dry-run", action="store_true", help="Parse sync-skills.sh --dry-run output instead of status output")
    args = ap.parse_args()

    text = sys.stdin.read() if args.report == "-" else Path(args.report).read_text(encoding="utf-8")
    parser = parse_sync_dry_run if args.sync_dry_run else parse_report
    print(json.dumps(parser(text), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
