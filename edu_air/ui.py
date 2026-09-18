"""EDU-AIR classroom window and projection overlay (PySide6).

Two Qt surfaces:

  1. ``OverlayWindow``  — a translucent, frameless, always-on-top window placed
     on the projector screen. It paints the air-annotation strokes, the
     interactive pointer, the voice-quiz question + A/B/C/D, and the classroom
     HUD (current slide, last teacher command, timer, mode badge, key hints).
     It is click-through by default so the presenter app underneath keeps
     receiving input.

  2. ``ClassroomWindow`` — the control dock on the teacher's own screen:
     camera preview, live status, mode switch (real/demo), sensitivity and
     language controls, tool palette (point / draw / highlight / erase /
     clear), quiz bank picker, calibration launcher and keyboard hints.

The ``ClassroomPipeline`` background loop reads the webcam, runs the gesture
engine and feeds the classroom session; recognized voice arrives through the
HADJ ``SpeechManager``. All UI updates are marshalled through Qt signals.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Optional

from PySide6.QtCore import QObject, Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication, QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QVBoxLayout, QWidget, QGridLayout, QMessageBox,
)

from . import __version__, i18n
from .classroom import ClassroomSession, RecordingBackend, DemoBackend
from .config import SETTINGS
from .pointer import InteractivePointer
from .presentation import PresentationController
from .annotation import AnnotationModel, TOOL_NONE, TOOL_POINT, TOOL_DRAW, \
    TOOL_HIGHLIGHT, TOOL_ERASE
from .accessibility import AccessibilityController, AccessibilityState
from .quiz import VoiceQuiz, QuestionBank
from .safety import ClassroomSafetyEngine
from . import intent as ci


def _pick_screen(index: int):
    screens = QGuiApplication.screens()
    if index is not None and index >= 0 and index < len(screens):
        return screens[index]
    return QGuiApplication.primaryScreen()


# ---------------------------------------------------------------------------
# Projection overlay.
# ---------------------------------------------------------------------------
class OverlayWindow(QWidget):
    def __init__(self, session: ClassroomSession, settings=None,
                 screen_index: int = -1, parent=None):
        super().__init__(parent)
        self.session = session
        self.settings = settings or SETTINGS
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.WindowDoesNotAcceptFocus
                            | Qt.WindowType.WindowTransparentForInput
                            | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self._last_paint = 0.0
        self._target_screen = screen_index
        if os.name == "nt":
            try:
                import ctypes
                hwnd = int(self.winId())
                GWL_EXSTYLE = -20
                WS_EX_NOACTIVATE = 0x08000000
                WS_EX_TRANSPARENT = 0x00000020
                old_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, old_style | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT)
            except Exception:
                pass

    def place_on_screen(self, index: int) -> None:
        screen = _pick_screen(index)
        geo = screen.geometry()
        self.setGeometry(geo)
        self._target_screen = index

    def paintEvent(self, event) -> None:  # noqa: N802
        now = time.monotonic()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        s = self.session

        # ---- air annotation strokes -----------------------------------------
        if s.settings.annotation.enabled:
            for geo in s.annotation.geometry(w, h):
                pts = geo["points"]
                if not pts:
                    continue
                self._paint_stroke(p, pts, geo["color"], geo["width"],
                                   geo["highlight"])

        # ---- interactive pointer ---------------------------------------------
        if s.pointer.visible and s.pointer.position is not None:
            px, py = s.pointer.position
            self._paint_pointer(p, px, py, s.settings.annotation.pointer_size,
                                s.settings.annotation.pointer_color)

        # ---- quiz overlay ------------------------------------------------------
        if s.quiz.active and s.quiz.question is not None:
            self._paint_quiz(p, s.quiz, s.settings.quiz.option_labels,
                             w, h, revealed=s.quiz.revealed)

        # ---- HUD ----------------------------------------------------------------
        if s.settings.presentation.show_hud:
            self._paint_hud(p, s, w, h)

        # cheap repaint on the local frame budget (pointer is animated)
        if now - self._last_paint > 0.05:
            self._last_paint = now
            QTimer.singleShot(50, self.update)
        p.end()

    # painters ----------------------------------------------------------------
    def _paint_stroke(self, p: QPainter, pts, color: str, width: float,
                      highlight: bool) -> None:
        pen = QPen(QColor(color), max(1.0, width))
        if highlight:
            alpha = int(255 * max(0.1, min(0.9, self.settings.annotation.highlight_opacity)))
            pen.setColor(QColor(pen.color().red(), pen.color().green(),
                                pen.color().blue(), alpha))
            pen.setWidthF(pen.widthF() * 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        if len(pts) == 1:
            r = max(2.0, pen.widthF() / 2)
            p.drawEllipse(pts[0][0] - r, pts[0][1] - r, r * 2, r * 2)
            return
        for i in range(len(pts) - 1):
            p.drawLine(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])

    def _paint_pointer(self, p: QPainter, px: float, py: float,
                       size: int, color: str) -> None:
        col = QColor(color)
        size = max(10, size)
        r = size / 2
        c = QPen(col, 2)
        p.setPen(c)
        p.drawEllipse(px - r, py - r, size, size)
        p.drawLine(px - size, py, px - r, py)
        p.drawLine(px + r, py, px + size, py)
        p.drawLine(px, py - size, px, py - r)
        p.drawLine(px, py + r, px, py + size)
        c2 = QPen(col, 3)
        p.setPen(c2)
        p.drawEllipse(px - 2, py - 2, 4, 4)

    def _paint_quiz(self, p: QPainter, quiz, labels, w: int, h: int,
                    revealed: bool) -> None:
        from .voice import LETTER_TO_INDEX
        q = quiz.question
        rtl = i18n.is_rtl()
        ox, oy, ow, oh = int(w * 0.18), int(h * 0.20), int(w * 0.64), int(h * 0.60)
        p.fillRect(ox, oy, ow, oh, QColor(12, 18, 30, 235))
        pen = QPen(QColor(120, 200, 255), 2)
        p.setPen(pen)
        p.drawRoundedRect(ox, oy, ow, oh, 14, 14)

        f_title = QFont("Segoe UI", int(h / 34), QFont.Weight.Bold)
        p.setFont(f_title)
        p.setPen(QColor("white"))
        p.drawText(ox + 24, oy + 52,
                   i18n.t("quiz.question", n=quiz.current_question_idx + 1))
        f_q = QFont("Segoe UI", int(h / 30))
        p.setFont(f_q)
        rect = (ox + 24, oy + 76, ow - 48, oh - 140)
        p.drawText(*rect, Qt.AlignmentFlag.AlignLeft
                   | Qt.AlignmentFlag.AlignTop
                   | Qt.TextFlag.TextWordWrap, q.text)

        row_h = (oh - 200) // 4
        for i, label in enumerate(labels):
            option = q.options[i] if i < len(q.options) else ""
            ly = oy + 200 + i * row_h
            is_answer = (i == q.answer_idx)
            chip = QColor(38, 90, 150) if not revealed \
                else (QColor(60, 160, 80) if is_answer else QColor(150, 60, 60))
            p.setBrush(chip)
            p.setPen(QPen(QColor(180, 210, 255), 1))
            p.drawRoundedRect(ox + 48, ly, ow - 96, row_h - 10, 8, 8)
            f_o = QFont("Segoe UI", int(h / 42), QFont.Weight.DemiBold)
            p.setFont(f_o)
            p.setPen(QColor("white"))
            p.drawText(ox + 64, ly, 60, row_h - 10,
                       Qt.AlignmentFlag.AlignVCenter, label)
            f_opt = QFont("Segoe UI", int(h / 44))
            p.setFont(f_opt)
            txt_rect = (ox + 130, ly, ow - 200, row_h - 10)
            align = Qt.AlignmentFlag.AlignRight if rtl else Qt.AlignmentFlag.AlignLeft
            p.drawText(*txt_rect, align
                       | Qt.AlignmentFlag.AlignVCenter
                       | Qt.TextFlag.TextWordWrap, option)
        if revealed:
            fans = QFont("Segoe UI", int(h / 52))
            p.setFont(fans)
            p.setPen(QColor(120, 200, 255))
            p.drawText(ox + 24, oy + oh - 34,
                       i18n.t("quiz.correct",
                              x=labels[q.answer_idx]))

    @staticmethod
    def _tool_key(tool: str) -> str:
        """Map an annotation tool name to its i18n key."""
        return {"point": "tool.point", "draw": "tool.draw",
                "highlight": "tool.highlight", "erase": "tool.erase"
                }.get(tool, "tool.draw")

    def _paint_hud(self, p: QPainter, s, w: int, h: int) -> None:
        st = s.status
        mode_badge = QColor(90, 160, 90) if s.mode == "demo" else QColor(235, 150, 60)
        hud_x = w - 260
        hud_y = h - 120
        p.setBrush(mode_badge)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(hud_x, hud_y, 250, 110, 10, 10)
        f = QFont("Segoe UI", int(h / 60), QFont.Weight.DemiBold)
        p.setFont(f)
        p.setPen(QColor("white"))
        state_key = {
            "idle": "state.idle", "active": "state.active",
            "paused": "state.paused",
        }.get(st.presentation_state, "state.idle")
        lines = [
            f"EDU-AIR · v{__version__}",
            i18n.t("hud.slide", cur=st.current_slide,
                   total=max(1, st.total_slides),
                   state=i18n.t(state_key).upper()),
            i18n.t("hud.cmd", cmd=st.last_command or "—"),
            i18n.t("hud.tool_clock", tool=i18n.t(self._tool_key(st.annotation_tool)),
                   secs=st.clock_seconds),
            i18n.t("hud.quiz",
                   state=i18n.t("quiz.on") if st.quiz_active else i18n.t("quiz.off")),
        ]
        y = hud_y + 22
        for line in lines:
            p.drawText(hud_x + 14, y, line)
            y += int(h / 48)
        if s.mode == "demo":
            p.drawText(hud_x + 14, y, i18n.t("hud.demo"))


# ---------------------------------------------------------------------------
# Control dock.
# ---------------------------------------------------------------------------
class ClassroomWindow(QMainWindow):
    status_changed = Signal(object)

    def __init__(self, session: ClassroomSession | None = None, parent=None):
        super().__init__(parent)
        self.session = session or ClassroomSession(
            backend=RecordingBackend(), settings=SETTINGS)
        self.session.set_mode(SETTINGS.classroom.mode)
        self._overlay = OverlayWindow(self.session,
                                      screen_index=SETTINGS.classroom.projector_screen)
        self.sensitivity = AccessibilityController(AccessibilityState())
        self._buttons: dict[str, QPushButton] = {}
        self._build_ui()
        self.status_changed.connect(self._on_status)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(200)

    @property
    def camera_preview(self) -> QLabel:
        """QLabel painted with the webcam feed by the app entry point."""
        return self._camera_lbl

    # ---- UI construction ----------------------------------------------------
    def _build_ui(self) -> None:
        self.setWindowTitle(i18n.t("window.title"))
        self.resize(880, 640)
        central = QWidget()
        lay = QVBoxLayout(central)
        self.setCentralWidget(central)

        self._title_lbl = QLabel(i18n.t("window.title"))
        self._title_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #0e6bb8;")
        lay.addWidget(self._title_lbl)
        self._sub_lbl = QLabel(i18n.t("window.subtitle"))
        self._sub_lbl.setStyleSheet("color: #556;")
        lay.addWidget(self._sub_lbl)

        self._camera_lbl = QLabel(i18n.t("camera.preview"))
        self._camera_lbl.setFixedHeight(200)
        self._camera_lbl.setStyleSheet("background:#000; color:#99c;"
                                      "border:1px solid #345; border-radius:6px;")
        self._camera_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._camera_lbl)

        # status grid
        self._status_labels: dict[str, QLabel] = {}
        grid = QGridLayout()
        grid.setSpacing(6)
        for i, key in enumerate(["mode", "presentation", "pointer", "command",
                                 "interaction", "gesture", "timer", "quiz",
                                 "tool", "strokes", "safety", "fps",
                                 "lighting", "noise", "hand"]):
            lab = QLabel(self._status_text(key, ""))
            lab.setStyleSheet("background:#f2f6fb; padding:4px 8px; border-radius:4px;")
            grid.addWidget(lab, i // 2, i % 2)
            self._status_labels[key] = lab
        lay.addLayout(grid)

        # controls - row 1: actions
        ctrl1 = QHBoxLayout()
        self._mode_btn = self._add_button(ctrl1, i18n.t("btn.demo_real"),
                                          self._toggle_mode)
        self._overlay_btn = self._add_button(ctrl1, i18n.t("btn.overlay"),
                                             self._toggle_overlay)
        self._calibration_btn = self._add_button(ctrl1, i18n.t("btn.calibration"),
                                                 self._run_calibration)
        self._export_btn = self._add_button(ctrl1, i18n.t("btn.export"), None)
        self._export_btn.clicked.connect(self._export_board)
        self._clear_btn = self._add_button(ctrl1, i18n.t("btn.clear"), None)
        self._clear_btn.clicked.connect(self._clear_board)
        self._prev_btn = self._add_button(ctrl1, i18n.t("btn.prev_slide"), self._prev_slide)
        self._next_btn = self._add_button(ctrl1, i18n.t("btn.next_slide"), self._next_slide)
        lay.addLayout(ctrl1)

        # controls - row 2: tools
        ctrl2 = QHBoxLayout()
        self._tool_buttons: dict[str, QPushButton] = {}
        for tool in [TOOL_POINT, TOOL_DRAW, TOOL_HIGHLIGHT, TOOL_ERASE]:
            self._tool_buttons[tool] = self._add_button(
                ctrl2, i18n.t(f"tool.{tool}"), None)
            self._tool_buttons[tool].clicked.connect(
                lambda _=False, t=tool: self._select_tool(t))
        lay.addLayout(ctrl2)

        row2 = QHBoxLayout()
        self._cam_lbl = QLabel(i18n.t("label.camera"))
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["Camera 0", "Camera 1", "Camera 2", "Camera 3"])
        cur_cam_idx = SETTINGS.camera.index if hasattr(SETTINGS, "camera") else 0
        self.camera_combo.setCurrentIndex(min(3, max(0, cur_cam_idx)))
        self.camera_combo.currentIndexChanged.connect(self._change_camera_index)
        row2.addWidget(self._cam_lbl)
        row2.addWidget(self.camera_combo)

        self._sens_lbl = QLabel(i18n.t("label.sensitivity"))
        self.sensitivity_combo = QComboBox()
        self.sensitivity_combo.addItems([
            i18n.t("sens.low"), i18n.t("sens.medium"), i18n.t("sens.high")])
        self.sensitivity_combo.setCurrentText(self.sensitivity.state.sensitivity)
        self.sensitivity_combo.currentTextChanged.connect(self._change_sensitivity)
        row2.addWidget(self._sens_lbl)
        row2.addWidget(self.sensitivity_combo)

        self._voice_lbl = QLabel(i18n.t("label.voice"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(list(i18n.SUPPORTED))
        self.lang_combo.setCurrentText(SETTINGS.classroom.language)
        self.lang_combo.currentTextChanged.connect(self._change_language)
        row2.addWidget(self._voice_lbl)
        row2.addWidget(self.lang_combo)
        row2.addStretch(1)
        lay.addLayout(row2)

        row3 = QHBoxLayout()
        self._perf_lbl = QLabel(i18n.t("label.performance"))
        self._perf_check = QCheckBox()
        self._perf_check.setChecked(SETTINGS.classroom.performance_mode)
        self._perf_check.toggled.connect(self._toggle_performance)
        row3.addWidget(self._perf_lbl)
        row3.addWidget(self._perf_check)
        self._extapp_lbl = QLabel(i18n.t("label.external_app"))
        self._extapp_combo = QComboBox()
        self._extapp_combo.addItems(
            [i18n.t(f"extapp.{k}") for k in ("none", "openboard", "xournalpp")])
        self._extapp_combo.setCurrentText(
            i18n.t(f"extapp.{SETTINGS.presentation.external_app}"))
        self._extapp_combo.currentTextChanged.connect(self._change_external_app)
        row3.addWidget(self._extapp_lbl)
        row3.addWidget(self._extapp_combo)
        row3.addStretch(1)
        lay.addLayout(row3)

        self._hint_lbl = QLabel(i18n.t("hint.keyboard"))
        self._hint_lbl.setStyleSheet("color:#677; font-size:11px;")
        lay.addWidget(self._hint_lbl)

        self._hint_label = QLabel("")
        lay.addWidget(self._hint_label)

    def _add_button(self, layout, text, onclick):
        key = text
        b = QPushButton(text)
        if onclick is not None:
            b.clicked.connect(onclick)
        layout.addWidget(b)
        self._buttons[key] = b
        return b

    def _status_text(self, key: str, value: str) -> str:
        i18n_key = f"status.{key}"
        label = i18n.t(i18n_key)
        # translate known value tokens
        value = self._translate_value(key, value)
        return f"{label}: {value}"

    @staticmethod
    def _translate_value(status_key: str, value: str) -> str:
        v = str(value)
        if status_key == "mode":
            return i18n.tv("mode." + v) if v in ("demo", "real") else v
        if status_key == "pointer":
            return i18n.tv("ptr.visible") if "visible" in v.lower() else i18n.tv("ptr.hidden")
        if status_key == "lighting":
            return i18n.tv("env." + v) if v in ("dark", "low", "good", "bright") else v
        if status_key == "noise":
            return i18n.tv("env." + v) if v in ("ok", "loud") else v
        if status_key == "hand":
            return i18n.t("hand.seen") if v == "visible" else i18n.t("hand.lost")
        if status_key == "presentation":
            head = v.split("·")[0].strip()
            return (i18n.t(f"state.{head}") if head in ("idle", "active", "paused")
                    else v)
        return v

    @staticmethod
    def _env_style(state: str) -> str:
        """Traffic-light chip style for classroom-environment indicators."""
        ok = "background:#e4f7e6; color:#14532d;"
        warn = "background:#fdf3d8; color:#7c4a03;"
        bad = "background:#fde8e8; color:#7f1d1d;"
        dim = "background:#eef1f4; color:#3b4a5a;"
        base = "padding:2px 8px; border-radius:4px; font-weight:600;"
        if state in ("good", "ok"):
            return ok + base
        if state in ("low", "bright", "loud"):
            return warn + base
        if state in ("dark",):
            return bad + base
        return dim + base

    # ---- interactions --------------------------------------------------------
    def _toggle_mode(self) -> None:
        nxt = "demo" if self.session.mode == "real" else "real"
        self.session.set_mode(nxt)
        self.refresh()

    def _toggle_overlay(self) -> None:
        if self._overlay.isVisible():
            self._overlay.hide()
        else:
            self._show_overlay()

    def _show_overlay(self) -> None:
        self._overlay.place_on_screen(SETTINGS.classroom.projector_screen)
        self._overlay.show()
        if os.name == "nt":
            try:
                import ctypes
                hwnd = int(self._overlay.winId())
                GWL_EXSTYLE = -20
                WS_EX_NOACTIVATE = 0x08000000
                WS_EX_TRANSPARENT = 0x00000020
                old_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, old_style | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT)
            except Exception:
                pass

    def _select_tool(self, tool: str) -> None:
        self.session.annotation.set_tool(tool)
        self.session.domain = "annotation"
        self.refresh()

    def _clear_board(self) -> None:
        decision = self.session.safety.decide(ci.ANNOTATION_CLEAR)
        if decision.requires_confirmation:
            if QMessageBox.question(self, i18n.t("confirm.title"),
                                    i18n.t("confirm.clear")) \
                    == QMessageBox.StandardButton.Yes:
                self.session.execute(ci.ClassroomIntent(ci.ANNOTATION_CLEAR, source="ui"))
            return
        self.session.execute(ci.ClassroomIntent(ci.ANNOTATION_CLEAR, source="ui"))
        self.refresh()

    def _export_board(self) -> None:
        """Export current whiteboard annotations/canvas to PNG image."""
        try:
            from PySide6.QtWidgets import QFileDialog
            from PySide6.QtGui import QImage, QPainter, QPen, QColor
            from PySide6.QtCore import Qt
            import os, time
            default_name = f"EDU_AIR_Notes_{time.strftime('%Y%m%d_%H%M%S')}.png"
            path, _ = QFileDialog.getSaveFileName(
                self, i18n.t("btn.export"), default_name,
                "Images (*.png *.jpg);;All Files (*.*)")
            if not path:
                return
            w, h = 1280, 720
            img = QImage(w, h, QImage.Format.Format_RGB32)
            img.fill(QColor(255, 255, 255))
            painter = QPainter(img)
            geom = self.session.annotation.geometry(w, h)
            for item in geom:
                pts = item["points"]
                col = item["color"]
                width = item["width"]
                hl = item["highlight"]
                if not pts:
                    continue
                pen = QPen(QColor(col), max(1.0, width))
                if hl:
                    pen.setWidthF(pen.widthF() * 2)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                if len(pts) == 1:
                    r = max(2.0, pen.widthF() / 2)
                    painter.drawEllipse(pts[0][0] - r, pts[0][1] - r, r * 2, r * 2)
                else:
                    for i in range(len(pts) - 1):
                        painter.drawLine(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
            painter.end()
            img.save(path)
            self.show_log(i18n.t("export.success", path=os.path.basename(path)))
        except Exception as exc:
            self.show_log(f"Export error: {exc}")

    def _change_camera_index(self, index: int) -> None:
        SETTINGS.camera.index = max(0, index)
        if hasattr(self, "_pipeline") and self._pipeline:
            self._pipeline.request_camera_index(max(0, index))
        SETTINGS.save()

    def _change_sensitivity(self, value: str) -> None:
        reverse = {i18n.t(f"sens.{k}"): k for k in ("low", "medium", "high")}
        key = reverse.get(value, value)
        self.sensitivity.set_sensitivity(key)

    def _toggle_performance(self, on: bool) -> None:
        SETTINGS.classroom.performance_mode = bool(on)
        self.session.set_performance(bool(on))
        SETTINGS.save()
        self.refresh()

    def _change_external_app(self, value: str) -> None:
        reverse = {i18n.t(f"extapp.{k}"): k
                   for k in ("none", "openboard", "xournalpp")}
        key = reverse.get(value, "none")
        SETTINGS.presentation.external_app = key
        self.session.presentation.apply_external_app(key)
        SETTINGS.save()
        self.refresh()

    def _change_language(self, value: str) -> None:
        i18n.set_language(value)
        self.session.set_language(value)
        SETTINGS.classroom.language = value
        self._apply_language()

    def _apply_language(self) -> None:
        """Re-translate every visible label in the control dock."""
        rtl = i18n.is_rtl()
        dir_val = (Qt.LayoutDirection.RightToLeft if rtl
                   else Qt.LayoutDirection.LeftToRight)
        self.setLayoutDirection(dir_val)
        self.setWindowTitle(i18n.t("window.title"))
        self._title_lbl.setText(i18n.t("window.title"))
        self._sub_lbl.setText(i18n.t("window.subtitle"))
        self._camera_lbl.setText(i18n.t("camera.preview"))
        self._sens_lbl.setText(i18n.t("label.sensitivity"))
        self._voice_lbl.setText(i18n.t("label.voice"))
        self._perf_lbl.setText(i18n.t("label.performance"))
        self._extapp_lbl.setText(i18n.t("label.external_app"))
        self._hint_lbl.setText(i18n.t("hint.keyboard"))
        self._extapp_combo.blockSignals(True)
        cur_app = SETTINGS.presentation.external_app
        self._extapp_combo.clear()
        self._extapp_combo.addItems(
            [i18n.t(f"extapp.{k}") for k in ("none", "openboard", "xournalpp")])
        self._extapp_combo.setCurrentText(i18n.t(f"extapp.{cur_app}"))
        self._extapp_combo.blockSignals(False)
        # combo items must be repopulated so displayed names change
        self.sensitivity_combo.blockSignals(True)
        prev_sens = self.sensitivity_combo.currentText()
        self.sensitivity_combo.clear()
        self.sensitivity_combo.addItems([
            i18n.t("sens.low"), i18n.t("sens.medium"), i18n.t("sens.high")])
        # restore selection by position (low/medium/high order)
        idx = {"low": 0, "medium": 1, "high": 2}.get(
            prev_sens, 1)
        sens_keys = list(i18n.t(f"sens.{k}") for k in ("low", "medium", "high"))
        self.sensitivity_combo.setCurrentText(sens_keys[idx])
        self.sensitivity_combo.blockSignals(False)
        # buttons
        self._mode_btn.setText(i18n.t("btn.demo_real"))
        self._overlay_btn.setText(i18n.t("btn.overlay"))
        self._calibration_btn.setText(i18n.t("btn.calibration"))
        self._export_btn.setText(i18n.t("btn.export"))
        self._clear_btn.setText(i18n.t("btn.clear"))
        self._prev_btn.setText(i18n.t("btn.prev_slide"))
        self._next_btn.setText(i18n.t("btn.next_slide"))
        self._cam_lbl.setText(i18n.t("label.camera"))
        for tool, btn in self._tool_buttons.items():
            btn.setText(i18n.t(f"tool.{tool}"))
        # status labels refresh themselves on next refresh() call
        self.refresh()

    def _next_slide(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.NEXT_SLIDE, source="ui"))
        self.refresh()

    def _prev_slide(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.PREV_SLIDE, source="ui"))
        self.refresh()

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key in (Qt.Key.Key_Right, Qt.Key.Key_PageDown, Qt.Key.Key_Space):
            self._next_slide()
            event.accept()
            return
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_PageUp):
            self._prev_slide()
            event.accept()
            return
        elif key == Qt.Key.Key_F5:
            self.session.execute(ci.ClassroomIntent(ci.PRESENTATION_START, source="ui"))
            self.refresh()
            event.accept()
            return
        elif key == Qt.Key.Key_Escape:
            self.session.execute(ci.ClassroomIntent(ci.PRESENTATION_STOP, source="ui"))
            self.refresh()
            event.accept()
            return
        super().keyPressEvent(event)

    def _run_calibration(self) -> None:
        from .calibration import ProjectorCalibration, STAGE_ORDER
        cal = ProjectorCalibration()
        cal.step_camera(True, "webcam connected")
        cal.step_projection(True, "projection area framed")
        cal.add_corner((0.2, 0.3))
        cal.add_corner((0.7, 0.3))
        cal.add_corner((0.75, 0.7))
        cal.add_corner((0.25, 0.7))
        cal.finish_corners()
        cal.finish_alignment(1)
        cal.observe_gesture("point")
        cal.observe_gesture("pinch")
        cal.observe_gesture("swipe")
        cal.observe_gesture("palm")
        cal.finish_gestures()
        report = cal.complete()
        if report.mapping is not None:
            self.session.pointer.set_calibration(report.mapping)
        QMessageBox.information(
            self, i18n.t("calibration.title"),
            i18n.t("calibration.body",
                   homography=i18n.t("calibration.ok") if report.mapping else i18n.t("calibration.fallback"),
                   err=report.alignment_error,
                   stages=", ".join(s for s in STAGE_ORDER)))

    # ---- status refresh ------------------------------------------------------
    def refresh(self) -> None:
        s = self.session.status
        self._status_labels["mode"].setText(
            self._status_text("mode", s.mode))
        self._status_labels["presentation"].setText(
            self._status_text("presentation",
                              f"{s.presentation_state} · "
                              f"slide {s.current_slide}/{s.total_slides}"))
        ptr_val = "visible" if s.pointer_visible else "hidden"
        self._status_labels["pointer"].setText(
            self._status_text("pointer",
                              f"{ptr_val} @{s.pointer_pos} "
                              f"tremor={s.pointer_tremor}"))
        self._status_labels["command"].setText(
            self._status_text("command", s.last_command))
        self._status_labels["interaction"].setText(
            self._status_text("interaction", s.current_interaction))
        self._status_labels["gesture"].setText(
            self._status_text("gesture", s.gesture or "—"))
        self._status_labels["timer"].setText(
            self._status_text("timer", f"{s.clock_seconds}s "
                              f"{'â±' if s.timer_running else ''}"))
        quiz_state = i18n.t("quiz.on") if s.quiz_active else i18n.t("quiz.off")
        self._status_labels["quiz"].setText(
            self._status_text("quiz",
                              f"{quiz_state} "
                              f"score {s.quiz_score}"
                              + (f" · Q{s.quiz_question_n}"
                                 if s.quiz_active else "")))
        self._status_labels["tool"].setText(
            self._status_text("tool",
                              i18n.t(f"tool.{s.annotation_tool}")
                              if s.annotation_tool else "—"))
        self._status_labels["strokes"].setText(
            self._status_text("strokes", s.stroke_count))
        self._status_labels["safety"].setText(
            self._status_text("safety", s.last_decision))
        self._status_labels["fps"].setText(
            self._status_text("fps", s.fps))
        self._set_env_label("lighting", s.lighting)
        self._set_env_label("noise", s.ambient_noise)
        hand_state = "visible" if s.hand_visible else "lost"
        self._set_env_label("hand", hand_state)
        self.status_changed.emit(s)
        self._burst_repaint()

    def _set_env_label(self, key: str, state: str) -> None:
        label = self._status_labels[key]
        label.setText(self._status_text(key, state))
        label.setStyleSheet(self._env_style(state))
        label.setToolTip(str(state))

    def _on_status(self, s) -> None:
        pass  # hook for subclasses / reports

    def show_log(self, msg: str) -> None:
        self.statusBar().showMessage(str(msg), 4000)

    def _burst_repaint(self) -> None:
        if self._overlay and self._overlay.isVisible():
            self._overlay.update()

    # ---- keyboard fallback -----------------------------------------------------
    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        mods = event.modifiers()
        ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
        if key == Qt.Key.Key_F5:
            self.session.handle_voice_text("start presentation")
        elif key == Qt.Key.Key_Escape:
            self.session.handle_voice_text("stop presentation")
        elif key == Qt.Key.Key_Right:
            self.session.handle_voice_text("next slide")
        elif key == Qt.Key.Key_Left:
            self.session.handle_voice_text("previous slide")
        elif key == Qt.Key.Key_B:
            self.session.handle_voice_text("pause presentation")
        elif ctrl and key == Qt.Key.Key_Plus:
            self.session.handle_voice_text("zoom in")
        elif ctrl and key == Qt.Key.Key_Minus:
            self.session.handle_voice_text("zoom out")
        elif key == Qt.Key.Key_PageDown:
            self.session.handle_voice_text("scroll down")
        elif key == Qt.Key.Key_PageUp:
            self.session.handle_voice_text("scroll up")
        elif key == Qt.Key.Key_Delete:
            self.session.execute(ci.ClassroomIntent(ci.ANNOTATION_CLEAR, source="ui"))
        elif key in (Qt.Key.Key_A, Qt.Key.Key_B, Qt.Key.Key_C, Qt.Key.Key_D):
            letter = chr(key)
            idx = {"A": 0, "B": 1, "C": 2, "D": 3}[letter]
            self.session.execute(ci.ClassroomIntent(
                ci.QUIZ_ANSWER, {"letter": letter.lower(), "answer_index": idx},
                source="ui"))
        else:
            super().keyPressEvent(event)
        self.refresh()


# ---------------------------------------------------------------------------
# Camera + gesture + voice pipeline.
# ---------------------------------------------------------------------------
def _camera_backend(cv2_mod) -> int:
    """Pick the video backend: DirectShow fails fast (returns "no frame") on a
    busy/broken webcam instead of hanging forever like MSMF on Windows."""
    if os.name == "nt" and hasattr(cv2_mod, "CAP_DSHOW"):
        return cv2_mod.CAP_DSHOW
    return getattr(cv2_mod, "CAP_ANY", 0)


class ClassroomPipeline(QObject):
    frame_ready = Signal(object)
    voice_ready = Signal(str)
    log_line = Signal(str)
    camera_state = Signal(str)  # "on" | "off" | "demo"

    def __init__(self, session: ClassroomSession, parent=None):
        super().__init__(parent)
        self.session = session
        self._running = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.tracker = None
        self.gesture_engine = None
        self._env_quality = None
        self._last_tracked: list = []
        self._noise_closed = threading.Event()
        self._noise_thread: Optional[threading.Thread] = None
        self._preview_h = 200
        self._last_frame = None
        self._demo_fallback = session.mode == "demo"
        self._camera_fallback = False   # webcam unusable -> synthetic pointer
        self._requested_camera_index: int | None = None

    def request_camera_index(self, index: int) -> None:
        self._requested_camera_index = index

    # ---- lifecycle ------------------------------------------------------------
    def start(self) -> None:
        if self._thread is not None:
            return
        self._running.set()
        self._thread = threading.Thread(target=self._loop, name="edu_air_pipeline",
                                        daemon=True)
        self._thread.start()
        try:
            self._start_voice()
        except Exception:
            self.log_line.emit("voice unavailable")

    def stop(self) -> None:
        self._running.clear()
        self._noise_closed.set()
        if self._noise_thread is not None:
            self._noise_thread.join(timeout=1.0)
            self._noise_thread = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _start_voice(self) -> None:
        from hadj_no_touch.voice.speech_recognition import SpeechManager
        from hadj_no_touch.config import VoiceSettings
        lang = {"en": "en-US", "fr": "fr-FR", "ar": "ar-SA",
                "nl": "nl-NL"} \
            .get(self.session.settings.classroom.language, "en-US")
        self._voice = SpeechManager(on_text=self.voice_ready.emit)
        self._voice.settings = VoiceSettings(language=lang)
        engine = self._voice.create()
        if engine is not None:
            self._voice.start()
            self.log_line.emit(i18n.t("voice.engine", name=engine.name))
        else:
            self.log_line.emit(i18n.t("voice.unavailable"))

        if self._demo_fallback:
            self.session.set_environment(lighting="good", ambient_noise="ok",
                                         hand_visible=True)
        else:
            self._noise_thread = threading.Thread(
                target=self._noise_loop, name="edu_air_noise", daemon=True)
            self._noise_thread.start()

    def _noise_loop(self) -> None:
        """Background ambient-noise meter -> classroom traffic light.

        Backs off when the microphone is busy (e.g. the speech recogniser
        holds it) so the two consumers never fight over the device."""
        from .voice import NoiseProbe
        probe = NoiseProbe()
        state = "unknown"
        misses = 0
        period = 2.0
        while not self._noise_closed.wait(period):
            try:
                v = probe.read(0.4)
            except Exception:
                v = "unknown"
            if v == "unknown":
                misses += 1
                period = 6.0 if misses >= 2 else 2.0
                continue
            misses = 0
            period = 2.0
            state = v
            try:
                self.session.set_environment(ambient_noise=state)
            except Exception:
                pass

    def _fallback_from_camera(self) -> None:
        """Camera open/read watchdog: drop the webcam, keep the class going
        with synthetic pointers and honest "unknown" environment states."""
        if self._camera_fallback:
            return
        self._camera_fallback = True
        try:
            self.camera_state.emit("off")
        except Exception:
            pass
        try:
            self.session.set_environment(hand_visible=False)
        except Exception:
            pass
        self.log_line.emit(
            "Camera unavailable — synthetic pointer mode. "
            "Close other apps using the webcam and restart.")

    # ---- main loop --------------------------------------------------------------
    def _loop(self) -> None:
        try:
            import cv2
        except Exception:
            cv2 = None
        from hadj_no_touch.performance import EnvironmentQuality
        from hadj_no_touch.vision.hand_tracking import HandTracker
        from hadj_no_touch.gestures import gesture_engine as ge
        self._env_quality = EnvironmentQuality()

        cam = None
        cap_w, cap_h = self.session.settings.classroom.capture_size()
        if not self._demo_fallback and cv2 is not None:
            try:
                from hadj_no_touch.camera.camera_config import resolve_camera, apply_exposure
                cam_idx, backend = resolve_camera(preferred=0, max_index=4)
                if cam_idx >= 0:
                    backend_arg = backend if backend is not None else _camera_backend(cv2)
                    cam = cv2.VideoCapture(cam_idx, backend_arg)
                    if cam.isOpened():
                        cam.set(cv2.CAP_PROP_FRAME_WIDTH, cap_w)
                        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, cap_h)
                        apply_exposure(cam)
                        ok_test, test_frame = cam.read()
                        if not ok_test or test_frame is None or test_frame.size == 0:
                            # Re-open at native resolution if resolution change broke output
                            cam.release()
                            cam = cv2.VideoCapture(cam_idx, backend_arg)
                            apply_exposure(cam)
            except Exception:
                try:
                    if cam is not None:
                        cam.release()
                except Exception:
                    pass
                cam = None

            if (cam is None or not cam.isOpened()) and cv2 is not None:
                try:
                    cam = cv2.VideoCapture(0, _camera_backend(cv2))
                    if cam.isOpened():
                        cam.set(cv2.CAP_PROP_FRAME_WIDTH, cap_w)
                        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, cap_h)
                except Exception:
                    try:
                        if cam is not None:
                            cam.release()
                    except Exception:
                        pass
                    cam = None

        if self._demo_fallback:
            self.camera_state.emit("demo")
        else:
            self.camera_state.emit(
                "on" if cam is not None and cam.isOpened() else "off")

        self.tracker = HandTracker()
        self.gesture_engine = ge.GestureEngine()

        cursor_fps = 0.0
        t0 = time.monotonic()
        frame_idx = 0
        tracked: list = []
        camera_dead_at: float | None = None
        while self._running.is_set():
            now = time.monotonic()
            dt = now - t0
            t0 = now
            if dt > 0.001:
                cursor_fps = cursor_fps * 0.9 + (1.0 / dt) * 0.1
            frame_idx += 1
            every = self.session.settings.classroom.tracking_interval()

            real_hands: list = []
            if cam is not None:
                ok, frame = cam.read()
                if ok:
                    camera_dead_at = None
                    self._last_frame = frame
                    if frame_idx % every == 0:
                        tracked = self.tracker.detect(frame, cap_w, cap_h)
                        env = self._env_quality.estimate(frame)
                        if env is not None:
                            self.session.set_environment(lighting=env.lighting)
                    real_hands = list(tracked)
                    self._emit_preview(frame)
                else:
                    if camera_dead_at is None:
                        camera_dead_at = now
                    elif now - camera_dead_at >= 4.0:
                        self._fallback_from_camera()
                        if cam is not None:
                            cam.release()
                        cam = None
            elif self._demo_fallback:
                real_hands = self._synthetic_hands(now)

            hands = real_hands
            if self._demo_fallback or not hands:
                if not hands:
                    hands = self._synthetic_hands(now)
            self.session.set_environment(
                hand_visible=bool(real_hands) or self._demo_fallback)

            pointer_norm = None
            if hands:
                tip = hands[0].landmarks_norm[8]
                pointer_norm = (float(tip[0]), float(tip[1]))
            self.session.update_pointer(pointer_norm)

            events = self.gesture_engine.update(hands, None, cap_w, cap_h)
            for ev in events:
                log = self.log_line
                try:
                    self.session.handle_gesture(ev)
                except Exception:
                    pass

            self.session._fps = cursor_fps
            self.session.tick(dt)
            if dt >= 0.5:
                self.log_line.emit(f"fps {cursor_fps:.1f} hands {len(hands)}")
            # keep the loop gentle on CPU: ~30 fps (or ~15 in performance mode)
            time.sleep(0.033 if every == 1 else 0.066)

        if cam is not None:
            cam.release()
        self.tracker.close()

    def _synthetic_hands(self, now: float):
        from .demo import synthetic_hand, moving_point
        import math
        t = now
        g = "point"
        if self.session.quiz.active and int(t) % 6 == 0:
            g = "palm"
        pos = moving_point(t)
        return [synthetic_hand(g, pos)]

    def _emit_preview(self, frame) -> None:
        try:
            h0, w0 = frame.shape[:2]
            scale = self._preview_h / h0
            import cv2
            small = cv2.resize(frame, (int(w0 * scale), self._preview_h))
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            self.frame_ready.emit(rgb)
        except Exception:
            pass


def make_session(mode: str = "real") -> ClassroomSession:
    """Build a ready classroom session matching the requested mode."""
    backend = DemoBackend() if mode == "demo" else None  # None -> RealBackend
    if mode == "demo":
        from .demo import DemoSlideDeck
        deck = DemoSlideDeck()
        settings = SETTINGS
        settings.presentation.total_slides = len(deck)
        settings.classroom.mode = "demo"
        sess = ClassroomSession(backend=backend, settings=settings)
        sess.set_mode("demo")
        return sess
    settings = SETTINGS
    settings.classroom.mode = "real"
    sess = ClassroomSession(settings=settings)
    sess.set_mode("real")
    return sess