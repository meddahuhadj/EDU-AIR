"""Wall/touch mode: contact-only writing on a projected surface.

Public surface:
  * :class:`TouchEvent` / :class:`TouchState` -- the normalized event the
    rest of EDU-AIR consumes (``edu_air.touch.events``);
  * :class:`SurfaceTouchDetector` -- per-frame entry point, owns the
    calibration mapping, hysteresis and stroke smoothing
    (``edu_air.touch.detector``);
  * :func:`build_backend` -- instantiate the configured backend
    (shadow_gap / ir_pen / color_marker) by name
    (``edu_air.touch.backends``).

See ``edu_air.classroom.ClassroomSession.handle_touch_event`` for how a
``TouchEvent`` reaches the existing ink pipeline, and
``edu_air.calibration.STAGE_TOUCH_PLANE`` for the additional calibration
step that learns each backend's contact baseline.
"""

from __future__ import annotations

from .backends import BACKEND_CLASSES, DEFAULT_BACKEND, build_backend
from .detector import SurfaceTouchDetector
from .events import TouchEvent, TouchState

__all__ = [
    "TouchEvent", "TouchState", "SurfaceTouchDetector",
    "build_backend", "BACKEND_CLASSES", "DEFAULT_BACKEND",
]
