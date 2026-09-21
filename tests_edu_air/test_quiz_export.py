"""VoiceQuiz answer history + CSV export -- turns "export quiz results" from
a single current-score snapshot into a real per-question session record for
the teacher's cahier de classe."""

from __future__ import annotations

import csv

import pytest

from edu_air.quiz import VoiceQuiz, QuestionBank, Question


def make_quiz() -> VoiceQuiz:
    bank = QuestionBank([
        Question("Q1", ["A0", "A1", "A2", "A3"], 2),
        Question("Q2", ["B0", "B1", "B2", "B3"], 0),
        Question("Q3", ["C0", "C1", "C2", "C3"], 3),
    ])
    return VoiceQuiz(bank)


def test_correct_answer_is_recorded():
    q = make_quiz()
    q.start()
    q.answer(2)   # Q1, correct (answer_idx=2)
    assert len(q.history) == 1
    rec = q.history[0]
    assert rec.question_number == 1
    assert rec.question_text == "Q1"
    assert rec.given_label == "C"    # index 2 -> "C"
    assert rec.correct_label == "C"
    assert rec.is_correct is True
    assert rec.was_skipped is False


def test_wrong_answer_is_recorded():
    q = make_quiz()
    q.start()
    q.answer(1)   # Q1, wrong (correct is index 2)
    rec = q.history[0]
    assert rec.given_label == "B"
    assert rec.correct_label == "C"
    assert rec.is_correct is False
    assert rec.was_skipped is False


def test_skipped_question_is_recorded_via_reveal():
    q = make_quiz()
    q.start()
    q.reveal()   # revealed without ever answering -> skipped
    assert len(q.history) == 1
    rec = q.history[0]
    assert rec.was_skipped is True
    assert rec.given_label == ""
    assert rec.correct_label == "C"
    assert rec.is_correct is False


def test_reveal_after_answer_does_not_duplicate_the_record():
    q = make_quiz()
    q.start()
    q.answer(2)
    q.reveal()   # already answered -- must not add a second history row
    assert len(q.history) == 1


def test_history_accumulates_across_the_whole_session():
    q = make_quiz()
    q.start()
    q.answer(2)              # Q1 correct
    q.next_question()
    q.answer(1)              # Q2 wrong (correct is 0)
    q.next_question()
    q.reveal()               # Q3 skipped
    assert len(q.history) == 3
    assert [r.question_number for r in q.history] == [1, 2, 3]
    assert [r.is_correct for r in q.history] == [True, False, False]
    assert [r.was_skipped for r in q.history] == [False, False, True]


def test_restart_clears_history():
    q = make_quiz()
    q.start()
    q.answer(2)
    assert len(q.history) == 1
    q.restart()
    assert q.history == []


def test_double_answer_attempt_does_not_duplicate_history():
    q = make_quiz()
    q.start()
    q.answer(2)
    q.answer(0)   # second attempt on the same question is ignored
    assert len(q.history) == 1


def test_csv_rows_header_and_body():
    q = make_quiz()
    q.start()
    q.answer(2)
    q.next_question()
    q.answer(1)
    rows = q.to_csv_rows()
    assert rows[0] == ["#", "Question", "Given answer", "Correct answer", "Result", "Time (s)"]
    assert rows[1][:5] == ["1", "Q1", "C", "C", "Correct"]
    assert rows[2][:5] == ["2", "Q2", "B", "A", "Wrong"]


def test_csv_rows_include_summary_footer():
    q = make_quiz()
    q.start()
    q.answer(2)
    q.next_question()
    q.reveal()
    rows = q.to_csv_rows()
    footer = {r[0]: r[1] for r in rows if len(r) == 2}
    assert footer["Correct"] == "1"
    assert footer["Skipped"] == "1"
    assert footer["Total questions"] == "1"   # only answer() increments stats.total


def test_export_csv_writes_a_real_readable_file(tmp_path):
    q = make_quiz()
    q.start()
    q.answer(2)
    q.next_question()
    q.answer(0)
    out = tmp_path / "quiz_results.csv"
    written = q.export_csv(out)
    assert written == out
    assert out.exists()
    with out.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0][0] == "#"
    assert rows[1][1] == "Q1"
    assert rows[2][1] == "Q2"


def test_empty_session_exports_just_the_header_and_zeroed_summary():
    q = make_quiz()
    q.start()
    rows = q.to_csv_rows()
    assert rows[0][0] == "#"
    footer = {r[0]: r[1] for r in rows if len(r) == 2}
    assert footer["Total questions"] == "0"
