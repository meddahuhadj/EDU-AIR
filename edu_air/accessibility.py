"""EDU-AIR accessibility.

Low-cost classroom accessibility for teachers who need help with the
contactless interaction:

  * large targets      — the projected pointer and on-screen targets are
                         oversized;
  * voice-first        — every classroom action has a voice alias;
  * one-hand gestures  — every gesture can be performed with a single hand;
  * keyboard fallback  — every action maps to plain keys (space/arrows/PgUp/
                         F5/ESC …) with on-screen hints, so a teacher can
                         control the lesson even if the camera or mic fails;
  * configurable sensitivity — low/medium/high dials that tune smoothing,
                         speed and dwell time together.

``apply()`` pushes the accessibility profile into the runtime classroom
settings (pointer, gestures, confirmation dwell).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .config import SETTINGS

DWELL_PRESETS = {
    "low": {"smoothing": 0.48, "speed": 0.70, "dead_zone": 0.010,
            "dwell_ms": 500},
    "medium": {"smoothing": 0.30, "speed": 1.00, "dead_zone": 0.006,
               "dwell_ms": 350},
    "high": {"smoothing": 0.18, "speed": 1.35, "dead_zone": 0.003,
             "dwell_ms": 250},
}


@dataclass
class AccessibilityState:
    large_targets: bool = True
    voice_first: bool = False
    one_hand: bool = True
    keyboard_fallback: bool = True
    sensitivity: str = "medium"     # low | medium | high
    dwell_ms: int = 350
    target_size_px: int = 48
    hints: list = field(default_factory=list)  # on-screen key hints

    KEYBOARD_HINTS: dict = field(default_factory=lambda: {
        "start": "F5", "stop": "ESC", "next_slide": "→",
        "prev_slide": "←", "pause": "B", "zoom_in": "Ctrl +",
        "zoom_out": "Ctrl -", "scroll_down": "PgDn", "scroll_up": "PgUp",
        "clear_annotations": "Ctrl+Shift+C",
    })


class AccessibilityController:
    def __init__(self, state: AccessibilityState | None = None,
                 pointer: Optional[PointerSettings] = None):
        self.state = state or AccessibilityState()
        self.pointer = pointer or SETTINGS.pointer

    def apply(self) -> None:
        """Push the accessibility profile into live settings."""
        preset = DWELL_PRESETS.get(self.state.sensitivity, DWELL_PRESETS["medium"])
        self.pointer.smoothing = preset["smoothing"]
        self.pointer.speed = preset["speed"]
        self.pointer.dead_zone = preset["dead_zone"]
        self.pointer.large_targets = self.state.large_targets
        self.pointer.sensitivity = self.state.sensitivity
        acc = SETTINGS.accessibility
        acc.dwell_ms = self.state.dwell_ms
        acc.large_targets = self.state.large_targets
        acc.one_hand_gestures = self.state.one_hand
        acc.keyboard_fallback = self.state.keyboard_fallback
        acc.voice_first = self.state.voice_first

    def set_sensitivity(self, level: str) -> None:
        if level in DWELL_PRESETS:
            self.state.sensitivity = level
            self.state.dwell_ms = DWELL_PRESETS[level]["dwell_ms"]
            self.apply()

    def key_hint(self, action: str) -> str:
        """Return the keyboard fallback hint for an action ('' if none)."""
        if not self.state.keyboard_fallback:
            return ""
        return self.state.KEYBOARD_HINTS.get(action, "")

    def targets_scaled(self, base_px: int = 22) -> int:
        if self.state.large_targets:
            return max(base_px, self.state.target_size_px)
        return base_px