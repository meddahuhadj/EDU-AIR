"""Wall/touch mode wiring inside ClassroomSession: the TOGGLE_WALL_MODE
action, routing TouchEvent into the existing ink pipeline, and the
contactless/wall interaction split for pinch-click ink."""

from __future__ import annotations

import pytest

from hadj_no_touch.gestures import gesture_engine as ge

from edu_air.classroom import ClassroomSession, RecordingBackend, MODE_CONTACTLESS, MODE_WALL
from edu_air import intent as ci
from edu_air.config import PresentationSettings
from edu_air.presentation import PresentationController, RecordingDriver
from edu_air.touch.events import TouchEvent, TouchState


def make_session(mode: str = "demo") -> ClassroomSession:
    backend = RecordingBackend()
    pres = PresentationController(driver=RecordingDriver(), settings=PresentationSettings())
    sess = ClassroomSession(backend=backend, presentation=pres)
    sess.set_mode(mode)
    return sess


def test_starts_in_contactless_mode():
    sess = make_session()
    assert sess.interaction_mode == MODE_CONTACTLESS


def test_toggle_wall_mode_action_flips_mode_and_settings_flag():
    sess = make_session()
    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    assert sess.interaction_mode == MODE_WALL
    assert sess.settings.touch.enabled is True
    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    assert sess.interaction_mode == MODE_CONTACTLESS
    assert sess.settings.touch.enabled is False


def test_toggle_wall_mode_bypasses_confirmation():
    sess = make_session()
    sess.safety.set_confirmation_level("all")
    decision = sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    assert decision.allowed
    assert not decision.requires_confirmation


def test_touch_event_ignored_outside_wall_mode():
    sess = make_session()
    sess.annotation.set_tool("draw")
    ev = TouchEvent(x=0.5, y=0.5, state=TouchState.DOWN)
    result = sess.handle_touch_event(ev)
    assert result is None
    assert sess.annotation.count == 0


def test_touch_down_move_up_produces_one_stroke():
    sess = make_session()
    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    sess.annotation.set_tool("draw")
    sess.handle_touch_event(TouchEvent(x=0.2, y=0.2, state=TouchState.DOWN))
    sess.handle_touch_event(TouchEvent(x=0.3, y=0.3, state=TouchState.MOVE))
    sess.handle_touch_event(TouchEvent(x=0.4, y=0.4, state=TouchState.UP))
    assert sess.annotation.count == 1
    assert sess.annotation.strokes[0].points == [(0.2, 0.2), (0.3, 0.3)]


def test_touch_dot_tool_drops_a_single_point():
    sess = make_session()
    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    sess.annotation.set_tool("point")
    sess.handle_touch_event(TouchEvent(x=0.5, y=0.5, state=TouchState.DOWN))
    assert sess.annotation.count == 1
    assert sess.annotation.strokes[0].tool == "point"


def test_touch_erase_removes_nearby_stroke():
    sess = make_session()
    sess.annotation.set_tool("draw")
    sess.annotation.begin((0.5, 0.5))
    sess.annotation.finish()
    assert sess.annotation.count == 1

    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    sess.annotation.set_tool("erase")
    sess.handle_touch_event(TouchEvent(x=0.5, y=0.5, state=TouchState.DOWN))
    assert sess.annotation.count == 0


def test_pinch_click_ink_disabled_in_wall_mode_navigation_still_works():
    sess = make_session()
    sess.execute(ci.ClassroomIntent(ci.PRESENTATION_START, source="test"))
    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    sess.annotation.set_tool("draw")

    # pinch-click must no longer draw while wall mode is active...
    sess.handle_gesture(ge.GestureEvent(kind=ge.LEFT_CLICK, x=0.5, y=0.5, confidence=0.9))
    assert sess.annotation.count == 0
    assert not sess.annotation.drawing

    # ...but a navigation swipe still advances the slide.
    slide_before = sess.presentation.slide_index
    sess.handle_gesture(ge.GestureEvent(kind=ge.SWIPE_LEFT, x=0.5, y=0.5, confidence=0.9))
    assert sess.presentation.slide_index == slide_before + 1


def test_leaving_wall_mode_finishes_a_hanging_stroke():
    sess = make_session()
    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    sess.annotation.set_tool("draw")
    sess.handle_touch_event(TouchEvent(x=0.5, y=0.5, state=TouchState.DOWN))
    assert sess.annotation.drawing
    sess.annotation.finish()  # what the pipeline does on a mode transition
    assert not sess.annotation.drawing
    assert sess.annotation.count == 1
