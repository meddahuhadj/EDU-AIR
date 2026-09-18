"""Presentation controller for the classroom.

Drives the real slide-deck application (PowerPoint / Impress / PDF reader /
web slides) through a thin driver abstraction so it can be:
  * unit-tested with a recording driver (nothing touches the OS);
  * wired to the real Win32 keyboard in production;
  * fully simulated in demo mode.

State machine: IDLE -> ACTIVE -> (PAUSED toggle) -> IDLE.
All commands produce a structured ``CommandRecord`` used by the classroom
HUD and the safety audit trail.
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from .config import PresentationSettings, SETTINGS

# ---------------------------------------------------------------------------
# External whiteboard app presets (OpenBoard / Xournal++).
#
# The keymaps below are *editable baselines*: whiteboard apps expose slightly
# different shortcuts per version, so every value can be overridden in the
# settings keymap. `launch_command` (when set) runs the app binary when the
# presentation starts; otherwise the shorthand in DEFAULT_LAUNCH is tried.
# ---------------------------------------------------------------------------
DEFAULT_LAUNCH: dict[str, str] = {
    "openboard": "openboard",
    "xournalpp": "xournalpp",
}

EXTERNAL_APP_PRESETS: dict[str, dict] = {
    "none": {},
    "openboard": {
        "start": "F2",              # OpenBoard often starts the deck from F2
        "stop": "ESC",
        "next_slide": "RIGHT",
        "prev_slide": "LEFT",
        "pause": "PAUSE",
        "zoom_in": "PLUS",
        "zoom_out": "MINUS",
        "scroll_down": "PAGEDOWN",
        "scroll_up": "PAGEUP",
    },
    "xournalpp": {
        "start": "F5",
        "stop": "ESC",
        "next_slide": "RIGHT",
        "prev_slide": "LEFT",
        "pause": "B",
        "zoom_in": "PLUS",
        "zoom_out": "MINUS",
        "zoom_in_mods": ["CTRL"],
        "zoom_out_mods": ["CTRL"],
        "scroll_down": "PAGEDOWN",
        "scroll_up": "PAGEUP",
    },
}


@dataclass
class CommandRecord:
    command: str
    key: str = ""
    modifiers: list = field(default_factory=list)
    simulated: bool = False
    ts: float = field(default_factory=time.monotonic)
    note: str = ""


class PresentationDriver:
    """Abstraction over the real OS input. Replaced by a recorder in tests
    and a no-op in demo mode."""

    def key(self, name: str, modifiers: list[str] | None = None) -> None:
        raise NotImplementedError

    def wheel(self, amount: int) -> None:
        raise NotImplementedError


class RealPresentationDriver(PresentationDriver):
    """Sends real keyboard input through the HADJ Win32 layer."""

    def __init__(self) -> None:
        from hadj_no_touch.windows import keyboard_control, window_control  # local import
        self._kc = keyboard_control
        self._wc = window_control

    def key(self, name: str, modifiers: list[str] | None = None) -> None:
        try:
            self._wc.ensure_presentation_focus()
        except Exception:
            pass
        self._kc.tap(name, modifiers)

    def wheel(self, amount: int) -> None:
        from hadj_no_touch.windows import mouse_control  # local import
        mouse_control.scroll(amount)


class RecordingDriver(PresentationDriver):
    """Test/demo driver: records every requested key/wheel event."""

    def __init__(self) -> None:
        self.keys: list[tuple[str, list]] = []
        self.wheels: list[int] = []

    def key(self, name: str, modifiers: list[str] | None = None) -> None:
        self.keys.append((name, list(modifiers or [])))

    def wheel(self, amount: int) -> None:
        self.wheels.append(amount)

    @property
    def key_sequence(self) -> list[str]:
        return [name for name, _ in self.keys]


if __name__ != "__main__":
    pass  # module is import-safe on any OS


class PresentationController:
    """Tracks the classroom presentation lifecycle and maps commands to keys."""

    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"

    def __init__(self, driver: PresentationDriver | None = None,
                 settings: PresentationSettings | None = None,
                 on_record: Optional[Callable[[CommandRecord], None]] = None):
        self.driver = driver or _default_driver()
        self.settings = settings or SETTINGS.presentation
        self.on_record = on_record
        self.state = self.IDLE
        self.slide_index = 0
        self.total_slides = max(1, self.settings.total_slides)
        self.history: list[CommandRecord] = []
        self._max_history = 60
        self._last_go_slide = 0
        self.suppress_launch = False    # demo mode never launches external apps
        if self.settings.external_app not in ("", "none"):
            self.apply_external_app(self.settings.external_app)

    # ---- state ------------------------------------------------------------
    def apply_external_app(self, name: str) -> None:
        """Merge an external-whiteboard keymap preset onto the current
        keymap and remember the selection for persistence."""
        preset = EXTERNAL_APP_PRESETS.get(name)
        if not preset:
            return
        self.settings.external_app = name
        self.settings.keymap.update(dict(preset))

    def _launch_external(self) -> str:
        """Start the external whiteboard app (honest best-effort: nothing
        happens when the binary is missing or demo mode suppresses it)."""
        if self.suppress_launch:
            return "launch suppressed (demo)"
        cmd = (self.settings.launch_command or
               DEFAULT_LAUNCH.get(self.settings.external_app, ""))
        if not cmd:
            return ""
        try:
            flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0  # DETACHED|CREATE_NEW_PROCESS_GROUP
            subprocess.Popen(cmd, shell=os.name != "nt",
                             creationflags=flags,
                             start_new_session=os.name != "nt")
            return f"launched {cmd}"
        except Exception:
            return f"launch failed: {cmd}"

    def start(self, total_slides: int | None = None) -> CommandRecord:
        if total_slides is not None:
            self.total_slides = max(1, total_slides)
        self.slide_index = 0
        self.state = self.ACTIVE
        note = "F5 starts the slideshow"
        if self.settings.external_app not in ("", "none"):
            extra = self._launch_external()
            if extra:
                note += " · " + extra
        return self._send("start", note=note)

    def stop(self) -> CommandRecord:
        r = self._send("stop", note="ESC ends the slideshow")
        self.state = self.IDLE
        self.slide_index = 0
        return r

    def pause(self) -> CommandRecord:
        """Black-screen pause (press again to resume)."""
        if self.state == self.IDLE:
            return CommandRecord("pause", note="ignored (no active presentation)")
        self.state = self.PAUSED if self.state == self.ACTIVE else self.ACTIVE
        return self._send("pause", note="black screen toggled")

    def resume(self) -> CommandRecord:
        if self.state == self.PAUSED:
            self.state = self.ACTIVE
            return self._send("pause", note="black screen cleared")
        return CommandRecord("resume", note="no paused presentation")

    # ---- slide movement ---------------------------------------------------
    def next_slide(self) -> CommandRecord:
        if self.state == self.IDLE:
            return CommandRecord("next_slide", note="ignored (no active presentation)")
        self.slide_index = min(self.total_slides - 1, self.slide_index + 1)
        return self._send("next_slide")

    def prev_slide(self) -> CommandRecord:
        if self.state == self.IDLE:
            return CommandRecord("prev_slide", note="ignored (no active presentation)")
        self.slide_index = max(0, self.slide_index - 1)
        return self._send("prev_slide")

    def go_to(self, index: int) -> CommandRecord:
        if self.state == self.IDLE:
            return CommandRecord("go_to", note="ignored (no active presentation)")
        self.slide_index = max(0, min(self.total_slides - 1, index))
        # PowerPoint cannot jump directly; scroll from current position.
        diff = self.slide_index - self._last_go_slide
        self._last_go_slide = self.slide_index
        if diff != 0:
            return self._send("go_to", note=f"advancing {abs(diff)} slides")
        return CommandRecord("go_to", note="already on that slide")

    # ---- view tools -------------------------------------------------------
    def zoom_in(self) -> CommandRecord:
        return self._send("zoom_in", mods=self.settings.keymap["zoom_in_mods"])

    def zoom_out(self) -> CommandRecord:
        return self._send("zoom_out", mods=self.settings.keymap["zoom_out_mods"])

    def scroll_down(self) -> CommandRecord:
        return self._send("scroll_down")

    def scroll_up(self) -> CommandRecord:
        return self._send("scroll_up")

    # ---- diagnostics ------------------------------------------------------
    @property
    def active(self) -> bool:
        return self.state in (self.ACTIVE, self.PAUSED)

    def _send(self, command: str, note: str = "", mods: list | None = None) -> CommandRecord:
        km = self.settings.keymap
        key = km.get(command, "")
        mods = list(mods or km.get(command + "_mods", []))
        r = CommandRecord(command=command, key=key, modifiers=mods, note=note)
        self.history.append(r)
        if len(self.history) > self._max_history:
            self.history = self.history[-self._max_history:]
        if self.on_record is not None:
            try:
                self.on_record(r)
            except Exception:
                pass
        if key:
            self.driver.key(key, mods)
        return r


_last_go_slide = 0  # placeholder for backward compat; real state is on the instance


def _default_driver() -> PresentationDriver:
    try:
        return RealPresentationDriver()
    except Exception:
        return RecordingDriver()