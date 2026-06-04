#!/usr/bin/env python3
"""Tests for the no-mutate SkillOpt pilot harness."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import skillopt_pilot  # noqa: E402


class SkillOptPilotTests(unittest.TestCase):
    def write_benchmark(self, path: Path) -> None:
        task = {
            "task_id": "quality-001",
            "description": "Purpose section is concrete",
            "checks": [
                {"op": "section_present", "arg": "Purpose"},
                {"op": "section_contains", "section": "Purpose", "arg": "specific operating procedure"},
            ],
            "patches": [
                {
                    "op": "replace_section",
                    "heading": "Purpose (TBU)",
                    "new_heading": "Purpose",
                    "content": "Use this as a specific operating procedure for repeatable work.",
                }
            ],
        }
        path.write_text(json.dumps(task) + "\n", encoding="utf-8")

    def test_proposal_improves_score_without_mutating_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "SKILL.md"
            bench = root / "bench.jsonl"
            out_dir = root / "out"
            skill.write_text(
                "---\nname: demo\ndescription: TBU\n---\n\n# Demo\n\n## Purpose (TBU)\n\n[your copy here]\n",
                encoding="utf-8",
            )
            self.write_benchmark(bench)

            with redirect_stdout(StringIO()):
                rc = skillopt_pilot.main([
                    "--skill", str(skill),
                    "--benchmark", str(bench),
                    "--out-dir", str(out_dir),
                ])

            self.assertEqual(0, rc)
            original = skill.read_text(encoding="utf-8")
            proposed = (out_dir / "proposed.md").read_text(encoding="utf-8")
            receipt = json.loads((out_dir / "receipt.json").read_text(encoding="utf-8"))

            self.assertIn("description: TBU", original)
            self.assertIn("description: TBU", proposed)
            self.assertFalse(receipt["frontmatter_mutated"])
            self.assertGreater(receipt["proposed_score"], receipt["baseline_score"])

    def test_held_out_overlap_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "SKILL.md"
            bench = root / "bench.jsonl"
            held = root / "held.jsonl"
            skill.write_text("---\nname: demo\n---\n\n# Demo\n", encoding="utf-8")
            self.write_benchmark(bench)
            held.write_text(bench.read_text(encoding="utf-8"), encoding="utf-8")

            with self.assertRaises(SystemExit), redirect_stdout(StringIO()):
                skillopt_pilot.main([
                    "--skill", str(skill),
                    "--benchmark", str(bench),
                    "--held-out", str(held),
                    "--check-only",
                ])


if __name__ == "__main__":
    unittest.main()
