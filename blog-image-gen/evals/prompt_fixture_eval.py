#!/usr/bin/env python3
"""Validate prompt extraction from a gen_blog_image.py dry-run transcript."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_BLOCK = re.compile(r"FINAL PROMPT:\s*```(?:text)?\s*(.*?)\s*```", re.DOTALL)


def extract_prompt(text):
    match = PROMPT_BLOCK.search(text)
    if not match:
        raise ValueError("dry-run output did not contain a fenced FINAL PROMPT block")
    return match.group(1).strip()


class PromptExtractionEval(unittest.TestCase):
    def test_extracts_specific_final_prompt_from_dry_run_fixture(self):
        text = (ROOT / "fixtures" / "dry-run-output.txt").read_text(encoding="utf-8")
        prompt = extract_prompt(text)

        self.assertIn("FP&A operating leverage", prompt)
        self.assertIn("no fake UI text", prompt)
        self.assertGreater(len(prompt.split()), 20)


if __name__ == "__main__":
    unittest.main()
