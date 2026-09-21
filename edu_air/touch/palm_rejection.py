"""Mono-point palm/wrist rejection shared by the hand-based touch backends.

v1 keeps exactly one candidate writing point at a time: the most confident
hand whose pose looks like a pointing finger (MediaPipe classifies it as
POINT -- one extended index finger, everything else curled). A flat palm or
a rested wrist/fist is never classified as POINT, so it is dropped here
before it ever reaches the shadow-gap/IR/color measurement -- it never gets
a chance to draw.
"""

from __future__ import annotations

from typing import Optional

from hadj_no_touch.gestures.gesture_classifier import GestureClassifier, GestureResult, POINT
from hadj_no_touch.vision.hand_tracking import HandData


class PalmRejectionFilter:
    def __init__(self, classifier: Optional[GestureClassifier] = None,
                 accepted_poses: tuple[str, ...] = (POINT,)):
        self.classifier = classifier or GestureClassifier()
        self.accepted_poses = accepted_poses

    def select_candidate(self, hands: list[HandData],
                         require_pose: bool = True) -> Optional[tuple[HandData, GestureResult]]:
        """Pick the single best writing candidate among tracked hands.

        With ``require_pose`` (the "rejet de paume" setting) on, only a
        pointing pose qualifies and a palm/fist is dropped entirely. With it
        off, any tracked hand is accepted -- classification still runs so
        callers get a confidence figure, it just no longer gates selection."""
        best: Optional[tuple[HandData, GestureResult, float]] = None
        for hand in hands:
            if not hand.tracked:
                continue
            result = self.classifier.classify(hand)
            if require_pose and (not result.recognized or result.name not in self.accepted_poses):
                continue
            score = result.confidence * max(hand.confidence, 0.05)
            if best is None or score > best[2]:
                best = (hand, result, score)
        return (best[0], best[1]) if best is not None else None
