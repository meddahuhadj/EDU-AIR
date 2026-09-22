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


class OneEuroFilter:
    """1€ Filter (Casiez et al., CHI 2012) for adaptive human hand tracking.

    Applies heavy smoothing at low speeds (eradicating hand tremor), while
    dynamically increasing responsiveness at high speeds (zero perceived lag).
    """
    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.05, d_cutoff: float = 1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev: tuple[float, float] | None = None
        self.dx_prev: tuple[float, float] = (0.0, 0.0)
        self.t_prev: float | None = None

    def _alpha(self, cutoff: float, dt: float) -> float:
        import math
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt) if dt > 0 else 1.0

    def filter(self, x: tuple[float, float], t: float) -> tuple[float, float]:
        if self.t_prev is None or self.x_prev is None:
            self.t_prev = t
            self.x_prev = x
            self.dx_prev = (0.0, 0.0)
            return x

        dt = max(0.001, t - self.t_prev)
        self.t_prev = t

        dx = ((x[0] - self.x_prev[0]) / dt, (x[1] - self.x_prev[1]) / dt)
        a_d = self._alpha(self.d_cutoff, dt)
        edx = (
            self.dx_prev[0] + a_d * (dx[0] - self.dx_prev[0]),
            self.dx_prev[1] + a_d * (dx[1] - self.dx_prev[1]),
        )
        self.dx_prev = edx

        speed = (edx[0] ** 2 + edx[1] ** 2) ** 0.5
        cutoff = self.min_cutoff + self.beta * speed
        a = self._alpha(cutoff, dt)

        filtered = (
            self.x_prev[0] + a * (x[0] - self.x_prev[0]),
            self.x_prev[1] + a * (x[1] - self.x_prev[1]),
        )
        self.x_prev = filtered
        return filtered

    def reset(self) -> None:
        self.x_prev = None
        self.dx_prev = (0.0, 0.0)
        self.t_prev = None


class MicroGestureMapper:
    """Micro-gesture ROI Mapper.

    Maps a compact hand movement ROI (e.g. chest-level 0.4 x 0.4 normalized area)
    to full 1.0 x 1.0 screen coordinates. This reduces arm fatigue for teachers,
    allowing full-screen control with small hand gestures.
    """
    def __init__(self, roi_center: tuple[float, float] = (0.5, 0.5),
                 roi_size: tuple[float, float] = (0.4, 0.4), enabled: bool = False):
        self.roi_center = roi_center
        self.roi_size = roi_size
        self.enabled = enabled

    def map(self, norm_pt: tuple[float, float]) -> tuple[float, float]:
        if not self.enabled:
            return norm_pt
        cx, cy = self.roi_center
        sw, sh = max(0.05, self.roi_size[0]), max(0.05, self.roi_size[1])
        min_x, max_x = cx - sw / 2.0, cx + sw / 2.0
        min_y, max_y = cy - sh / 2.0, cy + sh / 2.0

        nx = (norm_pt[0] - min_x) / sw
        ny = (norm_pt[1] - min_y) / sh
        return (_clip(nx), _clip(ny))


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
        self._one_euro = OneEuroFilter(min_cutoff=1.2, beta=0.04)
        self.micro_gesture_mapper = MicroGestureMapper()

        # Dwell click & Rest zone ergonomic additions
        self.dwell_enabled: bool = True
        self.dwell_delay: float = 0.55          # seconds needed to trigger dwell click
        self.dwell_radius_px: float = 22.0      # max displacement to consider pointer stationary
        self.dwell_progress: float = 0.0        # 0.0 to 1.0 (used for UI progress ring)
        self._dwell_anchor: tuple[float, float] | None = None
        self._dwell_start_t: float = 0.0
        self._dwell_fired: bool = False
        self.on_dwell_click: Optional[Callable[[tuple[float, float]], None]] = None

        self.in_rest_zone: bool = False
        self.rest_zone_enabled: bool = False
        self.rest_zone_threshold_y: float = 0.88 # bottom 12% of camera frame triggers rest pause
        self._offset_x: float = 0.0
        self._offset_y: float = 0.0
        self.active_preset: str = "normal"

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

    # core pipeline ---------------------------------------------------------
    def raw_to_screen(self, raw_norm: tuple[float, float]) -> tuple[float, float]:
        """Map normalized camera point to normalized screen point."""
        x, y = _clip(raw_norm[0]), _clip(raw_norm[1])
        if self.micro_gesture_mapper and self.micro_gesture_mapper.enabled:
            x, y = self.micro_gesture_mapper.map((x, y))
        s = self.settings
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
            self._reset_dwell()
            return self._pos

        # Rest zone check: if hand lowered to bottom border of camera frame, pause interaction
        if self.rest_zone_enabled and raw_norm[1] >= self.rest_zone_threshold_y:
            self.in_rest_zone = True
            self._reset_dwell()
            return self._pos
        else:
            self.in_rest_zone = False

        s = self.settings
        self.metrics.frames_processed += 1
        t_norm = self.raw_to_screen(raw_norm)
        target = (
            _clip((t_norm[0] * self.screen_w) + self._offset_x, 0, self.screen_w),
            _clip((t_norm[1] * self.screen_h) + self._offset_y, 0, self.screen_h)
        )

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
                # Still check dwell even when in dead zone (user is trying to stay still to click!)
                self._update_dwell(now)
                return self._pos

        # Adaptive 1€ Filter + EMA combination
        target = self._one_euro.filter(target, now)

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

        self.metrics.last_update = now
        self.metrics.latency_ms = (now - self._t0) * 1000.0 if self._t0 else 0.0
        self._t0 = now

        # Dwell clicking progress check
        self._update_dwell(now)

        if self.on_moved is not None:
            try:
                self.on_moved(self._pos)
            except Exception:
                pass
        return self._pos

    def _reset_dwell(self) -> None:
        self._dwell_anchor = None
        self._dwell_start_t = 0.0
        self._dwell_fired = False
        self.dwell_progress = 0.0

    def _update_dwell(self, now: float) -> None:
        if not self.dwell_enabled or self._pos is None:
            self._reset_dwell()
            return

        if self._dwell_anchor is None:
            self._dwell_anchor = self._pos
            self._dwell_start_t = now
            self._dwell_fired = False
            self.dwell_progress = 0.0
            return

        dist = ((self._pos[0] - self._dwell_anchor[0]) ** 2 +
                (self._pos[1] - self._dwell_anchor[1]) ** 2) ** 0.5

        if dist <= self.dwell_radius_px:
            elapsed = now - self._dwell_start_t
            self.dwell_progress = min(1.0, elapsed / max(0.01, self.dwell_delay))
            if self.dwell_progress >= 1.0 and not self._dwell_fired:
                self._dwell_fired = True
                if self.on_dwell_click is not None:
                    try:
                        self.on_dwell_click(self._pos)
                    except Exception:
                        pass
        else:
            # User moved beyond dwell radius, reset anchor to new position
            self._dwell_anchor = self._pos
            self._dwell_start_t = now
            self._dwell_fired = False
            self.dwell_progress = 0.0

    def apply_preset(self, preset: str) -> None:
        """Apply a sensitivity / smoothing profile preset."""
        preset = preset.lower()
        if preset == "smooth":
            self._one_euro.min_cutoff = 0.8
            self._one_euro.beta = 0.01
            self.settings.smoothing = 0.25
            self.settings.speed = 0.85
            self.active_preset = "smooth"
        elif preset == "fast":
            self._one_euro.min_cutoff = 2.0
            self._one_euro.beta = 0.08
            self.settings.smoothing = 0.80
            self.settings.speed = 1.30
            self.active_preset = "fast"
        else:  # normal
            self._one_euro.min_cutoff = 1.2
            self._one_euro.beta = 0.04
            self.settings.smoothing = 0.50
            self.settings.speed = 1.00
            self.active_preset = "normal"

    def recenter_offset(self, target_pos: tuple[float, float] | None = None) -> None:
        """Quick 1-point alignment: centers pointer to screen center or specified point."""
        if self._pos is None:
            return
        target = target_pos or (self.screen_w / 2.0, self.screen_h / 2.0)
        self._offset_x += (target[0] - self._pos[0])
        self._offset_y += (target[1] - self._pos[1])

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