#!/usr/bin/env python3
"""Cross-run repeated-failure ratchet for verify-text-wrap JSON reports.

runner.py already fingerprints failures that repeat across viewports in one run.
This script tracks those fingerprints across successive verification runs so the
same untriaged defect cannot keep cycling through advisory downgrades or one-off
page fixes without surfacing a governed repair signal.

Usage:
    python3 wrap-ratchet.py --check --report /tmp/verify-text-wrap-report.json
    python3 wrap-ratchet.py --check --report report.json --history .wrap-ratchet-history.json
    python3 wrap-ratchet.py --record --report report.json

Exit codes:
    0: no cross-run repeat detected (history updated when --check/--record)
    1: at least one failure fingerprint matches a prior recorded run
    2: operational error (missing report, unreadable history, etc.)
"""
import argparse
import importlib.util
import json
import os
import sys
import time

DEFAULT_HISTORY = ".wrap-ratchet-history.json"
MAX_RUNS_PER_FINGERPRINT = 20


def _load_runner():
    here = os.path.dirname(os.path.abspath(__file__))
    runner_path = os.path.join(here, "runner.py")
    spec = importlib.util.spec_from_file_location("verify_text_wrap_runner", runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import runner helpers from {runner_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _atomic_write(path, payload):
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def _empty_history():
    return {"schema_version": 1, "fingerprints": {}}


def _load_history(path):
    if not os.path.isfile(path):
        return _empty_history()
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise RuntimeError(f"history must be a JSON object: {path}")
    payload.setdefault("schema_version", 1)
    payload.setdefault("fingerprints", {})
    if not isinstance(payload["fingerprints"], dict):
        raise RuntimeError(f"history fingerprints must be an object: {path}")
    return payload


def _report_events(report_payload, runner):
    reports = report_payload.get("reports")
    if not isinstance(reports, list):
        raise RuntimeError("report JSON must include a reports array")
    return runner._failure_events(reports)


def _unique_failure_events(events):
    by_fp = {}
    for event in events:
        fp = event.get("fingerprint")
        if not fp:
            continue
        by_fp.setdefault(fp, event)
    return list(by_fp.values())


def _record_events(history, events, ts):
    fps = history.setdefault("fingerprints", {})
    for event in events:
        fp = event["fingerprint"]
        entry = fps.setdefault(
            fp,
            {
                "kind": event.get("kind", ""),
                "page": event.get("page", ""),
                "selector": event.get("selector", ""),
                "text_key": event.get("text_key", ""),
                "runs": [],
            },
        )
        entry["kind"] = event.get("kind", entry.get("kind", ""))
        entry["page"] = event.get("page", entry.get("page", ""))
        entry["selector"] = event.get("selector", entry.get("selector", ""))
        entry["text_key"] = event.get("text_key", entry.get("text_key", ""))
        runs = entry.setdefault("runs", [])
        runs.append({"ts": ts})
        if len(runs) > MAX_RUNS_PER_FINGERPRINT:
            del runs[:-MAX_RUNS_PER_FINGERPRINT]
    return history


def _cross_run_repeats(history, events):
    fps = history.get("fingerprints", {})
    repeated = []
    for event in _unique_failure_events(events):
        fp = event["fingerprint"]
        prior = fps.get(fp, {})
        prior_runs = prior.get("runs") or []
        if not prior_runs:
            continue
        repeated.append(
            {
                "fingerprint": fp,
                "kind": event.get("kind", prior.get("kind", "")),
                "page": event.get("page", prior.get("page", "")),
                "selector": event.get("selector", prior.get("selector", "")),
                "text_key": event.get("text_key", prior.get("text_key", "")),
                "prior_runs": len(prior_runs),
            }
        )
    return sorted(repeated, key=lambda item: (-item["prior_runs"], item["page"], item["kind"], item["selector"]))


def _in_run_repeats(report_payload):
    ratchet = report_payload.get("ratchet") or {}
    repeated = ratchet.get("repeated_failures") or []
    return repeated if isinstance(repeated, list) else []


def _print_repeats(cross_run, in_run):
    if in_run:
        print(f"[wrap-ratchet] in-run repeated failures: {len(in_run)}")
        for item in in_run[:6]:
            vp = ", ".join(item.get("viewports") or [])
            detail = item.get("text_key") or item.get("selector") or ""
            print(
                f"  {item.get('kind', '?')}: {item.get('page', '?')} "
                f"x{item.get('count', '?')} [{vp}] {detail}"
            )
    if cross_run:
        print(f"[wrap-ratchet] cross-run repeated failures: {len(cross_run)}")
        for item in cross_run[:6]:
            detail = item.get("text_key") or item.get("selector") or ""
            print(
                f"  {item.get('kind', '?')}: {item.get('page', '?')} "
                f"prior_runs={item.get('prior_runs', '?')} {detail}"
            )
        print(
            "[wrap-ratchet] fix the shared component or verification gap; "
            "do not broaden known-issues or advisory downgrades."
        )


def run_check(report_path, history_path, record=True):
    runner = _load_runner()
    report_payload = _load_json(report_path)
    history = _load_history(history_path)
    events = _report_events(report_payload, runner)
    cross_run = _cross_run_repeats(history, events)
    in_run = _in_run_repeats(report_payload)

    if record:
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _record_events(history, _unique_failure_events(events), ts)
        _atomic_write(history_path, history)

    if cross_run:
        _print_repeats(cross_run, in_run)
        return 1
    return 0


def run_record(report_path, history_path):
    runner = _load_runner()
    report_payload = _load_json(report_path)
    history = _load_history(history_path)
    events = _report_events(report_payload, runner)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _record_events(history, _unique_failure_events(events), ts)
    _atomic_write(history_path, history)
    print(
        f"[wrap-ratchet] recorded {len(_unique_failure_events(events))} "
        f"failure fingerprint(s) -> {history_path}"
    )
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, help="Path to runner --json-report output")
    parser.add_argument(
        "--history",
        default=DEFAULT_HISTORY,
        help=f"Cross-run fingerprint history JSON (default: {DEFAULT_HISTORY})",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check",
        action="store_true",
        help="Fail when a current failure fingerprint was seen in a prior run",
    )
    group.add_argument(
        "--record",
        action="store_true",
        help="Append current failure fingerprints to history without failing",
    )
    parser.add_argument(
        "--no-record-on-check",
        action="store_true",
        help="With --check, do not update the history file",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.check:
            return run_check(args.report, args.history, record=not args.no_record_on_check)
        return run_record(args.report, args.history)
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"[wrap-ratchet] ERROR - {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
