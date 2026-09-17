"""Safety gate: deny-by-default catalogue and confirmation levels."""

from __future__ import annotations

import pytest

from edu_air.intent import NEXT_SLIDE, ANNOTATION_CLEAR, QUIZ_STOP

from edu_air.safety import (
    ClassroomActionRegistry, ClassroomSafetyEngine,
    RISK_SAFE, RISK_CONFIRM, RISK_CRITICAL,
)


def test_unknown_action_denied_by_default():
    eng = ClassroomSafetyEngine()
    d = eng.decide("OPEN_SHELL")
    assert not d.allowed
    assert "denied by default" in d.reason


def test_known_safe_action_allowed():
    eng = ClassroomSafetyEngine()
    d = eng.decide(NEXT_SLIDE)
    assert d.allowed and d.risk == RISK_SAFE
    assert not d.requires_confirmation


def test_clear_annotations_requires_confirmation():
    eng = ClassroomSafetyEngine()  # smart level
    d = eng.decide(ANNOTATION_CLEAR)
    assert d.allowed
    assert d.risk == RISK_CONFIRM
    assert d.requires_confirmation
    # none level removes the confirmation
    eng2 = ClassroomSafetyEngine(confirmation_level="none")
    d2 = eng2.decide(ANNOTATION_CLEAR)
    assert d2.allowed and not d2.requires_confirmation


def test_quiz_stop_is_critical_always_confirmed():
    eng = ClassroomSafetyEngine(confirmation_level="none")
    d = eng.decide(QUIZ_STOP)
    assert d.allowed
    assert d.risk == RISK_CRITICAL
    assert d.requires_confirmation  # never auto-approved


def test_all_level_wants_everything_confirmed():
    eng = ClassroomSafetyEngine(confirmation_level="all")
    assert eng.decide(NEXT_SLIDE).requires_confirmation


def test_allowed_actions_restriction():
    eng = ClassroomSafetyEngine(allowed_actions=[NEXT_SLIDE])
    assert eng.decide(NEXT_SLIDE).allowed
    assert not eng.decide(QUIZ_STOP).allowed  # outside allow-list


def test_audit_records_events():
    eng = ClassroomSafetyEngine()
    eng.decide(NEXT_SLIDE)
    eng.audit(NEXT_SLIDE, "executed", "ok")
    rec = eng.recent_audit(1)[0]
    assert rec["action"] == NEXT_SLIDE
    assert rec["outcome"] == "executed"


def test_registry_catalogue_is_deny_by_default():
    reg = ClassroomActionRegistry()
    assert reg.known(NEXT_SLIDE)
    assert not reg.known("FOREIGN_ACTION")
    assert QUIZ_STOP in reg.ids()


def test_on_audit_callback():
    eng = ClassroomSafetyEngine()
    seen = []
    eng.on_audit = seen.append
    eng.audit(NEXT_SLIDE, "executed")
    assert len(seen) == 1 and seen[0]["action"] == NEXT_SLIDE