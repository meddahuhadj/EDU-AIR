"""ClassroomSession.handle_palm_wipe(): wall-mode only, erases with the
wide palm_erase_radius (not the narrow fingertip eraser radius), and never
fires outside wall mode -- mirrors test_classroom_touch.py's shape for
handle_touch_event."""

from __future__ import annotations

from edu_air.classroom import ClassroomSession, RecordingBackend, MODE_WALL
from edu_air import intent as ci
from edu_air.config import PresentationSettings
from edu_air.presentation import PresentationController, RecordingDriver


def make_session(mode: str = "demo") -> ClassroomSession:
    backend = RecordingBackend()
    pres = PresentationController(driver=RecordingDriver(), settings=PresentationSettings())
    sess = ClassroomSession(backend=backend, presentation=pres)
    sess.set_mode(mode)
    return sess


def test_palm_wipe_is_ignored_outside_wall_mode():
    sess = make_session("real")
    sess.annotation.set_tool("draw")
    sess.annotation.begin((0.5, 0.5))
    sess.annotation.finish()
    assert sess.annotation.count == 1

    sess.handle_palm_wipe((0.5, 0.5))  # still contactless mode
    assert sess.annotation.count == 1  # untouched


def test_palm_wipe_erases_strokes_in_wall_mode():
    sess = make_session("real")
    sess.annotation.set_tool("draw")
    sess.annotation.begin((0.5, 0.5))
    sess.annotation.finish()
    assert sess.annotation.count == 1

    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    assert sess.interaction_mode == MODE_WALL
    sess.handle_palm_wipe((0.5, 0.5))
    assert sess.annotation.count == 0


def test_palm_wipe_uses_the_wide_palm_radius_not_the_fingertip_radius():
    sess = make_session("real")
    sess.settings.touch.palm_erase_radius = 0.2
    sess.annotation.set_tool("draw")
    # A stroke just outside the narrow default fingertip radius (~0.03)
    # but well inside the wide palm radius (0.2).
    sess.annotation.begin((0.5 + 0.1, 0.5))
    sess.annotation.finish()
    assert sess.annotation.count == 1

    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    sess.handle_palm_wipe((0.5, 0.5))
    assert sess.annotation.count == 0


def test_palm_wipe_with_nothing_nearby_is_a_safe_no_op():
    sess = make_session("real")
    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    sess.handle_palm_wipe((0.5, 0.5))  # no strokes at all
    assert sess.annotation.count == 0


def test_palm_wipe_respects_control_lock():
    sess = make_session("real")
    sess.annotation.set_tool("draw")
    sess.annotation.begin((0.5, 0.5))
    sess.annotation.finish()
    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    sess.control_locked = True
    sess.handle_palm_wipe((0.5, 0.5))
    assert sess.annotation.count == 1  # locked out, nothing erased
