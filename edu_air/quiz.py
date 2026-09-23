"""Voice quiz: a classroom quiz driven entirely by speech.

The teacher says "Start quiz"; the projector shows QUESTION + options A B C D;
students answer out loud and the teacher advances:
  "Answer A" / "Next question" / "Show answer" / "End quiz".

The engine is pure logic (no Qt, no OS) and therefore fully unit-testable. A
question bank can be loaded from a JSON file or built from the built-in set.
"""

from __future__ import annotations

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

CURRICULUM_BANKS: dict[str, list[Question]] = {
    "maths": [
        Question("Quelle est la somme des angles d'un triangle ?",
                 ["90°", "180°", "360°", "270°"], 1, note="Dans un triangle euclidien, la somme des angles vaut toujours 180°."),
        Question("Si a = 5 et b = 12 dans un triangle rectangle, quelle est l'hypoténuse ?",
                 ["13", "15", "17", "10"], 0, note="D'après le théorème de Pythagore : 5² + 12² = 25 + 144 = 169 = 13²."),
        Question("Quelle est la dérivée de f(x) = x² ?",
                 ["x", "2x", "x³", "2"], 1, note="La dérivée de x^n est n*x^(n-1). Pour x², c'est 2x."),
    ],
    "svt": [
        Question("Quel organe est responsable de la circulation sanguine ?",
                 ["Le Foie", "Le Poumon", "Le Cœur", "Le Cerveau"], 2, note="Le cœur propulse le sang dans l'organisme."),
        Question("Quel gaz les plantes absorbent-elles lors de la photosynthèse ?",
                 ["L'Oxygène", "Le Dioxyde de Carbone (CO₂)", "L'Azote", "L'Hélium"], 1, note="La photosynthèse consomme du CO₂ et rejette de l'O₂."),
        Question("Où se situe l'ADN dans une cellule eucaryote ?",
                 ["Le Noyau", "Le Cytoplasme", "La Membrane", "Le Ribosome"], 0, note="L'ADN se trouve concentré dans le noyau cellulaire."),
    ],
    "physique_chimie": [
        Question("Quelle est la formule chimique de l'eau ?",
                 ["CO₂", "H₂O", "NaCl", "CH₄"], 1, note="H₂O signifie deux atomes d'hydrogène et un atome d'oxygène."),
        Question("Quelle est la vitesse de la lumière dans le vide ?",
                 ["300 000 km/s", "1 000 km/h", "300 km/s", "3 000 000 km/s"], 0, note="La lumière se propage à environ 300 000 km/s dans le vide."),
    ],
    "computer_science": [
        Question("Quel langage est principalement utilisé pour la Data Science et l'IA ?",
                 ["Python", "HTML", "CSS", "Assembly"], 0, note="Python possède un vaste écosystème de bibliothèques scientifiques."),
        Question("Que signifie l'acronyme HTML ?",
                 ["HyperText Markup Language", "HighTech Main Language", "Home Tool Markup Language", "Hyperlink Text Mode Language"], 0, note="HTML est le langage standard de structuration web."),
    ],
    "histoire_geo": [
        Question("En quelle année s'est déroulée la Révolution Française ?",
                 ["1789", "1914", "1815", "1492"], 0, note="1789 marque la prise de la Bastille et le début de la Révolution."),
        Question("Quelle est la capitale de l'Australie ?",
                 ["Sydney", "Melbourne", "Canberra", "Brisbane"], 2, note="Canberra est la capitale fédérale de l'Australie."),
        Question("Quel océan sépare l'Europe de l'Amérique du Nord ?",
                 ["Océan Pacifique", "Océan Atlantique", "Océan Indien", "Océan Arctique"], 1, note="L'Océan Atlantique sépare ces deux continents."),
    ],
    "english": [
        Question("Which sentence is grammatically correct?",
                 ["He go to school", "He goes to school", "He going school", "He gone to school"], 1, note="Third person singular takes '-s' in Present Simple."),
        Question("What is the past tense of 'write'?",
                 ["Writed", "Wrote", "Written", "Writing"], 1, note="'Write' is an irregular verb: write -> wrote -> written."),
    ],
    "arabic": [
        Question("ما هي عاصمة الجزائر؟",
                 ["الجزائر العاصمة", "وهران", "قسنطينة", "عنابة"], 0, note="الجزائر العاصمة هي عاصمة الجمهورية الجزائرية."),
        Question("كم عدد أضلاع المثلث؟",
                 ["اثنان", "ثلاثة", "أربعة", "خمسة"], 1, note="المثلث يتكون من ثلاثة أضلاع وثلاث زوايا."),
    ]
}


class QuestionBank:
    """Loads/serves questions from a JSON file, subject presets or built-in set."""

    def __init__(self, questions: Optional[list[Question]] = None):
        self.questions: list[Question] = list(questions or DEFAULT_QUESTIONS)
        self._idx = 0

    @classmethod
    def load_subject(cls, subject: str) -> "QuestionBank":
        bank_questions = CURRICULUM_BANKS.get(subject.lower(), DEFAULT_QUESTIONS)
        return cls(bank_questions)

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

    # ---- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        self.bank.reset()
        self.current_question_idx = 0
        self.state = STATE_QUESTION
        self.revealed = False
        self.last_answer_idx = None
        self.last_answer_correct = None
        self.stats = QuizStats()
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
        return correct

    def reveal(self) -> None:
        if self.state == STATE_ANSWERED or self.state == STATE_QUESTION:
            if self.state == STATE_QUESTION:
                self.stats.skipped += 1
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