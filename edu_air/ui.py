"""EDU-AIR control dock (PySide6).

``ClassroomWindow`` is the control dock on the teacher's own screen: camera
preview, live status, mode switch (real/demo), sensitivity and language
controls, tool palette (point / draw / highlight / erase / clear), quiz
bank picker, calibration wizard and keyboard hints.

The other two Qt-facing pieces this module used to hold now live next to
it as siblings (still re-exported here so existing
``from edu_air.ui import ...`` call sites are unaffected):

  * ``edu_air.overlay.OverlayWindow`` — the translucent, frameless,
    always-on-top projector window (annotation strokes, pointer, quiz,
    HUD). Click-through by default so the presenter app underneath keeps
    receiving input.
  * ``edu_air.pipeline.ClassroomPipeline`` — the background thread that
    reads the webcam, runs the gesture engine and feeds the classroom
    session; recognized voice arrives through the HADJ ``SpeechManager``.

All UI updates are marshalled through Qt signals.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QVBoxLayout, QWidget, QGridLayout, QMessageBox, QScrollArea,
)

from . import __version__, i18n
# Re-exported for existing `from edu_air.ui import OverlayWindow /
# ClassroomPipeline / ...` call sites -- their actual homes are
# edu_air.overlay / edu_air.pipeline (see module docstring above).
from .overlay import OverlayWindow, _pick_screen
from .pipeline import ClassroomPipeline, LowFpsWatchdog, _CameraReader, _camera_backend

__all__ = [
    "ClassroomWindow", "make_session",
    "OverlayWindow", "ClassroomPipeline", "LowFpsWatchdog",
    "_CameraReader", "_camera_backend", "_pick_screen",
]

# ---------------------------------------------------------------------------
# Dark, modern control-dock theme. Palette kept as named constants so status
# chips / env indicators (styled per-instance in Python, not pure QSS) stay
# visually consistent with the stylesheet below.
# ---------------------------------------------------------------------------
BG = "#12141a"
SURFACE = "#1b1e27"
SURFACE_ALT = "#242833"
BORDER = "#2e3340"
TEXT = "#eef1f6"
TEXT_MUTED = "#9aa2b4"
ACCENT = "#7c6cf0"
ACCENT_HOVER = "#8f81f5"
ACCENT_PRESSED = "#6a5ce0"
OK = "#34d399"
WARN = "#f5b942"
BAD = "#ef5b5b"

DARK_QSS = f"""
QMainWindow, QWidget#central {{
    background: {BG};
}}
QLabel {{
    color: {TEXT};
    font-size: 13px;
}}
QFrame#card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QLabel#cardTitle {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QPushButton {{
    background: {SURFACE_ALT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: #2b3040;
    border-color: {ACCENT};
}}
QPushButton:pressed {{
    background: #171922;
}}
QPushButton#primaryBtn {{
    background: {ACCENT};
    border: 1px solid {ACCENT};
    color: #ffffff;
}}
QPushButton#primaryBtn:hover {{
    background: {ACCENT_HOVER};
    border-color: {ACCENT_HOVER};
}}
QPushButton#primaryBtn:pressed {{
    background: {ACCENT_PRESSED};
}}
QComboBox, QCheckBox {{
    background: {SURFACE_ALT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 22px;
}}
QComboBox:hover {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background: {SURFACE_ALT};
    color: {TEXT};
    selection-background-color: {ACCENT};
    border: 1px solid {BORDER};
    outline: none;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 3px;
    border: 1px solid {BORDER};
    background: {SURFACE_ALT};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QStatusBar {{
    background: {SURFACE};
    color: {TEXT_MUTED};
    border-top: 1px solid {BORDER};
}}
QScrollArea#scrollArea, QScrollArea#scrollArea > QWidget > QWidget {{
    background: {BG};
    border: none;
}}
QScrollBar:vertical {{
    background: {BG};
    width: 12px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {SURFACE_ALT};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {BORDER};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
"""
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


def _median_point(samples: list[tuple[float, float]]) -> Optional[tuple[float, float]]:
    """Median x/y of a short fingertip-capture window -- robust to the odd
    tracking glitch in a ~1s hold in a way a plain average is not, without
    pulling in numpy for a list this small."""
    if not samples:
        return None
    xs = sorted(s[0] for s in samples)
    ys = sorted(s[1] for s in samples)
    mid = len(samples) // 2
    return (xs[mid], ys[mid])


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
        self._restore_board()
        self._restore_journal()
        self._build_ui()
        self.status_changed.connect(self._on_status)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(200)

    # ---- TNI notebook persistence ------------------------------------------
    def _board_nb_path(self) -> Path:
        from edu_air.config import data_dir
        p = Path(getattr(SETTINGS.board, "persist_path", "board.json"))
        return p if p.is_absolute() else data_dir() / p

    def _restore_board(self) -> None:
        """Load the saved notebook on startup (guarded, never crashes)."""
        if not getattr(SETTINGS.board, "persist", False):
            return
        if getattr(self.session, "mode", None) == "demo":
            return
        try:
            self.session.board.load_nb(self._board_nb_path())
        except Exception as exc:
            self._safe_log(f"Board restore skipped: {exc}")

    def _persist_board(self) -> None:
        """Save the notebook on exit (guarded, never crashes)."""
        if not getattr(SETTINGS.board, "persist", False):
            return
        if getattr(self.session, "mode", None) == "demo":
            return
        try:
            self.session.board.save_nb(self._board_nb_path())
        except Exception as exc:
            self._safe_log(f"Board save failed: {exc}")

    def _safe_log(self, msg: str) -> None:
        try:
            self.show_log(msg)
        except Exception:
            pass

    # ---- class journal persistence -----------------------------------------
    def _journal_path(self) -> Path:
        from edu_air.config import data_dir
        return data_dir() / "journal.json"

    def _restore_journal(self) -> None:
        """Load the saved journal on startup (guarded, never crashes) --
        same pattern as ``_restore_board``. Demo-mode "classes" never
        touch the real history, restored or written."""
        if getattr(self.session, "mode", None) == "demo":
            return
        try:
            self.session.journal.load_json(self._journal_path())
        except Exception as exc:
            self._safe_log(f"Journal restore skipped: {exc}")

    def _persist_journal(self) -> None:
        if getattr(self.session, "mode", None) == "demo":
            return
        try:
            self.session.journal.save_json(self._journal_path())
        except Exception as exc:
            self._safe_log(f"Journal save failed: {exc}")

    def closeEvent(self, event) -> None:
        self._persist_board()
        self._persist_journal()
        super().closeEvent(event)

    @property
    def camera_preview(self) -> QLabel:
        """QLabel painted with the webcam feed by the app entry point."""
        return self._camera_lbl

    # ---- UI construction ----------------------------------------------------
    def _card(self, lay: QVBoxLayout, title: str = "") -> QVBoxLayout:
        """A rounded dark panel added to ``lay``; returns its inner layout."""
        frame = QFrame()
        frame.setObjectName("card")
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(10)
        if title:
            t = QLabel(title)
            t.setObjectName("cardTitle")
            inner.addWidget(t)
        lay.addWidget(frame)
        return inner

    def _build_ui(self) -> None:
        self.setWindowTitle(i18n.t("window.title"))
        self.resize(1040, 760)
        self.setStyleSheet(DARK_QSS)

        central = QWidget()
        central.setObjectName("central")
        lay = QVBoxLayout(central)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)

        # The control dock has more content (status grid + 3 action rows +
        # settings) than fits on short/low-res displays — scroll instead of
        # silently clipping controls the teacher needs (e.g. slide nav).
        scroll = QScrollArea()
        scroll.setObjectName("scrollArea")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(central)
        self.setCentralWidget(scroll)

        header = QHBoxLayout()
        header.setSpacing(4)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self._title_lbl = QLabel(i18n.t("window.title"))
        self._title_lbl.setStyleSheet(
            f"font-size: 21px; font-weight: 700; color: {TEXT};")
        title_box.addWidget(self._title_lbl)
        self._sub_lbl = QLabel(i18n.t("window.subtitle"))
        self._sub_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        title_box.addWidget(self._sub_lbl)
        header.addLayout(title_box)
        header.addStretch(1)
        lay.addLayout(header)

        # ---- camera card --------------------------------------------------
        cam_box = self._card(lay)
        self._camera_lbl = QLabel(i18n.t("camera.preview"))
        self._camera_lbl.setFixedHeight(220)
        self._camera_lbl.setStyleSheet(
            f"background:#05060a; color:{TEXT_MUTED};"
            f"border:1px solid {BORDER}; border-radius:8px; font-size:13px;")
        self._camera_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cam_box.addWidget(self._camera_lbl)

        # ---- status card ----------------------------------------------------
        status_box = self._card(lay, "Statut")
        self._status_labels: dict[str, QLabel] = {}
        grid = QGridLayout()
        grid.setSpacing(8)
        for i, key in enumerate(["mode", "presentation", "pointer", "command",
                                 "interaction", "gesture", "timer", "quiz",
                                 "tool", "strokes", "board", "safety", "fps",
                                 "lighting", "noise", "hand"]):
            lab = QLabel(self._status_text(key, ""))
            lab.setStyleSheet(
                f"background:{SURFACE_ALT}; color:{TEXT}; padding:6px 10px;"
                f"border-radius:6px; border:1px solid {BORDER};")
            grid.addWidget(lab, i // 2, i % 2)
            self._status_labels[key] = lab
        status_box.addLayout(grid)

        # ---- actions card (row 1: slide navigation, kept on its own line so
        # it never gets pushed off-screen by the secondary actions below) ----
        actions_box = self._card(lay, "Actions")
        nav_row = QHBoxLayout()
        nav_row.setSpacing(8)
        self._prev_btn = self._add_button(nav_row, i18n.t("btn.prev_slide"), self._prev_slide)
        self._prev_btn.setObjectName("primaryBtn")
        self._next_btn = self._add_button(nav_row, i18n.t("btn.next_slide"), self._next_slide)
        self._next_btn.setObjectName("primaryBtn")
        nav_row.addStretch(1)
        actions_box.addLayout(nav_row)

        # ---- actions row 2: secondary actions ---------------------------------
        ctrl1 = QHBoxLayout()
        ctrl1.setSpacing(8)
        self._mode_btn = self._add_button(ctrl1, i18n.t("btn.demo_real"),
                                          self._toggle_mode)
        self._overlay_btn = self._add_button(ctrl1, i18n.t("btn.overlay"),
                                             self._toggle_overlay)
        self._rehearsal_btn = self._add_button(ctrl1, i18n.t("btn.rehearsal"),
                                               self._toggle_rehearsal)
        self._rehearsal_btn.setCheckable(True)
        self._calibration_btn = self._add_button(ctrl1, i18n.t("btn.calibration"),
                                                 self._run_calibration)
        self._quick_calibration_btn = self._add_button(
            ctrl1, i18n.t("btn.quick_calibration"), self._quick_calibrate_pointer)
        self._wall_mode_btn = self._add_button(ctrl1, i18n.t("btn.wall_mode"),
                                               self._toggle_wall_mode)
        self._wall_mode_btn.setCheckable(True)
        self._export_btn = self._add_button(ctrl1, i18n.t("btn.export"), None)
        self._export_btn.clicked.connect(self._export_board)
        self._export_pdf_btn = self._add_button(ctrl1, i18n.t("btn.export_pdf"), None)
        self._export_pdf_btn.clicked.connect(self._export_pdf)
        self._export_quiz_btn = self._add_button(ctrl1, i18n.t("btn.export_quiz"), None)
        self._export_quiz_btn.clicked.connect(self._export_quiz)
        self._participation_btn = self._add_button(ctrl1, i18n.t("btn.participation"), None)
        self._participation_btn.clicked.connect(self._mark_participation)
        self._export_participation_btn = self._add_button(
            ctrl1, i18n.t("btn.export_participation"), None)
        self._export_participation_btn.clicked.connect(self._export_participation)
        self._log_class_btn = self._add_button(ctrl1, i18n.t("btn.log_class"), None)
        self._log_class_btn.clicked.connect(self._log_class)
        self._export_journal_btn = self._add_button(
            ctrl1, i18n.t("btn.export_journal"), None)
        self._export_journal_btn.clicked.connect(self._export_journal)
        self._clear_btn = self._add_button(ctrl1, i18n.t("btn.clear"), None)
        self._clear_btn.clicked.connect(self._clear_board)
        ctrl1.addStretch(1)
        actions_box.addLayout(ctrl1)

        # ---- tools card (row 2) ----------------------------------------------
        ctrl2 = QHBoxLayout()
        ctrl2.setSpacing(8)
        self._tool_buttons: dict[str, QPushButton] = {}
        for tool in [TOOL_POINT, TOOL_DRAW, TOOL_HIGHLIGHT, TOOL_ERASE]:
            self._tool_buttons[tool] = self._add_button(
                ctrl2, i18n.t(f"tool.{tool}"), None)
            self._tool_buttons[tool].clicked.connect(
                lambda _=False, t=tool: self._select_tool(t))
        ctrl2.addStretch(1)
        actions_box.addLayout(ctrl2)

        # ---- interactive board (TNI) row ---------------------------------------
        board_row = QHBoxLayout()
        board_row.setSpacing(8)
        self._board_prev_btn = self._add_button(
            board_row, i18n.t("btn.board_prev"), self._board_prev)
        self._board_page_lbl = QLabel("1/1")
        self._board_page_lbl.setStyleSheet(
            f"background:{SURFACE_ALT}; color:{TEXT}; padding:6px 10px;"
            f"border-radius:6px; border:1px solid {BORDER}; min-width:56px;")
        self._board_page_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        board_row.addWidget(self._board_page_lbl)
        self._board_next_btn = self._add_button(
            board_row, i18n.t("btn.board_next"), self._board_next)
        self._board_add_btn = self._add_button(
            board_row, i18n.t("btn.board_add"), self._board_add)
        self._board_del_btn = self._add_button(
            board_row, i18n.t("btn.board_del"), self._board_del)
        self._board_undo_btn = self._add_button(
            board_row, i18n.t("btn.board_undo"), self._board_undo)
        self._board_bg_lbl = QLabel(i18n.t("label.board_bg"))
        board_row.addWidget(self._board_bg_lbl)
        self._board_bg_keys = ["blank", "grid", "lines"]
        self.board_bg_combo = QComboBox()
        self.board_bg_combo.addItems(
            [i18n.t(f"bg.{k}") for k in self._board_bg_keys])
        self.board_bg_combo.currentIndexChanged.connect(self._change_board_bg)
        board_row.addWidget(self.board_bg_combo)
        self._board_persist_chk = QCheckBox(i18n.t("label.board_persist"))
        self._board_persist_chk.setChecked(
            bool(getattr(SETTINGS.board, "persist", False)))
        self._board_persist_chk.toggled.connect(self._toggle_board_persist)
        board_row.addWidget(self._board_persist_chk)
        board_row.addStretch(1)
        actions_box.addLayout(board_row)

        # ---- lesson sequencer row ---------------------------------------------
        lesson_row = QHBoxLayout()
        lesson_row.setSpacing(8)
        self._lesson_load_btn = self._add_button(
            lesson_row, i18n.t("btn.lesson_load"), self._load_lesson)
        self._lesson_prev_btn = self._add_button(
            lesson_row, i18n.t("btn.lesson_prev"), self._lesson_prev)
        self._lesson_progress_lbl = QLabel(i18n.t("label.lesson_none"))
        self._lesson_progress_lbl.setStyleSheet(
            f"background:{SURFACE_ALT}; color:{TEXT}; padding:6px 10px;"
            f"border-radius:6px; border:1px solid {BORDER};")
        self._lesson_progress_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lesson_row.addWidget(self._lesson_progress_lbl, 1)
        self._lesson_next_btn = self._add_button(
            lesson_row, i18n.t("btn.lesson_next"), self._lesson_next)
        actions_box.addLayout(lesson_row)

        # ---- settings card ----------------------------------------------------
        settings_box = self._card(lay, "Réglages")
        row2 = QHBoxLayout()
        row2.setSpacing(8)
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
        self._offline_voice_chk = QCheckBox(i18n.t("label.offline_voice"))
        self._offline_voice_chk.setToolTip(i18n.t("label.offline_voice_tip"))
        self._offline_voice_chk.setChecked(bool(SETTINGS.classroom.offline_voice))
        self._offline_voice_chk.toggled.connect(self._toggle_offline_voice)
        row2.addWidget(self._offline_voice_chk)
        row2.addStretch(1)
        settings_box.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(8)
        self._perf_lbl = QLabel(i18n.t("label.performance"))
        self._perf_check = QCheckBox()
        self._perf_check.setChecked(SETTINGS.classroom.performance_mode)
        self._perf_check.toggled.connect(self._toggle_performance)
        row3.addWidget(self._perf_lbl)
        row3.addWidget(self._perf_check)
        self._shape_correction_chk = QCheckBox(i18n.t("label.shape_correction"))
        self._shape_correction_chk.setChecked(bool(SETTINGS.annotation.shape_correction))
        self._shape_correction_chk.toggled.connect(self._toggle_shape_correction)
        row3.addWidget(self._shape_correction_chk)
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
        settings_box.addLayout(row3)

        # ---- wall/touch mode settings ------------------------------------------
        row4 = QHBoxLayout()
        row4.setSpacing(8)
        self._touch_backend_lbl = QLabel(i18n.t("label.touch_backend"))
        self.touch_backend_combo = QComboBox()
        self._touch_backend_keys = ["shadow_gap", "ir_pen", "color_marker"]
        self.touch_backend_combo.addItems(
            [i18n.t(f"backend.{k}") for k in self._touch_backend_keys])
        cur_backend = SETTINGS.touch.backend
        if cur_backend in self._touch_backend_keys:
            self.touch_backend_combo.setCurrentIndex(self._touch_backend_keys.index(cur_backend))
        self.touch_backend_combo.currentIndexChanged.connect(self._change_touch_backend)
        row4.addWidget(self._touch_backend_lbl)
        row4.addWidget(self.touch_backend_combo)

        self._touch_sens_lbl = QLabel(i18n.t("label.touch_sensitivity"))
        self.touch_sensitivity_combo = QComboBox()
        self.touch_sensitivity_combo.addItems([
            i18n.t("sens.low"), i18n.t("sens.medium"), i18n.t("sens.high")])
        self.touch_sensitivity_combo.setCurrentText(
            i18n.t(f"sens.{SETTINGS.touch.sensitivity}"))
        self.touch_sensitivity_combo.currentTextChanged.connect(self._change_touch_sensitivity)
        row4.addWidget(self._touch_sens_lbl)
        row4.addWidget(self.touch_sensitivity_combo)
        row4.addStretch(1)
        settings_box.addLayout(row4)

        row5 = QHBoxLayout()
        row5.setSpacing(8)
        self._palm_lbl = QLabel(i18n.t("label.palm_rejection"))
        self._palm_check = QCheckBox()
        self._palm_check.setChecked(SETTINGS.touch.palm_rejection)
        self._palm_check.toggled.connect(self._toggle_palm_rejection)
        row5.addWidget(self._palm_lbl)
        row5.addWidget(self._palm_check)

        self._touch_debug_lbl = QLabel(i18n.t("label.touch_debug"))
        self._touch_debug_check = QCheckBox()
        self._touch_debug_check.setChecked(SETTINGS.touch.debug_visual)
        self._touch_debug_check.toggled.connect(self._toggle_touch_debug)
        row5.addWidget(self._touch_debug_lbl)
        row5.addWidget(self._touch_debug_check)
        row5.addStretch(1)
        settings_box.addLayout(row5)

        self._hint_lbl = QLabel(i18n.t("hint.keyboard"))
        self._hint_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px;")
        lay.addWidget(self._hint_lbl)

        self._hint_label = QLabel("")
        lay.addWidget(self._hint_label)
        lay.addStretch(1)

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
        ok = f"background:#173226; color:{OK};"
        warn = f"background:#332a12; color:{WARN};"
        bad = f"background:#331a1a; color:{BAD};"
        dim = f"background:{SURFACE_ALT}; color:{TEXT_MUTED};"
        base = f"padding:6px 10px; border-radius:6px; font-weight:600; border:1px solid {BORDER};"
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
        if not self._overlay._rehearsal_mode:
            self._overlay.place_on_screen(SETTINGS.classroom.projector_screen)
        self._overlay.show()
        self._overlay._apply_click_through(not self._overlay._rehearsal_mode)

    def _toggle_rehearsal(self) -> None:
        """Mode maquette: preview the lesson (slides, ink, quiz) in a
        normal, bordered window on the teacher's own screen instead of the
        full-screen click-through projector overlay -- for preparing a
        class with no projector plugged in."""
        enabled = self._rehearsal_btn.isChecked()
        self._overlay.set_rehearsal_mode(enabled)
        if not self._overlay.isVisible():
            self._show_overlay()

    def _select_tool(self, tool: str) -> None:
        self.session.board.set_tool(tool)
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

    def _board_prev(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.BOARD_PREV_PAGE, source="ui"))
        self.refresh()

    def _board_next(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.BOARD_NEXT_PAGE, source="ui"))
        self.refresh()

    def _board_add(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.BOARD_ADD_PAGE, source="ui"))
        self.refresh()

    def _board_undo(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.BOARD_UNDO, source="ui"))
        self.refresh()

    def _board_del(self) -> None:
        if self.session.board.page_count <= 1:
            self.show_log(i18n.t("confirm.last_page"))
            return
        decision = self.session.safety.decide(ci.BOARD_DELETE_PAGE)
        if decision.requires_confirmation:
            if QMessageBox.question(self, i18n.t("confirm.title"),
                                    i18n.t("confirm.del_page")) \
                    == QMessageBox.StandardButton.Yes:
                self.session.execute(ci.ClassroomIntent(ci.BOARD_DELETE_PAGE, source="ui"))
            return
        self.session.execute(ci.ClassroomIntent(ci.BOARD_DELETE_PAGE, source="ui"))
        self.refresh()

    def _lessons_dir(self) -> str:
        """The bundled ``lessons/`` folder next to the app entry point (see
        ``lessons/example_lesson.json``) -- opened by default so a teacher
        who has never used the sequencer sees a real, valid example instead
        of an empty file browser and no idea what shape to write."""
        d = Path(__file__).resolve().parent.parent / "lessons"
        return str(d) if d.is_dir() else ""

    def _load_lesson(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, i18n.t("btn.lesson_load"), self._lessons_dir(), "JSON (*.json)")
        if not path:
            return
        if not self.session.load_lesson_json(path):
            self.show_log(i18n.t("lesson.load_failed"))
            return
        self._refresh_lesson_label()

    def _lesson_next(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.LESSON_NEXT, source="ui"))
        self._refresh_lesson_label()
        self.refresh()

    def _lesson_prev(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.LESSON_PREV, source="ui"))
        self._refresh_lesson_label()
        self.refresh()

    def _refresh_lesson_label(self) -> None:
        text = self.session.lesson.progress_text()
        self._lesson_progress_lbl.setText(text or i18n.t("label.lesson_none"))

    def _change_board_bg(self, index: int) -> None:
        if 0 <= index < len(self._board_bg_keys):
            self.session.board.set_background(self._board_bg_keys[index])
            self.refresh()

    def _toggle_board_persist(self, checked: bool) -> None:
        SETTINGS.board.persist = bool(checked)
        if checked and getattr(self.session, "mode", None) != "demo":
            try:
                self.session.board.save_nb(self._board_nb_path())
                self._safe_log(f"Notebook saved: {self._board_nb_path()}")
            except Exception as exc:
                self._safe_log(f"Notebook save failed: {exc}")
        SETTINGS.save()
        self.refresh()

    def _export_pdf(self) -> None:
        """Export the whole multi-page whiteboard to a single PDF file."""
        try:
            from PySide6.QtWidgets import QFileDialog
            from PySide6.QtGui import (QImage, QPainter, QPdfWriter, QPen,
                                       QColor, QPageSize)
            from PySide6.QtCore import Qt, QSize
            from .board import background_lines as _bg_lines
            import os, time
            default_name = f"EDU_AIR_Board_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
            path, _ = QFileDialog.getSaveFileName(
                self, i18n.t("btn.export_pdf"), default_name,
                "PDF (*.pdf);;All Files (*.*)")
            if not path:
                return
            w, h = 1600, 900
            writer = QPdfWriter(path)
            writer.setPageSize(QPageSize(QSize(w, h)))
            writer.setResolution(96)
            painter = QPainter(writer)
            board = self.session.board
            for pi, page in enumerate(board.pages):
                painter.save()
                painter.fillRect(0, 0, w, h, QColor(255, 255, 255))
                cfg = board.settings
                if page.background != "blank":
                    step = cfg.bg_grid_step_norm if page.background == "grid" \
                        else cfg.bg_line_step_norm
                    pen = QPen(QColor(cfg.bg_grid_color), 1)
                    painter.setPen(pen)
                    for x1, y1, x2, y2 in _bg_lines(page.background, w, h, step):
                        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                for item in page.model.geometry(w, h):
                    pts = item["points"]
                    if not pts:
                        continue
                    pen = QPen(QColor(item["color"]), max(1.0, item["width"]))
                    if item["highlight"]:
                        pen.setWidthF(pen.widthF() * 2)
                    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                    painter.setPen(pen)
                    if len(pts) == 1:
                        r = max(2.0, pen.widthF() / 2)
                        painter.drawEllipse(pts[0][0] - r, pts[0][1] - r, r * 2, r * 2)
                    else:
                        for i in range(len(pts) - 1):
                            painter.drawLine(pts[i][0], pts[i][1],
                                             pts[i + 1][0], pts[i + 1][1])
                painter.restore()
                if pi < len(board.pages) - 1:
                    writer.newPage()
            painter.end()
            self.show_log(i18n.t("export.pdf_success", page=len(board.pages),
                                 path=os.path.basename(path)))
        except Exception as exc:
            self.show_log(f"Export error: {exc}")

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

    def _export_quiz(self) -> None:
        """Export the quiz's per-question answer history to CSV -- a real
        session record (question, given/correct answer, right/wrong/skipped,
        time) for the teacher's cahier de classe, not just the live score."""
        try:
            from PySide6.QtWidgets import QFileDialog
            import os, time
            if not self.session.quiz.history:
                self.show_log(i18n.t("export.quiz_empty"))
                return
            default_name = f"EDU_AIR_Quiz_{time.strftime('%Y%m%d_%H%M%S')}.csv"
            path, _ = QFileDialog.getSaveFileName(
                self, i18n.t("btn.export_quiz"), default_name,
                "CSV (*.csv);;All Files (*.*)")
            if not path:
                return
            self.session.quiz.export_csv(path)
            self.show_log(i18n.t("export.quiz_success", path=os.path.basename(path)))
        except Exception as exc:
            self.show_log(f"Export error: {exc}")

    def _mark_participation(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.PARTICIPATION_MARK, source="ui"))
        self.show_log(i18n.t("participation.marked", n=self.session.participation.count))
        self.refresh()

    def _export_participation(self) -> None:
        """Export the participation tally to CSV -- same shape as the quiz
        export, for the teacher's cahier de classe."""
        try:
            from PySide6.QtWidgets import QFileDialog
            import os, time
            if not self.session.participation.history:
                self.show_log(i18n.t("export.participation_empty"))
                return
            default_name = f"EDU_AIR_Participation_{time.strftime('%Y%m%d_%H%M%S')}.csv"
            path, _ = QFileDialog.getSaveFileName(
                self, i18n.t("btn.export_participation"), default_name,
                "CSV (*.csv);;All Files (*.*)")
            if not path:
                return
            self.session.participation.export_csv(path)
            self.show_log(i18n.t("export.participation_success", path=os.path.basename(path)))
        except Exception as exc:
            self.show_log(f"Export error: {exc}")

    # ---- class journal ------------------------------------------------------
    def _log_class(self) -> None:
        """One line in the journal for the class that just happened: date/
        time (automatic), board pages used (read from the live board),
        and an optional free-text note the teacher types now while it's
        fresh."""
        from PySide6.QtWidgets import QInputDialog
        notes, ok = QInputDialog.getText(self, i18n.t("journal.title"),
                                         i18n.t("journal.notes_prompt"))
        if not ok:
            return
        entry = self.session.journal.log(self.session.board.page_count, notes)
        self._persist_journal()
        self.show_log(i18n.t("journal.logged", date=entry.date, n=self.session.journal.count))

    def _export_journal(self) -> None:
        """Export the whole class journal to a PDF table, then open the
        default mail client's compose window and reveal the PDF in
        Explorer. Windows has no way to attach a file through a plain
        mailto: link, so this is the honest "one click" flow: it gets the
        teacher to compose-window-plus-file-ready, not a silent
        auto-attach-and-send that would need SMTP credentials stored on
        the classroom PC."""
        try:
            from PySide6.QtWidgets import QFileDialog
            from PySide6.QtGui import QPainter, QPdfWriter, QPageSize, QFont, QColor
            from PySide6.QtCore import QSize
            import os, time, subprocess, urllib.parse, webbrowser

            if not self.session.journal.entries:
                self.show_log(i18n.t("export.journal_empty"))
                return
            default_name = f"EDU_AIR_Journal_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
            path, _ = QFileDialog.getSaveFileName(
                self, i18n.t("btn.export_journal"), default_name,
                "PDF (*.pdf);;All Files (*.*)")
            if not path:
                return

            w, h = 1600, 2200
            writer = QPdfWriter(path)
            writer.setPageSize(QPageSize(QSize(w, h)))
            writer.setResolution(96)
            painter = QPainter(writer)
            col_x = [60, 320, 520, 700]

            def _new_page_header() -> int:
                painter.fillRect(0, 0, w, h, QColor(255, 255, 255))
                painter.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
                painter.setPen(QColor(20, 20, 20))
                painter.drawText(60, 80, i18n.t("journal.pdf_title"))
                painter.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
                headers = [i18n.t("journal.col_date"), i18n.t("journal.col_time"),
                          i18n.t("journal.col_pages"), i18n.t("journal.col_notes")]
                for x, htext in zip(col_x, headers):
                    painter.drawText(x, 150, htext)
                painter.drawLine(60, 170, w - 60, 170)
                return 210

            y = _new_page_header()
            painter.setFont(QFont("Segoe UI", 15))
            for entry in self.session.journal.entries:
                if y > h - 80:
                    writer.newPage()
                    y = _new_page_header()
                    painter.setFont(QFont("Segoe UI", 15))
                painter.drawText(col_x[0], y, entry.date)
                painter.drawText(col_x[1], y, entry.time)
                painter.drawText(col_x[2], y, str(entry.board_pages))
                painter.drawText(col_x[3], y, entry.notes)
                y += 36
            painter.end()

            self.show_log(i18n.t("export.journal_success", path=os.path.basename(path)))
            try:
                subprocess.run(["explorer", "/select,", os.path.normpath(path)])
            except Exception:
                pass
            try:
                mailto = ("mailto:?subject=" + urllib.parse.quote(i18n.t("journal.mail_subject"))
                          + "&body=" + urllib.parse.quote(i18n.t("journal.mail_body")))
                webbrowser.open(mailto)
            except Exception:
                pass
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

    # ---- wall/touch mode -------------------------------------------------------
    def _toggle_wall_mode(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="ui"))
        self._wall_mode_btn.setChecked(self.session.interaction_mode == "wall")
        self.refresh()

    def _change_touch_backend(self, index: int) -> None:
        if not (0 <= index < len(self._touch_backend_keys)):
            return
        name = self._touch_backend_keys[index]
        SETTINGS.touch.backend = name
        pipeline = getattr(self, "_pipeline", None)
        if pipeline is not None and pipeline.touch_detector is not None:
            from .touch import build_backend
            pipeline.touch_detector.set_backend(build_backend(name))
            # set_backend() starts the fresh backend blank -- without this
            # the teacher's already-learned "plan tactile" baseline is
            # silently lost the moment they try a different backend, even
            # switching straight back to the one they just calibrated.
            pipeline.touch_detector.load_plane_calibration(
                (SETTINGS.calibration or {}).get("touch_plane", {}))
        SETTINGS.save()

    def _change_touch_sensitivity(self, value: str) -> None:
        reverse = {i18n.t(f"sens.{k}"): k for k in ("low", "medium", "high")}
        SETTINGS.touch.sensitivity = reverse.get(value, value)
        SETTINGS.touch.apply_sensitivity()
        SETTINGS.save()

    def _toggle_palm_rejection(self, checked: bool) -> None:
        SETTINGS.touch.palm_rejection = bool(checked)
        SETTINGS.save()

    def _toggle_touch_debug(self, checked: bool) -> None:
        SETTINGS.touch.debug_visual = bool(checked)
        SETTINGS.save()

    def _toggle_performance(self, on: bool) -> None:
        SETTINGS.classroom.performance_mode = bool(on)
        self.session.set_performance(bool(on))
        SETTINGS.save()
        self.refresh()

    def _toggle_shape_correction(self, on: bool) -> None:
        SETTINGS.annotation.shape_correction = bool(on)
        SETTINGS.save()

    def _toggle_offline_voice(self, on: bool) -> None:
        """Takes effect the next time voice recognition (re)starts -- the
        active engine, if any, keeps running until then (same as changing
        the camera index while a pipeline is live)."""
        SETTINGS.classroom.offline_voice = bool(on)
        SETTINGS.save()

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
        SETTINGS.save()
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
        self._offline_voice_chk.setText(i18n.t("label.offline_voice"))
        self._offline_voice_chk.setToolTip(i18n.t("label.offline_voice_tip"))
        self._shape_correction_chk.setText(i18n.t("label.shape_correction"))
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
        self._rehearsal_btn.setText(i18n.t("btn.rehearsal"))
        if self._overlay._rehearsal_mode:
            self._overlay.setWindowTitle(i18n.t("rehearsal.window_title"))
        self._calibration_btn.setText(i18n.t("btn.calibration"))
        self._quick_calibration_btn.setText(i18n.t("btn.quick_calibration"))
        self._wall_mode_btn.setText(i18n.t("btn.wall_mode"))
        self._export_btn.setText(i18n.t("btn.export"))
        self._export_pdf_btn.setText(i18n.t("btn.export_pdf"))
        self._export_quiz_btn.setText(i18n.t("btn.export_quiz"))
        self._participation_btn.setText(i18n.t("btn.participation"))
        self._export_participation_btn.setText(i18n.t("btn.export_participation"))
        self._log_class_btn.setText(i18n.t("btn.log_class"))
        self._export_journal_btn.setText(i18n.t("btn.export_journal"))
        self._clear_btn.setText(i18n.t("btn.clear"))
        self._prev_btn.setText(i18n.t("btn.prev_slide"))
        self._next_btn.setText(i18n.t("btn.next_slide"))
        self._cam_lbl.setText(i18n.t("label.camera"))
        self._board_prev_btn.setText(i18n.t("btn.board_prev"))
        self._board_next_btn.setText(i18n.t("btn.board_next"))
        self._board_add_btn.setText(i18n.t("btn.board_add"))
        self._board_del_btn.setText(i18n.t("btn.board_del"))
        self._board_undo_btn.setText(i18n.t("btn.board_undo"))
        self._board_bg_lbl.setText(i18n.t("label.board_bg"))
        self._board_persist_chk.setText(i18n.t("label.board_persist"))
        self._lesson_load_btn.setText(i18n.t("btn.lesson_load"))
        self._lesson_prev_btn.setText(i18n.t("btn.lesson_prev"))
        self._lesson_next_btn.setText(i18n.t("btn.lesson_next"))
        self._refresh_lesson_label()
        cur_bg_idx = self.board_bg_combo.currentIndex()
        self.board_bg_combo.blockSignals(True)
        self.board_bg_combo.clear()
        self.board_bg_combo.addItems([i18n.t(f"bg.{k}") for k in self._board_bg_keys])
        self.board_bg_combo.setCurrentIndex(max(0, cur_bg_idx))
        self.board_bg_combo.blockSignals(False)
        for tool, btn in self._tool_buttons.items():
            btn.setText(i18n.t(f"tool.{tool}"))
        self._touch_backend_lbl.setText(i18n.t("label.touch_backend"))
        cur_backend_idx = self.touch_backend_combo.currentIndex()
        self.touch_backend_combo.blockSignals(True)
        self.touch_backend_combo.clear()
        self.touch_backend_combo.addItems(
            [i18n.t(f"backend.{k}") for k in self._touch_backend_keys])
        self.touch_backend_combo.setCurrentIndex(max(0, cur_backend_idx))
        self.touch_backend_combo.blockSignals(False)
        self._touch_sens_lbl.setText(i18n.t("label.touch_sensitivity"))
        self.touch_sensitivity_combo.blockSignals(True)
        prev_touch_sens = SETTINGS.touch.sensitivity
        self.touch_sensitivity_combo.clear()
        self.touch_sensitivity_combo.addItems([
            i18n.t("sens.low"), i18n.t("sens.medium"), i18n.t("sens.high")])
        self.touch_sensitivity_combo.setCurrentText(i18n.t(f"sens.{prev_touch_sens}"))
        self.touch_sensitivity_combo.blockSignals(False)
        self._palm_lbl.setText(i18n.t("label.palm_rejection"))
        self._touch_debug_lbl.setText(i18n.t("label.touch_debug"))
        # status labels refresh themselves on next refresh() call
        self.refresh()

    def _next_slide(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.NEXT_SLIDE, source="ui"))
        self.refresh()

    def _prev_slide(self) -> None:
        self.session.execute(ci.ClassroomIntent(ci.PREV_SLIDE, source="ui"))
        self.refresh()

    def _calibrate_corners_live(self, cal, pipeline) -> None:
        """Step 3: measure the 4 projected corners from the live air-pointer
        fingertip instead of trusting hardcoded placeholders -- this is
        what the whole homography (and therefore every pointer/ink
        position on screen) is built from, so it is the one step that
        matters most to get from real tracking rather than a guess."""
        if pipeline is None or pipeline.tracker is None:
            cal.estimate_corners(SETTINGS.classroom.calibration_resolution)
            return

        from PySide6.QtCore import QEventLoop

        corner_keys = ["calibration.corner_tl", "calibration.corner_tr",
                      "calibration.corner_br", "calibration.corner_bl"]
        measured = 0
        for idx, key in enumerate(corner_keys):
            QMessageBox.information(
                self, i18n.t("calibration.title"),
                i18n.t("calibration.corner_point_step", corner=i18n.t(key)))
            pipeline.begin_fingertip_capture()
            loop = QEventLoop()
            QTimer.singleShot(1200, loop.quit)
            loop.exec()
            median = _median_point(pipeline.end_fingertip_capture())
            if median is not None:
                cal.add_corner(median, index=idx)
                measured += 1

        cal.finish_corners()
        if measured == 0:
            cal.estimate_corners(SETTINGS.classroom.calibration_resolution)
            self.show_log(i18n.t("calibration.corners_incomplete", n=0))
        elif measured < 4:
            self.show_log(i18n.t("calibration.corners_incomplete", n=measured))
        else:
            self.show_log(i18n.t("calibration.corners_done", n=measured))

    def _calibrate_alignment_live(self, cal, pipeline) -> None:
        """Step 5: check the homography just built against real on-screen
        targets instead of reporting a cosmetic, never-measured error --
        each target is shown as a crosshair on the projector overlay so
        the teacher has something concrete to aim at."""
        from .calibration import ALIGN_TARGETS

        if pipeline is None or pipeline.tracker is None or cal.report.mapping is None:
            cal.finish_alignment(1)
            return

        from PySide6.QtCore import QEventLoop

        overlay = getattr(self, "_overlay", None)
        measured = 0
        for i, target in enumerate(ALIGN_TARGETS):
            if overlay is not None:
                overlay.set_calibration_target(target)
            QMessageBox.information(
                self, i18n.t("calibration.title"),
                i18n.t("calibration.alignment_step", n=i + 1, total=len(ALIGN_TARGETS)))
            pipeline.begin_fingertip_capture()
            loop = QEventLoop()
            QTimer.singleShot(1200, loop.quit)
            loop.exec()
            median = _median_point(pipeline.end_fingertip_capture())
            if median is not None:
                cal.add_alignment(target, median)
                measured += 1

        if overlay is not None:
            overlay.set_calibration_target(None)
        cal.finish_alignment(1)
        if measured:
            self.show_log(i18n.t("calibration.alignment_result", n=measured,
                                 err=cal.report.alignment_error))

    def _calibrate_touch_plane(self, cal, pipeline) -> None:
        """The "plan tactile" wizard step: optionally have the teacher
        touch each of the 4 board corners for real so the active wall-mode
        backend can learn its contact baseline (see
        ``ProjectorCalibration.finish_touch_plane`` /
        ``edu_air.touch.plane_calibration``). Skippable and reversible --
        wall mode is only toggled on here if it wasn't already, and is
        toggled back off afterward."""
        if pipeline is None or pipeline.touch_detector is None:
            cal.finish_touch_plane(backend=None)
            return
        if QMessageBox.question(self, i18n.t("calibration.title"),
                                i18n.t("calibration.touch_plane_prompt")) \
                != QMessageBox.StandardButton.Yes:
            cal.finish_touch_plane(backend=None)
            return

        from PySide6.QtCore import QEventLoop

        was_wall = self.session.interaction_mode == "wall"
        if not was_wall:
            self.session.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="ui"))

        corner_keys = ["calibration.corner_tl", "calibration.corner_tr",
                      "calibration.corner_br", "calibration.corner_bl"]
        total = 0
        for idx, key in enumerate(corner_keys):
            QMessageBox.information(
                self, i18n.t("calibration.title"),
                i18n.t("calibration.touch_plane_step", corner=i18n.t(key)))
            pipeline.touch_detector.begin_capture()
            loop = QEventLoop()
            QTimer.singleShot(1800, loop.quit)
            loop.exec()
            for s in pipeline.touch_detector.end_capture():
                cal.add_touch_sample(idx, s)
                total += 1

        if not was_wall:
            self.session.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="ui"))

        cal.finish_touch_plane(backend=pipeline.touch_detector.backend)
        if cal.touch_plane.get("zones"):
            self.show_log(i18n.t("calibration.touch_plane_done", n=total,
                                 corners=len(cal.touch_samples)))

    def _run_calibration(self) -> None:
        from .calibration import ProjectorCalibration, STAGE_ORDER
        cal = ProjectorCalibration()
        pipeline = getattr(self, "_pipeline", None)
        cal.step_camera(bool(self.session.status.hand_visible or pipeline is None),
                        "webcam connected")
        cal.step_projection(True, "projection area framed")
        self._calibrate_corners_live(cal, pipeline)
        self._calibrate_touch_plane(cal, pipeline)
        self._calibrate_alignment_live(cal, pipeline)
        cal.observe_gesture("point")
        cal.observe_gesture("pinch")
        cal.observe_gesture("swipe")
        cal.observe_gesture("palm")
        cal.finish_gestures()
        report = cal.complete()
        if report.mapping is not None:
            self.session.pointer.set_calibration(report.mapping)
            if pipeline is not None and pipeline.touch_detector is not None:
                pipeline.touch_detector.set_calibration(report.mapping)
                if cal.touch_plane:
                    pipeline.touch_detector.load_plane_calibration(cal.touch_plane)
        QMessageBox.information(
            self, i18n.t("calibration.title"),
            i18n.t("calibration.body",
                   homography=i18n.t("calibration.ok") if report.mapping else i18n.t("calibration.fallback"),
                   err=report.alignment_error,
                   stages=", ".join(s for s in STAGE_ORDER)))

    def _quick_calibrate_pointer(self) -> None:
        """A fast mid-class touch-up: 3 taps instead of the full wizard's 4
        corners + optional touch plane + 5-target alignment check. Updates
        the pointer (and, if wall mode's touch detector exists, that too)
        in place -- does not touch ``ProjectorCalibration``'s stage report,
        so it never interferes with a later full re-calibration."""
        from .calibration import QUICK_CALIB_TARGETS, quick_calibrate

        pipeline = getattr(self, "_pipeline", None)
        if pipeline is None or pipeline.tracker is None:
            self.show_log(i18n.t("calibration.quick_no_camera"))
            return

        from PySide6.QtCore import QEventLoop

        overlay = getattr(self, "_overlay", None)
        measured: list[tuple[float, float]] = []
        for i, target in enumerate(QUICK_CALIB_TARGETS):
            if overlay is not None:
                overlay.set_calibration_target(target)
            QMessageBox.information(
                self, i18n.t("calibration.title"),
                i18n.t("calibration.quick_point_step", n=i + 1,
                       total=len(QUICK_CALIB_TARGETS)))
            pipeline.begin_fingertip_capture()
            loop = QEventLoop()
            QTimer.singleShot(1200, loop.quit)
            loop.exec()
            median = _median_point(pipeline.end_fingertip_capture())
            if median is not None:
                measured.append(median)

        if overlay is not None:
            overlay.set_calibration_target(None)

        mapping = quick_calibrate(measured)
        if mapping is not None:
            self.session.pointer.set_calibration(mapping)
            if pipeline.touch_detector is not None:
                pipeline.touch_detector.set_calibration(mapping)
            self.show_log(i18n.t("calibration.quick_done", n=len(measured)))
        else:
            self.show_log(i18n.t("calibration.quick_incomplete", n=len(measured)))

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
        self._status_labels["board"].setText(
            self._status_text("board",
                              f"{s.board_page}/{s.board_pages} · "
                              f"{i18n.t('bg.' + s.board_background)}"))
        self._status_labels["safety"].setText(
            self._status_text("safety", s.last_decision))
        self._status_labels["fps"].setText(
            self._status_text("fps", s.fps))
        self._set_env_label("lighting", s.lighting)
        self._set_env_label("noise", s.ambient_noise)
        hand_state = "visible" if s.hand_visible else "lost"
        self._set_env_label("hand", hand_state)
        self._wall_mode_btn.setChecked(s.interaction_mode == "wall")
        self._lesson_progress_lbl.setText(s.lesson_progress or i18n.t("label.lesson_none"))
        board = self.session.board
        self._board_page_lbl.setText(f"{board.current_index + 1}/{board.page_count}")
        bg_idx = self._board_bg_keys.index(board.current.background)
        if self.board_bg_combo.currentIndex() != bg_idx:
            self.board_bg_combo.blockSignals(True)
            self.board_bg_combo.setCurrentIndex(bg_idx)
            self.board_bg_combo.blockSignals(False)
        if self._perf_check.isChecked() != s.performance_mode:
            # Reflects an auto-triggered low-CPU switch too, not just the
            # checkbox's own clicks -- see ClassroomPipeline's sustained-low-FPS
            # watchdog in _loop().
            self._perf_check.blockSignals(True)
            self._perf_check.setChecked(s.performance_mode)
            self._perf_check.blockSignals(False)
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
        """Direct action dispatch — never routed through the language-specific
        voice-text parser, so these shortcuts work regardless of the current
        voice recognition language."""
        key = event.key()
        mods = event.modifiers()
        ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)

        def run(action: str, params: dict | None = None) -> None:
            self.session.execute(ci.ClassroomIntent(action, params or {}, source="ui"))

        if key == Qt.Key.Key_F5:
            run(ci.PRESENTATION_START)
        elif key == Qt.Key.Key_Escape:
            run(ci.PRESENTATION_STOP)
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_PageDown, Qt.Key.Key_Space):
            run(ci.NEXT_SLIDE)
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_PageUp):
            run(ci.PREV_SLIDE)
        elif key == Qt.Key.Key_B:
            run(ci.PAUSE_PRESENTATION)
        elif ctrl and key == Qt.Key.Key_Plus:
            run(ci.ZOOM_IN)
        elif ctrl and key == Qt.Key.Key_Minus:
            run(ci.ZOOM_OUT)
        elif key == Qt.Key.Key_Delete:
            run(ci.ANNOTATION_CLEAR)
        elif key == Qt.Key.Key_W:
            run(ci.TOGGLE_WALL_MODE)
        elif ctrl and key == Qt.Key.Key_N:
            run(ci.BOARD_ADD_PAGE)
        elif ctrl and key == Qt.Key.Key_Z:
            run(ci.BOARD_UNDO)
        elif key == Qt.Key.Key_P:
            run(ci.PARTICIPATION_MARK)
        elif key in (Qt.Key.Key_A, Qt.Key.Key_C, Qt.Key.Key_D):
            letter = chr(key)
            idx = {"A": 0, "C": 2, "D": 3}[letter]
            run(ci.QUIZ_ANSWER, {"letter": letter.lower(), "answer_index": idx})
        else:
            super().keyPressEvent(event)
        self.refresh()


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