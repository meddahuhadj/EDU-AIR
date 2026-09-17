"""Classroom intent engine: voice/gesture mapping and context routing."""

from __future__ import annotations

import pytest

from hadj_no_touch.gestures import gesture_engine as ge
from hadj_no_touch.voice import voice_commands as vc

from edu_air.intent import (
    ClassroomIntentEngine, NEXT_SLIDE, PREV_SLIDE, QUIZ_START, QUIZ_ANSWER,
    QUIZ_STOP, PRESENTATION_START, PAUSE_PRESENTATION, ZOOM_IN, ZOOM_OUT,
)
from edu_air.voice import parse


def eng() -> ClassroomIntentEngine:
    return ClassroomIntentEngine(language="en")


def test_voice_slide_mapping():
    e = eng()
    i = e.from_voice(parse("next slide", "en"))
    assert i is not None and i.action == NEXT_SLIDE and i.source == "voice"
    i2 = e.from_voice(parse("slide précédente", "fr"))
    assert i2 is not None and i2.action == PREV_SLIDE
    assert i2.params.get("language") == "fr"


def test_voice_quiz_mapping():
    e = eng()
    i = e.from_voice(parse("start quiz", "en"))
    assert i is not None and i.action == QUIZ_START
    i2 = e.from_voice(parse("answer b", "en"))
    assert i2 is not None and i2.action == QUIZ_ANSWER
    assert i2.params.get("answer_index") == 1


def test_voice_presentation_start():
    e = eng()
    i = e.from_voice(parse("start presentation", "en"))
    assert i is not None and i.action == PRESENTATION_START


def test_unmapped_voice_returns_none():
    e = eng()
    assert e.from_voice(parse("kjhza xquw", "en")) is None


def test_gesture_mapping():
    e = eng()
    evt = ge.GestureEvent(kind=ge.SWIPE_LEFT, x=0.5, y=0.5, confidence=0.9)
    i = e.from_gesture(evt)
    assert i is not None and i.action == NEXT_SLIDE and i.source == "gesture"
    i2 = e.from_gesture(ge.GestureEvent(kind=ge.SWIPE_RIGHT, x=0.5, y=0.5))
    assert i2.action == PREV_SLIDE
    i3 = e.from_gesture(ge.GestureEvent(kind=ge.CIRCLE_CW, x=0.5, y=0.5))
    assert i3.action == ZOOM_IN
    i4 = e.from_gesture(ge.GestureEvent(kind=ge.CIRCLE_CCW, x=0.5, y=0.5))
    assert i4.action == ZOOM_OUT


def test_rest_gesture_is_none():
    e = eng()
    assert e.from_gesture(ge.GestureEvent(kind=ge.REST, x=0.5, y=0.5)) is None


def test_route_safety_toggle_always_passes():
    e = eng()
    i = e.from_voice(parse("pause the presentation", "en"))
    assert i.action == PAUSE_PRESENTATION
    assert e.route(i, quiz_active=True) is not None


def test_route_blocks_presentation_during_quiz():
    e = eng()
    i = e.from_voice(parse("next slide", "en"))
    assert e.route(i, quiz_active=False) is not None
    assert e.route(i, quiz_active=True) is None


def test_route_allows_quiz_during_quiz():
    e = eng()
    q = e.from_voice(parse("next question", "en"))
    assert q is not None  # NEXT_QUESTION maps to QUIZ_NEXT
    assert e.route(q, quiz_active=True) is not None
    stop = e.from_voice(parse("end quiz", "en"))
    assert e.route(stop, quiz_active=True) is not None


def test_route_allows_annotation_and_pointer_during_quiz():
    e = eng()
    ptr = e.from_voice(parse("show the pointer", "en"))
    assert e.route(ptr, quiz_active=True) is not None
    assert e.route(ptr, quiz_active=False) is not None