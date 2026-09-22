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