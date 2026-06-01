import importlib.util
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


RESKIN_DIR = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

spec = importlib.util.spec_from_file_location("reskin", RESKIN_DIR / "reskin.py")
reskin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reskin)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class ManifestValidationTests(unittest.TestCase):
    def test_accepts_generic_manifest_fixture(self):
        manifest = load_json(FIXTURES / "generic-site" / "reskin.json")

        self.assertIs(reskin.validate_manifest(manifest), manifest)

    def test_rejects_manifest_without_apply_engine(self):
        manifest = load_json(FIXTURES / "manifests" / "invalid-missing-engine.json")

        with self.assertRaisesRegex(reskin.ManifestError, "apply_command or design_system.frame"):
            reskin.validate_manifest(manifest)

    def test_rejects_init_placeholders(self):
        manifest = load_json(FIXTURES / "manifests" / "invalid-placeholder.json")

        with self.assertRaisesRegex(reskin.ManifestError, "design_system.source"):
            reskin.validate_manifest(manifest)


class ApplyCommandTests(unittest.TestCase):
    def test_cmd_apply_reports_invalid_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            shutil.copyfile(
                FIXTURES / "manifests" / "invalid-missing-engine.json",
                repo / "reskin.json",
            )
            out = io.StringIO()

            with contextlib.redirect_stdout(out):
                rc = reskin.cmd_apply(str(repo), SimpleNamespace(page=None, dry_run=True))

            self.assertEqual(1, rc)
            self.assertIn("Invalid reskin.json:", out.getvalue())
            self.assertIn("apply_command or design_system.frame", out.getvalue())

    def test_cmd_validate_checks_manifest_and_referenced_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "generic-site"
            shutil.copytree(FIXTURES / "generic-site", repo)
            out = io.StringIO()

            with contextlib.redirect_stdout(out):
                rc = reskin.cmd_validate(str(repo), SimpleNamespace())

            self.assertEqual(0, rc, out.getvalue())
            self.assertIn("reskin.json valid", out.getvalue())

    def test_bespoke_apply_command_does_not_use_a_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            page = repo / "index.html"
            page.write_text("<body>ok</body>", encoding="utf-8")
            apply_script = repo / "apply.py"
            apply_script.write_text(
                "from pathlib import Path\n"
                "Path('applied.txt').write_text('ran', encoding='utf-8')\n",
                encoding="utf-8",
            )
            manifest = {
                "apply_command": f"{sys.executable} apply.py {{page}} ; touch injected.txt",
            }

            status, note = reskin.bespoke_frame(str(repo), manifest, {"path": "index.html"}, dry=False)

            self.assertEqual("RAN", status, note)
            self.assertTrue((repo / "applied.txt").is_file())
            self.assertFalse((repo / "injected.txt").exists())

    def test_screenshot_diff_fixture_declares_visual_contract(self):
        fixture = load_json(FIXTURES / "screenshot-diff" / "expected-geometry.json")

        self.assertGreaterEqual(len(fixture["viewports"]), 2)
        self.assertEqual("brand-nav", fixture["selectors"][0]["name"])
        self.assertLessEqual(fixture["max_delta_px"], 2)


class GenericInjectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "generic-site"
        shutil.copytree(FIXTURES / "generic-site", self.repo)
        self.manifest = load_json(self.repo / "reskin.json")
        reskin.validate_manifest(self.manifest)

    def tearDown(self):
        self.tmp.cleanup()

    def test_sync_assets_and_generic_frame_injects_templates(self):
        moved = reskin.sync_assets(str(self.repo), self.manifest, dry=False)

        self.assertIn("assets/ -> assets/brand/", moved)
        self.assertIn("colors_and_type.css -> assets/brand/colors_and_type.css", moved)
        self.assertTrue((self.repo / "assets" / "brand" / "logo.txt").is_file())
        self.assertTrue((self.repo / "assets" / "brand" / "colors_and_type.css").is_file())

        status, note = reskin.generic_frame(str(self.repo), self.manifest, self.manifest["pages"][0], dry=False)

        self.assertEqual(("FRAMED", ""), (status, note))
        html = (self.repo / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="brand-nav"', html)
        self.assertIn("The platform", html)
        self.assertIn("One line of deck copy.", html)
        self.assertIn("<span>index.html</span>", html)
        self.assertIn("Original body content should survive the reskin.", html)
        self.assertNotIn("Old nav", html)
        self.assertNotIn("Old headline", html)

    def test_generic_frame_dry_run_does_not_modify_page(self):
        page_path = self.repo / "index.html"
        before = page_path.read_text(encoding="utf-8")

        status, note = reskin.generic_frame(str(self.repo), self.manifest, self.manifest["pages"][0], dry=True)

        self.assertEqual(("FRAMED", ""), (status, note))
        self.assertEqual(before, page_path.read_text(encoding="utf-8"))

    def test_generic_frame_is_idempotent_after_apply(self):
        page = self.manifest["pages"][0]

        first_status, _ = reskin.generic_frame(str(self.repo), self.manifest, page, dry=False)
        second_status, second_note = reskin.generic_frame(str(self.repo), self.manifest, page, dry=False)

        self.assertEqual("FRAMED", first_status)
        self.assertEqual(("SKIP", "already framed"), (second_status, second_note))


if __name__ == "__main__":
    unittest.main()
