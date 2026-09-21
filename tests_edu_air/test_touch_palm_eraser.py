"""PalmEraseDetector: wiping an open palm across the wall erases a wide
swath of ink, like a real whiteboard eraser -- independent of, and never
competing with, the fingertip draw/touch pipeline (which deliberately
rejects an open palm as a drawing candidate, see palm_rejection.py).

Uses the same synthetic-image integration style as
test_touch_backends_integration.py: real cv2/numpy pixel math, not
stubbed-out contact math.
"""

from __future__ import annotations

import cv2
import numpy as np

from edu_air.config import TouchSettings
from edu_air.touch.backends.shadow_gap import ShadowGapFingerBackend
from edu_air.touch.detector import SurfaceTouchDetector
from edu_air.touch.palm_eraser import PalmEraseDetector
from hadj_no_touch.vision.hand_tracking import (
    HandData, LM_WRIST, LM_THUMB_TIP, LM_INDEX_PIP, LM_INDEX_TIP,
    LM_MIDDLE_MCP, LM_MIDDLE_PIP, LM_MIDDLE_TIP, LM_RING_PIP, LM_RING_TIP,
    LM_PINKY_PIP, LM_PINKY_TIP,
)

W, H = 320, 240


def make_palm_hand(palm_xy: tuple[float, float]) -> HandData:
    """An OPEN_PALM-pose hand (every finger extended) whose wrist/MCP
    midpoint -- the actual point ``PalmEraseDetector`` searches from --
    lands exactly on ``palm_xy``. hand_scale_px comes out to 30, same as
    test_touch_backends_integration's make_pointing_hand."""
    px = np.zeros((21, 2), dtype=np.float32)
    cx, cy = palm_xy
    mcp_y = cy - 15.0
    wrist_y = cy + 15.0   # (wrist + mcp) / 2 == (wrist_y + mcp_y) / 2 == cy
    px[LM_WRIST] = (cx, wrist_y)
    px[LM_MIDDLE_MCP] = (cx, mcp_y)          # hand_scale_px = 30
    px[LM_THUMB_TIP] = (cx - 35.0, mcp_y - 10.0)
    px[LM_INDEX_PIP] = (cx - 10.0, mcp_y - 15.0)
    px[LM_INDEX_TIP] = (cx - 10.0, mcp_y - 40.0)   # extended
    px[LM_MIDDLE_PIP] = (cx, mcp_y - 15.0)
    px[LM_MIDDLE_TIP] = (cx, mcp_y - 45.0)          # extended
    px[LM_RING_PIP] = (cx + 10.0, mcp_y - 15.0)
    px[LM_RING_TIP] = (cx + 10.0, mcp_y - 40.0)     # extended
    px[LM_PINKY_PIP] = (cx + 18.0, mcp_y - 12.0)
    px[LM_PINKY_TIP] = (cx + 18.0, mcp_y - 35.0)    # extended
    norm = px / np.array([W, H], dtype=np.float32)
    return HandData(landmarks_norm=norm, landmarks_px=px, handedness="Right",
                    confidence=0.95, tracked=True)


def make_pointing_hand(tip_xy: tuple[float, float]) -> HandData:
    """A POINT-pose hand, exactly mirroring
    test_touch_backends_integration.make_pointing_hand -- used here only
    to prove a pointing hand never triggers the palm eraser."""
    px = np.zeros((21, 2), dtype=np.float32)
    px[LM_WRIST] = (tip_xy[0], tip_xy[1] + 60.0)
    px[LM_MIDDLE_MCP] = (tip_xy[0], tip_xy[1] + 30.0)
    px[LM_THUMB_TIP] = (tip_xy[0] - 20.0, tip_xy[1] + 50.0)
    px[LM_INDEX_PIP] = (tip_xy[0], tip_xy[1] + 15.0)
    px[LM_INDEX_TIP] = tip_xy
    px[LM_MIDDLE_PIP] = (tip_xy[0], tip_xy[1] + 15.0)
    px[LM_MIDDLE_TIP] = (tip_xy[0], tip_xy[1] + 25.0)
    px[LM_RING_PIP] = (tip_xy[0], tip_xy[1] + 15.0)
    px[LM_RING_TIP] = (tip_xy[0], tip_xy[1] + 25.0)
    px[LM_PINKY_PIP] = (tip_xy[0], tip_xy[1] + 15.0)
    px[LM_PINKY_TIP] = (tip_xy[0], tip_xy[1] + 25.0)
    norm = px / np.array([W, H], dtype=np.float32)
    return HandData(landmarks_norm=norm, landmarks_px=px, handedness="Right",
                    confidence=0.95, tracked=True)


def make_frame_with_shadow(center_xy: tuple[float, float], gap_px: float) -> np.ndarray:
    frame = np.full((H, W, 3), 220, dtype=np.uint8)
    shadow_xy = (int(center_xy[0]), int(center_xy[1] + gap_px))
    cv2.circle(frame, shadow_xy, 8, (30, 30, 30), -1)
    return frame


def make_settings(**kw) -> TouchSettings:
    s = TouchSettings()
    s.enabled = True
    s.min_contrast = 15.0
    s.palm_erase_contact_threshold = 0.35
    s.palm_erase_min_wipe_distance = 0.05
    for k, v in kw.items():
        setattr(s, k, v)
    return s


def test_a_stationary_palm_in_contact_never_starts_a_wipe():
    """The core anti-false-trigger requirement: contact alone is not
    enough, only a deliberate wipe is."""
    det = PalmEraseDetector(make_settings())
    center = (160.0, 100.0)
    for _ in range(20):  # many frames, palm never moves
        frame = make_frame_with_shadow(center, gap_px=3.0)
        hand = make_palm_hand(center)
        result = det.update(frame, [hand], W, H)
        assert result is None


def test_a_moving_palm_in_contact_eventually_starts_a_wipe():
    det = PalmEraseDetector(make_settings())
    y = 100.0
    saw_wipe = False
    for _ in range(40):
        center = (160.0, y)
        frame = make_frame_with_shadow(center, gap_px=3.0)
        hand = make_palm_hand(center)
        result = det.update(frame, [hand], W, H)
        if result is not None:
            saw_wipe = True
        y += 3.0  # sweeping across the wall
    assert saw_wipe


def test_a_palm_hovering_far_from_the_wall_never_erases():
    det = PalmEraseDetector(make_settings())
    y = 100.0
    for _ in range(40):
        center = (160.0, y)
        frame = make_frame_with_shadow(center, gap_px=60.0)  # far, not touching
        hand = make_palm_hand(center)
        assert det.update(frame, [hand], W, H) is None
        y += 3.0


def test_a_pointing_hand_never_triggers_the_palm_eraser():
    det = PalmEraseDetector(make_settings())
    y = 100.0
    for _ in range(40):
        tip = (160.0, y)
        frame = make_frame_with_shadow(tip, gap_px=3.0)
        hand = make_pointing_hand(tip)
        assert det.update(frame, [hand], W, H) is None
        y += 3.0


def test_losing_contact_resets_the_accumulated_wipe_path():
    det = PalmEraseDetector(make_settings())
    y = 100.0
    for _ in range(15):  # build up path length, in contact
        center = (160.0, y)
        frame = make_frame_with_shadow(center, gap_px=3.0)
        det.update(frame, [make_palm_hand(center)], W, H)
        y += 3.0
    # lift away -- contact lost, path must reset
    frame = make_frame_with_shadow((160.0, y), gap_px=80.0)
    assert det.update(frame, [make_palm_hand((160.0, y))], W, H) is None
    # come back down at the *same* spot: must need to travel the full
    # distance again, not resume where it left off
    frame2 = make_frame_with_shadow((160.0, y), gap_px=3.0)
    assert det.update(frame2, [make_palm_hand((160.0, y))], W, H) is None


def test_disabled_setting_always_returns_none():
    det = PalmEraseDetector(make_settings(palm_erase_enabled=False))
    y = 100.0
    for _ in range(40):
        center = (160.0, y)
        frame = make_frame_with_shadow(center, gap_px=3.0)
        assert det.update(frame, [make_palm_hand(center)], W, H) is None
        y += 3.0


def test_no_hands_returns_none_and_does_not_crash():
    det = PalmEraseDetector(make_settings())
    frame = np.full((H, W, 3), 220, dtype=np.uint8)
    assert det.update(frame, [], W, H) is None


# ---- SurfaceTouchDetector.update_palm_erase() integration -------------------
def test_detector_maps_palm_erase_position_through_calibration():
    settings = make_settings()
    detector = SurfaceTouchDetector(ShadowGapFingerBackend(), settings)
    detector.set_calibration(lambda p: (p[0] * 0.5, p[1] * 0.5 + 0.25))
    y = 100.0
    mapped = None
    for _ in range(40):
        center = (160.0, y)
        frame = make_frame_with_shadow(center, gap_px=3.0)
        pos = detector.update_palm_erase(frame, [make_palm_hand(center)], W, H)
        if pos is not None:
            mapped = pos
        y += 3.0
    assert mapped is not None
    assert 0.0 <= mapped[0] <= 0.5
    assert 0.25 <= mapped[1] <= 0.75


def test_detector_respects_the_enabled_flag():
    settings = make_settings()
    settings.enabled = False
    detector = SurfaceTouchDetector(ShadowGapFingerBackend(), settings)
    frame = make_frame_with_shadow((160.0, 100.0), gap_px=3.0)
    assert detector.update_palm_erase(frame, [make_palm_hand((160.0, 100.0))], W, H) is None
