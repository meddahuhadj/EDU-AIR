"""Palm eraser: wipe a wide swath of ink by passing an open palm over the
wall, like erasing a real whiteboard -- distinct from, and independent of,
the fingertip-based touch/draw pipeline, which deliberately *rejects* an
open palm as a drawing candidate (see ``palm_rejection.py``'s module
docstring: "A flat palm ... is never classified as POINT ... it never
gets a chance to draw"). This module is the other half of that decision:
the palm doesn't draw, but it can still act, on purpose, as an eraser.

Reuses the exact shadow-gap contact technique as
:class:`~edu_air.touch.backends.shadow_gap.ShadowGapFingerBackend`
(``shadow_search.find_shadow``), measured at the palm's own centroid
landmark instead of the index fingertip.

Anti-false-trigger ("appui long vs passage" -- a resting hand must not
erase, only a deliberate wipe should): contact alone is never enough.
``PalmEraseDetector`` also tracks the path length travelled while the
palm stays in contact, and only starts reporting erase positions once
that path crosses ``palm_erase_min_wipe_distance`` -- a real whiteboard
eraser, too, only cleans what it actually wipes across.
"""

from __future__ import annotations

from typing import Optional

from hadj_no_touch.gestures.gesture_classifier import GestureClassifier, OPEN_PALM
from hadj_no_touch.vision.hand_tracking import LM_MIDDLE_MCP, LM_WRIST

from .shadow_search import find_shadow

DEFAULT_SEARCH_DIR = (0.0, 1.0)


class PalmEraseDetector:
    def __init__(self, settings, classifier: Optional[GestureClassifier] = None):
        self.settings = settings
        self.classifier = classifier or GestureClassifier()
        self._wiping = False
        self._path_len = 0.0
        self._last_pos_norm: Optional[tuple[float, float]] = None
        self._cv2 = None
        self._np = None

    def _deps(self):
        if self._cv2 is None:
            import cv2
            import numpy as np
            self._cv2, self._np = cv2, np
        return self._cv2, self._np

    def reset(self) -> None:
        self._wiping = False
        self._path_len = 0.0
        self._last_pos_norm = None

    def _select_palm(self, hands: list):
        best = None
        for hand in hands:
            if not hand.tracked:
                continue
            result = self.classifier.classify(hand)
            if not result.recognized or result.name != OPEN_PALM:
                continue
            if best is None or result.confidence > best[1]:
                best = (hand, result.confidence)
        return best[0] if best is not None else None

    def update(self, bgr_frame, hands: list, frame_w: int, frame_h: int
              ) -> Optional[tuple[float, float]]:
        """Camera-normalized position to erase at *this frame* -- only
        while an open palm is both in contact with the wall and mid-wipe
        (has already travelled ``palm_erase_min_wipe_distance`` since
        contact began). Returns None otherwise, including every frame
        before that distance is reached (a palm that lands and stays put
        never starts a wipe)."""
        if not self.settings.palm_erase_enabled or bgr_frame is None or not hands:
            self.reset()
            return None

        hand = self._select_palm(hands)
        if hand is None:
            self.reset()
            return None

        cv2, np = self._deps()
        wrist = hand.landmarks_px[LM_WRIST]
        mcp = hand.landmarks_px[LM_MIDDLE_MCP]
        palm_px = ((wrist[0] + mcp[0]) / 2.0, (wrist[1] + mcp[1]) / 2.0)
        hand_scale_px = max(float(np.linalg.norm(mcp - wrist)), 4.0)

        try:
            gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        except Exception:
            self.reset()
            return None

        search_len = int(np.clip(hand_scale_px * self.settings.shadow_search_range, 6, 120))
        gap_px, shadow_px, _contrast = find_shadow(
            gray, palm_px, DEFAULT_SEARCH_DIR, search_len, hand_scale_px,
            self.settings.min_contrast, np)
        if shadow_px is None:
            self.reset()
            return None

        far_px = max(1.0, hand_scale_px * self.settings.gap_far_ratio)
        contact_metric = float(np.clip(gap_px / far_px, 0.0, 1.0))
        if contact_metric > self.settings.palm_erase_contact_threshold:
            self.reset()
            return None

        x_norm = float(np.clip(palm_px[0] / max(1, frame_w), 0.0, 1.0))
        y_norm = float(np.clip(palm_px[1] / max(1, frame_h), 0.0, 1.0))
        pos_norm = (x_norm, y_norm)

        if self._last_pos_norm is not None:
            dx = pos_norm[0] - self._last_pos_norm[0]
            dy = pos_norm[1] - self._last_pos_norm[1]
            self._path_len += (dx * dx + dy * dy) ** 0.5
        self._last_pos_norm = pos_norm

        if not self._wiping and self._path_len >= self.settings.palm_erase_min_wipe_distance:
            self._wiping = True

        return pos_norm if self._wiping else None
