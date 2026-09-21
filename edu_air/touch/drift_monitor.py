"""HomographyDriftMonitor -- flags when the calibrated mapping likely no
longer fits the physical setup, instead of silently going on writing at
what may be the wrong spot.

A single webcam has no independent ground truth to re-check calibration
against during normal use. The one concrete, honest signal available from
touch data alone is the homography's own output range: a mapping that
still fits the room places genuine touches inside the projected rectangle
(camera-normalized [0..1], see ``ProjectorCalibration._build_mapping``'s
screen corners). If the camera, projector or wall has moved since
calibration, touches increasingly land *outside* that range before
clamping. This tracks that overflow over a rolling window and only raises
drift once it is sustained, not on one stray reading (a single sloppy
touch near the very edge of the board is normal and must not trigger it).
"""

from __future__ import annotations

from collections import deque


class HomographyDriftMonitor:
    def __init__(self, window: int = 25, out_of_bounds_ratio: float = 0.35,
                 overflow_margin: float = 0.03, min_samples: int = 10):
        self.window = window
        self.out_of_bounds_ratio = out_of_bounds_ratio
        self.overflow_margin = overflow_margin
        self.min_samples = min_samples
        self._flags: deque[bool] = deque(maxlen=window)
        self.drift_suspected = False

    def reset(self) -> None:
        self._flags.clear()
        self.drift_suspected = False

    def observe(self, raw_x: float, raw_y: float) -> bool:
        """Feed one mapped touch position *before* it is clamped to
        [0, 1]. Returns the (possibly updated) ``drift_suspected`` flag."""
        overflow = max(0.0 - raw_x, raw_x - 1.0, 0.0 - raw_y, raw_y - 1.0, 0.0)
        self._flags.append(overflow > self.overflow_margin)
        if len(self._flags) >= self.min_samples:
            frac = sum(self._flags) / len(self._flags)
            self.drift_suspected = frac >= self.out_of_bounds_ratio
        return self.drift_suspected
