"""
Game Engine for the Open Trivia Database Quiz Game.
Manages question lifecycle, scoring, streaks, lifelines, and high score tracking
across multiple categories (Science: Mathematics, Science: Gadgets, etc.).
"""

from dataclasses import dataclass, field
import datetime
import json
import os
import random
import time
from typing import Any, Dict, List, Optional, Set

HIGH_SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscores.json")

DIFFICULTY_POINTS = {
    "easy": 100,
    "medium": 200,
    "hard": 300,
}

TIME_LIMIT_PER_QUESTION = 25  # seconds per question in timed mode


@dataclass
class PreparedQuestion:
    index: int
    question: str
    difficulty: str
    category: str
    options: Dict[str, str]  # e.g. {'A': 'Option 1', 'B': 'Option 2', ...}
    correct_letter: str  # 'A', 'B', 'C', or 'D'
    correct_answer: str
    disabled_options: Set[str] = field(default_factory=set)


@dataclass
class AnswerRecord:
    question: PreparedQuestion
    selected_letter: Optional[str]
    selected_text: Optional[str]
    is_correct: bool
    time_taken: float
    points_earned: int
    streak_at_time: int


class GameEngine:
    def __init__(
        self,
        raw_questions: List[Dict[str, Any]],
        category_name: str = "Science: Mathematics",
        mode: str = "marathon",
        time_limit: int = TIME_LIMIT_PER_QUESTION,
    ):
        """
        Modes:
          - 'marathon': All available questions (up to 50)
          - 'sprint': 25 questions
          - 'blitz': 10 questions
          - 'survival': 3 lives, ends when lives reach 0
        """
        self.category_name = category_name
        self.mode = mode.lower()
        self.time_limit = time_limit

        # Slice questions according to mode and availability
        if self.mode == "blitz":
            selected_raw = raw_questions[:min(10, len(raw_questions))]
        elif self.mode == "sprint":
            selected_raw = raw_questions[:min(25, len(raw_questions))]
        else:
            selected_raw = raw_questions[:min(50, len(raw_questions))]

        self.questions: List[PreparedQuestion] = self._prepare_questions(selected_raw)
        self.total_questions = len(self.questions)

        # Game status
        self.current_index = 0
        self.score = 0
        self.streak = 0
        self.max_streak = 0
        self.lives = 3 if self.mode == "survival" else None
        self.history: List[AnswerRecord] = []

        # Lifelines (each usable once per game session)
        self.lifelines = {
            "50_50": True,
            "skip": True,
        }

        self.question_start_time: float = time.time()
        self.game_start_time: float = time.time()
        self.game_over = False

    def _prepare_questions(self, raw_list: List[Dict[str, Any]]) -> List[PreparedQuestion]:
        prepared = []
        letters = ["A", "B", "C", "D"]

        for idx, item in enumerate(raw_list, start=1):
            q_text = item.get("question", "")
            correct_ans = item.get("correct_answer", "")
            incorrect_ans = list(item.get("incorrect_answers", []))
            difficulty = item.get("difficulty", "medium").lower()
            category = item.get("category", self.category_name)

            all_choices = incorrect_ans + [correct_ans]
            random.shuffle(all_choices)

            options_dict = {}
            correct_letter = "A"
            for letter, choice in zip(letters, all_choices):
                options_dict[letter] = choice
                if choice == correct_ans:
                    correct_letter = letter

            prepared.append(
                PreparedQuestion(
                    index=idx,
                    question=q_text,
                    difficulty=difficulty,
                    category=category,
                    options=options_dict,
                    correct_letter=correct_letter,
                    correct_answer=correct_ans,
                )
            )

        return prepared

    def get_current_question(self) -> Optional[PreparedQuestion]:
        if self.current_index < len(self.questions) and not self.game_over:
            return self.questions[self.current_index]
        return None

    def start_question_timer(self) -> None:
        self.question_start_time = time.time()

    def get_streak_multiplier(self) -> float:
        if self.streak >= 8:
            return 3.0
        if self.streak >= 5:
            return 2.0
        if self.streak >= 3:
            return 1.5
        return 1.0

    def use_fifty_fifty(self) -> bool:
        """Removes two incorrect options from the current question."""
        if not self.lifelines.get("50_50", False):
            return False

        curr_q = self.get_current_question()
        if not curr_q or curr_q.disabled_options:
            return False

        wrong_letters = [
            ltr for ltr in curr_q.options.keys() if ltr != curr_q.correct_letter
        ]
        to_disable = random.sample(wrong_letters, 2)
        curr_q.disabled_options = set(to_disable)
        self.lifelines["50_50"] = False
        return True

    def use_skip(self) -> bool:
        """Skips current question without penalty or streak break."""
        if not self.lifelines.get("skip", False):
            return False

        curr_q = self.get_current_question()
        if not curr_q:
            return False

        self.lifelines["skip"] = False
        elapsed = time.time() - self.question_start_time
        record = AnswerRecord(
            question=curr_q,
            selected_letter="SKIPPED",
            selected_text="[Question Skipped by Lifeline]",
            is_correct=False,
            time_taken=elapsed,
            points_earned=0,
            streak_at_time=self.streak,
        )
        self.history.append(record)
        self._advance_question()
        return True

    def submit_answer(self, choice_letter: Optional[str]) -> AnswerRecord:
        """
        Evaluates user's choice ('A', 'B', 'C', 'D' or None for timeout).
        Calculates points, updates streak, checks survival lives.
        """
        curr_q = self.get_current_question()
        if not curr_q:
            raise RuntimeError("No active question to answer.")

        elapsed = max(0.1, time.time() - self.question_start_time)
        choice_clean = choice_letter.strip().upper() if choice_letter else None

        is_correct = choice_clean == curr_q.correct_letter
        points = 0

        if is_correct:
            self.streak += 1
            if self.streak > self.max_streak:
                self.max_streak = self.streak

            base_pts = DIFFICULTY_POINTS.get(curr_q.difficulty, 150)
            multiplier = self.get_streak_multiplier()

            # Time bonus (up to 50 points if answered quickly)
            time_bonus = 0
            if self.time_limit and elapsed < self.time_limit:
                ratio = max(0.0, 1.0 - (elapsed / self.time_limit))
                time_bonus = int(50 * ratio)

            points = int((base_pts * multiplier) + time_bonus)
            self.score += points
        else:
            self.streak = 0
            if self.mode == "survival" and self.lives is not None:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True

        selected_text = curr_q.options.get(choice_clean) if choice_clean else "Time Expired"
        record = AnswerRecord(
            question=curr_q,
            selected_letter=choice_clean or "TIMEOUT",
            selected_text=selected_text,
            is_correct=is_correct,
            time_taken=elapsed,
            points_earned=points,
            streak_at_time=self.streak,
        )
        self.history.append(record)

        self._advance_question()
        return record

    def _advance_question(self) -> None:
        self.current_index += 1
        if self.current_index >= len(self.questions):
            self.game_over = True
        self.question_start_time = time.time()

    def get_summary(self) -> Dict[str, Any]:
        """Calculates final game performance metrics."""
        total_answered = len(self.history)
        correct_count = sum(1 for r in self.history if r.is_correct)
        accuracy = (correct_count / total_answered * 100.0) if total_answered > 0 else 0.0
        total_time = sum(r.time_taken for r in self.history)
        avg_time = (total_time / total_answered) if total_answered > 0 else 0.0

        difficulty_stats = {"easy": [0, 0], "medium": [0, 0], "hard": [0, 0]}
        for r in self.history:
            diff = r.question.difficulty
            if diff in difficulty_stats:
                difficulty_stats[diff][1] += 1
                if r.is_correct:
                    difficulty_stats[diff][0] += 1

        rank = self._calculate_rank(accuracy, self.score, correct_count, self.total_questions)

        return {
            "category": self.category_name,
            "mode": self.mode,
            "total_questions": self.total_questions,
            "answered_count": total_answered,
            "correct_count": correct_count,
            "accuracy_percent": round(accuracy, 1),
            "score": self.score,
            "max_streak": self.max_streak,
            "total_time_seconds": round(total_time, 1),
            "avg_time_per_question": round(avg_time, 1),
            "difficulty_stats": difficulty_stats,
            "rank": rank,
            "history": self.history,
        }

    def _calculate_rank(self, accuracy: float, score: int, correct: int, total: int) -> str:
        ratio = (correct / total) if total > 0 else 0.0
        if ratio >= 0.90 or (accuracy >= 90 and score >= 6000):
            return "Grand Champion (Legendary Scholar)"
        if ratio >= 0.78 or (accuracy >= 80 and score >= 4500):
            return "Senior Master / Professor"
        if ratio >= 0.65 or (accuracy >= 70 and score >= 3000):
            return "Expert Specialist"
        if ratio >= 0.45 or (accuracy >= 50 and score >= 1500):
            return "Adept Practitioner"
        if ratio >= 0.25:
            return "Curious Explorer"
        return "Novice Apprentice"


class HighScoreManager:
    @staticmethod
    def load_scores() -> List[Dict[str, Any]]:
        if not os.path.exists(HIGH_SCORES_FILE):
            return []
        try:
            with open(HIGH_SCORES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return sorted(data, key=lambda x: x.get("score", 0), reverse=True)
        except Exception:
            return []

    @staticmethod
    def save_score(name: str, summary: Dict[str, Any]) -> None:
        scores = HighScoreManager.load_scores()
        entry = {
            "name": name.strip() or "Anonymous Player",
            "score": summary["score"],
            "accuracy": summary["accuracy_percent"],
            "correct": summary["correct_count"],
            "total": summary["total_questions"],
            "category": summary.get("category", "Science: Mathematics"),
            "mode": summary["mode"],
            "rank": summary["rank"],
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        scores.append(entry)
        scores.sort(key=lambda x: x["score"], reverse=True)
        scores = scores[:15]  # Keep top 15

        try:
            with open(HIGH_SCORES_FILE, "w", encoding="utf-8") as f:
                json.dump(scores, f, indent=2)
        except Exception as e:
            print(f"[Warning] Failed to save high scores: {e}")
