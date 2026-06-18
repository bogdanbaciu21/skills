import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "table-ratchet.py"


def run_ratchet(root, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True,
        text=True,
    )


class TableRatchetTests(unittest.TestCase):
    def test_canonical_wrapped_table_passes_after_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "page.html").write_text(
                '<div class="table-scroll"><table class="content-table"><tr><td>Ok</td></tr></table></div>',
                encoding="utf-8",
            )

            baseline = run_ratchet(
                root,
                "--canonical-table-class",
                "content-table",
                "--canonical-wrapper-class",
                "table-scroll",
                "--write-baseline",
            )
            self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)

            result = run_ratchet(
                root,
                "--canonical-table-class",
                "content-table",
                "--canonical-wrapper-class",
                "table-scroll",
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_baseline_allows_existing_debt_but_blocks_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / "legacy.html"
            page.write_text("<table><tr><td>Legacy</td></tr></table>", encoding="utf-8")

            baseline = run_ratchet(root, "--write-baseline")
            self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)

            clean = run_ratchet(root)
            self.assertEqual(0, clean.returncode, clean.stdout + clean.stderr)

            page.write_text(
                "<table><tr><td>Legacy</td></tr></table><table><tr><td>New debt</td></tr></table>",
                encoding="utf-8",
            )
            regressed = run_ratchet(root)

            self.assertEqual(1, regressed.returncode)
            self.assertIn("increased beyond baseline", regressed.stdout.lower())

    def test_scans_markdown_html_but_ignores_fenced_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "post.md").write_text(
                "Intro\n\n<table><tr><td>Debt</td></tr></table>\n\n"
                "```html\n<table><tr><td>Example code only</td></tr></table>\n```\n",
                encoding="utf-8",
            )

            baseline = run_ratchet(root, "--write-baseline")
            self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)

            result = run_ratchet(root)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            baseline_json = root / ".table-ratchet-baseline.json"
            self.assertIn("post.md", baseline_json.read_text(encoding="utf-8"))

    def test_scans_mdx_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "page.mdx").write_text(
                '<div className="table-scroll"><table className="content-table"><tr><td>Ok</td></tr></table></div>',
                encoding="utf-8",
            )

            baseline = run_ratchet(root, "--write-baseline")
            self.assertEqual(0, baseline.returncode, baseline.stdout + baseline.stderr)
            result = run_ratchet(root)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_public_scrub_fixture_has_no_private_markers(self):
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "public-scrub" / "sanitized-writeup.md"
        text = fixture.read_text(encoding="utf-8")

        forbidden = ["/Users/", "http://localhost", "netlify.app", "@", "sk_live", "ghp_"]
        self.assertFalse([needle for needle in forbidden if needle in text])


if __name__ == "__main__":
    unittest.main()
