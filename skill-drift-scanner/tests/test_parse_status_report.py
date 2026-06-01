import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "parse_status_report.py"
spec = importlib.util.spec_from_file_location("parse_status_report", SCRIPT)
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)

RESOLVER = ROOT / "scripts" / "resolve_scanner.py"
resolver_spec = importlib.util.spec_from_file_location("resolve_scanner", RESOLVER)
resolver = importlib.util.module_from_spec(resolver_spec)
resolver_spec.loader.exec_module(resolver)


class ParseStatusReportTests(unittest.TestCase):
    def test_sample_report_matches_expected_summary(self):
        report = (ROOT / "fixtures" / "sample-status-report.txt").read_text(encoding="utf-8")
        expected = json.loads((ROOT / "fixtures" / "expected-summary.json").read_text(encoding="utf-8"))

        self.assertEqual(expected, parser.parse_report(report))

    def test_sync_skills_dry_run_summary(self):
        report = (ROOT / "fixtures" / "sample-sync-dry-run.txt").read_text(encoding="utf-8")
        summary = parser.parse_sync_dry_run(report)

        self.assertTrue(summary["dry_run"])
        self.assertEqual("/Users/example/Desktop/skills", summary["canonical"])
        self.assertEqual(2, len(summary["targets"]))
        self.assertEqual(["handoff", "pagecraft", "quiz-me"], summary["skills"])
        self.assertEqual(6, summary["planned_copies"])

    def test_resolver_prefers_explicit_override(self):
        command = resolver.resolve(
            environ={"CODEX_SKILL_SYNC": "/tmp/custom-sync", "HOME": "/Users/example"},
            which=lambda name: "/usr/local/bin/codex-skill-sync",
        )

        self.assertEqual("/tmp/custom-sync", command)

    def test_resolver_falls_back_to_path_then_home(self):
        self.assertEqual(
            "/opt/bin/codex-skill-sync",
            resolver.resolve(environ={"HOME": "/Users/example"}, which=lambda name: "/opt/bin/codex-skill-sync"),
        )
        self.assertEqual(
            "/Users/example/.local/bin/codex-skill-sync",
            resolver.resolve(environ={"HOME": "/Users/example"}, which=lambda name: None),
        )

    def test_scheduler_health_fixture_contains_required_fields(self):
        text = (ROOT / "fixtures" / "scheduler-health.txt").read_text(encoding="utf-8").lower()

        for needle in ("scheduler health", "last sync", "last report", "restart recommended"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
