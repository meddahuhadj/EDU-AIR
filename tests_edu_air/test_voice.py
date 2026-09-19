"""Classroom voice commands: EN / FR / AR parsing of the phrase catalogue."""

from __future__ import annotations

import pytest

from edu_air.voice import (
    parse, ANSWER_LETTER, START_QUIZ, STOP_QUIZ, NEXT_QUESTION,
    PREV_QUESTION, REVEAL_ANSWER, POINTER_ON, POINTER_OFF,
    DRAW, HIGHLIGHT, ERASE_ANNOTATION, CLEAR_ANNOTATIONS,
    START_TIMER, STOP_TIMER, PAUSE_PRESENTATION, RESUME_PRESENTATION, register_classroom_commands,
)


def test_register_idempotent():
    from hadj_no_touch.voice import voice_commands as vc
    register_classroom_commands()
    n1 = len(vc.COMMANDS)
    register_classroom_commands()
    assert len(vc.COMMANDS) == n1  # no duplicates on second call


def test_none_text_is_safe():
    r = parse("", "en")
    assert r.intent in ("NONE", "") and r.confidence == 0.0


def test_en_quiz_recognised():
    for phrase in ("start quiz", "begin the quiz", "end quiz"):
        r = parse(phrase, "en")
        assert r.intent in (START_QUIZ, STOP_QUIZ)
    assert parse("next question", "en").intent == NEXT_QUESTION
    assert parse("previous question", "en").intent == PREV_QUESTION
    assert parse("show me the answer", "en").intent == REVEAL_ANSWER


def test_fr_quiz_recognised():
    assert parse("démarrer le quiz", "fr").intent == START_QUIZ
    assert parse("arrêter le quiz", "fr").intent == STOP_QUIZ
    assert parse("question suivante", "fr").intent == NEXT_QUESTION
    assert parse("question précédente", "fr").intent == PREV_QUESTION
    assert parse("affiche la réponse", "fr").intent == REVEAL_ANSWER


def test_ar_quiz_recognised():
    assert parse("ابدا الاختبار", "ar").intent == START_QUIZ
    assert parse("انهي الاختبار", "ar").intent == STOP_QUIZ
    assert parse("السؤال التالي", "ar").intent == NEXT_QUESTION
    assert parse("اظهر الاجابة", "ar").intent == REVEAL_ANSWER


def test_answer_letter_params_en():
    r = parse("answer c", "en")
    assert r.intent == ANSWER_LETTER
    assert r.params["letter"] == "c"
    assert r.params["answer_index"] == 2
    r2 = parse("i choose B", "en")
    assert r2.params["answer_index"] == 1


def test_answer_letter_params_fr():
    r = parse("réponse a", "fr")
    assert r.intent == ANSWER_LETTER
    assert r.params["answer_index"] == 0
    r2 = parse("choisis la lettre d", "fr")
    assert r2.params["answer_index"] == 3


def test_answer_letter_params_ar():
    r = parse("الاجابه ب", "ar")
    assert r.intent == ANSWER_LETTER
    assert r.params["letter"] == "b"
    assert r.params["answer_index"] == 1


def test_pointer_and_annotation_speech():
    assert parse("show the pointer", "en").intent == POINTER_ON
    assert parse("pointeur en marche", "fr").intent == POINTER_ON
    assert parse("hide pointer", "en").intent == POINTER_OFF
    assert parse("drawing mode", "en").intent == DRAW
    assert parse("dessin mode", "fr").intent == DRAW
    assert parse("highlight mode", "en").intent == HIGHLIGHT
    assert parse("surligner", "fr").intent == HIGHLIGHT
    assert parse("erase mode", "en").intent == ERASE_ANNOTATION
    assert parse("clear the annotations", "en").intent == CLEAR_ANNOTATIONS
    assert parse("وضع المسح", "ar").intent == ERASE_ANNOTATION
    assert parse("مسح الكل", "ar").intent == CLEAR_ANNOTATIONS


def test_timer_and_pause():
    assert parse("start a class timer", "en").intent == START_TIMER
    assert parse("stop the timer", "en").intent == STOP_TIMER
    assert parse("lance le chrono", "fr").intent == START_TIMER
    assert parse("pause the presentation", "en").intent == PAUSE_PRESENTATION
    assert parse("continuer", "fr").intent == RESUME_PRESENTATION
    assert parse("reprendre", "fr").intent == RESUME_PRESENTATION
    assert parse("continuer la présentation", "fr").intent == RESUME_PRESENTATION
    assert parse("resume", "en").intent == RESUME_PRESENTATION


def test_unknown_text_gives_none():
    r = parse("kljh weiur qpz", "en")
    assert r.intent in ("NONE", "")