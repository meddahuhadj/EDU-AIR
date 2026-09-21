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
from typing import Optional

from hadj_no_touch.gestures import gesture_engine as ge
from hadj_no_touch.voice import voice_commands as vc

from . import voice as cvoice
from . import intent as ci
from .annotation import AnnotationModel, TOOL_NONE
from .backends import (
    ClassroomBackend, RealBackend, DemoBackend, RecordingBackend,
)
from .board import WhiteboardModel
from .classroom_status import ClassroomStatus
from .config import SETTINGS
from .journal import ClassJournal
from .lesson import LessonPlan, STEP_SLIDE, STEP_QUIZ, STEP_TIMER, STEP_BOARD
from .participation import ParticipationTracker
from .pointer import InteractivePointer
from .presentation import PresentationController, RecordingDriver
from .quiz import VoiceQuiz, QuestionBank
from .safety import (
    ClassroomSafetyEngine,
    SafetyDecision,
    RISK_SAFE, RISK_CONFIRM, RISK_CRITICAL,
)
from .touch.events import TouchEvent, TouchState
from . import wall_toolbar

__all__ = [
    "ClassroomBackend", "RealBackend", "DemoBackend", "RecordingBackend",
    "ClassroomStatus", "ClassroomSession",
    "MODE_CONTACTLESS", "MODE_WALL",
    "OUT_EXECUTED", "OUT_SIMULATED", "OUT_BLOCKED", "OUT_PENDING", "OUT_FAILED",
]

MODE_CONTACTLESS = "contactless"
MODE_WALL = "wall"

OUT_EXECUTED = "executed"
OUT_SIMULATED = "simulated"
OUT_BLOCKED = "blocked"
OUT_PENDING = "pending"
OUT_FAILED = "failed"


# ---------------------------------------------------------------------------
# The classroom session.
#
# ``ClassroomBackend``/``RealBackend``/``DemoBackend``/``RecordingBackend``
# now live in ``edu_air.backends``, and ``ClassroomStatus`` in
# ``edu_air.classroom_status`` -- both re-exported here (see ``__all__``)
# so existing ``from edu_air.classroom import ...`` call sites are
# unaffected by the split.
# ---------------------------------------------------------------------------
class ClassroomSession:
    def __init__(self, backend: ClassroomBackend | None = None,
                 settings=None, pointer: InteractivePointer | None = None,
                 presentation: PresentationController | None = None,
                 annotation: AnnotationModel | None = None,
                 board: WhiteboardModel | None = None,
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
        # Interactive whiteboard: each page owns its ink; ``annotation`` stays
        # the *current* page's model so every legacy drawing path (gestures,
        # touch, annotation actions) keeps working against the live page.
        if board is None:
            self.board = WhiteboardModel(self.settings.board, self.settings.annotation)
            if annotation is not None:
                self.board.pages[0].model = annotation
        else:
            self.board = board
        self.quiz = quiz or VoiceQuiz(QuestionBank(), self.settings.quiz)
        self.participation = ParticipationTracker()
        self.journal = ClassJournal()
        self.lesson = LessonPlan()
        self._lesson_timer_limit: float = 0.0
        self._touch_toolbar_active = False
        self.intent_engine = intent_engine or ci.ClassroomIntentEngine()
        self.safety = safety or ClassroomSafetyEngine()
        self.auto_approve = self.mode == "demo"
        self.control_locked = False
        self.interaction_mode = MODE_CONTACTLESS  # contactless | wall (see TOGGLE_WALL_MODE)
        self.domain = "idle"               # idle | presentation | quiz | annotation
        self._clock_s: float = 0.0
        self._timer_running = False
        self._fps = 0.0
        self._last_frame_t = time.monotonic()
        self.pending_confirmations: list[str] = []
        self.interaction_log: deque = deque(maxlen=120)
        self.status = ClassroomStatus(mode=self.mode)
        self._snapshot()

    # ---- whiteboard access ---------------------------------------------------
    @property
    def annotation(self) -> AnnotationModel:
        """The interactive board's current-page ink model (legacy API)."""
        return self.board.annotation

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

    def set_calibration_drift(self, suspected: bool) -> None:
        """Fed by ``SurfaceTouchDetector.drift`` (see ui.py's pipeline loop):
        the homography no longer seems to fit the room -- surfaced to the
        UI/HUD instead of silently keeping on writing at a possibly wrong
        spot. Clears itself once a fresh calibration run resets the
        detector's monitor."""
        self.status.calibration_drift = bool(suspected)
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

    @property
    def _pinch_ink_enabled(self) -> bool:
        """Pinch-click ink is only meaningful in contactless mode -- once
        wall mode is on, contact IS the click (see ``handle_touch_event``);
        navigation gestures (swipe/circle/palm, handled elsewhere) and the
        remote-cursor paths below stay available in both modes."""
        return self.interaction_mode != MODE_WALL

    def _handle_pointer_gesture(self, event: ge.GestureEvent) -> SafetyDecision | None:
        """Pointer-dependent gestures (move, click, drag, erase)."""
        x, y = event.x, event.y
        if self.pointer.position is not None:
            x, y = self.pointer.position

        tool = self.annotation.tool
        ink_ok = self._pinch_ink_enabled
        if event.kind == ge.MOVE:
            if self.pointer.visible and self.presentation.active and self.mode == "real":
                self.backend.move_cursor(int(x), int(y))
            self._set_interaction("point" if self.pointer.visible else "none")
            return None

        if event.kind == ge.LEFT_CLICK:
            norm = (x / max(1, self.pointer.screen_w), y / max(1, self.pointer.screen_h))
            if ink_ok and tool in ("draw", "highlight"):
                self.annotation.begin(norm)
                self._set_interaction(f"{tool} stroke start")
                self._snapshot()
                return SafetyDecision("ANNOTATION_DRAW", True, RISK_SAFE, False,
                                      "annotation stroke started")
            if ink_ok and tool == "point":
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
            if ink_ok and tool in ("draw", "highlight"):
                self.annotation.begin(norm)
                self._set_interaction(f"{tool} stroke")
                self._snapshot()
            return None

        if event.kind == ge.DRAG_UPDATE:
            norm = (x / max(1, self.pointer.screen_w), y / max(1, self.pointer.screen_h))
            if self.annotation.drawing:
                self.annotation.move(norm)
                self._snapshot()
            elif ink_ok and tool == "erase":
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

    # ---- wall/touch mode ---------------------------------------------------------
    def handle_touch_event(self, ev: TouchEvent) -> SafetyDecision | None:
        """Route one ``SurfaceTouchDetector`` event into the ink pipeline.

        Contact IS the click here: DOWN starts a stroke/dot/erase exactly
        where the pinch-click LEFT_CLICK path does for the contactless
        pointer, MOVE follows while touching, UP lifts the pen. Mirrors
        ``_handle_pointer_gesture`` -- per-stroke geometry is not re-audited
        every frame, only the tool selection (ANNOTATION_DRAW/HIGHLIGHT/
        ERASE) that already went through the safety gate when it was
        chosen.

        A DOWN inside the projected wall toolbar (``wall_toolbar.py``) is
        never ink: it fires that button's action instead, and every MOVE/UP
        of the same physical touch is swallowed (``_touch_toolbar_active``)
        so dragging off the toolbar afterward can never be misread as an
        erase/draw stroke."""
        if self.control_locked or self.interaction_mode != MODE_WALL:
            return None

        pos = (ev.x, ev.y)

        if ev.state == TouchState.DOWN:
            action = wall_toolbar.hit_test(pos)
            if action is not None:
                self._touch_toolbar_active = True
                return self.execute(ci.ClassroomIntent(action=action, source="touch"))
            self._touch_toolbar_active = False

        elif self._touch_toolbar_active:
            if ev.state == TouchState.UP:
                self._touch_toolbar_active = False
            return None

        tool = self.annotation.tool

        if ev.state == TouchState.DOWN:
            if tool in ("draw", "highlight"):
                self.annotation.begin(pos)
                self._set_interaction(f"{tool} touch start")
                self._snapshot()
                return SafetyDecision("ANNOTATION_DRAW", True, RISK_SAFE, False,
                                      "touch stroke started")
            if tool == "point":
                self.annotation.dot(pos)
                self._set_interaction("touch dot")
                self._snapshot()
                return SafetyDecision("ANNOTATION_DOT", True, RISK_SAFE, False,
                                      "touch dot added")
            if tool == "erase":
                self.annotation.erase_at(pos)
                self._set_interaction("touch erase")
                self._snapshot()
                return SafetyDecision("ANNOTATION_ERASE", True, RISK_SAFE, False,
                                      "touch erase")
            return None

        if ev.state == TouchState.MOVE:
            if self.annotation.drawing:
                self.annotation.move(pos)
                self._snapshot()
            elif tool == "erase":
                self.annotation.erase_at(pos)
                self._snapshot()
            return None

        if ev.state == TouchState.UP:
            self.annotation.finish()
            self._set_interaction("idle")
            self._snapshot()
            return None

        return None

    # ---- palm eraser ---------------------------------------------------------
    def handle_palm_wipe(self, pos_norm: tuple[float, float]) -> None:
        """One frame of an active palm wipe (see
        ``edu_air.touch.palm_eraser.PalmEraseDetector`` -- only called once
        the palm has already travelled far enough in contact to count as a
        deliberate wipe, never for a hand merely resting near the wall).
        Wall mode only, like the rest of the touch pipeline; a wide radius
        (``TouchSettings.palm_erase_radius``) mirrors a real whiteboard
        eraser rather than the narrow fingertip eraser tool."""
        if self.control_locked or self.interaction_mode != MODE_WALL:
            return
        removed = self.annotation.erase_at(pos_norm, radius_norm=self.settings.touch.palm_erase_radius)
        if removed:
            self._set_interaction("palm erase")
            self._snapshot()

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
        routed = self.intent_engine.route(intent, quiz_active=self.quiz.active,
                                          domain=self.domain,
                                          presentation_active=self.presentation.active)
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

    def _ensure_presentation_active(self) -> None:
        """Slide nav / zoom / scroll all imply an in-progress presentation.

        Without this, sending scroll or zoom straight through (bypassing
        ``start()``) moved the real deck but left ``presentation.state`` at
        IDLE forever — the HUD badge stayed stuck on INACTIF even while
        gesture/voice scroll commands were visibly working.
        """
        if not self.presentation.active:
            self.presentation.start(self.settings.presentation.total_slides)
        elif self.presentation.state == self.presentation.PAUSED:
            self.presentation.resume()

    def _apply(self, intent: ci.ClassroomIntent) -> str:
        """Run an approved classroom action on the right subsystem."""
        action = intent.action
        demo = self.mode == "demo"

        # Board domain focus: while the interactive whiteboard is the active
        # surface and no real presentation deck is running, slide navigation
        # (swipe gesture, PageUp/Down, generic "next"/"previous" voice)
        # advances the board pages instead.
        if (action in (ci.NEXT_SLIDE, ci.PREV_SLIDE)
                and self.domain == "board"
                and not self.presentation.active):
            action = ci.BOARD_NEXT_PAGE if action == ci.NEXT_SLIDE \
                else ci.BOARD_PREV_PAGE

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
            self._ensure_presentation_active()
            self.presentation.next_slide()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.PREV_SLIDE:
            self._ensure_presentation_active()
            self.presentation.prev_slide()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.PAUSE_PRESENTATION:
            self.presentation.pause()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.RESUME_PRESENTATION:
            self.presentation.resume()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.ZOOM_IN:
            self._ensure_presentation_active()
            self.presentation.zoom_in()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.ZOOM_OUT:
            self._ensure_presentation_active()
            self.presentation.zoom_out()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.SCROLL_UP:
            self._ensure_presentation_active()
            self.presentation.scroll_up()
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.SCROLL_DOWN:
            self._ensure_presentation_active()
            self.presentation.scroll_down()
            return OUT_EXECUTED if not demo else OUT_SIMULATED

        # --- pointer ----------------------------------------------------------
        if action == ci.POINTER_ON:
            self.pointer.visible = True
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.POINTER_OFF:
            self.pointer.visible = False
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.TOGGLE_WALL_MODE:
            self.interaction_mode = MODE_CONTACTLESS if self.interaction_mode == MODE_WALL else MODE_WALL
            # Keep the persisted "wall mode in use" flag in sync so the
            # per-frame detector's own enabled check (defense in depth
            # alongside the ui.py call-site gate) never silently disagrees
            # with the session's active interaction mode.
            self.settings.touch.enabled = (self.interaction_mode == MODE_WALL)
            self._set_interaction(f"mode: {self.interaction_mode}")
            return OUT_EXECUTED if not demo else OUT_SIMULATED

        # --- annotation ---------------------------------------------------------
        if action == ci.ANNOTATION_DRAW:
            self.board.set_tool("draw")
            self.domain = "annotation"
            self._set_interaction("draw")
            return OUT_EXECUTED
        if action == ci.ANNOTATION_HIGHLIGHT:
            self.board.set_tool("highlight")
            self.domain = "annotation"
            self._set_interaction("highlight")
            return OUT_EXECUTED
        if action == ci.ANNOTATION_ERASE:
            self.board.set_tool("erase")
            self.domain = "annotation"
            self._set_interaction("erase")
            return OUT_EXECUTED
        if action == ci.ANNOTATION_CLEAR:
            self.annotation.clear()
            self.board.set_tool(TOOL_NONE)
            self._set_interaction("annotations cleared")
            return OUT_EXECUTED

        # --- interactive board (TNI) --------------------------------------------
        if action == ci.BOARD_NEXT_PAGE:
            self.domain = "board"
            self.board.next_page()
            return OUT_EXECUTED
        if action == ci.BOARD_PREV_PAGE:
            self.domain = "board"
            self.board.prev_page()
            return OUT_EXECUTED
        if action == ci.BOARD_ADD_PAGE:
            self.domain = "board"
            self.board.add_page()
            return OUT_EXECUTED
        if action == ci.BOARD_CLEAR_PAGE:
            self.board.clear_current()
            return OUT_EXECUTED
        if action == ci.BOARD_DELETE_PAGE:
            self.domain = "board"
            self.board.delete_page()
            return OUT_EXECUTED
        if action == ci.BOARD_BACKGROUND:
            self.domain = "board"
            self.board.set_background(intent.params.get("name", "blank"))
            return OUT_EXECUTED
        if action == ci.BOARD_UNDO:
            self.domain = "board"
            self.board.undo()
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
            self._lesson_timer_limit = 0.0
            return OUT_EXECUTED
        if action == ci.TIMER_STOP:
            self._timer_running = False
            return OUT_EXECUTED

        # --- participation tally -------------------------------------------------------
        if action == ci.PARTICIPATION_MARK:
            rec = self.participation.mark()
            self._set_interaction(f"participation #{rec.index}")
            return OUT_EXECUTED if not demo else OUT_SIMULATED

        # --- lesson sequencer -----------------------------------------------------------
        if action == ci.LESSON_NEXT:
            self._apply_lesson_step(self.lesson.advance())
            return OUT_EXECUTED if not demo else OUT_SIMULATED
        if action == ci.LESSON_PREV:
            self.lesson.back()
            self._set_interaction(f"lesson: {self.lesson.progress_text()}")
            return OUT_EXECUTED if not demo else OUT_SIMULATED

        return OUT_FAILED

    def _apply_lesson_step(self, step) -> None:
        """Trigger the classroom action a lesson step stands for.

        Each step kind maps onto the exact same subsystem call a teacher
        would reach for by hand (``next_slide``/``quiz.start``/timer/
        board page) -- the plan is a named shortcut, not a new capability.
        A step of ``None`` (plan exhausted) only updates the status label.
        """
        if step is None:
            self._set_interaction(f"lesson: {self.lesson.progress_text()}")
            return
        if step.kind == STEP_SLIDE:
            self._ensure_presentation_active()
            self.presentation.next_slide()
        elif step.kind == STEP_QUIZ:
            if not self.quiz.active:
                self.quiz.start()
            self.domain = "quiz"
        elif step.kind == STEP_TIMER:
            self._timer_running = True
            self._clock_s = 0.0
            self._lesson_timer_limit = max(0.0, step.duration_s)
        elif step.kind == STEP_BOARD:
            self.domain = "board"
            self.board.next_page()
        self._set_interaction(f"lesson: {self.lesson.progress_text()}")

    def load_lesson_json(self, path) -> bool:
        """Load a lesson plan prepared ahead of class (see
        :meth:`edu_air.lesson.LessonPlan.load_json`). Returns False when the
        file is missing or unreadable (the current plan is left untouched)."""
        ok = self.lesson.load_json(path)
        if ok:
            self._set_interaction(f"lesson loaded: {self.lesson.progress_text()}")
        return ok

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
            if self._lesson_timer_limit and self._clock_s >= self._lesson_timer_limit:
                self._timer_running = False
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
        s.interaction_mode = self.interaction_mode
        s.clock_seconds = int(self._clock_s)
        s.timer_running = self._timer_running
        s.participation_count = self.participation.count
        s.lesson_progress = self.lesson.progress_text()
        s.annotation_tool = self.annotation.tool
        s.stroke_count = self.annotation.count
        s.board_page = self.board.current_index + 1
        s.board_pages = self.board.page_count
        s.board_background = self.board.current.background
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
        s.calibration_drift = bool(getattr(self.status, "calibration_drift", False))
        self.status = s