#!/usr/bin/env python3
"""Eval runner for the handoff skill.

This runner validates the static trigger/output assertions and the artifact path
selection policy described in SKILL.md.
"""

import json
import tempfile
import unittest
from pathlib import Path


EVALS = Path(__file__).with_name("evals.json")


def choose_artifact_dir(cwd: Path, repo_root: Path | None, tmp_root: Path) -> Path:
    """Mirror the skill's artifact-location priority."""
    if repo_root is not None:
        return repo_root / ".agent-handoffs"
    if cwd.exists():
        return cwd / ".agent-handoffs"
    return tmp_root / "agent-handoffs"


class StaticEvalDataTests(unittest.TestCase):
    def test_eval_file_has_positive_negative_and_output_assertions(self):
        data = json.loads(EVALS.read_text(encoding="utf-8"))

        self.assertGreaterEqual(len(data["positive_triggers"]), 5)
        self.assertGreaterEqual(len(data["negative_triggers"]), 5)
        self.assertGreaterEqual(len(data["output_assertions"]), 8)

    def test_cross_environment_trigger_is_present(self):
        data = json.loads(EVALS.read_text(encoding="utf-8"))
        prompts = " ".join(item["prompt"] for item in data["positive_triggers"])

        self.assertIn("Codex", prompts)
        self.assertIn("VPS", prompts)


class ArtifactPathPolicyTests(unittest.TestCase):
    def test_prefers_repo_local_handoffs_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            cwd = repo / "subdir"
            cwd.mkdir(parents=True)

            self.assertEqual(repo / ".agent-handoffs", choose_artifact_dir(cwd, repo, root))

    def test_uses_workspace_local_when_not_in_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cwd = root / "workspace"
            cwd.mkdir()

            self.assertEqual(cwd / ".agent-handoffs", choose_artifact_dir(cwd, None, root))

    def test_uses_temp_when_workspace_is_not_meaningful(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing"

            self.assertEqual(root / "agent-handoffs", choose_artifact_dir(missing, None, root))


if __name__ == "__main__":
    unittest.main()
