#!/usr/bin/env python3
"""Static evals for quiz-me modes and weak-concept retry contract."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WeakConceptQueue:
    def __init__(self):
        self.items = []

    def record(self, concept, result):
        if result in {"partial", "incorrect"} and concept not in self.items:
            self.items.append(concept)
        if result == "correct" and concept in self.items:
            self.items.remove(concept)


class QuizMeEvalTests(unittest.TestCase):
    def test_modes_cover_finance_code_and_interview(self):
        modes = (ROOT / "references" / "modes.md").read_text(encoding="utf-8")

        for heading in ("## Finance", "## Code", "## Interview"):
            self.assertIn(heading, modes)

    def test_weak_concept_retry_queue_adds_and_clears_items(self):
        queue = WeakConceptQueue()

        queue.record("deferred revenue", "partial")
        queue.record("deferred revenue", "incorrect")
        queue.record("working capital", "incorrect")
        self.assertEqual(["deferred revenue", "working capital"], queue.items)

        queue.record("deferred revenue", "correct")
        self.assertEqual(["working capital"], queue.items)


if __name__ == "__main__":
    unittest.main()
