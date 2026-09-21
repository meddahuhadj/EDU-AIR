"""ShadowGapFingerBackend -- the default, webcam-only touch backend.

A single 2D camera cannot measure depth directly, but the projector is
itself the room's dominant light source, sitting a little off-axis from the
camera. A fingertip hovering above the wall therefore casts a visible
shadow that is offset from the fingertip in the camera image; as the finger
closes in on the wall that offset (the "shadow gap") shrinks to ~0 px right
at contact -- the same triangulation cue structured-light rigs use, just
read passively off the projector's own image instead of a dedicated pattern.

Per frame this backend:
  1. asks :class:`~edu_air.touch.palm_rejection.PalmRejectionFilter` for the
     single best pointing-pose hand (rejects flat palms/fists/rested wrists);
  2. walks a short search corridor from the index fingertip, in the
     direction learned for that screen zone during the "plan tactile" step
     (or a straight-down default before calibration), looking for the
     darkest pixel;
  3. compares that darkest pixel against the *local* background brightness
     sampled just off to the side of the corridor -- an adaptive contrast
     test, not a fixed brightness constant, so ambient light and projector
     glare do not need their own tuning;
  4. turns the pixel gap into a scale-invariant ``contact_metric`` by
     dividing by the hand's own on-screen size (distance webcam-to-wall
     changes that size, not the physical relationship being measured).

The result is one ``TouchSample`` per frame; DOWN/MOVE/UP debouncing is not
this backend's job -- see ``ContactStateMachine``.
"""

from __future__ import annotations

from typing import Optional

from hadj_no_touch.vision.hand_tracking import LM_INDEX_TIP, LM_MIDDLE_MCP, LM_WRIST

from .. import plane_calibration as plane
from ..palm_rejection import PalmRejectionFilter
from ..shadow_search import find_shadow
from .base import SurfaceTouchBackend, TouchSample

DEFAULT_SHADOW_DIR = (0.0, 1.0)  # "below the fingertip", before any calibration


class ShadowGapFingerBackend(SurfaceTouchBackend):
    name = "shadow_gap"

    def __init__(self):
        self.settings = None
        self._palm_filter = PalmRejectionFilter()
        self._cv2 = None
        self._np = None
        self._plane: dict = {}   # learned per-zone {"grid": n, "zones": {...}}, see plane_calibration.py

    def configure(self, settings) -> None:
        self.settings = settings

    def load_plane_calibration(self, data: dict) -> None:
        self._plane = data or {}

    def reset(self) -> None:
        pass

    # ---- deps ---------------------------------------------------------------
    def _deps(self):
        if self._cv2 is None:
            import cv2
            import numpy as np
            self._cv2, self._np = cv2, np
        return self._cv2, self._np

    # ---- per-frame sample -----------------------------------------------------
    def process_frame(self, bgr_frame, hands: list, frame_w: int, frame_h: int,
                       now: float) -> Optional[TouchSample]:
        if bgr_frame is None or not hands or self.settings is None:
            return None
        picked = self._palm_filter.select_candidate(
            hands, require_pose=self.settings.palm_rejection)
        if picked is None:
            return None
        hand, pose = picked
        cv2, np = self._deps()

        tip = hand.landmarks_px[LM_INDEX_TIP]
        wrist = hand.landmarks_px[LM_WRIST]
        mcp = hand.landmarks_px[LM_MIDDLE_MCP]
        hand_scale_px = max(float(np.linalg.norm(mcp - wrist)), 4.0)

        try:
            gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        except Exception:
            return None

        x_norm = float(np.clip(tip[0] / max(1, frame_w), 0.0, 1.0))
        y_norm = float(np.clip(tip[1] / max(1, frame_h), 0.0, 1.0))
        direction, gap_bias = self._zone_baseline(x_norm, y_norm)

        search_len = int(np.clip(hand_scale_px * self.settings.shadow_search_range, 6, 120))
        gap_px, shadow_px, contrast = find_shadow(
            gray, tip, direction, search_len, hand_scale_px, self.settings.min_contrast, np)

        debug = {"tip_px": (float(tip[0]), float(tip[1])), "hand_scale_px": hand_scale_px}
        if shadow_px is None:
            debug["shadow_px"] = None
            debug["gap_px"] = None
            return TouchSample(x_cam_norm=x_norm, y_cam_norm=y_norm, contact_metric=1.0,
                               confidence=0.25 * pose.confidence, tool_id="finger", debug=debug)

        adjusted_gap = max(0.0, gap_px - gap_bias)
        far_px = max(1.0, hand_scale_px * self.settings.gap_far_ratio)
        contact_metric = float(np.clip(adjusted_gap / far_px, 0.0, 1.0))
        contrast_score = float(np.clip(contrast / max(self.settings.min_contrast, 1.0), 0.0, 1.0))
        confidence = float(np.clip(0.35 + 0.65 * contrast_score, 0.0, 1.0)) * pose.confidence
        debug["shadow_px"] = shadow_px
        debug["gap_px"] = gap_px
        debug["contrast"] = contrast
        return TouchSample(x_cam_norm=x_norm, y_cam_norm=y_norm, contact_metric=contact_metric,
                           confidence=confidence, tool_id="finger", debug=debug)

    def _zone_baseline(self, x_norm: float, y_norm: float) -> tuple[tuple[float, float], float]:
        z = plane.lookup_zone(self._plane, x_norm, y_norm)
        if z is None:
            return DEFAULT_SHADOW_DIR, 0.0
        d = z.get("dir", DEFAULT_SHADOW_DIR)
        return (float(d[0]), float(d[1])), float(z.get("gap_bias", 0.0))

    # ---- calibration ----------------------------------------------------------
    def calibrate_plane(self, samples: list[TouchSample]) -> dict:
        result = plane.learn_zone_baselines(samples)
        self._plane = result
        return result
