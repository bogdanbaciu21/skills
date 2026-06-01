import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_token_integrity.py"
spec = importlib.util.spec_from_file_location("check_token_integrity", CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class BogdanBrandFixtureTests(unittest.TestCase):
    def test_token_integrity_checker_passes_packaged_assets(self):
        self.assertEqual([], checker.check(ROOT))

    def test_screenshot_contract_matches_public_safe_fixtures(self):
        fixture_dir = ROOT / "fixtures" / "brand-regression"
        contract = json.loads((fixture_dir / "screenshot-contract.json").read_text(encoding="utf-8"))

        self.assertEqual(["desktop", "mobile"], [v["name"] for v in contract["viewports"]])
        for fixture in contract["fixtures"]:
            html = (fixture_dir / fixture["file"]).read_text(encoding="utf-8")
            for needle in fixture["must_contain"]:
                self.assertIn(needle, html)
            for needle in fixture["must_not_contain"]:
                self.assertNotIn(needle, html)

    def test_reskin_example_has_no_placeholders(self):
        manifest = json.loads((ROOT / "reskin.example.json").read_text(encoding="utf-8"))
        encoded = json.dumps(manifest)

        self.assertNotIn("TBU", encoded)
        self.assertEqual("assets/bogdan-brand", manifest["assets_target"])
        self.assertEqual("data-brand=\"bogdan-baciu\"", manifest["framed_marker"])


if __name__ == "__main__":
    unittest.main()
