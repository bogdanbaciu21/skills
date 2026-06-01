#!/usr/bin/env python3
"""Fixture evals for weekly-update evidence aggregation."""

import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "fake-project"


def summarize_fixture():
    commits = [line for line in (FIXTURE / "git-log.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    issues = json.loads((FIXTURE / "issues.json").read_text(encoding="utf-8"))
    by_state = Counter(issue["state"] for issue in issues)
    by_milestone = Counter((issue.get("milestone") or {}).get("title", "No milestone") for issue in issues)
    return {"commits": len(commits), "by_state": dict(by_state), "by_milestone": dict(by_milestone)}


class WeeklyUpdateEvalTests(unittest.TestCase):
    def test_fake_git_and_issues_fixture_aggregates(self):
        summary = summarize_fixture()

        self.assertEqual(3, summary["commits"])
        self.assertEqual({"CLOSED": 2, "OPEN": 1}, summary["by_state"])
        self.assertEqual({"Reporting": 2, "Operations": 1}, summary["by_milestone"])

    def test_tracker_reference_was_split_out(self):
        ref = (ROOT / "references" / "tracker-providers.md").read_text(encoding="utf-8")
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## GitHub Issues", ref)
        self.assertIn("references/tracker-providers.md", skill)


if __name__ == "__main__":
    unittest.main()
