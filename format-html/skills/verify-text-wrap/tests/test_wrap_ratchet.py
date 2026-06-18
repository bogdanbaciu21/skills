import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "runner.py"
WRATCHET = ROOT / "wrap-ratchet.py"

runner_spec = importlib.util.spec_from_file_location("verify_text_wrap_runner", RUNNER)
runner = importlib.util.module_from_spec(runner_spec)
runner_spec.loader.exec_module(runner)

ratchet_spec = importlib.util.spec_from_file_location("wrap_ratchet", WRATCHET)
wrap_ratchet = importlib.util.module_from_spec(ratchet_spec)
ratchet_spec.loader.exec_module(wrap_ratchet)


class WrapRatchetTests(unittest.TestCase):
    def sample_report_path(self, tmpdir):
        reports = [
            {
                "page": "management-cockpit.html",
                "viewport": {"name": "desktop", "width": 1280, "height": 900},
                "findings_new": [
                    {
                        "kind": "clipped-text",
                        "selector": "div.workbook-wrap",
                        "textPreview": "portal only status",
                    }
                ],
                "findings_known": 0,
                "edge_failure": None,
            },
            {
                "page": "management-cockpit.html",
                "viewport": {"name": "mobile", "width": 390, "height": 844},
                "findings_new": [
                    {
                        "kind": "clipped-text",
                        "selector": "div.workbook-wrap",
                        "textPreview": "portal only status",
                    }
                ],
                "findings_known": 0,
                "edge_failure": None,
            },
        ]
        repeated = runner._collect_repeated_failures(reports)
        payload = {
            "schema_version": 1,
            "summary": {"repeated_failures": len(repeated)},
            "ratchet": {
                "mode": "same-fingerprint-across-viewports",
                "repeated_failures": repeated,
            },
            "reports": reports,
        }
        path = Path(tmpdir) / "report.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_first_seen_failure_records_without_cross_run_repeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = self.sample_report_path(tmp)
            history = Path(tmp) / "history.json"
            self.assertEqual(0, wrap_ratchet.run_check(str(report), str(history)))
            stored = json.loads(history.read_text(encoding="utf-8"))
            self.assertEqual(1, len(stored["fingerprints"]))

    def test_second_run_with_same_fingerprint_is_cross_run_repeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = self.sample_report_path(tmp)
            history = Path(tmp) / "history.json"
            self.assertEqual(0, wrap_ratchet.run_check(str(report), str(history)))
            self.assertEqual(1, wrap_ratchet.run_check(str(report), str(history)))

    def test_in_run_repeated_failures_are_exposed_from_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = self.sample_report_path(tmp)
            payload = json.loads(report.read_text(encoding="utf-8"))
            repeated = wrap_ratchet._in_run_repeats(payload)
            self.assertEqual(1, len(repeated))
            self.assertEqual("clipped-text", repeated[0]["kind"])


if __name__ == "__main__":
    unittest.main()
