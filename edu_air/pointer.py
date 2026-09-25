"""Interactive pointer: webcam fingertip -> projected display position.

Implements the classroom pointer quality pipeline:

  raw fingertip (normalized)
      -> clamp
      -> calibration mapping (homography, optional)
      -> spike rejection (single-frame jump = tracking glitch)
      -> dead zone (ignore sub-threshold tremor)
      -> sensitivity gain
      -> exponential smoothing (EMA) + jitter damping
      -> projected screen position (pixels)

Pure geometry — no Qt, no camera, no OS calls — so it is fully unit-testable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from .config import PointerSettings, SETTINGS

Mapping = Callable[[tuple[float, float]], tuple[float, float]]


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


@dataclass
class PointerMetrics:
    """Quality metrics reported to the classroom HUD / test lab."""
    latency_ms: float = 0.0
    tremor_px: float = 0.0           # observed high-frequency jitter magnitude
    spikes_rejected: int = 0
    frames_processed: int = 0
    last_update: float = field(default=0.0)


class InteractivePointer:
    def __init__(self, screen_w: int = 1280, screen_h: int = 720,
                 settings: PointerSettings | None = None):
        self.screen_w = max(1, screen_w)
        self.screen_h = max(1, screen_h)
        self.settings = settings or SETTINGS.pointer
        self.enabled = True
        self.visible = True
        self._pos: tuple[float, float] | None = None          # filtered (screen px)
        self._t0: float = 0.0
        self._tremor_buf: list[float] = []
        self._max_tremor_samples = 30
        self.metrics = PointerMetrics()
        self.mapping: Optional[Mapping] = None
        self.on_moved: Optional[Callable[[tuple[float, float]], None]] = None
        self.active_preset: str = "normal"
        self.micro_gesture_mapper = MicroGestureMapper()
        self.rest_zone_enabled: bool = False
        self.in_rest_zone: bool = False
        self.dwell_enabled: bool = False
        self.dwell_delay: float = 0.5
        self.dwell_progress: float = 0.0
        self.on_dwell_click: Optional[Callable[[tuple[float, float]], None]] = None

    @property
    def _diag_px(self) -> float:
        return (self.screen_w ** 2 + self.screen_h ** 2) ** 0.5

    # configuration ---------------------------------------------------------
    def set_screen_size(self, w: int, h: int) -> None:
        self.screen_w = max(1, w)
        self.screen_h = max(1, h)

    def set_calibration(self, mapping: Optional[Mapping]) -> None:
        """Attach a homography callable (norm -> norm) from the calibration
        wizard. Passing None restores the identity/fallback mapping."""
        self.mapping = mapping
        self.settings.calibration = mapping

    def apply_sensitivity(self) -> None:
        self.settings.apply_sensitivity()

    def raw_to_screen(self, raw_norm: tuple[float, float]) -> tuple[float, float]:
        """Map normalized camera point to normalized screen point."""
        x, y = _clip(raw_norm[0]), _clip(raw_norm[1])
        s = self.settings
        if hasattr(self, "micro_gesture_mapper") and self.micro_gesture_mapper.enabled:
            x, y = self.micro_gesture_mapper.map((x, y))
        if self.mapping is not None:
            try:
                x, y = self.mapping((x, y))
                x, y = _clip(x), _clip(y)
            except Exception:
                pass
        elif s.mirror_x:
            x = 1.0 - x
        return (x, y)

    def update(self, raw_norm: tuple[float, float] | None) -> tuple[float, float] | None:
        """Feed one frame of raw fingertip coordinates.

        Returns the filtered position in screen pixels, or None when the
        sample was rejected (spike) or nothing has been seen yet.
        """
        now = time.monotonic()
        if not self.enabled or raw_norm is None:
            return self._pos
        s = self.settings
        self.metrics.frames_processed += 1
        t_norm = self.raw_to_screen(raw_norm)
        target = (t_norm[0] * self.screen_w, t_norm[1] * self.screen_h)

        if self.rest_zone_enabled:
            self.in_rest_zone = (t_norm[1] > 0.85)

        # spike rejection: a single-frame jump beyond the threshold is a
        # tracking glitch and must never yank the projected pointer.
        if self._pos is not None:
            if abs(target[0] - self._pos[0]) + abs(target[1] - self._pos[1]) \
                    > s.max_jump_ratio * self._diag_px:
                self.metrics.spikes_rejected += 1
                return self._pos

        # dead zone: ignore sub-threshold movement (hand tremor).
        delta = 0.0
        if self._pos is not None:
            delta = abs(target[0] - self._pos[0]) + abs(target[1] - self._pos[1])
            if delta < s.dead_zone * self._diag_px:
                self._feed_tremor(delta)
                return self._pos

        # jitter suppression: for tiny motions (in the tremor band between the
        # dead zone and the jitter floor) the smoothing weight is scaled down
        # so the pointer barely tracks high-frequency micro-movement.
        if self._pos is not None and s.jitter_suppression > 0:
            jitter_bool = delta < s.jitter_floor * self._diag_px
        else:
            jitter_bool = False
        alpha = min(1.0, max(0.02, s.smoothing))
        if jitter_bool:
            alpha *= (1.0 - s.jitter_suppression)

        gain = max(0.2, s.speed)
        if self._pos is None:
            self._pos = (target[0], target[1])
        else:
            nx = self._pos[0] + (target[0] - self._pos[0]) * gain * alpha
            ny = self._pos[1] + (target[1] - self._pos[1]) * gain * alpha
            self._pos = (nx, ny)

        if self.dwell_enabled and self._pos is not None:
            if not hasattr(self, "_dwell_start_t") or getattr(self, "_dwell_start_t", None) is None:
                self._dwell_start_t = now
                self._dwell_anchor = self._pos
                self.dwell_progress = 0.0
            else:
                dx = abs(self._pos[0] - self._dwell_anchor[0])
                dy = abs(self._pos[1] - self._dwell_anchor[1])
                if dx < 30 and dy < 30:
                    elapsed = now - self._dwell_start_t
                    if elapsed >= self.dwell_delay:
                        self.dwell_progress = 1.0
                        if self.on_dwell_click:
                            self.on_dwell_click(self._pos)
                        self._dwell_start_t = None
                    else:
                        self.dwell_progress = min(1.0, elapsed / max(0.001, self.dwell_delay))
                else:
                    self._dwell_start_t = now
                    self._dwell_anchor = self._pos
                    self.dwell_progress = 0.0

        self.metrics.last_update = now
        self.metrics.latency_ms = (now - self._t0) * 1000.0 if self._t0 else 0.0
        self._t0 = now
        if self.on_moved is not None:
            try:
                self.on_moved(self._pos)
            except Exception:
                pass
        return self._pos

    # internal --------------------------------------------------------------
    def _feed_tremor(self, delta_px: float) -> None:
        diag = self._diag_px
        if diag <= 0:
            return
        self._tremor_buf.append(delta_px / diag)
        if len(self._tremor_buf) > self._max_tremor_samples:
            self._tremor_buf.pop(0)
        self.metrics.tremor_px = (sum(self._tremor_buf) / len(self._tremor_buf)) * diag

    # public ----------------------------------------------------------------
    def recenter_offset(self) -> None:
        if self._pos is not None:
            cx, cy = self.screen_w / 2.0, self.screen_h / 2.0
            self._offset = (cx - self._pos[0], cy - self._pos[1])

    @property
    def position(self) -> tuple[float, float] | None:
        return self._pos

    def reset(self) -> None:
        self._pos = None
        self._tremor_buf.clear()
        self.metrics.tremor_px = 0.0
        self._t0 = 0.0

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            self.visible = False

    def apply_preset(self, name: str) -> None:
        self.active_preset = name
        if name == "smooth":
            self.settings.smoothing = 0.25
        elif name == "fast":
            self.settings.smoothing = 0.80
        else:
            self.settings.smoothing = 0.50

    def raw_to_screen(self, raw: tuple[float, float]) -> tuple[float, float]:
        if hasattr(self, "micro_gesture_mapper") and self.micro_gesture_mapper.enabled:
            raw = self.micro_gesture_mapper.map(raw)
        return raw


class OneEuroFilter:
    """1€ Filter for low-latency adaptive jitter smoothing."""

    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.05, d_cutoff: float = 1.0) -> None:
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev: tuple[float, float] | None = None
        self.dx_prev: tuple[float, float] = (0.0, 0.0)
        self.t_prev: float | None = None

    def reset(self) -> None:
        self.x_prev = None
        self.dx_prev = (0.0, 0.0)
        self.t_prev = None

    def filter(self, x: tuple[float, float], timestamp: float) -> tuple[float, float]:
        import math
        if self.x_prev is None:
            self.x_prev = x
            self.t_prev = timestamp
            return x

        dt = timestamp - self.t_prev if self.t_prev is not None and timestamp > self.t_prev else 0.033
        self.t_prev = timestamp

        def alpha(cutoff: float) -> float:
            tau = 1.0 / (2.0 * math.pi * cutoff) if cutoff > 0 else 0.0
            return 1.0 / (1.0 + tau / dt) if (tau + dt) > 0 else 1.0

        dx = ((x[0] - self.x_prev[0]) / dt if dt > 0 else 0.0, (x[1] - self.x_prev[1]) / dt if dt > 0 else 0.0)
        a_d = alpha(self.d_cutoff)
        dx_hat = (
            self.dx_prev[0] + a_d * (dx[0] - self.dx_prev[0]),
            self.dx_prev[1] + a_d * (dx[1] - self.dx_prev[1]),
        )
        self.dx_prev = dx_hat

        speed = math.hypot(dx_hat[0], dx_hat[1])
        cutoff = self.min_cutoff + self.beta * speed
        a = alpha(cutoff)

        x_hat = (
            self.x_prev[0] + a * (x[0] - self.x_prev[0]),
            self.x_prev[1] + a * (x[1] - self.x_prev[1]),
        )
        self.x_prev = x_hat
        return x_hat


@dataclass
class MicroGestureMapper:
    """ROI micro-gesture mapper for precise finger tracking."""
    roi_center: tuple[float, float] = (0.5, 0.5)
    roi_size: tuple[float, float] = (0.4, 0.4)
    enabled: bool = False

    def map(self, pt: tuple[float, float]) -> tuple[float, float]:
        if not self.enabled:
            return pt
        cx, cy = self.roi_center
        w, h = self.roi_size
        min_x, max_x = cx - w / 2.0, cx + w / 2.0
        min_y, max_y = cy - h / 2.0, cy + h / 2.0
        norm_x = (pt[0] - min_x) / w if w > 0 else pt[0]
        norm_y = (pt[1] - min_y) / h if h > 0 else pt[1]
        return (_clip(norm_x), _clip(norm_y))