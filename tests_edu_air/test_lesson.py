"""LessonPlan: an ordered course outline the teacher steps through live,
pure logic no Qt, mirroring board.py/participation.py's JSON persistence
shape."""

from __future__ import annotations

from pathlib import Path

from edu_air.lesson import LessonPlan, LessonStep, STEP_BOARD, STEP_QUIZ, STEP_SLIDE, STEP_TIMER, validate_kind


def test_empty_plan_has_no_progress_text():
    plan = LessonPlan()
    assert plan.step_count == 0
    assert plan.progress_text() == ""
    assert plan.current is None
    assert not plan.started
    assert not plan.finished


def test_validate_kind_falls_back_to_slide():
    assert validate_kind("timer") == "timer"
    assert validate_kind("nonsense") == STEP_SLIDE


def test_step_constructor_normalises_an_unknown_kind():
    step = LessonStep(kind="bogus", label="x")
    assert step.kind == STEP_SLIDE


def test_advance_walks_through_steps_in_order():
    plan = LessonPlan([
        LessonStep(STEP_SLIDE, "Intro"),
        LessonStep(STEP_QUIZ, "Quick check"),
        LessonStep(STEP_TIMER, "Group work", duration_s=300),
    ])
    assert not plan.started
    s1 = plan.advance()
    assert s1.label == "Intro"
    assert plan.current_index == 0
    s2 = plan.advance()
    assert s2.label == "Quick check"
    s3 = plan.advance()
    assert s3.label == "Group work"
    assert plan.advance() is None   # exhausted
    assert plan.finished


def test_advance_stays_exhausted_until_reset():
    plan = LessonPlan([LessonStep(STEP_SLIDE, "Only step")])
    plan.advance()
    assert plan.advance() is None
    assert plan.advance() is None
    plan.reset()
    assert not plan.started
    step = plan.advance()
    assert step.label == "Only step"


def test_back_moves_the_cursor_without_reapplying_effects():
    plan = LessonPlan([
        LessonStep(STEP_SLIDE, "A"),
        LessonStep(STEP_SLIDE, "B"),
    ])
    plan.advance()
    plan.advance()
    assert plan.current.label == "B"
    step = plan.back()
    assert step.label == "A"
    step = plan.back()
    assert step is None
    assert not plan.started


def test_back_before_starting_is_a_no_op():
    plan = LessonPlan([LessonStep(STEP_SLIDE, "A")])
    assert plan.back() is None
    assert not plan.started


def test_progress_text_reflects_state():
    plan = LessonPlan([LessonStep(STEP_SLIDE, "A"), LessonStep(STEP_SLIDE, "B")])
    assert plan.progress_text() == "Ready (0/2)"
    plan.advance()
    assert plan.progress_text() == "1/2: A"
    plan.advance()
    assert plan.progress_text() == "2/2: B"
    plan.advance()
    assert plan.progress_text() == "Done (2/2)"


def test_set_steps_resets_the_cursor():
    plan = LessonPlan([LessonStep(STEP_SLIDE, "A")])
    plan.advance()
    plan.set_steps([LessonStep(STEP_QUIZ, "New plan")])
    assert not plan.started
    assert plan.step_count == 1
    assert plan.advance().label == "New plan"


def test_as_dict_round_trips_through_load_dict():
    plan = LessonPlan([
        LessonStep(STEP_SLIDE, "Intro"),
        LessonStep(STEP_TIMER, "Work", duration_s=120.0),
    ])
    data = plan.as_dict()
    restored = LessonPlan()
    restored.load_dict(data)
    assert restored.step_count == 2
    assert restored.steps[0].kind == STEP_SLIDE
    assert restored.steps[1].duration_s == 120.0
    assert not restored.started


def test_load_dict_with_no_steps_leaves_an_empty_plan():
    plan = LessonPlan([LessonStep(STEP_SLIDE, "Intro")])
    plan.load_dict({"steps": []})
    assert plan.step_count == 0


def test_save_and_load_json_round_trip(tmp_path):
    plan = LessonPlan([
        LessonStep(STEP_SLIDE, "Intro"),
        LessonStep(STEP_BOARD, "Draw the diagram"),
    ])
    out = tmp_path / "lesson.json"
    written = plan.save_json(out)
    assert written == out
    assert out.exists()

    loaded = LessonPlan()
    assert loaded.load_json(out) is True
    assert loaded.step_count == 2
    assert loaded.steps[1].kind == STEP_BOARD
    assert loaded.steps[1].label == "Draw the diagram"


def test_load_json_missing_file_returns_false_and_leaves_plan_untouched():
    plan = LessonPlan([LessonStep(STEP_SLIDE, "Keep me")])
    ok = plan.load_json("Z:/does/not/exist.json")
    assert ok is False
    assert plan.step_count == 1
    assert plan.steps[0].label == "Keep me"


def test_load_json_corrupt_file_is_ignored(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    plan = LessonPlan([LessonStep(STEP_SLIDE, "Keep me")])
    assert plan.load_json(bad) is False
    assert plan.step_count == 1


def test_bundled_example_lesson_loads_cleanly():
    """lessons/example_lesson.json ships with the app and is what a teacher
    sees the first time they click "Load lesson..." (see
    ClassroomWindow._lessons_dir in ui.py) -- it must always be valid."""
    path = Path(__file__).resolve().parent.parent / "lessons" / "example_lesson.json"
    plan = LessonPlan()
    assert plan.load_json(path) is True
    assert plan.step_count > 0
    assert all(s.label for s in plan.steps)


def test_load_json_wrong_shape_is_rejected(tmp_path):
    wrong = tmp_path / "wrong.json"
    wrong.write_text('{"not_steps": []}', encoding="utf-8")
    plan = LessonPlan([LessonStep(STEP_SLIDE, "Keep me")])
    assert plan.load_json(wrong) is False
    assert plan.step_count == 1


def test_load_json_with_a_non_numeric_duration_does_not_crash(tmp_path):
    """A hand-edited lesson file with a typo (duration_s as text instead of
    a number) is syntactically valid JSON -- only load_dict()'s float()
    conversion fails. That must be reported as a clean False, not an
    uncaught ValueError that would crash the whole app."""
    bad = tmp_path / "typo.json"
    bad.write_text('{"steps": [{"kind": "timer", "label": "Work", '
                    '"duration_s": "soon"}]}', encoding="utf-8")
    plan = LessonPlan([LessonStep(STEP_SLIDE, "Keep me")])
    assert plan.load_json(bad) is False
    assert plan.step_count == 1
    assert plan.steps[0].label == "Keep me"
