import importlib.util
import contextlib
import io
import json
import shutil
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
