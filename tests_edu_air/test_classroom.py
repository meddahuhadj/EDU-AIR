"""ClassroomSession end-to-end (no hardware): voice, gestures, safety gating,
demo simulation and backend recording."""

from __future__ import annotations

import pytest

from hadj_no_touch.gestures import gesture_engine as ge

from edu_air.classroom import (
    ClassroomSession, RecordingBackend,
)
from edu_air.config import PresentationSettings
from edu_air.demo import DemoSession, default_script
from edu_air.presentation import PresentationController, RecordingDriver


def make_session(mode: str = "demo") -> "tuple[ClassroomSession, RecordingBackend]":
    backend = RecordingBackend()
    pres = PresentationController(driver=RecordingDriver(),
                                  settings=PresentationSettings())
    sess = ClassroomSession(backend=backend, presentation=pres)
    sess.set_mode(mode)
    return sess, backend


def test_demo_session_runs_three_languages_end_to_end():
    for lang in ("en", "fr", "ar"):
        sess, backend = make_session("demo")
        DemoSession(sess, default_script(lang), lang).run_all()
        st = sess.status
        assert st.presentation_state == "active"
        assert st.current_slide == 2
        assert st.quiz_state == "idle"
        assert st.quiz_score == (1, 1)
        assert len(sess.interaction_log) >= 9
        # demo mode: no OS keys ever sent
        assert backend.key_sequence == []


def test_real_mode_sends_keys_to_presentation_driver():
    sess, _ = make_session("real")
    sess.handle_voice_text("start presentation", "en")
    sess.handle_voice_text("next slide", "en")
    driver = sess.presentation.driver
    assert isinstance(driver, RecordingDriver)
    assert driver.key_sequence == ["F5", "RIGHT"]


def test_unknown_voice_is_ignored_safely():
    sess, _ = make_session("demo")
    d = sess.handle_voice_text("gibberish word xyz")
    assert d is None


def test_gesture_swipe_advances_slide():
    sess, _ = make_session("demo")
    sess.handle_voice_text("start presentation", "en")
    sess.handle_gesture(ge.GestureEvent(kind=ge.SWIPE_LEFT, x=0.5, y=0.5,
                                        confidence=0.9))
    assert sess.status.current_slide == 2


def test_gesture_circle_zooms():
    sess, _ = make_session("demo")
    sess.handle_gesture(ge.GestureEvent(kind=ge.CIRCLE_CW, x=0.5, y=0.5))
    assert sess.status.last_command == "ZOOM_IN"


def test_quiz_stop_is_critical_and_pending_without_approval():
    sess, _ = make_session("real")
    sess.auto_approve = False
    sess.handle_voice_text("start quiz", "en")
    assert sess.quiz.active
    d = sess.handle_voice_text("end quiz", "en")
    assert d is not None and d.requires_confirmation
    assert sess.quiz.active  # not stopped until approved
    assert sess.pending_count == 1


def test_approve_pending_executes_quiz_stop():
    sess, _ = make_session("real")
    sess.auto_approve = False
    sess.handle_voice_text("start quiz", "en")
    sess.handle_voice_text("end quiz", "en")
    approved = sess.approve_pending()
    assert approved == ["QUIZ_STOP"]
    assert not sess.quiz.active


def test_deny_pending_keeps_quiz_running():
    sess, _ = make_session("real")
    sess.auto_approve = False
    sess.handle_voice_text("start quiz", "en")
    sess.handle_voice_text("end quiz", "en")
    d = sess.acknowledge_pending("QUIZ_STOP", allow=False)
    assert d is not None and not d.allowed
    assert sess.quiz.active
    assert sess.pending_count == 0


def test_annotation_draw_from_gesture():
    sess, _ = make_session("demo")
    sess.handle_voice_text("drawing mode", "en")
    sess.pointer.update((0.5, 0.5))
    sess.handle_gesture(ge.GestureEvent(kind=ge.DRAG_START, x=0.5, y=0.5))
    sess.handle_gesture(ge.GestureEvent(kind=ge.DRAG_UPDATE, x=0.6, y=0.5))
    sess.handle_gesture(ge.GestureEvent(kind=ge.DRAG_END, x=0.6, y=0.5))
    assert sess.annotation.count == 1


def test_clear_annotations_requires_confirm_in_real_mode():
    sess, _ = make_session("real")
    sess.auto_approve = False
    sess.handle_voice_text("drawing mode", "en")
    sess.annotation.begin((0.5, 0.5))
    sess.annotation.finish()
    d = sess.handle_voice_text("clear the annotations", "en")
    assert d is not None and d.requires_confirmation
    assert sess.annotation.count == 1


def test_demo_mode_auto_approves_clear():
    sess, _ = make_session("demo")
    sess.annotation.begin((0.5, 0.5))
    sess.annotation.finish()
    sess.handle_voice_text("clear the annotations", "en")
    assert sess.annotation.count == 0


def test_timer_runs_through_tick():
    sess, _ = make_session("demo")
    sess.handle_voice_text("start a class timer", "en")
    assert sess.status.timer_running
    sess.tick(2.5)
    sess.tick(1.0)
    assert sess.status.clock_seconds == 3
    sess.handle_voice_text("stop the timer", "en")
    assert not sess.status.timer_running


def test_session_status_snapshot_fields():
    sess, _ = make_session("demo")
    st = sess.status
    assert st.mode == "demo"
    assert "synthetic" in st.detector
    assert st.presentation_state == "idle"
    assert st.annotation_tool == "none"
    assert st.quiz_state == "idle"
    assert st.control_locked is False


def test_control_lock_blocks_gestures():
    sess, _ = make_session("demo")
    sess.handle_voice_text("start presentation", "en")
    sess.control_locked = True
    sess.handle_gesture(ge.GestureEvent(kind=ge.SWIPE_LEFT, x=0.5, y=0.5))
    assert sess.status.current_slide == 1


def test_quiz_answer_via_voice_updates_score():
    sess, _ = make_session("demo")
    sess.handle_voice_text("start quiz", "en")
    # Q1: "capital of France ?" -> correct answer is Paris (index 0 = 'A')
    sess.handle_voice_text("answer a", "en")
    assert sess.quiz.stats.correct == 1
    assert sess.quiz.stats.answered == 1


def test_recording_backend_captures_clicks():
    sess, backend = make_session("real")
    sess.pointer.set_screen_size(100, 100)
    sess.pointer.update((0.5, 0.5))
    sess.pointer.visible = True
    sess.handle_gesture(ge.GestureEvent(kind=ge.LEFT_CLICK, x=50, y=50))
    assert len(backend.left_clicks) == 1
    assert backend.left_clicks[0] == (50, 50)


def test_scroll_activates_presentation():
    """Regression: scroll/zoom used to move the real deck via SCROLL_DOWN
    without ever flipping ``presentation.state`` out of IDLE, so the HUD kept
    showing INACTIF even though the command visibly worked."""
    sess, _ = make_session("demo")
    assert sess.status.presentation_state == "idle"
    sess.handle_voice_text("scroll down", "en")
    assert sess.status.presentation_state == "active"


def test_pause_and_resume_presentation():
    sess, _ = make_session("demo")
    sess.handle_voice_text("start presentation", "en")
    assert sess.status.presentation_state == "active"
    sess.handle_voice_text("pause the presentation", "en")
    assert sess.status.presentation_state == "paused"
    sess.handle_voice_text("continuer", "fr")
    assert sess.status.presentation_state == "active"
    sess.handle_voice_text("pause la présentation", "fr")
    assert sess.status.presentation_state == "paused"
    # slide navigation auto-resumes
    sess.handle_voice_text("slide suivante", "fr")
    assert sess.status.presentation_state == "active"