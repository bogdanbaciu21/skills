#!/usr/bin/env python3
"""Validate a parallel-dispatch track plan.

Input JSON/YAML shape:
{
  "tracks": [
    {
      "name": "Track A",
      "type": "code",
      "goal": "...",
      "evidence": ["failing test ..."],
      "can_touch": ["src/a.py"],
      "cannot_touch": ["src/b.py"],
      "dependencies": []
    }
  ]
}
"""

import argparse
import fnmatch
import json
import sys


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def overlaps(a, b):
    if a == b:
        return True
    return fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a)


def has_dependency(a, b):
    deps_a = set(as_list(a.get("dependencies")))
    deps_b = set(as_list(b.get("dependencies")))
    return b.get("name") in deps_a or a.get("name") in deps_b


def parse_scalar(value):
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
    if value in {"[]", "{}"}:
        return [] if value == "[]" else {}
    return value.strip("'\"")


def parse_simple_yaml(text):
    """Parse the small YAML subset used for track plans when PyYAML is absent."""
    tracks = []
    current = None
    active_list_key = None
    in_tracks = False

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()

        if indent == 0 and line == "tracks:":
            in_tracks = True
            continue
        if not in_tracks:
            continue

        if line.startswith("- "):
            rest = line[2:].strip()
            if indent <= 2 and (":" in rest or current is None):
                current = {}
                tracks.append(current)
                active_list_key = None
                if rest:
                    key, value = rest.split(":", 1)
                    current[key.strip()] = parse_scalar(value)
                continue
            if current is not None and active_list_key:
                current.setdefault(active_list_key, []).append(parse_scalar(rest))
                continue

        if current is not None and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                current[key] = parse_scalar(value)
                active_list_key = None
            else:
                current[key] = []
                active_list_key = key

    return {"tracks": tracks}


def load_plan(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if path.endswith(".json"):
        return json.loads(text)
    try:
        import yaml
    except ImportError:
        return parse_simple_yaml(text)
    return yaml.safe_load(text)


BROAD_GLOBS = {"**", "**/*", "src/**", "app/**", "bin/**"}


def is_broad_glob(pattern):
    normalized = pattern.strip().rstrip("/")
    return normalized in BROAD_GLOBS or normalized.endswith("/**")


def broad_glob_errors(tracks):
    errors = []
    code_tracks = [t for t in tracks if t.get("type", "code") != "analysis"]
    for track in code_tracks:
        name = track.get("name") or "unnamed"
        broad = [p for p in as_list(track.get("can_touch")) if is_broad_glob(p)]
        if broad:
            errors.append(
                f"{name}: can_touch uses broad glob(s) {', '.join(repr(b) for b in broad)}; narrow scope or mark landing_mode serial with single owner"
            )
    owners = {}
    for track in code_tracks:
        for pattern in as_list(track.get("can_touch")):
            if is_broad_glob(pattern):
                owners.setdefault(pattern, []).append(track.get("name") or "unnamed")
    for pattern, names in owners.items():
        if len(names) > 1:
            errors.append(
                f"multiple tracks claim broad glob {pattern!r}: {', '.join(names)}"
            )
    return errors


def validate(plan):
    errors = []
    tracks = plan.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        return ["tracks must be a non-empty list"]

    for i, track in enumerate(tracks):
        name = track.get("name") or f"tracks[{i}]"
        track_type = track.get("type", "code")
        can_touch = as_list(track.get("can_touch"))
        evidence = as_list(track.get("evidence")) or ([track.get("goal")] if track.get("goal") else [])

        if not track.get("name"):
            errors.append(f"{name}: name is required")
        if track_type not in {"code", "analysis"}:
            errors.append(f"{name}: type must be code or analysis")
        if not evidence:
            errors.append(f"{name}: missing goal/evidence")
        if track_type != "analysis" and not can_touch:
            errors.append(f"{name}: code tracks need can_touch file scope")

    code_tracks = [t for t in tracks if t.get("type", "code") != "analysis"]
    for i, left in enumerate(code_tracks):
        for right in code_tracks[i + 1:]:
            for lp in as_list(left.get("can_touch")):
                for rp in as_list(right.get("can_touch")):
                    if overlaps(lp, rp) and not has_dependency(left, right):
                        errors.append(
                            f"{left.get('name')} and {right.get('name')}: overlapping can_touch scope {lp!r} vs {rp!r} without dependency"
                        )
            shared_left = set(as_list(left.get("shared_state")))
            shared_right = set(as_list(right.get("shared_state")))
            shared = sorted(shared_left & shared_right)
            if shared and not has_dependency(left, right):
                errors.append(
                    f"{left.get('name')} and {right.get('name')}: shared state {', '.join(shared)} without dependency"
                )

    errors.extend(broad_glob_errors(tracks))

    return errors


def main():
    ap = argparse.ArgumentParser(description="Validate a parallel-dispatch track JSON/YAML plan.")
    ap.add_argument("plan")
    args = ap.parse_args()

    plan = load_plan(args.plan)
    if not isinstance(plan, dict):
        plan = {}
    errors = validate(plan)
    if errors:
        print("parallel-dispatch plan is not safe:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("parallel-dispatch plan ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
