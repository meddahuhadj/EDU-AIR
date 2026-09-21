"""Registry of interchangeable :class:`SurfaceTouchBackend` implementations."""

from __future__ import annotations

from .base import SurfaceTouchBackend, TouchSample
from .color_marker import ColorMarkerBackend
from .ir_pen import IRPenBackend
from .shadow_gap import ShadowGapFingerBackend

BACKEND_CLASSES: dict[str, type[SurfaceTouchBackend]] = {
    ShadowGapFingerBackend.name: ShadowGapFingerBackend,
    IRPenBackend.name: IRPenBackend,
    ColorMarkerBackend.name: ColorMarkerBackend,
}

DEFAULT_BACKEND = ShadowGapFingerBackend.name


def build_backend(name: str | None) -> SurfaceTouchBackend:
    cls = BACKEND_CLASSES.get(name or DEFAULT_BACKEND, ShadowGapFingerBackend)
    return cls()


__all__ = [
    "SurfaceTouchBackend", "TouchSample",
    "ShadowGapFingerBackend", "IRPenBackend", "ColorMarkerBackend",
    "BACKEND_CLASSES", "DEFAULT_BACKEND", "build_backend",
]
