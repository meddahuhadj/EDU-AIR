"""Classroom intent engine.

Maps classroom voice intents and gesture events onto a small catalogue of
approved classroom actions (see ``edu_air.safety``). This is the layer that
keeps the "classroom domain" clean: while a quiz is running, presentation
gestures are routed away; while presenting, quiz clues are ignored, etc.

Only intents that resolve to a *registered* action are ever executed — the
safety gate re-checks every one right before it runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from hadj_no_touch.gestures import gesture_engine as ge
from hadj_no_touch.voice import voice_commands as vc

from . import voice as cvoice
from .config import SETTINGS


# ---------------------------------------------------------------------------
# Classroom action names (approved catalogue keys).
# ---------------------------------------------------------------------------
PRESENTATION_START = "PRESENTATION_START"
PRESENTATION_STOP = "PRESENTATION_STOP"
NEXT_SLIDE = "NEXT_SLIDE"
PREV_SLIDE = "PREV_SLIDE"
PAUSE_PRESENTATION = "PAUSE_PRESENTATION"
ZOOM_IN = "ZOOM_IN"
ZOOM_OUT = "ZOOM_OUT"
SCROLL_UP = "SCROLL_UP"
SCROLL_DOWN = "SCROLL_DOWN"

POINTER_ON = "POINTER_ON"
POINTER_OFF = "POINTER_OFF"

ANNOTATION_DRAW = "ANNOTATION_DRAW"
ANNOTATION_HIGHLIGHT = "ANNOTATION_HIGHLIGHT"
ANNOTATION_ERASE = "ANNOTATION_ERASE"
ANNOTATION_CLEAR = "ANNOTATION_CLEAR"

QUIZ_START = "QUIZ_START"
QUIZ_STOP = "QUIZ_STOP"
QUIZ_NEXT = "QUIZ_NEXT"
QUIZ_PREV = "QUIZ_PREV"
QUIZ_ANSWER = "QUIZ_ANSWER"              # params: letter, answer_index
QUIZ_REVEAL = "QUIZ_REVEAL"
QUIZ_RESTART = "QUIZ_RESTART"

TIMER_START = "TIMER_START"
TIMER_STOP = "TIMER_STOP"


@dataclass
class ClassroomIntent:
    action: str
    params: dict = field(default_factory=dict)
    confidence: float = 1.0
    source: str = "context"      # voice | gesture | ui
    description: str = ""

    def describe(self) -> str:
        return self.description or self.action


# Segment: which classroom domain this action belongs to. Used for
# context routing (e.g. quiz voice while presenting).
ACTION_DOMAIN: dict[str, str] = {
    PRESENTATION_START: "presentation", PRESENTATION_STOP: "presentation",
    NEXT_SLIDE: "presentation", PREV_SLIDE: "presentation",
    PAUSE_PRESENTATION: "presentation", ZOOM_IN: "presentation",
    ZOOM_OUT: "presentation", SCROLL_UP: "presentation", SCROLL_DOWN: "presentation",
    POINTER_ON: "pointer", POINTER_OFF: "pointer",
    ANNOTATION_DRAW: "annotation", ANNOTATION_HIGHLIGHT: "annotation",
    ANNOTATION_ERASE: "annotation", ANNOTATION_CLEAR: "annotation",
    QUIZ_START: "quiz", QUIZ_STOP: "quiz", QUIZ_NEXT: "quiz",
    QUIZ_PREV: "quiz", QUIZ_ANSWER: "quiz", QUIZ_REVEAL: "quiz",
    QUIZ_RESTART: "quiz",
    TIMER_START: "timer", TIMER_STOP: "timer",
}

SAFETY_TOGGLES = {PAUSE_PRESENTATION, POINTER_ON, POINTER_OFF}


# ---------------------------------------------------------------------------
# Gesture -> classroom action (presentation domain).
# ---------------------------------------------------------------------------
GESTURE_ACTIONS: dict[str, str] = {
    ge.SWIPE_LEFT: NEXT_SLIDE,
    ge.SWIPE_RIGHT: PREV_SLIDE,
    ge.SWIPE_UP: SCROLL_UP,
    ge.SWIPE_DOWN: SCROLL_DOWN,
    ge.CIRCLE_CW: ZOOM_IN,
    ge.CIRCLE_CCW: ZOOM_OUT,
    ge.PALM_HOLD: PAUSE_PRESENTATION,
}


class ClassroomIntentEngine:
    def __init__(self, language: str = "en"):
        self.language = language or SETTINGS.classroom.language
        self.last: Optional[ClassroomIntent] = None

    def set_language(self, language: str) -> None:
        self.language = language

    # ---- voice -------------------------------------------------------------
    def from_voice(self, result: cvoice.ClassroomVoiceResult,
                   quiz_active: bool = False) -> Optional[ClassroomIntent]:
        if result.intent in (vc.NONE_INTENT, ""):
            return None
        action = self._voice_to_action(result.intent)
        if action is None:
            return None
        params = dict(result.params)
        params["language"] = result.language
        params["confidence"] = result.confidence
        self.last = ClassroomIntent(
            action=action,
            params=params,
            confidence=result.confidence,
            source="voice",
            description=f"Voice {result.raw_text!r} -> {action}",
        )
        return self.last

    def _voice_to_action(self, intent: str) -> str | None:
        mapped = {
            vc.START_PRESENTATION: PRESENTATION_START,
            vc.END_PRESENTATION: PRESENTATION_STOP,
            vc.NEXT_SLIDE: NEXT_SLIDE,
            vc.PREV_SLIDE: PREV_SLIDE,
            vc.ZOOM_IN: ZOOM_IN,
            vc.ZOOM_OUT: ZOOM_OUT,
            vc.SCROLL_UP: SCROLL_UP,
            vc.SCROLL_DOWN: SCROLL_DOWN,
            cvoice.START_QUIZ: QUIZ_START,
            cvoice.STOP_QUIZ: QUIZ_STOP,
            cvoice.RESTART_QUIZ: QUIZ_RESTART,
            cvoice.NEXT_QUESTION: QUIZ_NEXT,
            cvoice.PREV_QUESTION: QUIZ_PREV,
            cvoice.REVEAL_ANSWER: QUIZ_REVEAL,
            cvoice.ANSWER_LETTER: QUIZ_ANSWER,
            cvoice.POINTER_ON: POINTER_ON,
            cvoice.POINTER_OFF: POINTER_OFF,
            cvoice.DRAW: ANNOTATION_DRAW,
            cvoice.HIGHLIGHT: ANNOTATION_HIGHLIGHT,
            cvoice.ERASE_ANNOTATION: ANNOTATION_ERASE,
            cvoice.CLEAR_ANNOTATIONS: ANNOTATION_CLEAR,
            cvoice.PAUSE_PRESENTATION: PAUSE_PRESENTATION,
            cvoice.NEXT_EXERCISE: NEXT_SLIDE,
            cvoice.START_TIMER: TIMER_START,
            cvoice.STOP_TIMER: TIMER_STOP,
        }
        return mapped.get(intent)

    # ---- gestures ----------------------------------------------------------
    def from_gesture(self, event: ge.GestureEvent) -> Optional[ClassroomIntent]:
        if event.kind == ge.REST:
            return None
        action = GESTURE_ACTIONS.get(event.kind)
        if action is None:
            return None
        self.last = ClassroomIntent(
            action=action,
            params={"event": event.kind, "x": event.x, "y": event.y,
                    "confidence": event.confidence},
            confidence=min(1.0, 0.6 + event.confidence),
            source="gesture",
            description=f"Gesture {event.kind} -> {action}",
        )
        return self.last

    # ---- context routing ---------------------------------------------------
    def route(self, intent: ClassroomIntent, quiz_active: bool) -> Optional[ClassroomIntent]:
        """Filter an intent based on the current classroom state.

        Rules:
          * safety toggles always pass (stop accidents, never blocked);
          * while a quiz is running, presentation/animation actions that are
            not quiz-related are diverted to the background (ignored) except
            pause/stop of the quiz itself;
          * pointer / annotation actions always pass.
        """
        if intent.action in SAFETY_TOGGLES:
            return intent
        domain = ACTION_DOMAIN.get(intent.action, "general")
        if quiz_active and domain in ("presentation", "annotation", "timer"):
            return None
        return intent


class AutoProfileManager:
    """Detects active window title to switch presentation/web/pdf intent profiles."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.current_profile = "default"

    def detect_profile(self, window_title: str) -> str:
        if not self.enabled:
            return "default"
        title = (window_title or "").lower()
        if any(k in title for k in ("powerpoint", "presentation", "pdf", "acrobat")):
            self.current_profile = "presentation"
        elif any(k in title for k in ("browser", "chrome", "edge")):
            self.current_profile = "web"
        elif any(k in title for k in ("spotify", "media", "vlc", "music", "video")):
            self.current_profile = "media"
        else:
            self.current_profile = "default"
        return self.current_profile