"""Classroom session: the central state machine and intent executor.

Aggregates every EDU-AIR subsystem — interactive pointer, presentation
controller, air annotation, voice quiz, classroom timer, safety gate, intent
engine — behind one class that the UI, the demo runner and the tests share.

Inputs:
  * ``update_pointer(raw_norm)``   — webcam fingertip -> filtered pointer;
  * ``handle_gesture(event)``      — gesture engine events;
  * ``handle_voice_text(text)``    — recognised classroom voice.

Every input is converted to a :class:`ClassroomIntent` which must pass the
deny-by-default safety gate before it is executed. In demo mode execution is
simulated (nothing touches the OS); in real mode it drives the computer
through the injected backend (HADJ Win32 by default).
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from hadj_no_touch.gestures import gesture_engine as ge
from hadj_no_touch.voice import voice_commands as vc

from . import voice as cvoice
from . import intent as ci
from .annotation import AnnotationModel, TOOL_NONE
from .config import SETTINGS
from .pointer import InteractivePointer
from .presentation import PresentationController, RecordingDriver
from .quiz import VoiceQuiz, QuestionBank
from .safety import (
    ClassroomSafetyEngine,
    SafetyDecision,
    RISK_SAFE, RISK_CONFIRM, RISK_CRITICAL,
)

OUT_EXECUTED = "executed"
OUT_SIMULATED = "simulated"
OUT_BLOCKED = "blocked"
OUT_PENDING = "pending"
OUT_FAILED = "failed"


# ---------------------------------------------------------------------------
# OS backend abstraction (real classroom = HADJ Win32, demo/tests = recorded).
# ---------------------------------------------------------------------------
class ClassroomBackend:
    """Thin seam over the computer the classroom controls."""

    def key(self, name: str, modifiers: list[str] | None = None) -> None:
        raise NotImplementedError

    def wheel(self, amount: int) -> None:
        raise NotImplementedError

    def move_cursor(self, x: int, y: int) -> None:
        raise NotImplementedError

    def click_left(self, x: int | None = None, y: int | None = None) -> None:
        raise NotImplementedError

    def click_right(self, x: int | None = None, y: int | None = None) -> None:
        raise NotImplementedError


class RealBackend(ClassroomBackend):
    def __init__(self) -> None:
        from hadj_no_touch.windows import keyboard_control, mouse_control
        self._kc = keyboard_control
        self._mc = mouse_control

    def key(self, name, modifiers=None):
        self._kc.tap(name, modifiers)

    def wheel(self, amount):
        self._mc.scroll(amount)

    def move_cursor(self, x, y):
        self._mc.move_to(int(x), int(y))

    def click_left(self, x=None, y=None):
        self._mc.click_left(x, y)

    def click_right(self, x=None, y=None):
        self._mc.click_right(x, y)


class DemoBackend(ClassroomBackend):
    """Forgets every request — demo mode never touches the OS."""

    def key(self, name, modifiers=None):
        pass

    def wheel(self, amount):
        pass

    def move_cursor(self, x, y):
        pass

    def click_left(self, x=None, y=None):
        pass

    def click_right(self, x=None, y=None):
        pass


class RecordingBackend(ClassroomBackend):
    """Records every request for tests / the report."""

    def __init__(self) -> None:
        self.keys: list[tuple[str, list]] = []
        self.wheels: list[int] = []
        self.cursor_moves: list[tuple[int, int]] = []
        self.left_clicks: list[tuple[int, int]] = []
        self.right_clicks: list[tuple[int, int]] = []

    def key(self, name, modifiers=None):
        self.keys.append((name, list(modifiers or [])))

    def wheel(self, amount):
        self.wheels.append(amount)

    def move_cursor(self, x, y):
        self.cursor_moves.append((int(x), int(y)))

    def click_left(self, x=None, y=None):
        self.left_clicks.append((int(x) if x is not None else None,
                                 int(y) if y is not None else None))

    def click_right(self, x=None, y=None):
        self.right_clicks.append((int(x) if x is not None else None,
                                  int(y) if y is not None else None))

    @property
    def key_sequence(self) -> list[str]:
        return [name for name, _ in self.keys]


# ---------------------------------------------------------------------------
# Status snapshot consumed by the HUD / overlay.
# ---------------------------------------------------------------------------
@dataclass
class ClassroomStatus:
    mode: str = "real"                     # real | demo
    detector: str = ""
    fps: float = 0.0
    # presentation
    presentation_state: str = "idle"       # idle | active | paused
    current_slide: int = 0
    total_slides: int = 0
    # pointer
    pointer_visible: bool = True
    pointer_pos: tuple = (0, 0)
    pointer_tremor: float = 0.0
    pointer_spikes: int = 0
    # interaction
    last_command: str = ""
    last_event: str = ""
    current_interaction: str = "none"
    gesture: str = ""
    control_locked: bool = False
    # classroom timer
    clock_seconds: int = 0
    timer_running: bool = False
    # annotation
    annotation_tool: str = TOOL_NONE
    stroke_count: int = 0
    # quiz
    quiz_active: bool = False
    quiz_state: str = "idle"
    quiz_score: tuple = (0, 0)             # (correct, wrong)
    quiz_question_n: int = 0
    quiz_question: str = ""
    quiz_options: list = field(default_factory=list)
    quiz_revealed: bool = False
    # safety
    last_decision: str = ""
    confirmed_required: int = 0
    # environment (traffic light)
    lighting: str = "unknown"          # dark | low | good | bright
    ambient_noise: str = "unknown"     # ok | loud
    hand_visible: bool = False
    performance_mode: bool = False


# ---------------------------------------------------------------------------
# The classroom session.
# ---------------------------------------------------------------------------
class ClassroomSession:
    def __init__(self, backend: ClassroomBackend | None = None,
                 settings=None, pointer: InteractivePointer | None = None,
                 presentation: PresentationController | None = None,
                 annotation: AnnotationModel | None = None,
                 quiz: VoiceQuiz | None = None,
                 intent_engine: ci.ClassroomIntentEngine | None = None,
                 safety: ClassroomSafetyEngine | None = None):
        self.settings = settings or SETTINGS
        self.backend = backend or RealBackend()
        self.mode = self.settings.classroom.mode
        self.pointer = pointer or InteractivePointer(1280, 720, self.settings.pointer)
        self.presentation = presentation or PresentationController(
            driver=self._make_presentation_driver(), settings=self.settings.presentation)
        self.presentation.on_record = self._on_command_record
        if self.mode == "demo":
            self.presentation.suppress_launch = True
        self.annotation = annotation or AnnotationModel(self.settings.annotation)
        self.quiz = quiz or VoiceQuiz(QuestionBank(), self.settings.quiz)
        self.intent_engine = intent_engine or ci.ClassroomIntentEngine()
        self.safety = safety or ClassroomSafetyEngine()
        self.auto_approve = self.mode == "demo"
        self.control_locked = False
        self.domain = "idle"               # idle | presentation | quiz | annotation
        self._clock_s: float = 0.0
        self._timer_running = False
        self._fps = 0.0
        self._last_frame_t = time.monotonic()
        self.pending_confirmations: list[str] = []
        self.interaction_log: deque = deque(maxlen=120)
        self.status = ClassroomStatus(mode=self.mode)
        self._snapshot()

    # ---- wiring ------------------------------------------------------------
    def _make_presentation_driver(self):
        if self.mode == "demo":
            return RecordingDriver()
        try:
            from .presentation import _default_driver
            return _default_driver()
        except Exception:
            return RecordingDriver()

    def _on_command_record(self, rec) -> None:
        self._record(f"presentation.{rec.command}", rec.note or "")

    def set_mode(self, mode: str) -> None:
        if mode not in ("real", "demo"):
            return
        self.mode = mode
        self.auto_approve = mode == "demo"
        self.presentation.suppress_launch = mode == "demo"
        self.status.mode = mode
        self._snapshot()

    def set_language(self, language: str) -> None:
        self.settings.classroom.language = language
        self.intent_engine.set_language(language)

    # ---- environment -----------------------------------------------------------
    def set_environment(self, *, lighting: str | None = None,
                        ambient_noise: str | None = None,
                        hand_visible: bool | None = None) -> None:
        """Feed classroom-environment estimates (lighting / noise / hand in
        frame). Values survive the status snapshot cycle; demo mode can also
        feed a healthy synthetic environment."""
        if lighting is not None:
            self.status.lighting = lighting
        if ambient_noise is not None:
            self.status.ambient_noise = ambient_noise
        if hand_visible is not None:
            self.status.hand_visible = bool(hand_visible)
        self._snapshot()

    def set_performance(self, on: bool) -> None:
        """Toggle the low-CPU classroom preset (pipeline re-reads it live)."""
        self.settings.classroom.performance_mode = bool(on)
        self._snapshot()

    # ---- inputs ---------------------------------------------------------------
    def update_pointer(self, raw_norm: tuple[float, float] | None) -> tuple[float, float] | None:
        """Feed the raw fingertip; stores/returns filtered screen position."""
        pos = self.pointer.update(raw_norm)
        self._snapshot()
        return pos

    def handle_gesture(self, event: ge.GestureEvent) -> SafetyDecision | None:
        """Process one gesture-engine event. Returns the safety decision of
        the action it triggered (or None when nothing fired)."""
        self.status.gesture = event.gesture or event.kind
        self.status.last_event = event.kind
        self._snapshot()
        if self.control_locked and event.kind not in (ge.FIST_LOCK,):
            return None

        # --- annotation strokes / clicks -------------------------------------
        decision = self._handle_pointer_gesture(event)
        if decision is not None:
            return decision

        # --- discrete gesture -> classroom action ------------------------------
        if event.kind in (ge.REST, ge.MOVE, ge.LEFT_CLICK, ge.RIGHT_CLICK,
                          ge.DRAG_START, ge.DRAG_UPDATE, ge.DRAG_END,
                          ge.SCROLL_V, ge.SCROLL_H, ge.DOUBLE_CLICK):
            return None
        intent = self.intent_engine.from_gesture(event)
        if intent is None:
            return None
        return self.execute(intent)

    def _handle_pointer_gesture(self, event: ge.GestureEvent) -> SafetyDecision | None:
        """Pointer-dependent gestures (move, click, drag, erase)."""
        x, y = event.x, event.y
        if self.pointer.position is not None:
            x, y = self.pointer.position

        tool = self.annotation.tool
        if event.kind == ge.MOVE:
            if self.pointer.visible and self.presentation.active and self.mode == "real":
                self.backend.move_cursor(int(x), int(y))
            self._set_interaction("point" if self.pointer.visible else "none")
            return None

        if event.kind == ge.LEFT_CLICK:
            norm = (x / max(1, self.pointer.screen_w), y / max(1, self.pointer.screen_h))
            if tool in ("draw", "highlight"):
                self.annotation.begin(norm)
                self._set_interaction(f"{tool} stroke start")
                self._snapshot()
                return SafetyDecision("ANNOTATION_DRAW", True, RISK_SAFE, False,
                                      "annotation stroke started")
            if tool == "point":
                self.annotation.dot(norm)
                self._set_interaction("dot dropped")
                self._snapshot()
                return SafetyDecision("ANNOTATION_DOT", True, RISK_SAFE, False,
                                      "annotation dot added")
            if self.pointer.visible and self.mode == "real":
                self.backend.click_left(int(x), int(y))
                self._record("CLICK", f"click @ ({int(x)},{int(y)})")
            return None

        if event.kind == ge.DRAG_START:
            norm = (x / max(1, self.pointer.screen_w), y / max(1, self.pointer.screen_h))
            if tool in ("draw", "highlight"):
                self.annotation.begin(norm)
                self._set_interaction(f"{tool} stroke")
                self._snapshot()
            return None

        if event.kind == ge.DRAG_UPDATE:
            norm = (x / max(1, self.pointer.screen_w), y / max(1, self.pointer.screen_h))
            if self.annotation.drawing:
                self.annotation.move(norm)
                self._snapshot()
            elif tool == "erase":
                self.annotation.erase_at(norm)
                self._set_interaction("erase")
                self._snapshot()
            elif self.mode == "real":
                self.backend.move_cursor(int(x), int(y))
            return None

        if event.kind == ge.DRAG_END:
            self.annotation.finish()
            self._set_interaction("idle")
            self._snapshot()
            return None

        return None

    # ---- voice -----------------------------------------------------------------
    def handle_voice_text(self, text: str, language: str | None = None) -> SafetyDecision | None:
        """Recognised speech -> classroom intent -> safety-approved action."""
        lang = language or self.settings.classroom.language
        result = cvoice.parse(text, lang)
        if result.intent == vc.NONE_INTENT or result.intent in (None, "NONE"):
            return None
        intent = self.intent_engine.from_voice(result, quiz_active=self.quiz.active)
        if intent is None:
            return None
        routed = self.intent_engine.route(intent, quiz_active=self.quiz.active)
        if routed is None:
            return None
        return self.execute(routed)

    # ---- execution (through the safety gate) ------------------------------------
    def execute(self, intent: ci.ClassroomIntent) -> SafetyDecision:
        decision = self.safety.decide(intent.action)
        if not decision.allowed:
            self.safety.audit(intent.action, OUT_BLOCKED, decision.reason)
            self._record(intent.action, decision.reason, outcome=OUT_BLOCKED)
            self._snap_decision(decision)
            return decision

        if decision.requires_confirmation:
            if not self.auto_approve:
                self.pending_confirmations.append(intent.action)
                self.safety.audit(intent.action, OUT_PENDING, decision.reason)
                self._record(intent.action, "awaiting confirmation", outcome=OUT_PENDING)
                self._snap_decision(decision)
                return decision
            decision = SafetyDecision(intent.action, True, decision.risk, False,
                                      decision.reason + " (auto-approved in demo)")

        outcome = self._apply(intent) if decision.allowed else OUT_FAILED
        label = OUT_SIMULATED if (self.mode == "demo" and outcome == OUT_EXECUTED) else outcome
        self.safety.audit(intent.action, label, decision.reason)
        self._record(intent.action, decision.reason, outcome=label)
        self.status.last_command = intent.action
        self._snap_decision(decision)
        self._snapshot()
        return decision

    def _apply(self, intent: ci.ClassroomIntent) -> str:
        """Run an approved classroom action on the right subsystem."""
        action = intent.action
        demo = self.mode == "demo"

        # --- presentation ---------------------------------------------------
        if action in (ci.PRESENTATION_START,):
            self.domain = "presentation"
            self.presentation.start(self.settings.presentation.total_slides)
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.PRESENTATION_STOP:
            self.presentation.stop()
            self.domain = "idle"
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.NEXT_SLIDE:
            if not self.presentation.active:
                self.presentation.start(self.settings.presentation.total_slides)
            elif self.presentation.state == self.presentation.PAUSED:
                self.presentation.resume()
            self.presentation.next_slide()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.PREV_SLIDE:
            if not self.presentation.active:
                self.presentation.start(self.settings.presentation.total_slides)
            elif self.presentation.state == self.presentation.PAUSED:
                self.presentation.resume()
            self.presentation.prev_slide()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.PAUSE_PRESENTATION:
            self.presentation.pause()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.RESUME_PRESENTATION:
            self.presentation.resume()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.ZOOM_IN:
            self.presentation.zoom_in()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.ZOOM_OUT:
            self.presentation.zoom_out()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.SCROLL_UP:
            self.presentation.scroll_up()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.SCROLL_DOWN:
            self.presentation.scroll_down()
            return OUT_EXECUTED if not demo else OUT_SIMULATED

        # --- pointer ----------------------------------------------------------
        if action == ci.POINTER_ON:
            self.pointer.visible = True
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.POINTER_OFF:
            self.pointer.visible = False
            return OUT_EXECUTED if not demo else OUT_SIMULATED

        # --- annotation ---------------------------------------------------------
        if action == ci.ANNOTATION_DRAW:
            self.annotation.set_tool("draw")
            self.domain = "annotation"
            self._set_interaction("draw")
            return OUT_EXECUTED
        if action == ci.ANNOTATION_HIGHLIGHT:
            self.annotation.set_tool("highlight")
            self.domain = "annotation"
            self._set_interaction("highlight")
            return OUT_EXECUTED
        if action == ci.ANNOTATION_ERASE:
            self.annotation.set_tool("erase")
            self.domain = "annotation"
            self._set_interaction("erase")
            return OUT_EXECUTED
        if action == ci.ANNOTATION_CLEAR:
            self.annotation.clear()
            self.annotation.set_tool(TOOL_NONE)
            self._set_interaction("annotations cleared")
            return OUT_EXECUTED

        # --- quiz ----------------------------------------------------------------
        if action == ci.QUIZ_START:
            self.quiz.start()
            self.domain = "quiz"
            return OUT_EXECUTED
        if action == ci.QUIZ_STOP:
            self.quiz.stop()
            self.domain = "idle"
            return OUT_EXECUTED
        if action == ci.QUIZ_NEXT:
            self.quiz.next_question()
            return OUT_EXECUTED
        if action == ci.QUIZ_PREV:
            self.quiz.prev_question()
            return OUT_EXECUTED
        if action == ci.QUIZ_RESTART:
            self.quiz.restart()
            return OUT_EXECUTED
        if action == ci.QUIZ_REVEAL:
            self.quiz.reveal()
            return OUT_EXECUTED
        if action == ci.QUIZ_ANSWER:
            idx = intent.params.get("answer_index", -1)
            if idx < 0:
                letter = str(intent.params.get("letter", "")).lower()
                idx = cvoice.LETTER_TO_INDEX.get(letter, -1)
            if idx < 0 or not self.quiz.active:
                return OUT_FAILED
            self.quiz.answer(idx)
            return OUT_EXECUTED

        # --- timer ----------------------------------------------------------------
        if action == ci.TIMER_START:
            self._timer_running = True
            self._clock_s = 0.0
            return OUT_EXECUTED
        if action == ci.TIMER_STOP:
            self._timer_running = False
            return OUT_EXECUTED

        return OUT_FAILED

    # ---- api for the UI / tests ------------------------------------------------
    def approve_pending(self) -> list[str]:
        approved = list(self.pending_confirmations)
        self.pending_confirmations.clear()
        for action in approved:
            decision = self.safety.decide(action)
            if decision.allowed:
                intent = ci.ClassroomIntent(action=action, source="ui")
                outcome = self._apply(intent)
                label = OUT_SIMULATED if (self.mode == "demo" and outcome == OUT_EXECUTED) else outcome
                self.safety.audit(action, label, decision.reason)
                self._record(action, "user approved", outcome=label)
                self.status.last_command = action
                self._snap_decision(decision)
                self._snapshot()
        return approved

    def acknowledge_pending(self, action: str, allow: bool) -> Optional[SafetyDecision]:
        if action in self.pending_confirmations:
            self.pending_confirmations.remove(action)
        if not allow:
            self.safety.audit(action, OUT_BLOCKED, "user denied confirmation")
            return SafetyDecision(action, False, RISK_CONFIRM, False, "user denied")
        decision = self.safety.decide(action)
        if decision.allowed:
            intent = ci.ClassroomIntent(action=action, source="ui")
            return self.execute(intent)
        return decision

    # ---- clock/metrics -------------------------------------------------------------
    def tick(self, dt: float | None = None) -> None:
        now = time.monotonic()
        dt = dt if dt is not None else now - self._last_frame_t
        self._last_frame_t = now
        if dt > 0:
            self._fps = self._fps * 0.9 + (1.0 / dt) * 0.1
        self.quiz.tick(dt)
        if self._timer_running:
            self._clock_s += dt
        self._snapshot()

    # ---- status -------------------------------------------------------------------
    @property
    def pending_count(self) -> int:
        return len(self.pending_confirmations)

    def _set_interaction(self, label: str) -> None:
        self.status.current_interaction = label

    def _snap_decision(self, decision: SafetyDecision) -> None:
        self.status.last_decision = (
            f"{decision.action}:{'ALLOWED' if decision.allowed else 'DENIED'}"
            f"{' (confirm)' if decision.requires_confirmation else ''}"
        )

    def _record(self, action: str, note: str, outcome: str = OUT_EXECUTED) -> None:
        self.interaction_log.append({"ts": time.monotonic(), "action": action,
                                     "note": note, "outcome": outcome})

    def _snapshot(self) -> None:
        s = ClassroomStatus(mode=self.mode)
        s.detector = "demo (synthetic)" if self.mode == "demo" else "camera tracker"
        s.fps = round(self._fps, 1)
        s.presentation_state = self.presentation.state
        s.current_slide = self.presentation.slide_index + 1
        s.total_slides = self.presentation.total_slides
        s.pointer_visible = self.pointer.visible
        if self.pointer.position:
            s.pointer_pos = (round(self.pointer.position[0], 1),
                             round(self.pointer.position[1], 1))
        s.pointer_tremor = round(self.pointer.metrics.tremor_px, 2)
        s.pointer_spikes = self.pointer.metrics.spikes_rejected
        s.last_command = self.status.last_command
        s.last_event = self.status.last_event
        s.current_interaction = self.status.current_interaction
        s.gesture = self.status.gesture
        s.control_locked = self.control_locked
        s.clock_seconds = int(self._clock_s)
        s.timer_running = self._timer_running
        s.annotation_tool = self.annotation.tool
        s.stroke_count = self.annotation.count
        s.quiz_active = self.quiz.active
        s.quiz_state = self.quiz.state
        s.quiz_score = (self.quiz.stats.correct, self.quiz.stats.wrong)
        s.quiz_question_n = self.quiz.current_question_idx + 1
        if self.quiz.question is not None:
            s.quiz_question = self.quiz.question.text
            s.quiz_options = list(self.quiz.question.options)
        s.quiz_revealed = self.quiz.revealed
        s.last_decision = self.status.last_decision
        s.confirmed_required = len(self.pending_confirmations)
        s.lighting = getattr(self.status, "lighting", "unknown")
        s.ambient_noise = getattr(self.status, "ambient_noise", "unknown")
        s.hand_visible = bool(getattr(self.status, "hand_visible", False))
        s.performance_mode = bool(getattr(self.settings.classroom,
                                          "performance_mode", False))
        self.status = s