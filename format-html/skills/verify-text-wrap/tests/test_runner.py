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
    def repeated_failure_reports(self):
        viewports = [
            {"name": "desktop", "width": 1280, "height": 900},
            {"name": "mobile", "width": 390, "height": 844},
        ]
        return [
            {
                "page": "management-cockpit.html",
                "viewport": viewports[0],
                "findings_new": [
                    {
                        "kind": "heading-many-lines",
                        "tag": "h1",
                        "cls": "hero-title",
                        "cellWidth": 288,
                        "textLines": 4,
                        "textPreview": "Acme Management Cockpit",
                    },
                    {
                        "kind": "typography-anti-pattern",
                        "selector": "p.sub",
                        "rules": ["text-wrap:balance"],
                        "textPreview": "downloadable as Excel",
                    },
                    {
                        "kind": "dense-prose-in-narrow-column",
                        "selector": "p.note",
                        "textPreview": "A long card note trapped in a narrow column after the grid collapsed.",
                    },
                ],
                "findings_known": 0,
                "edge_failure": {
                    "spread": 84,
                    "rightEdges": [520, 604],
                    "counts": {"520": 2, "604": 5},
                    "samplesByEdge": {},
                },
            },
            {
                "page": "management-cockpit.html",
                "viewport": viewports[1],
                "findings_new": [
                    {
                        "kind": "heading-many-lines",
                        "tag": "h1",
                        "cls": "hero-title",
                        "cellWidth": 242,
                        "textLines": 4,
                        "textPreview": "Acme Management Cockpit",
                    },
                    {
                        "kind": "typography-anti-pattern",
                        "selector": "p.sub",
                        "rules": ["text-wrap:balance"],
                        "textPreview": "downloadable as Excel",
                    },
                    {
                        "kind": "dense-prose-in-narrow-column",
                        "selector": "p.note",
                        "textPreview": "A long card note trapped in a narrow column after the grid collapsed.",
                    },
                ],
                "findings_known": 0,
                "edge_failure": {
                    "spread": 72,
                    "rightEdges": [304, 376],
                    "counts": {"304": 3, "376": 4},
                    "samplesByEdge": {},
                },
            },
            {
                "page": "final-vendor-table.html",
                "viewport": viewports[0],
                "findings_new": [
                    {
                        "kind": "element-horizontal-overflow",
                        "selector": "table#vendor-roi",
                        "overflowPx": 96,
                        "textPreview": "Vendor ROI table",
                    },
                    {
                        "kind": "clipped-text",
                        "selector": "p.status-strip",
                        "hiddenY": 24,
                        "textPreview": "Portal only status",
                    },
                ],
                "findings_known": 0,
                "edge_failure": None,
            },
            {
                "page": "final-vendor-table.html",
                "viewport": viewports[1],
                "findings_new": [
                    {
                        "kind": "element-horizontal-overflow",
                        "selector": "table#vendor-roi",
                        "overflowPx": 96,
                        "textPreview": "Vendor ROI table",
                    },
                    {
                        "kind": "clipped-text",
                        "selector": "p.status-strip",
                        "hiddenY": 24,
                        "textPreview": "Portal only status",
                    },
                ],
                "findings_known": 0,
                "edge_failure": None,
            },
        ]

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
            self.assertEqual(1, report["summary"]["checks"])
            self.assertEqual(0, report["summary"]["failures"])
            self.assertEqual({}, report["summary"]["failure_types"])
            self.assertEqual(0, report["summary"]["repeated_failures"])
            self.assertIn("ratchet", report)
            self.assertEqual("index.html", report["reports"][0]["page"])

    def test_repeated_failure_ratchet_covers_recent_page_types(self):
        repeated = runner._collect_repeated_failures(self.repeated_failure_reports())

        kinds = {item["kind"] for item in repeated}
        self.assertIn("heading-many-lines", kinds)
        self.assertIn("dense-prose-in-narrow-column", kinds)
        self.assertIn("element-horizontal-overflow", kinds)
        self.assertIn("clipped-text", kinds)
        self.assertIn("typography-anti-pattern", kinds)
        self.assertIn("right-edge-alignment", kinds)
        self.assertTrue(all(item["count"] == 2 for item in repeated))
        self.assertTrue(all(item["viewports"] == ["desktop", "mobile"] for item in repeated))

    def test_ratchet_requires_more_than_one_viewport(self):
        reports = [
            {
                "page": "index.html",
                "viewport": {"name": "mobile", "width": 390, "height": 844},
                "findings_new": [
                    {
                        "kind": "element-horizontal-overflow",
                        "selector": "table#dense",
                        "overflowPx": 40,
                        "textPreview": "Dense table",
                    },
                    {
                        "kind": "element-horizontal-overflow",
                        "selector": "table#dense",
                        "overflowPx": 40,
                        "textPreview": "Dense table",
                    },
                ],
                "findings_known": 0,
                "edge_failure": None,
            }
        ]

        self.assertEqual([], runner._collect_repeated_failures(reports))

    def test_json_report_includes_failure_taxonomy_and_ratchet(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            runner._write_json_report(str(path), self.repeated_failure_reports())

            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(4, report["summary"]["checks"])
            self.assertEqual(4, report["summary"]["failures"])
            self.assertEqual(6, report["summary"]["repeated_failures"])
            self.assertEqual("same-fingerprint-across-viewports", report["ratchet"]["mode"])
            self.assertEqual(
                {
                    "clipped-text": 2,
                    "dense-prose-in-narrow-column": 2,
                    "element-horizontal-overflow": 2,
                    "heading-many-lines": 2,
                    "right-edge-alignment": 2,
                    "typography-anti-pattern": 2,
                },
                report["summary"]["failure_types"],
            )

    def test_fixture_known_issues_shape(self):
        data = json.loads((ROOT / "fixtures" / "known-issues.json").read_text(encoding="utf-8"))

        self.assertIn("known", data)
        self.assertIsInstance(data["known"], list)


if __name__ == "__main__":
    unittest.main()
