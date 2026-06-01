import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "runner.py"
spec = importlib.util.spec_from_file_location("verify_text_wrap_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class VerifyTextWrapRunnerTests(unittest.TestCase):
    def test_parse_named_and_explicit_viewports(self):
        viewports = runner._parse_viewports(["mobile,800x600"])

        self.assertEqual("mobile", viewports[0]["name"])
        self.assertEqual({"name": "800x600", "width": 800, "height": 600}, viewports[1])

    def test_json_report_schema_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            runner._write_json_report(
                str(path),
                [
                    {
                        "page": "index.html",
                        "viewport": {"name": "mobile", "width": 390, "height": 844},
                        "findings_new": [],
                        "edge_failure": None,
                    }
                ],
            )

            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(1, report["schema_version"])
            self.assertEqual({"checks": 1, "failures": 0}, report["summary"])
            self.assertEqual("index.html", report["reports"][0]["page"])

    def test_fixture_known_issues_shape(self):
        data = json.loads((ROOT / "fixtures" / "known-issues.json").read_text(encoding="utf-8"))

        self.assertIn("known", data)
        self.assertIsInstance(data["known"], list)


if __name__ == "__main__":
    unittest.main()
