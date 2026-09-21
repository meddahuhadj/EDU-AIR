"""LESSON_NEXT/LESSON_PREV end-to-end: a lesson step is a named shortcut
through the same safety-gated actions a teacher would trigger by hand
(slide / quiz / timer / board), mirroring test_classroom_participation.py."""

from __future__ import annotations

from edu_air.classroom import ClassroomSession, RecordingBackend
from edu_air import intent as ci
from edu_air.config import PresentationSettings
from edu_air.lesson import LessonPlan, LessonStep, STEP_BOARD, STEP_QUIZ, STEP_SLIDE, STEP_TIMER
from edu_air.presentation import PresentationController, RecordingDriver


def make_session(mode: str = "demo") -> ClassroomSession:
    backend = RecordingBackend()
    pres = PresentationController(driver=RecordingDriver(), settings=PresentationSettings())
    sess = ClassroomSession(backend=backend, presentation=pres)
    sess.set_mode(mode)
    return sess


def test_lesson_next_with_no_plan_loaded_is_a_safe_no_op():
    sess = make_session("real")
    decision = sess.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="test"))
    assert decision.allowed
    assert sess.lesson.current is None


def test_lesson_next_on_a_slide_step_advances_the_presentation():
    sess = make_session("real")
    sess.lesson.set_steps([LessonStep(STEP_SLIDE, "Intro")])
    decision = sess.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="test"))
    assert decision.allowed
    assert sess.presentation.active
    # _ensure_presentation_active() starts the deck (slide_index 0) then
    # next_slide() advances it once, same as a bare "next slide" command.
    assert sess.presentation.slide_index == 1
    assert sess.status.lesson_progress == "1/1: Intro"


def test_lesson_next_on_a_quiz_step_starts_the_quiz():
    sess = make_session("real")
    sess.lesson.set_steps([LessonStep(STEP_QUIZ, "Quick check")])
    sess.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="test"))
    assert sess.quiz.active
    assert sess.domain == "quiz"


def test_lesson_next_on_a_board_step_advances_the_whiteboard_page():
    sess = make_session("real")
    sess.lesson.set_steps([LessonStep(STEP_BOARD, "Diagram")])
    start_page = sess.board.current_index
    sess.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="test"))
    assert sess.board.current_index == start_page + 1
    assert sess.domain == "board"


def test_lesson_next_on_a_timer_step_starts_the_timer_with_its_duration():
    sess = make_session("real")
    sess.lesson.set_steps([LessonStep(STEP_TIMER, "Group work", duration_s=5.0)])
    sess.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="test"))
    assert sess._timer_running
    assert sess._clock_s == 0.0
    assert sess._lesson_timer_limit == 5.0


def test_lesson_timer_step_auto_stops_after_its_planned_duration():
    sess = make_session("real")
    sess.lesson.set_steps([LessonStep(STEP_TIMER, "Short break", duration_s=1.0)])
    sess.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="test"))
    sess.tick(dt=0.5)
    assert sess._timer_running
    sess.tick(dt=0.6)
    assert not sess._timer_running


def test_manual_timer_start_clears_any_stale_lesson_limit():
    sess = make_session("real")
    sess.lesson.set_steps([LessonStep(STEP_TIMER, "Group work", duration_s=5.0)])
    sess.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="test"))
    assert sess._lesson_timer_limit == 5.0
    sess.execute(ci.ClassroomIntent(ci.TIMER_START, source="test"))
    assert sess._lesson_timer_limit == 0.0
    sess.tick(dt=100.0)
    assert sess._timer_running  # a manual timer never auto-stops


def test_lesson_advances_through_multiple_steps_in_order():
    sess = make_session("real")
    sess.lesson.set_steps([
        LessonStep(STEP_SLIDE, "A"),
        LessonStep(STEP_SLIDE, "B"),
    ])
    sess.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="test"))
    assert sess.status.lesson_progress == "1/2: A"
    sess.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="test"))
    assert sess.status.lesson_progress == "2/2: B"
    assert sess.presentation.slide_index == 2


def test_lesson_prev_moves_the_cursor_back():
    sess = make_session("real")
    sess.lesson.set_steps([
        LessonStep(STEP_SLIDE, "A"),
        LessonStep(STEP_SLIDE, "B"),
    ])
    sess.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="test"))
    sess.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="test"))
    decision = sess.execute(ci.ClassroomIntent(ci.LESSON_PREV, source="test"))
    assert decision.allowed
    assert sess.lesson.current.label == "A"
    assert sess.status.lesson_progress == "1/2: A"


def test_load_lesson_json_updates_the_session_plan(tmp_path):
    sess = make_session("real")
    plan = LessonPlan([LessonStep(STEP_SLIDE, "Intro"), LessonStep(STEP_QUIZ, "Check")])
    path = plan.save_json(tmp_path / "lesson.json")
    ok = sess.load_lesson_json(path)
    assert ok is True
    assert sess.lesson.step_count == 2
    assert sess.lesson.steps[1].kind == STEP_QUIZ


def test_load_lesson_json_missing_file_returns_false():
    sess = make_session("real")
    assert sess.load_lesson_json("Z:/nope/lesson.json") is False
    assert sess.lesson.step_count == 0


def test_voice_phrase_advances_the_lesson():
    sess = make_session("real")
    sess.lesson.set_steps([LessonStep(STEP_SLIDE, "Intro")])
    decision = sess.handle_voice_text("next step", "en")
    assert decision is not None
    assert decision.allowed
    assert sess.status.lesson_progress == "1/1: Intro"


def test_voice_phrase_french_advances_the_lesson():
    sess = make_session("real")
    sess.lesson.set_steps([LessonStep(STEP_SLIDE, "Intro")])
    decision = sess.handle_voice_text("étape suivante", "fr")
    assert decision is not None
    assert decision.allowed
    assert sess.status.lesson_progress == "1/1: Intro"
