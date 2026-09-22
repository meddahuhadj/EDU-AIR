"""EDU-AIR classroom configuration.

Settings are persisted as JSON in the per-user data directory (same style as
the HADJ base configuration). Everything is local: no cloud processing, no
network dependency. Defaults are tuned for the low-cost classroom setup:
a standard computer, a webcam and a projector — no touchscreen hardware.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path

APP_DIR_NAME = "EDU-AIR"


def data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    path = Path(base) / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_config_path() -> Path:
    return data_dir() / "config.json"


# --------------------------------------------------------------------------
# Pointer: smoothing / dead zone / jitter / sensitivity / calibration hook.
# --------------------------------------------------------------------------
@dataclass
class PointerSettings:
    enabled: bool = True
    smoothing: float = 0.30          # EMA alpha applied to target displacement
    speed: float = 1.0               # sensitivity gain on displacement
    dead_zone: float = 0.006         # normalized movement below -> hold position
    max_jump_ratio: float = 0.30     # single-frame spike rejection (fraction of screen diagonal)
    jitter_suppression: float = 0.35 # 0..1 damping of sub-dead-zone tremor
    jitter_floor: float = 0.003      # movements smaller than this (normalized) are tremor
    large_targets: bool = True       # enlarged pointer targets / big crosshair
    left_handed: bool = False
    mirror_x: bool = True            # webcam sees you mirrored; flip for correctness
    sensitivity: str = "medium"      # low | medium | high (user-facing dial)
    # Calibration hook: a callable(norm)->norm homography supplied by the
    # projector calibration wizard (or the HADJ CalibrationManager).
    calibration: object = None

    SENSITIVITY_SETS: dict = field(default_factory=lambda: {
        "low": {"smoothing": 0.48, "speed": 0.70, "dead_zone": 0.010,
                "jitter_suppression": 0.55},
        "medium": {"smoothing": 0.30, "speed": 1.00, "dead_zone": 0.006,
                   "jitter_suppression": 0.35},
        "high": {"smoothing": 0.18, "speed": 1.35, "dead_zone": 0.003,
                 "jitter_suppression": 0.20},
    })

    def apply_sensitivity(self) -> None:
        preset = self.SENSITIVITY_SETS.get(self.sensitivity)
        if preset is None:
            self.sensitivity = "medium"
            preset = self.SENSITIVITY_SETS["medium"]
        for k, v in preset.items():
            setattr(self, k, v)


# --------------------------------------------------------------------------
# Air annotation tools.
# --------------------------------------------------------------------------
@dataclass
class AnnotationSettings:
    enabled: bool = True
    default_tool: str = "none"       # none | point | draw | highlight | erase
    draw_color: str = "#ff3b30"
    draw_width: int = 3
    highlight_color: str = "#ffd60a"
    highlight_width: int = 18
    highlight_opacity: float = 0.35
    pointer_color: str = "#ff2d55"
    pointer_size: int = 22
    erase_radius: int = 28
    max_strokes: int = 200


# --------------------------------------------------------------------------
# Voice quiz.
# --------------------------------------------------------------------------
@dataclass
class QuizSettings:
    enabled: bool = True
    question_bank_path: str = ""
    default_timeout_s: int = 60
    reveal_on_answer: bool = False    # auto-show correct answer after a guess
    option_labels: tuple = ("A", "B", "C", "D")


# --------------------------------------------------------------------------
# Presentation control.
# --------------------------------------------------------------------------
@dataclass
class PresentationSettings:
    total_slides: int = 10
    app: str = "powerpoint"           # powerpoint | impress | pdf
    auto_start_on_voice: bool = True
    show_hud: bool = True
    hud_corners: str = "bottom-right" # bottom-right | top-right | ...
    external_app: str = "none"        # none | openboard | xournalpp
    launch_command: str = ""          # optional command/EXE run when starting
    keymap: dict = field(default_factory=lambda: {
        "start": "F5",
        "stop": "ESC",
        "next_slide": "RIGHT",
        "prev_slide": "LEFT",
        "pause": "B",
        "zoom_in": "PLUS",
        "zoom_out": "MINUS",
        "scroll_down": "PAGEDOWN",
        "scroll_up": "PAGEUP",
        "zoom_in_mods": ["CTRL"],
        "zoom_out_mods": ["CTRL"],
    })


# --------------------------------------------------------------------------
# Accessibility.
# --------------------------------------------------------------------------
@dataclass
class AccessibilitySettings:
    large_targets: bool = True
    one_hand_gestures: bool = True
    voice_first: bool = False
    keyboard_fallback: bool = True    # on-screen key hints + space/arrow hotkeys
    dwell_ms: int = 350
    confirmation_gate_ms: int = 5000
    reduced_motion: bool = False


# --------------------------------------------------------------------------
# Classroom presentation / projector.
# --------------------------------------------------------------------------
PROJECTOR_PRESETS = ("1920x1080", "1280x800", "1024x768")
EXTERNAL_APP_OPTIONS = ("none", "openboard", "xournalpp")


@dataclass
class ClassroomSettings:
    mode: str = "real"                # real | demo
    language: str = "en"              # en | fr | ar | nl (voice recognition)
    projector_screen: int = -1        # -1 = primary; >=0 = secondary monitor index
    show_camera_preview: bool = True
    interaction_timeout_s: int = 300  # hands idle -> pointer auto-hide
    wake_word: str = ""               # optional voice gate, e.g. "EDU AIR"
    performance_mode: bool = False    # low-CPU classroom PC preset (320x240 @ 2)
    camera_width: int = 640
    camera_height: int = 480
    process_every: int = 1            # tracking passes between heavy frames
    calibration_resolution: str = "1920x1080"  # projector-guide preset

    def capture_size(self) -> tuple[int, int]:
        """Capture resolution actually used by the pipeline. Performance mode
        halves the workload for older classroom PCs."""
        if self.performance_mode:
            return 320, 240
        return self.camera_width, self.camera_height

    def tracking_interval(self) -> int:
        """Hand-tracking passes performed: every Nth frame. Doubled (lighter)
        in performance mode."""
        if self.performance_mode:
            return max(1, self.process_every * 2)
        return max(1, self.process_every)


@dataclass
class Settings:
    pointer: PointerSettings = field(default_factory=PointerSettings)
    annotation: AnnotationSettings = field(default_factory=AnnotationSettings)
    quiz: QuizSettings = field(default_factory=QuizSettings)
    presentation: PresentationSettings = field(default_factory=PresentationSettings)
    accessibility: AccessibilitySettings = field(default_factory=AccessibilitySettings)
    classroom: ClassroomSettings = field(default_factory=ClassroomSettings)
    calibration: dict = field(default_factory=dict)

    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def load(self, path: Path | None = None) -> "Settings":
        with self._lock:
            p = path or default_config_path()
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    for key in ("pointer", "annotation", "quiz", "presentation",
                                "accessibility", "classroom"):
                        blk = getattr(self, key)
                        sub = data.pop(key, {})
                        for f in fields(blk):
                            if f.name in sub:
                                setattr(blk, f.name, sub[f.name])
                    if "calibration" in data:
                        self.calibration = dict(data["calibration"])
                except Exception:
                    pass
            return self

    def save(self, path: Path | None = None) -> None:
        with self._lock:
            p = path or default_config_path()
            p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def to_dict(self) -> dict:
        d = {}
        for f in fields(self):
            if f.name == "_lock":
                continue
            val = getattr(self, f.name)
            if hasattr(val, "__dataclass_fields__"):
                val = asdict(val)
            d[f.name] = val
        return d


SETTINGS = Settings()