"""PARTICIPATION_MARK end-to-end: safety-gated, bypasses confirmation like
the other reflexive toggles, and increments the same ParticipationTracker
the CSV export reads from."""

from __future__ import annotations

import pytest

from edu_air.classroom import ClassroomSession, RecordingBackend
from edu_air import intent as ci
from edu_air.config import PresentationSettings
from edu_air.presentation import PresentationController, RecordingDriver


def make_session(mode: str = "demo") -> ClassroomSession:
    backend = RecordingBackend()
    pres = PresentationController(driver=RecordingDriver(), settings=PresentationSettings())
    sess = ClassroomSession(backend=backend, presentation=pres)
    sess.set_mode(mode)
    return sess


def test_starts_at_zero():
    sess = make_session()
    assert sess.participation.count == 0


def test_mark_increments_and_is_safety_gated():
    sess = make_session("real")
    decision = sess.execute(ci.ClassroomIntent(ci.PARTICIPATION_MARK, source="test"))
    assert decision.allowed
    assert sess.participation.count == 1
    assert sess.status.participation_count == 1


def test_mark_bypasses_confirmation_even_at_all_level():
    sess = make_session("real")
    sess.safety.set_confirmation_level("all")
    decision = sess.execute(ci.ClassroomIntent(ci.PARTICIPATION_MARK, source="test"))
    assert decision.allowed
    assert not decision.requires_confirmation
    assert sess.participation.count == 1


def test_mark_still_works_while_quiz_is_active():
    sess = make_session("real")
    sess.execute(ci.ClassroomIntent(ci.QUIZ_START, source="test"))
    intent = ci.ClassroomIntent(ci.PARTICIPATION_MARK, source="voice")
    routed = sess.intent_engine.route(intent, quiz_active=sess.quiz.active)
    assert routed is not None
    assert routed.action == ci.PARTICIPATION_MARK


def test_multiple_marks_accumulate():
    sess = make_session("real")
    for _ in range(5):
        sess.execute(ci.ClassroomIntent(ci.PARTICIPATION_MARK, source="test"))
    assert sess.participation.count == 5
    assert sess.status.participation_count == 5


def test_voice_phrase_marks_a_participation():
    sess = make_session("real")
    decision = sess.handle_voice_text("participation", "en")
    assert decision is not None
    assert decision.allowed
    assert sess.participation.count == 1
