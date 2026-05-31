#!/usr/bin/env python3
"""Static evals for grill-me trigger boundaries and examples."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def should_trigger_grill(prompt):
    p = prompt.lower()
    return any(term in p for term in ("grill me", "stress-test this plan", "poke holes", "interview me")) and not should_trigger_quiz(prompt)


def should_trigger_quiz(prompt):
    p = prompt.lower()
    return any(term in p for term in ("quiz me", "test me on", "flashcard", "help me study"))


class GrillMeEvalTests(unittest.TestCase):
    def test_grill_triggers_do_not_catch_quiz_prompts(self):
        self.assertTrue(should_trigger_grill("grill me on this implementation plan"))
        self.assertTrue(should_trigger_grill("stress-test this plan before we build"))
        self.assertFalse(should_trigger_grill("quiz me on deferred revenue"))
        self.assertFalse(should_trigger_grill("test me on Python list comprehensions"))

    def test_domain_examples_cover_code_business_and_fpa(self):
        examples = (ROOT / "references" / "domain-examples.md").read_text(encoding="utf-8")

        for heading in ("## Code", "## Business", "## FP&A"):
            self.assertIn(heading, examples)
        self.assertIn("Recommended first question", examples)


if __name__ == "__main__":
    unittest.main()
