#!/usr/bin/env python3
"""Eval runner for the parallel-dispatch track validator."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_tracks.py"


def run_plan(plan):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)


def run_plan_text(text, suffix):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"plan{suffix}"
        path.write_text(text, encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)


class ParallelDispatchEvalTests(unittest.TestCase):
    def test_rejects_false_parallelism_from_overlapping_scope(self):
        result = run_plan(
            {
                "tracks": [
                    {"name": "A", "goal": "Fix auth", "evidence": ["test A"], "can_touch": ["src/auth.py"]},
                    {"name": "B", "goal": "Fix login", "evidence": ["test B"], "can_touch": ["src/*.py"]},
                ]
            }
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("overlapping can_touch", result.stdout)

    def test_rejects_missing_evidence(self):
        result = run_plan({"tracks": [{"name": "A", "can_touch": ["src/a.py"]}]})

        self.assertEqual(1, result.returncode)
        self.assertIn("missing goal/evidence", result.stdout)

    def test_accepts_dependent_overlap(self):
        result = run_plan(
            {
                "tracks": [
                    {"name": "A", "goal": "Base change", "evidence": ["test A"], "can_touch": ["src/auth.py"]},
                    {
                        "name": "B",
                        "goal": "Follow-on change",
                        "evidence": ["test B"],
                        "can_touch": ["src/*.py"],
                        "dependencies": ["A"],
                    },
                ]
            }
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_accepts_yaml_plan(self):
        result = run_plan_text(
            """
tracks:
  - name: Analysis
    type: analysis
    goal: Map the evidence first
    evidence:
      - source audit complete
  - name: Code
    type: code
    goal: Patch the CLI
    evidence:
      - failing CLI eval
    can_touch:
      - scripts/validate_tracks.py
""",
            ".yaml",
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_coordinator_playbook_mentions_evidence_and_merge_order(self):
        playbook = (Path(__file__).resolve().parents[1] / "assets" / "coordinator-playbook.md").read_text(encoding="utf-8")

        self.assertIn("evidence", playbook.lower())
        self.assertIn("merge", playbook.lower())


if __name__ == "__main__":
    unittest.main()
