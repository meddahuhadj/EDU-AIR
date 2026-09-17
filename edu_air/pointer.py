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
            return self._pos
        s = self.settings
        self.metrics.frames_processed += 1
        t_norm = self.raw_to_screen(raw_norm)
        target = (t_norm[0] * self.screen_w, t_norm[1] * self.screen_h)

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