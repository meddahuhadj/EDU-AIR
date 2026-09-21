"""The projector overlay window (PySide6).

A translucent, frameless, always-on-top window placed on the projector
screen. It paints the whiteboard/annotation strokes, the interactive
pointer, the voice-quiz question + A/B/C/D, and the classroom HUD (current
slide, last teacher command, timer, mode badge, key hints). It is
click-through by default so the presenter app underneath keeps receiving
input -- see :meth:`OverlayWindow.set_rehearsal_mode` for the one mode that
turns that off (rehearsing a lesson with no projector plugged in).

Extracted out of ``edu_air.ui`` (still re-exported there) purely to keep
that module to a readable size; nothing about its behaviour changed.
"""

from __future__ import annotations

import os
import time
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget

from . import __version__, i18n
from .classroom import ClassroomSession
from .config import SETTINGS
from .wall_toolbar import WALL_TOOLBAR_BUTTONS


def _pick_screen(index: int):
    screens = QGuiApplication.screens()
    if index is not None and index >= 0 and index < len(screens):
        return screens[index]
    return QGuiApplication.primaryScreen()


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
        self._calibration_target: Optional[tuple[float, float]] = None
        self._rehearsal_mode = False
        self._apply_click_through(True)

    def _apply_click_through(self, enabled: bool) -> None:
        """Toggle the Windows extended styles that make the overlay
        click-through and never steal focus. Off in rehearsal mode, where
        the window behaves like any normal window the teacher can move,
        resize and focus."""
        if os.name != "nt":
            return
        try:
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_TRANSPARENT = 0x00000020
            old_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            new_style = (old_style | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT) if enabled \
                else (old_style & ~WS_EX_NOACTIVATE & ~WS_EX_TRANSPARENT)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        except Exception:
            pass

    def place_on_screen(self, index: int) -> None:
        screen = _pick_screen(index)
        geo = screen.geometry()
        self.setGeometry(geo)
        self._target_screen = index

    def set_rehearsal_mode(self, enabled: bool) -> None:
        """Off (default): the real full-screen, click-through, always-on-top
        projector overlay. On: a normal bordered, movable, focusable window
        with an opaque dark backdrop -- lets a teacher rehearse a lesson
        (slides, ink, quiz) on just their own screen without a projector
        plugged in, instead of a full-screen transparent window sitting on
        top of their whole desktop."""
        if enabled == self._rehearsal_mode:
            return
        self._rehearsal_mode = enabled
        was_visible = self.isVisible()
        if enabled:
            self.setWindowFlags(Qt.WindowType.Window)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
            self.setWindowTitle(i18n.t("rehearsal.window_title"))
            self.resize(960, 540)
        else:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint
                                | Qt.WindowType.WindowStaysOnTopHint
                                | Qt.WindowType.WindowDoesNotAcceptFocus
                                | Qt.WindowType.WindowTransparentForInput
                                | Qt.WindowType.Tool)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        if was_visible:
            self.show()
        if not enabled:
            self.place_on_screen(self._target_screen)
        self._apply_click_through(not enabled)

    def set_calibration_target(self, target_norm: Optional[tuple[float, float]]) -> None:
        """Show (or, with None, clear) a crosshair at a projector-normalized
        position -- what the calibration wizard's corner/alignment steps
        point the teacher at, so "point at this corner" has an actual mark
        to aim for instead of a bare instruction."""
        self._calibration_target = target_norm
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        now = time.monotonic()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        s = self.session

        if self._rehearsal_mode:
            # No real wall/projector behind this window in rehearsal mode --
            # paint a dark backdrop so ink/pointer/HUD stay legible instead
            # of sitting on whatever happens to be on the teacher's desktop.
            p.fillRect(0, 0, w, h, QColor(18, 20, 26))

        # ---- board background (TNI pages) ------------------------------------
        if s.settings.board.enabled and s.board.current.background != "blank":
            self._paint_board_background(p, s.board)

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

        # ---- wall-mode badge + toolbar ---------------------------------------------
        if s.interaction_mode == "wall":
            self._paint_wall_badge(p, drift=s.status.calibration_drift)
            self._paint_wall_toolbar(p, w, h)

        # ---- calibration wizard target -----------------------------------------
        if self._calibration_target is not None:
            self._paint_calibration_target(p, self._calibration_target, w, h)

        # cheap repaint on the local frame budget (pointer is animated)
        if now - self._last_paint > 0.05:
            self._last_paint = now
            QTimer.singleShot(50, self.update)
        p.end()

    # painters ----------------------------------------------------------------
    def _paint_board_background(self, p: QPainter, board) -> None:
        """Draw the current page's grid / ruled-lines skin (blank = nothing)."""
        from .board import background_lines as _bg_lines
        cfg = board.settings
        name = board.current.background
        step = cfg.bg_grid_step_norm if name == "grid" else cfg.bg_line_step_norm
        lines = _bg_lines(name, p.device().width(), p.device().height(), step)
        if not lines:
            return
        col = QColor(cfg.bg_grid_color)
        col.setAlpha(90 if not self._rehearsal_mode else 255)
        p.setPen(QPen(col, 1))
        for x1, y1, x2, y2 in lines:
            p.drawLine(int(x1), int(y1), int(x2), int(y2))

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

    def _paint_calibration_target(self, p: QPainter, target_norm: tuple[float, float],
                                  w: int, h: int) -> None:
        """A pulsing ring the calibration wizard points the teacher at
        (corner or alignment target) -- distinct from the pointer reticle
        so it's unmistakably "aim here", not "you are here"."""
        tx, ty = target_norm[0] * w, target_norm[1] * h
        pulse = 0.5 + 0.5 * abs(((time.monotonic() * 1.5) % 2.0) - 1.0)
        r = 22 + 10 * pulse
        col = QColor(80, 200, 255)
        p.setPen(QPen(col, 3))
        p.drawEllipse(tx - r, ty - r, r * 2, r * 2)
        p.setPen(QPen(col, 2))
        p.drawLine(tx - 34, ty, tx - 12, ty)
        p.drawLine(tx + 12, ty, tx + 34, ty)
        p.drawLine(tx, ty - 34, tx, ty - 12)
        p.drawLine(tx, ty + 12, tx, ty + 34)
        p.setBrush(col)
        p.drawEllipse(tx - 3, ty - 3, 6, 6)

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
        # A board line appears once the whiteboard is actually in use (more
        # than one page, or ink on the page) -- the HUD box grows upwards so
        # the fixed bottom edge stays put.
        show_board = st.board_pages > 1 or st.stroke_count > 0
        line_h = int(h / 48)
        extra = line_h if show_board else 0
        hud_x = w - 260
        hud_h = 110 + extra
        hud_y = h - 120 - extra
        p.setBrush(mode_badge)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(hud_x, hud_y, 250, hud_h, 10, 10)
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
        if show_board:
            lines.append(i18n.t("hud.board_page", cur=st.board_page,
                                total=st.board_pages,
                                bg=i18n.t("bg." + st.board_background)))
        y = hud_y + 22
        for line in lines:
            p.drawText(hud_x + 14, y, line)
            y += line_h
        if s.mode == "demo":
            p.drawText(hud_x + 14, y, i18n.t("hud.demo"))

    def _paint_wall_badge(self, p: QPainter, drift: bool = False) -> None:
        """Small top-left indicator so the class can see wall mode is on --
        kept independent from the bottom-right HUD box so it never affects
        that box's fixed sizing. Grows a second line when
        ``HomographyDriftMonitor`` thinks calibration no longer fits: the
        teacher is looking at the wall, not the control-dock log, so the
        warning has to live here to actually be seen."""
        f = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        p.setFont(f)
        metrics = p.fontMetrics()
        pad = 10
        text = i18n.t("hud.wall_mode")
        drift_text = i18n.t("hud.calibration_drift") if drift else None
        box_w = metrics.horizontalAdvance(text) + pad * 2
        if drift_text is not None:
            box_w = max(box_w, metrics.horizontalAdvance(drift_text) + pad * 2)
        line_h = metrics.height()
        box_h = line_h + pad + (line_h + 4 if drift_text is not None else 0)
        p.setBrush(QColor(210, 60, 60, 235))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(20, 20, box_w, box_h, 8, 8)
        p.setPen(QColor("white"))
        p.drawText(20 + pad, 20 + pad + metrics.ascent() - 2, text)
        if drift_text is not None:
            p.drawText(20 + pad, 20 + pad + line_h + metrics.ascent() + 2, drift_text)

    def _paint_wall_toolbar(self, p: QPainter, w: int, h: int) -> None:
        """Four big buttons along the bottom edge (see ``wall_toolbar.py``)
        so a teacher in wall mode never has to walk back to the PC to
        advance a slide, switch tool or start a new page -- the touch
        router (``ClassroomSession.handle_touch_event``) hit-tests the
        exact same normalized rectangles, so what is drawn here is always
        what is actually touchable."""
        f = QFont("Segoe UI", max(11, int(h / 46)), QFont.Weight.DemiBold)
        p.setFont(f)
        for btn in WALL_TOOLBAR_BUTTONS:
            x0, y0, x1, y1 = btn.rect
            bx, by, bw, bh = x0 * w, y0 * h, (x1 - x0) * w, (y1 - y0) * h
            p.setBrush(QColor(30, 34, 46, 230))
            p.setPen(QPen(QColor(120, 200, 255), 2))
            p.drawRoundedRect(bx, by, bw, bh, 10, 10)
            p.setPen(QColor("white"))
            p.drawText(bx, by, bw, bh, Qt.AlignmentFlag.AlignCenter,
                       i18n.t(btn.label_key))
