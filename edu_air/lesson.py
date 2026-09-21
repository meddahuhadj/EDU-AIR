"""Lesson sequencer: an ordered course outline a teacher can prepare ahead
of class and step through live -- pure logic, no Qt.

A step never touches presentation/quiz/board state itself: it only names
*what kind* of classroom action "next step" should trigger
(:mod:`edu_air.classroom` translates that into the exact same
``NEXT_SLIDE``/``QUIZ_START``/``TIMER_START``/``BOARD_NEXT_PAGE`` actions a
teacher would otherwise reach for by hand, each still going through the
usual safety gate). A ``LessonPlan`` is therefore nothing more than a named
shortcut through the already-approved action catalogue -- it cannot invent
a new capability the classroom doesn't already expose.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

STEP_SLIDE = "slide"
STEP_QUIZ = "quiz"
STEP_TIMER = "timer"
STEP_BOARD = "board"
STEP_KINDS = (STEP_SLIDE, STEP_QUIZ, STEP_TIMER, STEP_BOARD)


def validate_kind(kind: str) -> str:
    """Map an arbitrary string onto a known step kind (slide fallback)."""
    return kind if kind in STEP_KINDS else STEP_SLIDE


@dataclass
class LessonStep:
    kind: str
    label: str
    duration_s: float = 0.0  # only meaningful for STEP_TIMER (0 = no auto-stop)

    def __post_init__(self) -> None:
        self.kind = validate_kind(self.kind)


class LessonPlan:
    """An ordered course outline the teacher steps through with one
    "next step" command (voice, button or shortcut) per moment of class."""

    def __init__(self, steps: Optional[list[LessonStep]] = None) -> None:
        self._steps: list[LessonStep] = list(steps or [])
        self._current = -1  # -1 == not started yet

    # ---- read access ---------------------------------------------------------
    @property
    def steps(self) -> list[LessonStep]:
        return self._steps

    @property
    def step_count(self) -> int:
        return len(self._steps)

    @property
    def current_index(self) -> int:
        return self._current

    @property
    def current(self) -> Optional[LessonStep]:
        if 0 <= self._current < len(self._steps):
            return self._steps[self._current]
        return None

    @property
    def started(self) -> bool:
        return self._current >= 0

    @property
    def finished(self) -> bool:
        return self.step_count > 0 and self._current >= self.step_count

    def progress_text(self) -> str:
        if not self._steps:
            return ""
        if self.finished:
            return f"Done ({self.step_count}/{self.step_count})"
        if not self.started:
            return f"Ready (0/{self.step_count})"
        return f"{self._current + 1}/{self.step_count}: {self.current.label}"

    # ---- navigation -----------------------------------------------------------
    def advance(self) -> Optional[LessonStep]:
        """Move to the next step and return it (``None`` once the plan is
        exhausted -- call :meth:`reset` to run it again)."""
        if self._current < self.step_count:
            self._current += 1
        return self.current

    def back(self) -> Optional[LessonStep]:
        """Move the cursor back one step (a correction, not an "undo" of the
        previous step's on-screen effect)."""
        if self._current > 0:
            self._current -= 1
        elif self._current == 0:
            self._current = -1
        return self.current

    def reset(self) -> None:
        self._current = -1

    def set_steps(self, steps: list[LessonStep]) -> None:
        self._steps = list(steps)
        self._current = -1

    # ---- persistence -----------------------------------------------------------
    def as_dict(self) -> dict:
        return {"steps": [{"kind": s.kind, "label": s.label, "duration_s": s.duration_s}
                           for s in self._steps]}

    def load_dict(self, data: dict) -> None:
        data = data or {}
        steps = []
        for raw in data.get("steps") or []:
            steps.append(LessonStep(
                kind=str(raw.get("kind", STEP_SLIDE)),
                label=str(raw.get("label", "")),
                duration_s=float(raw.get("duration_s", 0.0) or 0.0),
            ))
        self.set_steps(steps)

    def save_json(self, path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.as_dict(), ensure_ascii=False, indent=1),
                     encoding="utf-8")
        return p

    def load_json(self, path) -> bool:
        """Restore a plan saved with :meth:`save_json`. Returns False when
        the file is missing or unreadable (the plan is left untouched)."""
        p = Path(path)
        if not p.is_file():
            return False
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "steps" not in data:
                return False
            self.load_dict(data)
        except (ValueError, OSError, TypeError):
            # Syntactically valid JSON with a malformed field (e.g. a
            # hand-edited "duration_s": "soon") must not crash the app --
            # ``load_dict`` calls ``float()``/``str()`` on untrusted input.
            return False
        return True
