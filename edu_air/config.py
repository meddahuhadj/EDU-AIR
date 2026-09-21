"""EDU-AIR classroom configuration.

Settings are persisted as JSON in the per-user data directory (same style as
the HADJ base configuration). Everything is local: no cloud processing, no
network dependency. Defaults are tuned for the low-cost classroom setup:
a standard computer, a webcam and a projector — no touchscreen hardware.
"""

from __future__ import annotations

import json
import os
import sys
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


def _app_base_dirs() -> list[Path]:
    """Where a bundled ``models/`` folder could live: next to the frozen
    .exe (PyInstaller sets ``sys.frozen``/``sys.executable``) and next to
    the source tree when running ``py edu_air_main.py`` directly."""
    dirs = []
    if getattr(sys, "frozen", False):
        dirs.append(Path(sys.executable).resolve().parent)
    dirs.append(Path(__file__).resolve().parent.parent)
    return dirs


def resolve_vosk_model_path(language: str, explicit_path: str = "") -> str:
    """Locate an offline Vosk model directory for ``language`` (en/fr/ar/nl).

    An explicit path always wins. Otherwise this looks for
    ``models/vosk-<lang>/`` next to the app (see the "Vosk offline" README
    note) -- no model shipped by default, so this returns "" (never raises)
    when nothing is found, matching VoskSpeechEngine.available()'s own
    honest not-available contract."""
    if explicit_path and os.path.isdir(explicit_path):
        return explicit_path
    lang = (language or "").split("-")[0].lower()
    for base in _app_base_dirs():
        candidate = base / "models" / f"vosk-{lang}"
        if candidate.is_dir():
            return str(candidate)
    return ""


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
    shape_correction: bool = True     # "ink to shape": clean up an intentional circle/rectangle on release


# --------------------------------------------------------------------------
# Wall/touch mode: contact-only writing on the projected surface.
# --------------------------------------------------------------------------
@dataclass
class TouchSettings:
    enabled: bool = False             # wall mode off by default; contactless remains the default UX
    backend: str = "shadow_gap"       # shadow_gap | ir_pen | color_marker
    sensitivity: str = "medium"       # low | medium | high (down/up threshold + debounce preset)
    down_threshold: float = 0.18      # contact_metric <= this (sustained) -> DOWN
    up_threshold: float = 0.38        # contact_metric >= this (sustained) -> UP
    down_frames: int = 2              # consecutive frames under down_threshold before DOWN fires
    up_frames: int = 3                # consecutive frames over up_threshold before UP fires
    lost_frames_up: int = 6           # frames with no usable sample before a live stroke is force-lifted
    min_confidence: float = 0.25      # samples below this are treated as "no sample"
    palm_rejection: bool = True
    debug_visual: bool = False        # overlay tip/shadow/gap/state on the camera preview
    predict_one_frame: bool = True    # linear 1-frame extrapolation to mask camera/processing latency
    smoothing_min_cutoff: float = 1.0 # One-Euro filter (reused from pointer.py) applied to the stroke
    smoothing_beta: float = 0.03
    # shadow-gap / color-marker geometry (scaled by hand/blob size, not fixed pixels)
    shadow_search_range: float = 2.2  # search corridor length, x hand/blob scale
    gap_far_ratio: float = 1.6        # gap considered "fully hovering" (contact_metric=1.0), x hand/blob scale
    min_contrast: float = 18.0        # gray-level contrast vs local background required to trust a shadow (0..255)
    # IR pen: detection is contrast-vs-background (see min_contrast above,
    # shared with shadow_gap), not a fixed cutoff. ir_threshold is only a
    # low noise floor -- it never gates detection by itself.
    ir_threshold: int = 220           # min plausible bright-spot level (0..255), noise floor only
    # color marker (default: a red tip)
    color_marker_hsv_low: list = field(default_factory=lambda: [0, 120, 70])
    color_marker_hsv_high: list = field(default_factory=lambda: [10, 255, 255])
    # palm eraser: wipe a wide swath of ink by passing an open palm over the
    # wall, like erasing a real whiteboard -- see edu_air.touch.palm_eraser
    palm_erase_enabled: bool = True
    palm_erase_contact_threshold: float = 0.35   # looser than the fingertip's down_threshold: a palm's shadow is coarser to measure
    palm_erase_min_wipe_distance: float = 0.035  # normalized path length the palm must travel while in contact before it starts erasing (anti-false-trigger: resting the hand never erases)
    palm_erase_radius: float = 0.09              # much wider than the fingertip eraser's ~0.03

    SENSITIVITY_SETS: dict = field(default_factory=lambda: {
        "low":    {"down_threshold": 0.12, "up_threshold": 0.30, "down_frames": 3, "up_frames": 4},
        "medium": {"down_threshold": 0.18, "up_threshold": 0.38, "down_frames": 2, "up_frames": 3},
        "high":   {"down_threshold": 0.26, "up_threshold": 0.46, "down_frames": 1, "up_frames": 2},
    })

    def apply_sensitivity(self) -> None:
        preset = self.SENSITIVITY_SETS.get(self.sensitivity)
        if preset is None:
            self.sensitivity = "medium"
            preset = self.SENSITIVITY_SETS["medium"]
        for k, v in preset.items():
            setattr(self, k, v)


# --------------------------------------------------------------------------
# Interactive whiteboard (TNI): multi-page digital board on any surface.
# --------------------------------------------------------------------------
@dataclass
class BoardSettings:
    enabled: bool = True
    max_pages: int = 60
    default_background: str = "blank"   # blank | grid | lines
    bg_grid_step_norm: float = 0.10     # grid cell size (fraction of the board)
    bg_line_step_norm: float = 0.20     # ruled-line spacing (fraction of the board)
    bg_grid_color: str = "#9aa0b4"
    bg_line_color: str = "#9aa0b4"
    persist: bool = False               # save/restore the notebook on exit/start
    persist_path: str = "board.json"    # relative to the per-user data dir


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
    offline_voice: bool = False       # prefer local Vosk over online Google
    vosk_model_path: str = ""         # explicit override; "" = auto-detect
                                       # models/vosk-<lang>/ next to the app
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
    touch: TouchSettings = field(default_factory=TouchSettings)
    board: BoardSettings = field(default_factory=BoardSettings)
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
                    for key in ("pointer", "annotation", "touch", "quiz", "presentation",
                                "accessibility", "classroom", "board"):
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