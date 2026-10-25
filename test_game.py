"""
Unit tests for the Trivia Game with Category Support.
Verifies category resolution, API decoding, GameEngine mechanics, lifelines, scoring, and persistence.
"""

import os
import unittest
from game_engine import GameEngine, HighScoreManager, PreparedQuestion
from trivia_api import (
    CATEGORIES,
    DEFAULT_CATEGORY,
    fetch_questions,
    resolve_category_id,
    unescape_question_data,
)


class TestTriviaGame(unittest.TestCase):
    def setUp(self):
        self.sample_raw_question = {
            "type": "multiple",
            "difficulty": "medium",
            "category": "Science: Gadgets",
            "question": "Which buzzword did Apple Inc. use to describe their removal of the headphone jack?",
            "correct_answer": "Courage",
            "incorrect_answers": ["Innovation", "Bravery", "Future"],
        }
        self.sample_pool = [
            {
                "type": "multiple",
                "difficulty": "easy" if i % 3 == 0 else ("medium" if i % 3 == 1 else "hard"),
                "category": "Science: Gadgets",
                "question": f"Gadget Question {i} test?",
                "correct_answer": f"Answer {i}",
                "incorrect_answers": [f"Wrong {i}A", f"Wrong {i}B", f"Wrong {i}C"],
            }
            for i in range(1, 35)  # 34 questions like OpenTDB Gadgets
        ]

    def test_category_resolution(self):
        self.assertEqual(resolve_category_id("gadgets"), 30)
        self.assertEqual(resolve_category_id("Science: Gadgets"), 30)
        self.assertEqual(resolve_category_id(30), 30)
        self.assertEqual(resolve_category_id("30"), 30)
        self.assertEqual(resolve_category_id("math"), 19)
        self.assertEqual(resolve_category_id("Science: Mathematics"), 19)
        self.assertEqual(resolve_category_id(19), 19)
        self.assertEqual(resolve_category_id("computers"), 18)
        self.assertEqual(resolve_category_id(None), DEFAULT_CATEGORY)

    def test_html_unescaping(self):
        cleaned = unescape_question_data(self.sample_raw_question)
        self.assertEqual(cleaned["question"], "Which buzzword did Apple Inc. use to describe their removal of the headphone jack?")
        self.assertEqual(cleaned["correct_answer"], "Courage")

    def test_gadgets_cached_load(self):
        qs = fetch_questions(amount=34, category=30, force_refresh=False)
        self.assertGreaterEqual(len(qs), 30)
        self.assertIn("category", qs[0])

    def test_marathon_mode_length(self):
        engine = GameEngine(self.sample_pool, category_name="Science: Gadgets", mode="marathon")
        self.assertEqual(engine.total_questions, 34)
        self.assertEqual(len(engine.questions), 34)

    def test_sprint_mode_length(self):
        engine = GameEngine(self.sample_pool, category_name="Science: Gadgets", mode="sprint")
        self.assertEqual(engine.total_questions, 25)

    def test_blitz_mode_length(self):
        engine = GameEngine(self.sample_pool, category_name="Science: Gadgets", mode="blitz")
        self.assertEqual(engine.total_questions, 10)

    def test_fifty_fifty_lifeline(self):
        engine = GameEngine(self.sample_pool, category_name="Science: Gadgets", mode="blitz")
        curr_q = engine.get_current_question()
        self.assertTrue(engine.lifelines["50_50"])

        used = engine.use_fifty_fifty()
        self.assertTrue(used)
        self.assertFalse(engine.lifelines["50_50"])
        self.assertEqual(len(curr_q.disabled_options), 2)
        self.assertNotIn(curr_q.correct_letter, curr_q.disabled_options)

    def test_skip_lifeline(self):
        engine = GameEngine(self.sample_pool, category_name="Science: Gadgets", mode="blitz")
        engine.streak = 4
        used = engine.use_skip()
        self.assertTrue(used)
        self.assertFalse(engine.lifelines["skip"])
        self.assertEqual(engine.streak, 4)
        self.assertEqual(len(engine.history), 1)
        self.assertEqual(engine.history[0].selected_letter, "SKIPPED")

    def test_scoring_and_streak(self):
        engine = GameEngine(self.sample_pool, category_name="Science: Gadgets", mode="blitz", time_limit=25)
        curr_q = engine.get_current_question()
        rec = engine.submit_answer(curr_q.correct_letter)
        self.assertTrue(rec.is_correct)
        self.assertEqual(engine.streak, 1)
        self.assertGreater(engine.score, 0)

        # Wrong answer resets streak
        curr_q2 = engine.get_current_question()
        wrong_ltr = [l for l in curr_q2.options if l != curr_q2.correct_letter][0]
        rec2 = engine.submit_answer(wrong_ltr)
        self.assertFalse(rec2.is_correct)
        self.assertEqual(engine.streak, 0)

    def test_survival_lives(self):
        engine = GameEngine(self.sample_pool, category_name="Science: Gadgets", mode="survival")
        self.assertEqual(engine.lives, 3)

        for _ in range(3):
            q = engine.get_current_question()
            wrong_ltr = [l for l in q.options if l != q.correct_letter][0]
            engine.submit_answer(wrong_ltr)

        self.assertEqual(engine.lives, 0)
        self.assertTrue(engine.game_over)

    def test_high_score_recording(self):
        summary = {
            "score": 8500,
            "accuracy_percent": 94.0,
            "correct_count": 32,
            "total_questions": 34,
            "category": "Science: Gadgets",
            "mode": "marathon",
            "rank": "Grand Champion",
        }
        HighScoreManager.save_score("GadgetPro", summary)
        scores = HighScoreManager.load_scores()
        names = [s["name"] for s in scores]
        self.assertIn("GadgetPro", names)


if __name__ == "__main__":
    unittest.main()
