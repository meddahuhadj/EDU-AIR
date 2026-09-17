"""Countdown-gated confirmation for sensitive one-shot actions.

A sensitive intent (launch that opens a document, profile switch, etc.) is
routed through the Safety Engine's confirmation gate. This dialog shows the
proposed action for a short *anti-reflex* countdown before the Confirm button
becomes enabled, so a split-second gesture reflex can never slam an
affirmative through the gate. Highly sensitive ("CRITICAL") actions demand a
second, explicit tap after the countdown has elapsed.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from ..config import SETTINGS
from ..logging_setup import get_logger

log = get_logger("ui.confirm")

# Actions considered CRITICAL: even after the gate countdown, the operator
# must confirm a second time so a reflex double-trigger can never slip in.
CRITICAL_ACTIONS = {"OPEN_DOCUMENT", "PROFILE_SWITCH", "OPEN_APP"}


class ConfirmationCountdownDialog(QDialog):
    """Non-modal, single-instance confirmation with an anti-reflex countdown.

    The ``confirmed`` signal carries the original :class:`~Intent`; the caller
    (MainWindow) forwards it to ``AppCore.confirm_pending``. The default
    ``rejected`` signal is emitted when the operator cancels.
    """

    confirmed = Signal(object)  # Intent

    def __init__(self, intent, parent=None):
        super().__init__(parent)
        self._intent = intent
        self._stage = "wait"          # wait -> arm -> (critical) -> second
        self._seconds_left = SETTINGS.gestures.confirmation_countdown_ms / 1000.0
        self.setWindowTitle("Confirm action")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool)
        self.setModal(False)

        self._title = QLabel("Confirm action")
        f = self._title.font()
        f.setBold(True)
        f.setPixelSize(16)
        self._title.setFont(f)

        self._desc = QLabel(intent.describe() if hasattr(intent, "describe") else str(intent))
        self._desc.setWordWrap(True)

        self._timer_label = QLabel()
        self._timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._confirm_btn = QPushButton("Confirm")
        self._confirm_btn.setDefault(True)
        self._confirm_btn.clicked.connect(self._on_click)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)

        layout_right = QVBoxLayout()
        layout_right.addWidget(self._timer_label)
        layout_right.addWidget(self._confirm_btn)
        layout_right.addWidget(self._cancel_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._desc)
        layout.addLayout(self._row())
        layout.addLayout(layout_right)

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        self._render()

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _row(self) -> None:
        pass

    def _tick(self) -> None:
        if self._stage == "wait":
            self._seconds_left -= 0.1
            if self._seconds_left <= 0.0:
                self._seconds_left = 0.0
                self._stage = "arm"
        self._render()

    def _seconds_text(self) -> str:
        return f"{self._seconds_left:04.1f}s"

    def _on_click(self) -> None:
        if self._stage == "wait":
            return
        if self._stage == "arm" and self._is_critical():
            # CRITICAL: arm a second explicit tap.
            self._stage = "second"
            self._render()
            return
        self._timer.stop()
        self.confirmed.emit(self._intent)
        self.accept()

    def _render(self) -> None:
        if self._stage == "wait":
            self._timer_label.setText("Confirm enabled in " + self._seconds_text())
            self._timer_label.setStyleSheet(f"color: #8a5a00; font-weight: bold;")
            self._confirm_btn.setEnabled(False)
            self._confirm_btn.setText("Confirm")
        elif self._stage == "arm":
            self._timer_label.setText("Tap Confirm to proceed")
            self._timer_label.setStyleSheet(f"color: #0a6b2b; font-weight: bold;")
            self._confirm_btn.setEnabled(True)
            self._confirm_btn.setText("Confirm" if not self._is_critical() else "Confirm (1/2)")
        else:  # second
            self._timer_label.setText("This is a sensitive action — tap again to confirm")
            self._timer_label.setStyleSheet("color: #b30000; font-weight: bold;")
            self._confirm_btn.setEnabled(True)
            self._confirm_btn.setText("Confirm (2/2)")

    @staticmethod
    def _is_critical(intent) -> bool:
        action = getattr(intent, "action", "")
        return action in CRITICAL_ACTIONS

    def _is_critical(self) -> bool:
        return self._is_critical(self._intent)

    # ------------------------------------------------------------------
    # qdialog contract
    # ------------------------------------------------------------------
    def done(self, r: int) -> None:
        self._timer.stop()
        super().done(r)
