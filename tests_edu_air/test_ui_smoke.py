"""GUI boot smoke test (Windows only, requires a usable display).

The pipeline and classroom window are created and torn down without touching
hardware (demo mode). Skipped when no display is available.
"""

from __future__ import annotations

import platform
import sys

import pytest

pytestmark = pytest.mark.skipif(
    platform.system() != "Windows",
    reason="GUI smoke test requires a Windows display",
)


def test_gui_boots_in_demo_mode():
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    from edu_air.ui import ClassroomWindow, ClassroomPipeline, make_session

    sess = make_session(mode="demo")
    win = ClassroomWindow(sess)
    win.show()
    pipe = ClassroomPipeline(sess, parent=win)
    pipe.frame_ready.connect(win.status_changed.emit)

    done = {}

    def _quit():
        app.quit()
        done["ok"] = True

    QTimer.singleShot(1500, _quit)
    pipe.start()
    rc = app.exec()
    pipe.stop()
    win.close()
    assert rc == 0
    assert done.get("ok")
    assert sess.status.mode == "demo"


def test_wall_mode_toggle_survives_a_live_pipeline():
    """Flip wall mode on and off (button + 'W' shortcut) while the pipeline
    thread is running -- exercises ClassroomWindow's touch settings widgets,
    ClassroomPipeline's mode-transition reset and the projector badge
    together, live, instead of only through isolated unit tests."""
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    from edu_air.ui import ClassroomWindow, ClassroomPipeline, make_session

    sess = make_session(mode="demo")
    win = ClassroomWindow(sess)
    win.show()
    pipe = ClassroomPipeline(sess, parent=win)
    win._pipeline = pipe
    pipe.frame_ready.connect(win.status_changed.emit)

    seen_modes = []

    def _click_wall_mode_button():
        win._wall_mode_btn.click()
        seen_modes.append(sess.interaction_mode)

    def _press_w():
        ev = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_W, Qt.KeyboardModifier.NoModifier)
        win.keyPressEvent(ev)
        seen_modes.append(sess.interaction_mode)

    def _quit():
        app.quit()

    QTimer.singleShot(200, _click_wall_mode_button)   # off -> wall
    QTimer.singleShot(600, _press_w)                  # wall -> off
    QTimer.singleShot(1000, _click_wall_mode_button)  # off -> wall
    QTimer.singleShot(1500, _quit)
    pipe.start()
    rc = app.exec()
    pipe.stop()
    win.close()

    assert rc == 0
    assert seen_modes == ["wall", "contactless", "wall"]
    assert sess.interaction_mode == "wall"
    assert win._wall_mode_btn.isChecked()


def test_lesson_sequencer_advances_live_through_the_dock():
    """Click through a small lesson plan on the real dock widgets -- proves
    the "Step ▶"/"◀ Step" buttons, the progress label and the underlying
    LESSON_NEXT/LESSON_PREV actions all agree while a live pipeline runs."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    from edu_air.ui import ClassroomWindow, ClassroomPipeline, make_session
    from edu_air.lesson import LessonStep, STEP_SLIDE, STEP_QUIZ

    sess = make_session(mode="demo")
    sess.lesson.set_steps([LessonStep(STEP_SLIDE, "Intro"), LessonStep(STEP_QUIZ, "Check")])
    win = ClassroomWindow(sess)
    win.show()
    pipe = ClassroomPipeline(sess, parent=win)
    win._pipeline = pipe
    pipe.frame_ready.connect(win.status_changed.emit)

    seen_labels = []

    def _step_once():
        win._lesson_next_btn.click()
        seen_labels.append(win._lesson_progress_lbl.text())

    def _step_again():
        win._lesson_next_btn.click()
        seen_labels.append(win._lesson_progress_lbl.text())

    def _step_back():
        win._lesson_prev_btn.click()
        seen_labels.append(win._lesson_progress_lbl.text())

    def _quit():
        app.quit()

    QTimer.singleShot(200, _step_once)
    QTimer.singleShot(600, _step_again)
    QTimer.singleShot(1000, _step_back)
    QTimer.singleShot(1500, _quit)
    pipe.start()
    rc = app.exec()
    pipe.stop()
    win.close()

    assert rc == 0
    assert seen_labels == ["1/2: Intro", "2/2: Check", "1/2: Intro"]
    assert sess.presentation.active   # the slide step really drove it
    assert sess.quiz.active           # the quiz step really drove it


def test_fingertip_capture_and_overlay_target_survive_a_live_pipeline():
    """The calibration wizard's live corner/alignment capture rides on
    ClassroomPipeline.begin_fingertip_capture()/end_fingertip_capture() and
    OverlayWindow.set_calibration_target() -- exercise both against a real
    running pipeline instead of only unit-testing them in isolation."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    from edu_air.ui import ClassroomWindow, ClassroomPipeline, make_session

    sess = make_session(mode="demo")
    win = ClassroomWindow(sess)
    win.show()
    win._show_overlay()
    pipe = ClassroomPipeline(sess, parent=win)
    win._pipeline = pipe

    captured = {}

    def _capture_cycle():
        win._overlay.set_calibration_target((0.5, 0.5))
        captured["target_while_set"] = win._overlay._calibration_target
        pipe.begin_fingertip_capture()
        captured["capturing_flag"] = pipe._fingertip_capturing

    def _end_cycle():
        captured["samples"] = pipe.end_fingertip_capture()
        captured["capturing_flag_after"] = pipe._fingertip_capturing
        win._overlay.set_calibration_target(None)
        captured["target_after_clear"] = win._overlay._calibration_target

    def _quit():
        app.quit()

    QTimer.singleShot(200, _capture_cycle)
    QTimer.singleShot(900, _end_cycle)
    QTimer.singleShot(1300, _quit)
    pipe.start()
    rc = app.exec()
    pipe.stop()
    win.close()

    assert rc == 0
    assert captured["target_while_set"] == (0.5, 0.5)
    assert captured["capturing_flag"] is True
    assert captured["capturing_flag_after"] is False
    assert captured["target_after_clear"] is None
    # Demo mode has no real camera, so no *real* fingertip samples should
    # have been buffered -- confirms the capture path does not silently
    # "calibrate" against the synthetic demo hand (see _loop()'s use of
    # real_hands, not hands, to feed the capture buffer).
    assert captured["samples"] == []


def test_rehearsal_mode_toggles_the_overlay_window_live():
    """Mode maquette: the overlay swaps from a full-screen click-through
    projector window to a normal bordered preview window and back, live,
    while the pipeline keeps running -- exercised against real Qt window
    flags/attributes, not just the ``_rehearsal_mode`` bookkeeping flag."""
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    from edu_air.ui import ClassroomWindow, ClassroomPipeline, make_session

    sess = make_session(mode="demo")
    win = ClassroomWindow(sess)
    win.show()
    win._show_overlay()
    pipe = ClassroomPipeline(sess, parent=win)
    win._pipeline = pipe

    captured = {}

    def _enable_rehearsal():
        win._rehearsal_btn.setChecked(True)
        win._toggle_rehearsal()
        ov = win._overlay
        captured["flag_on"] = ov._rehearsal_mode
        captured["visible_on"] = ov.isVisible()
        captured["frameless_gone"] = not bool(
            ov.windowFlags() & Qt.WindowType.FramelessWindowHint)
        captured["translucent_gone"] = not ov.testAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground)

    def _disable_rehearsal():
        win._rehearsal_btn.setChecked(False)
        win._toggle_rehearsal()
        ov = win._overlay
        captured["flag_off"] = ov._rehearsal_mode
        captured["frameless_back"] = bool(
            ov.windowFlags() & Qt.WindowType.FramelessWindowHint)

    def _quit():
        app.quit()

    QTimer.singleShot(200, _enable_rehearsal)
    QTimer.singleShot(600, _disable_rehearsal)
    QTimer.singleShot(1000, _quit)
    pipe.start()
    rc = app.exec()
    pipe.stop()
    win.close()

    assert rc == 0
    assert captured["flag_on"] is True
    assert captured["visible_on"] is True
    assert captured["frameless_gone"] is True
    assert captured["translucent_gone"] is True
    assert captured["flag_off"] is False
    assert captured["frameless_back"] is True