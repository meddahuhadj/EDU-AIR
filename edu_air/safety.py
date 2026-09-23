"""EDU-AIR classroom safety.

A deny-by-default gate in front of every classroom action. Only actions that
are *registered* in the classroom action catalogue may run; everything else —
including anything an LLM or a typo could produce from natural language — is
refused.

Risk model (mirrors HADJ):
  SAFE      — runs freely (slide nav, pointer, zoom, quiz state…);
  CONFIRM   — requires a confirmation prompt first (e.g. clearing the board);
  CRITICAL  — always an explicit confirmation (e.g. ending the presentation
              while a quiz is live is never auto-approved).

Safety toggles (pause/stop/lock) bypass confirmations so a reflexive command
can always stop an accident.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from hadj_no_touch.safety import ActionSpec

from .intent import (
    PRESENTATION_START, PRESENTATION_STOP, NEXT_SLIDE, PREV_SLIDE,
    PAUSE_PRESENTATION, RESUME_PRESENTATION, ZOOM_IN, ZOOM_OUT, SCROLL_UP, SCROLL_DOWN,
    POINTER_ON, POINTER_OFF, MICRO_GESTURES_TOGGLE,
    ANNOTATION_DRAW, ANNOTATION_HIGHLIGHT, ANNOTATION_ERASE, ANNOTATION_CLEAR,
    ANNOTATION_SHAPE, LESSON_SAVE,
    QUIZ_START, QUIZ_STOP, QUIZ_NEXT, QUIZ_PREV, QUIZ_ANSWER, QUIZ_REVEAL,
    QUIZ_RESTART, TIMER_START, TIMER_STOP,
    GEOMETRY_START, LAB3D_START, LAB3D_ROTATE, LAB3D_EXPLODE, AI_TEACHER_ASK,
    SAFETY_TOGGLES,
)

RISK_SAFE = "safe"
RISK_CONFIRM = "confirm"
RISK_CRITICAL = "critical"


@dataclass
class SafetyDecision:
    action: str
    allowed: bool
    risk: str
    requires_confirmation: bool
    reason: str = ""


def _safe(action: str, description: str) -> ActionSpec:
    return ActionSpec(action, description, RISK_SAFE, "classroom")


def _confirm(action: str, description: str) -> ActionSpec:
    return ActionSpec(action, description, RISK_CONFIRM, "classroom")


def _critical(action: str, description: str) -> ActionSpec:
    return ActionSpec(action, description, RISK_CRITICAL, "classroom")


CLASSROOM_ACTIONS: list[ActionSpec] = [
    # --- presentation --------------------------------------------------------
    _safe(PRESENTATION_START, "Start the slideshow"),
    _safe(PRESENTATION_STOP, "End the slideshow"),
    _safe(NEXT_SLIDE, "Next slide"),
    _safe(PREV_SLIDE, "Previous slide"),
    _safe(PAUSE_PRESENTATION, "Pause presentation (black screen)"),
    _safe(RESUME_PRESENTATION, "Resume presentation (clear black screen)"),
    _safe(ZOOM_IN, "Zoom in"),
    _safe(ZOOM_OUT, "Zoom out"),
    _safe(SCROLL_UP, "Scroll up"),
    _safe(SCROLL_DOWN, "Scroll down"),
    # --- interactive pointer & micro-gestures ---------------------------------
    _safe(POINTER_ON, "Show the pointer"),
    _safe(POINTER_OFF, "Hide the pointer"),
    _safe(MICRO_GESTURES_TOGGLE, "Toggle micro-gesture anti-fatigue mode"),
    # --- air annotation -------------------------------------------------------
    _safe(ANNOTATION_DRAW, "Use the drawing pen"),
    _safe(ANNOTATION_HIGHLIGHT, "Use the highlighter"),
    _safe(ANNOTATION_ERASE, "Use the eraser"),
    _safe(ANNOTATION_SHAPE, "Use the geometric shape tool"),
    _safe(LESSON_SAVE, "Save/export lesson notes to image"),
    _confirm(ANNOTATION_CLEAR, "Clear all annotations"),
    # --- voice quiz -------------------------------------------------------------
    _safe(QUIZ_START, "Start the quiz"),
    _safe(QUIZ_NEXT, "Next question"),
    _safe(QUIZ_PREV, "Previous question"),
    _safe(QUIZ_ANSWER, "Submit an answer"),
    _safe(QUIZ_REVEAL, "Reveal the answer"),
    _safe(QUIZ_RESTART, "Restart the quiz"),
    _critical(QUIZ_STOP, "End the quiz session"),
    # --- classroom timer ---------------------------------------------------------
    _safe(TIMER_START, "Start the classroom timer"),
    _safe(TIMER_STOP, "Stop the classroom timer"),
    # --- interactive geometry, 3d lab & ai teacher ------------------------------
    _safe(GEOMETRY_START, "Start dynamic geometry mode"),
    _safe(LAB3D_START, "Open 3D science lab"),
    _safe(LAB3D_ROTATE, "Rotate 3D model"),
    _safe(LAB3D_EXPLODE, "Toggle 3D exploded view"),
    _safe(AI_TEACHER_ASK, "Ask AI teacher copilot"),
]


class ClassroomActionRegistry:
    """The controlled catalogue of classroom actions (deny-by-default)."""

    def __init__(self) -> None:
        self._specs: dict[str, ActionSpec] = {}
        self.register_many(CLASSROOM_ACTIONS)

    def register(self, spec: ActionSpec) -> None:
        self._specs[spec.action] = spec

    def register_many(self, specs: list[ActionSpec]) -> None:
        for s in specs:
            self.register(s)

    def spec(self, action: str) -> ActionSpec | None:
        return self._specs.get(action)

    def known(self, action: str) -> bool:
        return action in self._specs

    def risk(self, action: str) -> str:
        spec = self._specs.get(action)
        return spec.risk if spec else RISK_SAFE

    def describe(self, action: str) -> str:
        spec = self._specs.get(action)
        return spec.description if spec else action

    def all(self) -> list[ActionSpec]:
        return list(self._specs.values())

    def ids(self) -> list[str]:
        return sorted(self._specs)


class ClassroomSafetyEngine:
    """Evaluates every classroom intent against the registered catalogue."""

    def __init__(self, registry: ClassroomActionRegistry | None = None,
                 confirmation_level: str = "smart",
                 allowed_actions: list[str] | None = None):
        self.registry = registry or ClassroomActionRegistry()
        self.confirmation_level = confirmation_level          # none | smart | all
        self.allowed_actions: set[str] = set(allowed_actions or [])
        self._audit: list[dict] = []
        self._max_audit = 300
        self.on_audit = None

    def set_confirmation_level(self, level: str) -> None:
        if level in ("none", "smart", "all"):
            self.confirmation_level = level

    def set_allowed_actions(self, actions: list[str] | None) -> None:
        self.allowed_actions = set(actions or [])

    def _is_allowed(self, action: str) -> bool:
        if not self.registry.known(action):
            return False
        if self.allowed_actions and action not in self.allowed_actions:
            return False
        return True

    def decide(self, action: str, needs_confirmation: bool = False) -> SafetyDecision:
        if not self._is_allowed(action):
            return SafetyDecision(
                action=action, allowed=False,
                risk=self.registry.risk(action),
                requires_confirmation=False,
                reason="action not in the classroom catalogue — denied by default",
            )
        spec = self.registry.spec(action)
        risk = spec.risk
        level = self.confirmation_level
        if risk == RISK_CRITICAL:
            requires = True
        elif risk == RISK_CONFIRM:
            requires = {"none": False, "smart": True, "all": True}[level]
        elif level == "all" and action not in SAFETY_TOGGLES:
            requires = True
        else:
            requires = needs_confirmation
        return SafetyDecision(
            action=action, allowed=True, risk=risk,
            requires_confirmation=requires,
            reason=f"{spec.description} [{risk}]",
        )

    def audit(self, action: str, outcome: str, reason: str = "") -> None:
        self._audit.append({
            "ts": time.monotonic(),
            "action": action,
            "outcome": outcome,
            "reason": reason,
        })
        if len(self._audit) > self._max_audit:
            self._audit = self._audit[-self._max_audit:]
        if self.on_audit is not None:
            try:
                self.on_audit(self._audit[-1])
            except Exception:
                pass

    def recent_audit(self, n: int = 40) -> list[dict]:
        return self._audit[-n:]