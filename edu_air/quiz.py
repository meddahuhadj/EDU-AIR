"""Voice quiz: a classroom quiz driven entirely by speech.

The teacher says "Start quiz"; the projector shows QUESTION + options A B C D;
students answer out loud and the teacher advances:
  "Answer A" / "Next question" / "Show answer" / "End quiz".

The engine is pure logic (no Qt, no OS) and therefore fully unit-testable. A
question bank can be loaded from a JSON file or built from the built-in set.
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import QuizSettings, SETTINGS

STATE_IDLE = "idle"
STATE_QUESTION = "question"
STATE_ANSWERED = "answered"
STATE_RESULTS = "results"


@dataclass
class Question:
    text: str
    options: list = field(default_factory=lambda: ["", "", "", ""])  # A B C D
    answer_idx: int = 0              # 0..3
    note: str = ""                   # optional teacher note revealed with answer

    def option(self, idx: int) -> str:
        if 0 <= idx < 4:
            return self.options[idx]
        return ""


@dataclass
class QuizStats:
    total: int = 0
    correct: int = 0
    wrong: int = 0
    answered: int = 0
    skipped: int = 0


@dataclass
class QuizAnswerRecord:
    """One row of the class's answer history -- what CSV export reads from.
    ``VoiceQuiz`` only ever kept the *last* answer before this; recording
    each one as it happens is what turns "export results" from a single
    current-question snapshot into an actual session record for the
    teacher's cahier de classe."""
    question_number: int
    question_text: str
    given_label: str          # "A".."D", or "" when skipped/never answered
    correct_label: str        # "A".."D"
    is_correct: bool
    was_skipped: bool
    elapsed_s: float


DEFAULT_QUESTIONS: list[Question] = [
    Question("What is the capital of France?",
             ["Paris", "London", "Berlin", "Rome"], 0,
             note="Paris is the capital of France."),
    Question("How many sides does a triangle have?",
             ["Two", "Three", "Four", "Five"], 1,
             note="A triangle has exactly three sides."),
    Question("Which planet is known as the Red Planet?",
             ["Venus", "Jupiter", "Mars", "Saturn"], 2,
             note="Mars appears red because of iron oxide on its surface."),
    Question("What is 7 × 8?",
             ["48", "54", "56", "64"], 2,
             note="7 × 8 = 56."),
    Question("Which of these is a programming language?",
             ["Python", "Elephant", "Water", "Cloud"], 0,
             note="Python is a widely-used programming language."),
]


class QuestionBank:
    """Loads/serves questions from a JSON file or the built-in set."""

    def __init__(self, questions: Optional[list[Question]] = None):
        self.questions: list[Question] = list(questions or DEFAULT_QUESTIONS)
        self._idx = 0

    @classmethod
    def load(cls, path: str | Path) -> "QuestionBank":
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        qs = []
        for item in data:
            qs.append(Question(
                text=str(item.get("text", "")),
                options=list(item.get("options", ["", "", "", ""]))[:4],
                answer_idx=int(item.get("answer", item.get("answer_idx", 0))),
                note=str(item.get("note", "")),
            ))
        return cls(qs)

    def reset(self) -> None:
        self._idx = 0

    @property
    def current(self) -> Optional[Question]:
        if 0 <= self._idx < len(self.questions):
            return self.questions[self._idx]
        return None

    def next(self) -> Optional[Question]:
        self._idx += 1
        return self.current

    def prev(self) -> Optional[Question]:
        self._idx = max(0, self._idx - 1)
        return self.current

    def go_to(self, index: int) -> Optional[Question]:
        self._idx = max(0, min(len(self.questions) - 1, index))
        return self.current

    def __len__(self) -> int:
        return len(self.questions)


class VoiceQuiz:
    def __init__(self, bank: QuestionBank | None = None,
                 settings: QuizSettings | None = None):
        self.bank = bank or QuestionBank()
        self.settings = settings or SETTINGS.quiz
        self.state = STATE_IDLE
        self.current_question_idx = 0
        self.revealed = False
        self.last_answer_idx: Optional[int] = None
        self.last_answer_correct: Optional[bool] = None
        self.stats = QuizStats()
        self.question_started: Optional[float] = None
        self.question_elapsed_s: float = 0.0
        self.total_elapsed_s: float = 0.0
        self._started_at: Optional[float] = None
        self._active = False
        self.history: list[QuizAnswerRecord] = []

    # ---- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        self.bank.reset()
        self.current_question_idx = 0
        self.state = STATE_QUESTION
        self.revealed = False
        self.last_answer_idx = None
        self.last_answer_correct = None
        self.stats = QuizStats()
        self.history = []
        self._started_at = time.monotonic()
        self.question_started = self._started_at
        self._active = True

    def stop(self) -> None:
        self.state = STATE_IDLE
        self.revealed = False
        self.last_answer_idx = None
        self.last_answer_correct = None
        self._active = False
        if self._started_at is not None:
            self.total_elapsed_s = time.monotonic() - self._started_at

    @property
    def active(self) -> bool:
        return self._active and self.state in (STATE_QUESTION, STATE_ANSWERED)

    # ---- navigation --------------------------------------------------------
    def next_question(self) -> Optional[Question]:
        if not self._active:
            return None
        q = self.bank.next()
        if q is None and self.state in (STATE_QUESTION, STATE_ANSWERED):
            self.state = STATE_RESULTS
            self._active = False
            return None
        self.current_question_idx = self.bank._idx
        self._load_question()
        return q

    def prev_question(self) -> Optional[Question]:
        if not self._active:
            return None
        q = self.bank.prev()
        self.current_question_idx = self.bank._idx
        self._load_question()
        return q

    def _load_question(self) -> None:
        self.state = STATE_QUESTION
        self.revealed = False
        self.last_answer_idx = None
        self.last_answer_correct = None
        self.question_started = time.monotonic()
        self.question_elapsed_s = 0.0

    def restart(self) -> None:
        self.start()

    # ---- answering ---------------------------------------------------------
    def _label_for(self, index: int) -> str:
        labels = self.labels
        return labels[index] if 0 <= index < len(labels) else ""

    def answer(self, index: int) -> bool:
        """Submit an option index (0..3). Returns True when correct."""
        if not self.active or self.state == STATE_ANSWERED:
            return False
        q = self.bank.current
        if q is None:
            return False
        correct = (index == q.answer_idx)
        self.last_answer_idx = index
        self.last_answer_correct = correct
        self.stats.answered += 1
        if correct:
            self.stats.correct += 1
        else:
            self.stats.wrong += 1
        self.stats.total += 1
        self.state = STATE_ANSWERED
        if self.question_started is not None:
            self.question_elapsed_s = time.monotonic() - self.question_started
        if self.settings.reveal_on_answer:
            self.revealed = True
        self.history.append(QuizAnswerRecord(
            question_number=self.current_question_idx + 1,
            question_text=q.text,
            given_label=self._label_for(index),
            correct_label=self._label_for(q.answer_idx),
            is_correct=correct,
            was_skipped=False,
            elapsed_s=round(self.question_elapsed_s, 1),
        ))
        return correct

    def reveal(self) -> None:
        if self.state == STATE_ANSWERED or self.state == STATE_QUESTION:
            if self.state == STATE_QUESTION:
                self.stats.skipped += 1
                q = self.bank.current
                if self.question_started is not None:
                    self.question_elapsed_s = time.monotonic() - self.question_started
                if q is not None:
                    self.history.append(QuizAnswerRecord(
                        question_number=self.current_question_idx + 1,
                        question_text=q.text,
                        given_label="",
                        correct_label=self._label_for(q.answer_idx),
                        is_correct=False,
                        was_skipped=True,
                        elapsed_s=round(self.question_elapsed_s, 1),
                    ))
            self.revealed = True
            if self.state == STATE_QUESTION:
                self.state = STATE_ANSWERED

    # ---- current question ---------------------------------------------------
    @property
    def question(self) -> Optional[Question]:
        return self.bank.current

    @property
    def labels(self) -> tuple:
        return tuple(self.settings.option_labels)

    def tick(self, dt: float) -> None:
        if self._active and self.question_started is not None:
            self.question_elapsed_s += dt

    def summary(self) -> dict:
        return {
            "state": self.state,
            "total": self.stats.total,
            "correct": self.stats.correct,
            "wrong": self.stats.wrong,
            "skipped": self.stats.skipped,
            "elapsed_s": round(self.total_elapsed_s, 1) if self._started_at
            else round(time.monotonic() - self._started_at, 1) if self._started_at else 0.0,
            "question": self.current_question_idx + 1,
        }

    # ---- export --------------------------------------------------------------
    def to_csv_rows(self) -> list[list[str]]:
        """Header + one row per answered/skipped question -- what "Export
        quiz results" writes to disk. Kept as plain data (no file I/O) so
        it is testable without touching a real file."""
        rows = [["#", "Question", "Given answer", "Correct answer", "Result", "Time (s)"]]
        for rec in self.history:
            if rec.was_skipped:
                result = "Skipped"
            elif rec.is_correct:
                result = "Correct"
            else:
                result = "Wrong"
            rows.append([
                str(rec.question_number), rec.question_text,
                rec.given_label or "-", rec.correct_label, result,
                f"{rec.elapsed_s:.1f}",
            ])
        rows.append([])
        s = self.summary()
        rows.append(["Total questions", str(s["total"])])
        rows.append(["Correct", str(s["correct"])])
        rows.append(["Wrong", str(s["wrong"])])
        rows.append(["Skipped", str(s["skipped"])])
        rows.append(["Duration (s)", str(s["elapsed_s"])])
        return rows

    def export_csv(self, path: str | Path) -> Path:
        """Write the quiz session's answer history to a CSV file (UTF-8
        with BOM, so accented question text opens correctly in Excel).
        Returns the written path."""
        p = Path(path)
        with p.open("w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(self.to_csv_rows())
        return p