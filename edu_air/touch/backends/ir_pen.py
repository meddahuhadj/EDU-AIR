"""IRPenBackend -- IR stylus with a tip switch (robustness option).

**Experimental**: functional but not the tuned default. Unlike the
shadow-gap backend this one does not need MediaPipe hand landmarks at all --
an IR stylus only lights its tip while it is physically pressed against the
surface, so the camera sees a small bright spot if and only if the pen is
in contact. That makes "presence = contact" instead of a continuous gap
measurement, which is why this backend is the most reliable option for
sustained fine writing once the hardware is available (a webcam with its IR
filter removed, or a cheap dedicated IR camera).

Detection is contrast-based, not a fixed brightness cutoff: the brightest
point in the frame is compared against that same frame's *own* background
median (the same "adaptive contrast, no hard-coded constant" principle the
shadow-gap backend uses for ambient light and projector glare). A bright
room raises both the pen's peak and the background together, so the
contrast margin -- not the absolute brightness -- is what has to hold.
``ir_threshold`` remains as a secondary, low floor: it only guards against
triggering on pure sensor noise in a fully dark frame, it is never the
primary decision by itself.

No plane calibration is required for the contact decision itself (presence
already means contact); ``calibrate_plane`` is intentionally a no-op here.
"""

from __future__ import annotations

from typing import Optional

from .base import SurfaceTouchBackend, TouchSample


class IRPenBackend(SurfaceTouchBackend):
    name = "ir_pen"

    def __init__(self):
        self.settings = None
        self._cv2 = None
        self._np = None

    def configure(self, settings) -> None:
        self.settings = settings

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
            gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        except Exception:
            return None

        # A slight blur turns a single hot pixel (sensor noise) into a soft
        # peak and merges the true LED spot into one coherent blob, so the
        # brightest-point search below does not chase noise frame to frame.
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        _, max_val, _, max_loc = cv2.minMaxLoc(blurred)
        background = float(np.median(gray))
        contrast = max_val - background
        if contrast < self.settings.min_contrast or max_val < self.settings.ir_threshold * 0.5:
            return None

        # Threshold halfway between the background and the peak to trace
        # the blob's actual extent around that peak (adaptive to this
        # frame's own brightness range, not a fixed cutoff).
        local_cut = background + contrast * 0.5
        _, mask = cv2.threshold(gray, local_cut, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = max(1.0, (frame_w * frame_h) * 0.00002)
        max_area = (frame_w * frame_h) * 0.01
        blob = None
        for c in contours:
            if cv2.pointPolygonTest(c, max_loc, False) < 0:
                continue
            area = cv2.contourArea(c)
            if min_area <= area <= max_area:
                blob = (c, area)
                break
        if blob is None:
            # No coherent small blob around the peak -- likely a large
            # glare/reflection region rather than a pinpoint LED.
            return None
        contour, area = blob

        m = cv2.moments(contour)
        cx, cy = (float(max_loc[0]), float(max_loc[1]))
        if m["m00"] > 0:
            cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]

        size_score = float(np.clip(area / (min_area * 4.0), 0.0, 1.0))
        contrast_score = float(np.clip(contrast / max(self.settings.min_contrast, 1.0), 0.0, 1.0))
        confidence = 0.5 * size_score + 0.5 * contrast_score

        return TouchSample(
            x_cam_norm=float(np.clip(cx / max(1, frame_w), 0.0, 1.0)),
            y_cam_norm=float(np.clip(cy / max(1, frame_h), 0.0, 1.0)),
            contact_metric=0.05,   # lit tip == pressed == touching, by construction
            confidence=confidence,
            tool_id="ir_pen",
            debug={"blob_px": (cx, cy), "area": float(area),
                  "brightness": float(max_val), "contrast": contrast},
        )
