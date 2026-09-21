"""ColorMarkerBackend -- plain colored-tip marker (simple hardware option).

**Experimental**: functional but not the tuned default. Detects the
marker's tip as an HSV color blob (no MediaPipe hand tracking involved),
then estimates contact the same way the default backend does for a bare
finger: by looking for the blob's shadow and measuring how far apart they
are (see :mod:`edu_air.touch.shadow_search`). No hand-size reference is
available for a marker, so the blob's own on-screen radius is used to scale
the search corridor and the far-gap normalization instead.
"""

from __future__ import annotations

from typing import Optional

from .. import plane_calibration as plane
from ..shadow_search import find_shadow
from .base import SurfaceTouchBackend, TouchSample

DEFAULT_SHADOW_DIR = (0.0, 1.0)


class ColorMarkerBackend(SurfaceTouchBackend):
    name = "color_marker"

    def __init__(self):
        self.settings = None
        self._cv2 = None
        self._np = None
        self._plane: dict = {}

    def configure(self, settings) -> None:
        self.settings = settings

    def load_plane_calibration(self, data: dict) -> None:
        self._plane = data or {}

    def reset(self) -> None:
        pass

    def _deps(self):
        if self._cv2 is None:
            import cv2
            import numpy as np
            self._cv2, self._np = cv2, np
        return self._cv2, self._np

    def process_frame(self, bgr_frame, hands: list, frame_w: int, frame_h: int,
                       now: float) -> Optional[TouchSample]:
        if bgr_frame is None or self.settings is None:
            return None
        cv2, np = self._deps()
        try:
            hsv = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        except Exception:
            return None

        lo = np.array(self.settings.color_marker_hsv_low, dtype=np.uint8)
        hi = np.array(self.settings.color_marker_hsv_high, dtype=np.uint8)
        mask = cv2.inRange(hsv, lo, hi)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        best = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(best)
        if area < 4.0:
            return None
        m = cv2.moments(best)
        if m["m00"] <= 0:
            return None
        cx = m["m10"] / m["m00"]
        cy = m["m01"] / m["m00"]
        blob_radius_px = max(4.0, (area / np.pi) ** 0.5)

        x_norm = float(np.clip(cx / max(1, frame_w), 0.0, 1.0))
        y_norm = float(np.clip(cy / max(1, frame_h), 0.0, 1.0))
        z = plane.lookup_zone(self._plane, x_norm, y_norm)
        direction = tuple(z["dir"]) if z else DEFAULT_SHADOW_DIR
        gap_bias = float(z.get("gap_bias", 0.0)) if z else 0.0

        scale_px = blob_radius_px * 3.0
        search_len = int(np.clip(scale_px * self.settings.shadow_search_range, 6, 120))
        gap_px, shadow_px, contrast = find_shadow(
            gray, (cx, cy), direction, search_len, scale_px, self.settings.min_contrast, np)

        debug = {"tip_px": (float(cx), float(cy)), "blob_radius_px": blob_radius_px}
        if shadow_px is None:
            debug["shadow_px"] = None
            debug["gap_px"] = None
            return TouchSample(x_cam_norm=x_norm, y_cam_norm=y_norm, contact_metric=1.0,
                               confidence=0.3, tool_id="marker", debug=debug)

        adjusted_gap = max(0.0, gap_px - gap_bias)
        far_px = max(1.0, scale_px * self.settings.gap_far_ratio)
        contact_metric = float(np.clip(adjusted_gap / far_px, 0.0, 1.0))
        contrast_score = float(np.clip(contrast / max(self.settings.min_contrast, 1.0), 0.0, 1.0))
        debug["shadow_px"] = shadow_px
        debug["gap_px"] = gap_px
        return TouchSample(x_cam_norm=x_norm, y_cam_norm=y_norm, contact_metric=contact_metric,
                           confidence=float(np.clip(0.35 + 0.65 * contrast_score, 0.0, 1.0)),
                           tool_id="marker", debug=debug)

    def calibrate_plane(self, samples: list[TouchSample]) -> dict:
        result = plane.learn_zone_baselines(samples)
        self._plane = result
        return result
