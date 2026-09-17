"""Demo mode: synthetic hands, gesture events and the scripted sequence."""

from __future__ import annotations

import pytest

from edu_air.classroom import ClassroomSession, RecordingBackend
from edu_air.demo import (
    synthetic_hand, finger_tip, moving_point, default_script, DemoSession,
)


def test_synthetic_hand_point_has_index_tip():
    hand = synthetic_hand("point", (0.5, 0.5))
    assert hand.tracked
    assert hand.landmarks_norm[8][0] >= 0.0  # index fingertip present
    x, y = finger_tip(hand)
    assert 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0


def test_pinch_thumb_touches_index():
    hand = synthetic_hand("pinch", (0.5, 0.5))
    thumb = hand.landmarks_norm[4]
    index = hand.landmarks_norm[8]
    assert abs(thumb[0] - index[0]) < 0.01
    assert abs(thumb[1] - index[1]) < 0.01


def test_moving_point_stays_in_frame():
    for t in (0, 1, 2, 5, 10):
        x, y = moving_point(t)
        assert 0.05 <= x <= 0.95
        assert 0.05 <= y <= 0.95


def test_default_script_contains_start_marker():
    for lang in ("en", "fr", "ar"):
        steps = default_script(lang)
        starts = [s for s in steps
                  if s.kind == "voice" and s.value in ("start presentation",
                                                       "démarrer la présentation",
                                                       "ابدأ العرض التقديمي")]
        assert starts, f"lang {lang} has no start phrase"
        # the very first DemoStep must be a voice step
        assert steps[0].kind == "voice"


def test_demo_session_feeds_classroom():
    sess = ClassroomSession(backend=RecordingBackend())
    sess.set_mode("demo")
    demo = DemoSession(sess, default_script("en"), "en")
    lines = demo.run_all()
    assert len(lines) > 0
    assert sess.status.current_slide >= 1
    assert sess.status.last_command == "QUIZ_STOP"