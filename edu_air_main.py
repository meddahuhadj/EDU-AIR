"""EDU-AIR — application entry point.

Launches the PySide6 classroom application. Pass ``--demo`` to start in the
fully simulated demo mode (no webcam / mic / OS control required).

Startup is staged so the window appears immediately:
  1. lightweight splASH first;
  2. event loop paint pass;
  3. main window + pipeline built, camera/voice start on background threads.
"""

from __future__ import annotations

import ctypes
import os
import sys


def _bootstrap() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    if root not in sys.path:
        sys.path.insert(0, root)


def _check_python() -> None:
    if not (3, 10) <= sys.version_info[:2] < (3, 13):
        print(
            "EDU-AIR requires Python 3.10, 3.11 or 3.12 (MediaPipe)\n"
            f"Found: {sys.version.split()[0]}.\n"
            "Tip: run with `py -3.12 edu_air_main.py --demo`.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def _claim_single_instance() -> bool:
    try:
        k32 = ctypes.windll.kernel32
        k32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_long, ctypes.c_wchar_p]
        k32.CreateMutexW.restype = ctypes.c_void_p
        handle = k32.CreateMutexW(None, False, "Local\\EDU_AIR_SINGLE")
        if not handle:
            return True
        if k32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            k32.CloseHandle(handle)
            return False
        global _SINGLE_INSTANCE_HANDLE
        _SINGLE_INSTANCE_HANDLE = handle
        return True
    except Exception:
        return True


_SINGLE_INSTANCE_HANDLE = None


def main(argv: list[str] | None = None) -> int:
    _bootstrap()
    _check_python()
    argv = list(argv if argv is not None else sys.argv[1:])
    demo_mode = "--demo" in argv

    if not _claim_single_instance():
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication(sys.argv)
        box = QMessageBox(QMessageBox.Icon.Information, "EDU-AIR",
                          "EDU-AIR is already running.")
        box.setModal(False)
        box.show()
        QTimer.singleShot(3000, app.quit)
        app.exec()
        return 0

    from PySide6.QtWidgets import QApplication
    from edu_air.logging_setup import setup_logging

    setup_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("EDU-AIR")
    app.setOrganizationName("EDU-AIR")
    app.setQuitOnLastWindowClosed(False)

    from edu_air.ui import ClassroomWindow, ClassroomPipeline, make_session

    session = make_session(mode="demo" if demo_mode else "real")
    window = ClassroomWindow(session)
    window.show()
    window._show_overlay()

    def _set_camera_text(text: str) -> None:
        try:
            window.camera_preview.setText(text)
        except Exception:
            pass

    if demo_mode:
        _set_camera_text("Demo mode — no camera preview")

    def _on_camera_state(state: str) -> None:
        if state == "on":
            _set_camera_text("")
        elif state == "demo":
            _set_camera_text("Demo mode — no camera preview")
        else:
            _set_camera_text(
                "Camera unavailable — close other apps using the webcam "
                "and restart.")

    def _show_preview(frame):
        try:
            from PySide6.QtGui import QImage, QPixmap
            h, w, ch = frame.shape
            img = QImage(frame.tobytes(), w, h, ch * w, QImage.Format.Format_RGB888).copy()
            pw = window.camera_preview.width()
            ph = window.camera_preview.height()
            if pw <= 1 or ph <= 1:
                pw, ph = 400, 200
            pix = QPixmap.fromImage(img).scaled(
                pw, ph, ignoreAspectRatio=True)
            window.camera_preview.setPixmap(pix)
        except Exception as exc:
            _set_camera_text(f"Preview error: {exc}")

    pipeline = ClassroomPipeline(session, parent=window)
    pipeline.voice_ready.connect(session.handle_voice_text)
    pipeline.log_line.connect(lambda msg, _w=window: _w.show_log(msg))
    pipeline.frame_ready.connect(_show_preview)
    pipeline.camera_state.connect(_on_camera_state)

    pipeline.start()
    window._pipeline = pipeline
    window._session = session

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())