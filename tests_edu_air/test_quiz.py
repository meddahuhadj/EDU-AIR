"""VoiceQuiz: lifecycle, navigation, answering, scoring and reveal."""

from __future__ import annotations

import pytest

from edu_air.quiz import (
    VoiceQuiz, QuestionBank, Question,
    STATE_IDLE, STATE_QUESTION, STATE_ANSWERED, STATE_RESULTS,
)


def make_quiz() -> VoiceQuiz:
    bank = QuestionBank([
        Question("Q1", ["A0", "A1", "A2", "A3"], 2),
        Question("Q2", ["B0", "B1", "B2", "B3"], 0),
        Question("Q3", ["C0", "C1", "C2", "C3"], 3),
    ])
    return VoiceQuiz(bank)


def test_start_prepares_first_question():
    q = make_quiz()
    assert q.state == STATE_IDLE
    assert not q.active
    q.start()
    assert q.state == STATE_QUESTION
    assert q.active
    assert q.question is not None
    assert q.current_question_idx == 0


def test_answer_correct_updates_stats():
    q = make_quiz()
    q.start()
    ok = q.answer(2)  # Q1 correct
    assert ok is True
    assert q.state == STATE_ANSWERED
    assert q.stats.correct == 1
    assert q.stats.answered == 1
    assert q.last_answer_idx == 2


def test_answer_second_attempt_ignored():
    q = make_quiz()
    q.start()
    q.answer(2)
    assert q.answer(0) is False  # already answered
    assert q.stats.answered == 1


def test_wrong_answer_tallied():
    q = make_quiz()
    q.start()
    assert q.answer(0) is False
    assert q.stats.wrong == 1
    assert q.stats.correct == 0


def test_inactive_answer_is_safe():
    q = make_quiz()
    assert q.answer(0) is False
    assert q.stats.answered == 0


def test_navigation_and_reveal():
    q = make_quiz()
    q.start()
    q.reveal()
    assert q.revealed
    assert q.state == STATE_ANSWERED
    q.next_question()
    assert q.current_question_idx == 1
    q.prev_question()
    assert q.current_question_idx == 0
    assert q.stats.skipped == 1  # revealed Q1 without answering


def test_last_question_advances_to_results():
    q = make_quiz()
    q.start()
    q.answer(2)
    q.next_question()   # -> Q2
    q.answer(0)
    q.next_question()   # -> Q3
    q.answer(3)
    q.next_question()   # exhausted -> results
    assert q.state == STATE_RESULTS
    assert not q.active
    assert q.stats.total == 3
    assert q.stats.correct == 3


def test_stop_returns_to_idle():
    q = make_quiz()
    q.start()
    q.stop()
    assert q.state == STATE_IDLE
    assert not q.active


def test_restart_resets_score():
    q = make_quiz()
    q.start()
    q.answer(2)
    assert q.stats.correct == 1
    q.restart()
    assert q.stats.correct == 0
    assert q.stats.answered == 0
    assert q.current_question_idx == 0


def test_tick_accumulates_question_time():
    q = make_quiz()
    q.start()
    q.tick(1.0)
    q.tick(0.5)
    assert q.question_elapsed_s == pytest.approx(1.5)


def test_labels_default_abcd():
    q = make_quiz()
    assert q.labels == ("A", "B", "C", "D")