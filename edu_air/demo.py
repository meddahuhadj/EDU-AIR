"""EDU-AIR demo mode.

A fully simulated classroom so the whole experience can be shown, tested and
trained without a webcam, microphone or any real computer control:

  * ``DemoSlideDeck``     — a virtual 10-slide lesson;
  * ``synthetic_hand``    — builds MediaPipe-style hand landmarks for the
                            gesture engine (same trick the HADJ test suite
                            uses), so the real classifier is exercised;
  * ``DemoVoiceScript``   — a scripted teaching sequence
                            (start presentation, next slide, quiz, answer …);
  * ``DemoSession``       — drives a :class:`ClassroomSession` from a script,
                            running every action in safe demo mode.

Nothing ever touches the OS in demo mode: every action is logged as
SIMULATED and the projection only shows the progress of the virtual class.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from hadj_no_touch.vision.hand_tracking import HandData  # re-export convenience

# ---------------------------------------------------------------------------
# Virtual slide deck.
# ---------------------------------------------------------------------------
DEMO_SLIDES: list[dict] = [
    {"title": "Welcome to EDU-AIR", "body": "Contactless Interactive Classroom"},
    {"title": "Today's Lesson", "body": "How organs work · Chapter 3"},
    {"title": "Key Idea #1", "body": "The heart pumps blood through arteries."},
    {"title": "Key Idea #2", "body": "Veins return blood to the heart."},
    {"title": "Key Idea #3", "body": "Capillaries exchange oxygen and nutrients."},
    {"title": "Quick Exercise", "body": "Which vessel carries blood away?"},
    {"title": "Group Activity", "body": "Draw the path of a red blood cell."},
    {"title": "Vocabulary", "body": "Artery · Vein · Capillary · Atrium"},
    {"title": "Homework", "body": "Complete worksheet pages 12–14"},
    {"title": "Thank You", "body": "See you next lesson!"},
]


class DemoSlideDeck:
    def __init__(self, slides: list[dict] | None = None):
        self.slides = slides or DEMO_SLIDES
        self.index = 0

    @property
    def current(self) -> dict:
        return self.slides[self.index]

    def next(self) -> dict:
        self.index = min(len(self.slides) - 1, self.index + 1)
        return self.current

    def prev(self) -> dict:
        self.index = max(0, self.index - 1)
        return self.current

    def go(self, index: int) -> dict:
        self.index = max(0, min(len(self.slides) - 1, index))
        return self.current

    def __len__(self) -> int:
        return len(self.slides)


# ---------------------------------------------------------------------------
# Synthetic hands for the gesture engine (no webcam required).
# ---------------------------------------------------------------------------
def _fan_landmarks(fingers: dict, pos: tuple[float, float]) -> np.ndarray:
    """Build a (21,2) normalized landmark array. ``fingers`` maps the medial
    indices to 'straight' or 'curled'. Mirrors the HADJ test helper."""
    pts = np.zeros((21, 2), dtype=np.float32)
    wrist = np.array([pos[0], pos[1]], dtype=np.float32)
    pts[0] = wrist
    dirs = {
        8: np.array([0.95, -0.30]), 12: np.array([0.85, 0.05]),
        16: np.array([0.70, 0.38]), 20: np.array([0.50, 0.70]),
    }
    mids = {8: 5, 12: 9, 16: 13, 20: 17}
    for tip, d in dirs.items():
        d = d / np.linalg.norm(d)
        mcp = mids[tip]
        straight = fingers.get(tip, "curled") == "straight"
        pts[mcp] = wrist + 0.04 * d
        pts[mcp + 1] = wrist + 0.10 * d
        pts[mcp + 2] = wrist + 0.16 * d
        pts[tip] = wrist + (0.24 * d if straight else 0.03 * d)
    t = np.array([-0.6, 0.35])
    t = t / np.linalg.norm(t)
    pts[1] = wrist + 0.02 * t
    pts[2] = wrist + 0.05 * t
    pts[3] = wrist + 0.08 * t
    if fingers.get(4, "curled") == "straight":
        pts[4] = wrist + 0.20 * t
    else:
        pts[4] = wrist + 0.02 * t
    return pts


def synthetic_hand(gesture: str, pos: tuple[float, float],
                   frame: tuple[int, int] = (640, 480)) -> HandData:
    """Build a single HandData for the given gesture name.

    Supported: point, pinch, open (palm), fist, two, highlight (palm-like).
    """
    fx, fy = float(frame[0]), float(frame[1])
    fingers: dict = {}
    if gesture == "point":
        fingers = {8: "straight"}
    elif gesture in ("two", "two_finger"):
        fingers = {8: "straight", 12: "straight"}
    elif gesture == "fist":
        fingers = {}
    elif gesture in ("open", "palm", "highlight", "erase"):
        fingers = {4: "straight", 8: "straight", 12: "straight",
                   16: "straight", 20: "straight"}
    lm = _fan_landmarks(fingers, pos)
    if gesture == "pinch":
        lm = lm.copy()
        lm[4] = lm[8].copy()  # thumb onto index tip = perfect pinch
    return HandData(landmarks_norm=lm, landmarks_px=lm * np.array([fx, fy]),
                    handedness="Right", confidence=0.92, tracked=True)


def finger_tip(hand: HandData) -> tuple[float, float]:
    """Normalized index-tip position (the point the pointer follows)."""
    return (float(hand.landmarks_norm[8][0]), float(hand.landmarks_norm[8][1]))


def moving_point(t: float, speed: float = 0.18) -> tuple[float, float]:
    """A slow figure that wanders around the frame (demo pointer motion)."""
    x = 0.5 + 0.32 * math.sin(t * 0.7)
    y = 0.5 + 0.24 * math.sin(t * 1.3 + 1.1)
    return (max(0.05, min(0.95, x)), max(0.05, min(0.95, y)))


# ---------------------------------------------------------------------------
# Scripted teaching sequence.
# ---------------------------------------------------------------------------
@dataclass
class DemoStep:
    kind: str                 # "voice" | "gesture" | "wait"
    value: str = ""
    params: dict = field(default_factory=dict)

    @classmethod
    def voice(cls, phrase: str, lang: str = "en") -> "DemoStep":
        return cls("voice", phrase, {"lang": lang})

    @classmethod
    def gesture(cls, name: str, pos: tuple[float, float]) -> "DemoStep":
        return cls("gesture", name, {"pos": pos})

    @classmethod
    def wait(cls, seconds: float) -> "DemoStep":
        return cls("wait", f"{seconds}", {})


def default_script(language: str = "en") -> list[DemoStep]:
    if language == "fr":
        v = ["START", "slide suivante", "slide suivante", "slide précédente",
             "démarrer le quiz", "réponse c", "question suivante", "réponse b",
             "affiche la réponse", "arrêter le quiz"]
        start_phrase = "démarrer la présentation"
    elif language == "ar":
        v = ["START", "الشريحة التالية", "الشريحة التالية", "الشريحة السابقة",
             "ابدأ الاختبار", "الاجابه ج", "السؤال التالي", "الاجابه ب",
             "اظهر الاجابة", "انهي الاختبار"]
        start_phrase = "ابدأ العرض التقديمي"
    elif language == "nl":
        v = ["START", "volgende dia", "volgende dia", "vorige dia",
             "start de quiz", "antwoord c", "volgende vraag", "antwoord b",
             "toon het antwoord", "stop de quiz"]
        start_phrase = "start presentatie"
    else:
        v = ["START", "next slide", "next slide", "previous slide",
             "start quiz", "answer c", "next question", "answer b",
             "show answer", "end quiz"]
        start_phrase = "start presentation"
    steps: list[DemoStep] = []
    for phrase in v:
        if phrase == "START":
            steps.append(DemoStep.voice(start_phrase, language))
            steps.append(DemoStep.wait(0.4))
            steps.append(DemoStep.voice("start", language))
        else:
            steps.append(DemoStep.voice(phrase, language))
        steps.append(DemoStep.gesture("point", moving_point(time.monotonic() % 5)))
        steps.append(DemoStep.wait(0.3))
    return steps


# ---------------------------------------------------------------------------
# Demo runner: feeds a ClassroomSession through a script in demo mode.
# ---------------------------------------------------------------------------
class DemoSession:
    def __init__(self, session, script: list[DemoStep] | None = None,
                 language: str = "en"):
        self.session = session
        self.language = language
        self.script = list(script or default_script(language))
        self.index = 0
        self.log: list[str] = []
        self.voice_texts: list[str] = []

    @property
    def done(self) -> bool:
        return self.index >= len(self.script)

    def step(self, dt: float = 0.0) -> Optional[str]:
        """Run the next script step; returns a human-readable log line."""
        if self.done:
            return None
        step = self.script[self.index]
        self.index += 1
        if step.kind == "wait":
            return f"wait {step.value}s"
        if step.kind == "voice":
            self.voice_texts.append(step.value)
            self.session.handle_voice_text(step.value, step.params.get("lang", self.language))
            return f"voice: {step.value}"
        if step.kind == "gesture":
            from hadj_no_touch.gestures import gesture_engine as ge
            hand = synthetic_hand(step.value, step.params.get("pos", (0.5, 0.5)))
            tip = finger_tip(hand)
            self.session.update_pointer(tip)
            evt = ge.GestureEvent(kind=ge.MOVE, x=tip[0], y=tip[1], confidence=0.9,
                                  ts=time.monotonic())
            self.session.handle_gesture(evt)
            return f"gesture: {step.value} @ ({tip[0]:.2f},{tip[1]:.2f})"
        return None

    def run_all(self) -> list[str]:
        lines = []
        while not self.done:
            line = self.step()
            if line:
                lines.append(line)
        return lines