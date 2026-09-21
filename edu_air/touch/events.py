"""Normalized touch events emitted by :class:`~edu_air.touch.detector.SurfaceTouchDetector`.

Every backend (shadow-gap, IR pen, color marker) ultimately produces this one
shape, so the ink pipeline and the safety gate never need to know which
backend is active.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class TouchState(str, Enum):
    DOWN = "down"   # hover -> contact transition (ink should start)
    MOVE = "move"   # sustained contact, position updated (ink should follow)
    UP = "up"       # contact -> hover/lost transition (ink should lift)


@dataclass(frozen=True)
class TouchEvent:
    """x, y are projector-normalized [0..1], already mapped through the
    existing calibration homography — consumers never see camera space."""
    x: float
    y: float
    state: TouchState
    confidence: float = 1.0
    tool_id: str = "finger"       # "finger" | "ir_pen" | "marker:<color>"
    track_id: int = 0             # stable id across one DOWN..UP stroke
    gap: float = 0.0              # raw contact metric (0=touch..1=hover), for debug/tuning
    ts: float = field(default_factory=time.monotonic)
