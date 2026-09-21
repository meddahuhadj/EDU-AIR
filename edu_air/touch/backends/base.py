"""Common interface every touch backend implements.

A backend's only job is per-frame geometry: find the writing point and
report *how close* it is to the surface. It never decides DOWN/MOVE/UP --
that debouncing lives once, centrally, in
:class:`~edu_air.touch.state_machine.ContactStateMachine`, so every backend
gets the same anti-flicker behaviour for free.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TouchSample:
    """One raw candidate for the current frame, in camera-normalized space,
    before hysteresis and before the calibration mapping is applied."""
    x_cam_norm: float
    y_cam_norm: float
    contact_metric: float          # 0.0 = touching .. 1.0 = clearly hovering
    confidence: float               # 0..1, how much to trust this sample
    tool_id: str = "finger"
    debug: dict = field(default_factory=dict)   # tip_px/shadow_px/gap_px/... for the debug overlay


class SurfaceTouchBackend(ABC):
    """Base class for ShadowGapFingerBackend / IRPenBackend / ColorMarkerBackend."""

    name: str = "base"

    @abstractmethod
    def configure(self, settings) -> None:
        """Attach the live :class:`edu_air.config.TouchSettings` block."""

    @abstractmethod
    def process_frame(self, bgr_frame, hands: list, frame_w: int, frame_h: int,
                       now: float) -> Optional[TouchSample]:
        """Return a single candidate sample for this frame, or None when no
        writing point is present (nothing tracked / rejected as palm)."""

    def calibrate_plane(self, samples: list[TouchSample]) -> dict:
        """Learn a per-zone contact baseline from the "touch plane" wizard
        step (real contact at the 4 projected corners). Returns a plain,
        JSON-serializable dict persisted into ``SETTINGS.calibration``.
        Backends that need no plane baseline (e.g. IR pen) may no-op."""
        return {}

    def load_plane_calibration(self, data: dict) -> None:
        """Restore a previously learned baseline (mirror of calibrate_plane)."""
        return None

    def reset(self) -> None:
        """Drop any per-stroke/tracking state (called on mode toggle)."""
        return None
