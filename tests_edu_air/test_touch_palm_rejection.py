"""PalmRejectionFilter: mono-point selection -- only a pointing-pose hand
(POINT: index extended, everything else curled) is ever handed to a touch
backend as a writing candidate. A flat palm or a fist resting on the wall
must never be picked, even when it is the only hand in frame."""

from __future__ import annotations

import numpy as np
import pytest

from hadj_no_touch.vision.hand_tracking import (
    HandData, LM_WRIST, LM_THUMB_TIP, LM_INDEX_PIP, LM_INDEX_TIP,
    LM_MIDDLE_MCP, LM_MIDDLE_PIP, LM_MIDDLE_TIP, LM_RING_PIP, LM_RING_TIP,
    LM_PINKY_PIP, LM_PINKY_TIP,
)

from edu_air.touch.palm_rejection import PalmRejectionFilter


def make_hand(index=False, middle=False, ring=False, pinky=False,
             confidence=0.9, handedness="Right", tracked=True) -> HandData:
    """A synthetic 21-landmark hand where each finger is either "extended"
    (tip far from the wrist relative to its PIP joint) or "curled" (tip
    folded back near the wrist) -- exactly the ratio
    ``GestureClassifier.fingers_extended`` tests, so real classification
    logic decides the pose instead of a stub."""
    norm = np.zeros((21, 2), dtype=np.float32)
    norm[LM_WRIST] = (0.5, 0.9)
    norm[LM_MIDDLE_MCP] = (0.5, 0.75)     # scale = |wrist - middle_mcp| = 0.15
    norm[LM_THUMB_TIP] = (0.4, 0.85)      # curled thumb, irrelevant to POINT/OPEN_PALM

    def place(pip_idx, tip_idx, x, extended):
        norm[pip_idx] = (x, 0.75)
        norm[tip_idx] = (x, 0.55) if extended else (x, 0.83)

    place(LM_INDEX_PIP, LM_INDEX_TIP, 0.45, index)
    place(LM_MIDDLE_PIP, LM_MIDDLE_TIP, 0.50, middle)
    place(LM_RING_PIP, LM_RING_TIP, 0.55, ring)
    place(LM_PINKY_PIP, LM_PINKY_TIP, 0.60, pinky)

    px = norm * 100.0
    return HandData(landmarks_norm=norm, landmarks_px=px, handedness=handedness,
                    confidence=confidence, tracked=tracked)


def test_pointing_hand_is_selected():
    f = PalmRejectionFilter()
    hand = make_hand(index=True)
    picked = f.select_candidate([hand])
    assert picked is not None
    assert picked[0] is hand


def test_open_palm_is_rejected():
    f = PalmRejectionFilter()
    hand = make_hand(index=True, middle=True, ring=True, pinky=True)
    assert f.select_candidate([hand]) is None


def test_fist_is_rejected():
    f = PalmRejectionFilter()
    hand = make_hand()  # everything curled
    assert f.select_candidate([hand]) is None


def test_untracked_hand_is_ignored():
    f = PalmRejectionFilter()
    hand = make_hand(index=True, tracked=False)
    assert f.select_candidate([hand]) is None


def test_no_hands_returns_none():
    f = PalmRejectionFilter()
    assert f.select_candidate([]) is None


def test_picks_most_confident_pointing_hand_among_several():
    f = PalmRejectionFilter()
    weak = make_hand(index=True, confidence=0.3)
    strong = make_hand(index=True, confidence=0.95)
    palm = make_hand(index=True, middle=True, ring=True, pinky=True, confidence=0.99)
    picked = f.select_candidate([weak, palm, strong])
    assert picked is not None
    assert picked[0] is strong


def test_require_pose_false_lets_a_flat_palm_through():
    """The "rejet de paume" UI toggle maps to this flag -- turning it off
    must actually disable the pose gate, not just look disabled."""
    f = PalmRejectionFilter()
    palm = make_hand(index=True, middle=True, ring=True, pinky=True)
    assert f.select_candidate([palm], require_pose=True) is None
    picked = f.select_candidate([palm], require_pose=False)
    assert picked is not None
    assert picked[0] is palm


def test_require_pose_false_still_ranks_by_confidence():
    f = PalmRejectionFilter()
    # Same pose (OPEN_PALM) on both hands so only hand.confidence differs --
    # isolates the ranking from pose-classification confidence quirks.
    weak_palm = make_hand(index=True, middle=True, ring=True, pinky=True, confidence=0.2)
    strong_palm = make_hand(index=True, middle=True, ring=True, pinky=True, confidence=0.95)
    picked = f.select_candidate([weak_palm, strong_palm], require_pose=False)
    assert picked is not None
    assert picked[0] is strong_palm
