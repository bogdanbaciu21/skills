#!/usr/bin/env python3
"""No-mutate SkillOpt-style pilot for local SKILL.md files.

This is a deliberately conservative Track 0 harness:

- score the skill document against deterministic benchmark requirements;
- apply curated, benchmark-owned section patches to a copy of the body only;
- write proposed.md + receipt.json for human review;
- never mutate SKILL.md and never change YAML frontmatter.

The goal is to prove the control loop before adding live agent rollouts or LLM
judges.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)


@dataclass(frozen=True)
class CheckResult:
    op: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class TaskResult:
    task_id: str
    description: str
    score: float
    checks: list[CheckResult]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_frontmatter(text: str) -> tuple[str, str, dict[str, str]]:
    """Return (frontmatter_block, body, simple_frontmatter_map)."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return "", text, {}
    block = match.group(0)
    raw = match.group(1)
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"')
    return block, text[len(block):], meta


def normalize_heading(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lstrip("#").strip()).lower()


def section_bounds(body: str, heading: str) -> tuple[int, int, int, str] | None:
    """Find a markdown section by heading text.

    Returns (heading_start, content_start, section_end, heading_prefix).
    Heading matching is case-insensitive and ignores leading # characters.
    """
    wanted = normalize_heading(heading)
    matches = list(HEADING_RE.finditer(body))
    for idx, match in enumerate(matches):
        prefix, title = match.group(1), match.group(2)
        if normalize_heading(title) != wanted:
            continue
        level = len(prefix)
        end = len(body)
        for next_match in matches[idx + 1:]:
            next_level = len(next_match.group(1))
            if next_level <= level:
                end = next_match.start()
                break
        return match.start(), match.end(), end, prefix
    return None


def extract_section(body: str, heading: str) -> str:
    bounds = section_bounds(body, heading)
    if bounds is None:
        return ""
    _, content_start, section_end, _ = bounds
    return body[content_start:section_end].strip()


def has_section(body: str, heading: str) -> bool:
    return section_bounds(body, heading) is not None


def regex_check(pattern: str, text: str) -> bool:
    try:
        return re.search(pattern, text, re.MULTILINE | re.IGNORECASE) is not None
    except re.error:
        return False


def evaluate_check(check: dict[str, Any], *, full_text: str, body: str, frontmatter: dict[str, str]) -> CheckResult:
    op = str(check.get("op", ""))
    arg = check.get("arg", "")
    target = str(check.get("target", "body"))
    haystack = full_text if target == "full_text" else body

    if op == "contains":
        passed = str(arg) in haystack
        return CheckResult(op, passed, f"contains {arg!r} in {target}")
    if op == "not_contains":
        passed = str(arg) not in haystack
        return CheckResult(op, passed, f"does not contain {arg!r} in {target}")
    if op == "regex":
        passed = regex_check(str(arg), haystack)
        return CheckResult(op, passed, f"matches /{arg}/ in {target}")
    if op == "section_present":
        passed = has_section(body, str(arg))
        return CheckResult(op, passed, f"section present: {arg}")
    if op == "section_contains":
        section = str(check.get("section", ""))
        section_text = extract_section(body, section)
        passed = str(arg) in section_text
        return CheckResult(op, passed, f"section {section!r} contains {arg!r}")
    if op == "section_regex":
        section = str(check.get("section", ""))
        section_text = extract_section(body, section)
        passed = regex_check(str(arg), section_text)
        return CheckResult(op, passed, f"section {section!r} matches /{arg}/")
    if op == "frontmatter_no_tbu":
        value = frontmatter.get(str(arg), "")
        passed = "TBU" not in value
        return CheckResult(op, passed, f"frontmatter {arg!r} has no TBU")
    if op == "max_chars":
        try:
            limit = int(arg)
        except (TypeError, ValueError):
            limit = -1
        passed = limit >= 0 and len(haystack) <= limit
        return CheckResult(op, passed, f"{target} length <= {limit}")

    return CheckResult(op or "unknown", False, f"unknown check op {op!r}")


def evaluate_tasks(skill_text: str, tasks: list[dict[str, Any]]) -> tuple[float, list[TaskResult]]:
    frontmatter_block, body, frontmatter = split_frontmatter(skill_text)
    full_text = frontmatter_block + body
    results: list[TaskResult] = []
    for idx, task in enumerate(tasks, 1):
        checks = task.get("checks", [])
        if not isinstance(checks, list):
            checks = []
        check_results = [
            evaluate_check(c, full_text=full_text, body=body, frontmatter=frontmatter)
            for c in checks
            if isinstance(c, dict)
        ]
        score = (
            sum(1 for c in check_results if c.passed) / len(check_results)
            if check_results else 0.0
        )
        results.append(TaskResult(
            task_id=str(task.get("task_id", f"task-{idx:03d}")),
            description=str(task.get("description", "")),
            score=score,
            checks=check_results,
        ))
    overall = sum(r.score for r in results) / len(results) if results else 0.0
    return overall, results


def replace_section(body: str, heading: str, new_heading: str, content: str) -> tuple[str, str]:
    bounds = section_bounds(body, heading)
    if bounds is None:
        prefix = "##"
        replacement = f"\n{prefix} {new_heading}\n\n{content.strip()}\n"
        return body.rstrip() + "\n" + replacement, f"added missing section {new_heading!r}"
    start, _, end, prefix = bounds
    replacement = f"{prefix} {new_heading}\n\n{content.strip()}\n\n"
    return body[:start] + replacement + body[end:].lstrip("\n"), f"replaced section {heading!r}"


def add_section(body: str, heading: str, content: str, level: int = 2) -> tuple[str, str]:
    if has_section(body, heading):
        return body, f"skipped existing section {heading!r}"
    hashes = "#" * max(1, min(6, level))
    addition = f"\n{hashes} {heading}\n\n{content.strip()}\n"
    return body.rstrip() + "\n" + addition, f"added section {heading!r}"


def replace_text(body: str, target: str, replacement: str) -> tuple[str, str]:
    if not target:
        return body, "skipped empty replace_text target"
    if target not in body:
        return body, "skipped replace_text target not found"
    return body.replace(target, replacement, 1), "replaced text"


def apply_patch(body: str, patch: dict[str, Any]) -> tuple[str, str]:
    op = str(patch.get("op", ""))
    if op == "replace_section":
        return replace_section(
            body,
            str(patch.get("heading", "")),
            str(patch.get("new_heading", patch.get("heading", ""))),
            str(patch.get("content", "")),
        )
    if op == "add_section":
        return add_section(
            body,
            str(patch.get("heading", "")),
            str(patch.get("content", "")),
            int(patch.get("level", 2)),
        )
    if op == "replace_text":
        return replace_text(
            body,
            str(patch.get("target", "")),
            str(patch.get("replacement", "")),
        )
    return body, f"skipped unknown patch op {op!r}"


def propose(skill_text: str, tasks: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    frontmatter_block, body, _frontmatter = split_frontmatter(skill_text)
    baseline_score, baseline_tasks = evaluate_tasks(skill_text, tasks)
    failed_ids = {r.task_id for r in baseline_tasks if r.score < 1.0}
    applied: list[dict[str, Any]] = []

    for task in tasks:
        task_id = str(task.get("task_id", ""))
        if task_id not in failed_ids:
            continue
        patches = task.get("patches", [])
        if not isinstance(patches, list):
            continue
        for patch in patches:
            if not isinstance(patch, dict):
                continue
            before = body
            body, status = apply_patch(body, patch)
            changed = body != before
            applied.append({
                "task_id": task_id,
                "op": patch.get("op", ""),
                "status": status,
                "changed": changed,
            })

    proposed = frontmatter_block + body
    # Avoid returning a byte-for-byte identical proposal when no patch applied.
    _ = baseline_score
    return proposed, applied


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{lineno}: invalid JSONL: {exc}") from exc
        if not isinstance(obj, dict):
            raise SystemExit(f"{path}:{lineno}: each row must be a JSON object")
        tasks.append(obj)
    return tasks


def task_ids(tasks: list[dict[str, Any]]) -> set[str]:
    return {str(t.get("task_id", "")) for t in tasks}


def result_to_dict(result: TaskResult) -> dict[str, Any]:
    return {
        "task_id": result.task_id,
        "description": result.description,
        "score": result.score,
        "checks": [
            {"op": c.op, "passed": c.passed, "detail": c.detail}
            for c in result.checks
        ],
    }


def write_outputs(out_dir: Path, proposed_text: str, receipt: dict[str, Any], *, no_proposed: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if not no_proposed:
        (out_dir / "proposed.md").write_text(proposed_text, encoding="utf-8")
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score and propose review-only SKILL.md improvements.")
    parser.add_argument("--skill", required=True, type=Path, help="Path to SKILL.md")
    parser.add_argument("--benchmark", required=True, type=Path, help="Benchmark JSONL")
    parser.add_argument("--held-out", type=Path, help="Optional held-out JSONL with disjoint task_id values")
    parser.add_argument("--out-dir", type=Path, help="Output directory for proposed.md and receipt.json")
    parser.add_argument("--min-delta", type=float, default=0.05, help="Minimum benchmark improvement to call accepted")
    parser.add_argument("--check-only", action="store_true", help="Score only; do not write proposed.md")
    parser.add_argument("--json", action="store_true", help="Print receipt JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    skill_path: Path = args.skill
    benchmark_path: Path = args.benchmark
    if not skill_path.exists():
        raise SystemExit(f"skill file not found: {skill_path}")
    if not benchmark_path.exists():
        raise SystemExit(f"benchmark file not found: {benchmark_path}")

    skill_text = skill_path.read_text(encoding="utf-8")
    benchmark_tasks = load_jsonl(benchmark_path)
    held_tasks = load_jsonl(args.held_out) if args.held_out else []
    overlap = task_ids(benchmark_tasks) & task_ids(held_tasks)
    if overlap:
        raise SystemExit(f"held-out task_id values overlap benchmark: {', '.join(sorted(overlap)[:5])}")

    baseline_score, baseline_results = evaluate_tasks(skill_text, benchmark_tasks)
    proposed_text, applied = propose(skill_text, benchmark_tasks)
    proposed_score, proposed_results = evaluate_tasks(proposed_text, benchmark_tasks)
    heldout_score = None
    heldout_results: list[TaskResult] = []
    if held_tasks:
        heldout_score, heldout_results = evaluate_tasks(proposed_text, held_tasks)

    accepted = proposed_score >= baseline_score + args.min_delta
    manual_frontmatter = [
        key for key, value in split_frontmatter(skill_text)[2].items()
        if "TBU" in value
    ]
    receipt = {
        "schema_version": 1,
        "tool": "skillopt_pilot",
        "mode": "check_only" if args.check_only else "propose",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill": str(skill_path),
        "benchmark": str(benchmark_path),
        "held_out": str(args.held_out) if args.held_out else None,
        "skill_sha256": sha256_text(skill_text),
        "proposed_sha256": sha256_text(proposed_text),
        "frontmatter_mutated": split_frontmatter(skill_text)[0] != split_frontmatter(proposed_text)[0],
        "baseline_score": baseline_score,
        "proposed_score": proposed_score,
        "delta": proposed_score - baseline_score,
        "min_delta": args.min_delta,
        "accepted_for_review": accepted,
        "manual_frontmatter_fields": manual_frontmatter,
        "applied_patches": applied,
        "baseline_tasks": [result_to_dict(r) for r in baseline_results],
        "proposed_tasks": [result_to_dict(r) for r in proposed_results],
        "heldout_score": heldout_score,
        "heldout_tasks": [result_to_dict(r) for r in heldout_results],
    }

    if not args.check_only:
        out_dir = args.out_dir or skill_path.parent / "skillopt-pilot"
        write_outputs(out_dir, proposed_text, receipt, no_proposed=not accepted)
        receipt["out_dir"] = str(out_dir)
        receipt["proposed_path"] = str(out_dir / "proposed.md") if accepted else None
        # Rewrite receipt with path fields included.
        write_outputs(out_dir, proposed_text, receipt, no_proposed=not accepted)

    if args.json:
        print(json.dumps(receipt, indent=2))
    else:
        print(f"SKILLOPT_PILOT baseline={baseline_score:.3f} proposed={proposed_score:.3f} delta={proposed_score - baseline_score:+.3f} accepted_for_review={accepted}")
        if manual_frontmatter:
            print("MANUAL_FRONTMATTER_FIELDS " + ",".join(manual_frontmatter))
        if not args.check_only:
            print(f"OUT_DIR {receipt.get('out_dir')}")
    return 0 if accepted or args.check_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
