"""End-to-end integration for the touch backends against real cv2/numpy
image data -- unlike the other touch tests, this one does not stub out the
pixel math. It renders a synthetic "projected wall" frame with a dark
shadow blob near a fingertip and checks the whole
ShadowGapFingerBackend -> SurfaceTouchDetector -> DOWN/MOVE/UP chain
reacts the way a real approach-and-touch gesture should."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from edu_air.config import TouchSettings
from edu_air.touch.backends.color_marker import ColorMarkerBackend
from edu_air.touch.backends.ir_pen import IRPenBackend
from edu_air.touch.backends.shadow_gap import ShadowGapFingerBackend
from edu_air.touch.detector import SurfaceTouchDetector
from edu_air.touch.events import TouchState
from hadj_no_touch.vision.hand_tracking import (
    HandData, LM_WRIST, LM_THUMB_TIP, LM_INDEX_PIP, LM_INDEX_TIP,
    LM_MIDDLE_MCP, LM_MIDDLE_PIP, LM_MIDDLE_TIP, LM_RING_PIP, LM_RING_TIP,
    LM_PINKY_PIP, LM_PINKY_TIP,
)

W, H = 320, 240


def make_pointing_hand(tip_xy: tuple[float, float]) -> HandData:
    """A POINT-pose hand (index extended, rest curled) whose fingertip sits
    at ``tip_xy`` in pixel space, scaled so PalmRejectionFilter accepts it
    and hand_scale_px comes out sane for the shadow-search corridor."""
    px = np.zeros((21, 2), dtype=np.float32)
    wrist = (tip_xy[0], tip_xy[1] + 60.0)
    middle_mcp = (tip_xy[0], tip_xy[1] + 30.0)   # hand_scale_px = 30
    px[LM_WRIST] = wrist
    px[LM_MIDDLE_MCP] = middle_mcp
    px[LM_THUMB_TIP] = (tip_xy[0] - 20.0, tip_xy[1] + 50.0)
    px[LM_INDEX_PIP] = (tip_xy[0], tip_xy[1] + 15.0)
    px[LM_INDEX_TIP] = tip_xy
    px[LM_MIDDLE_PIP] = (tip_xy[0], tip_xy[1] + 15.0)
    px[LM_MIDDLE_TIP] = (tip_xy[0], tip_xy[1] + 25.0)   # curled
    px[LM_RING_PIP] = (tip_xy[0], tip_xy[1] + 15.0)
    px[LM_RING_TIP] = (tip_xy[0], tip_xy[1] + 25.0)     # curled
    px[LM_PINKY_PIP] = (tip_xy[0], tip_xy[1] + 15.0)
    px[LM_PINKY_TIP] = (tip_xy[0], tip_xy[1] + 25.0)    # curled
    norm = px / np.array([W, H], dtype=np.float32)
    return HandData(landmarks_norm=norm, landmarks_px=px, handedness="Right",
                    confidence=0.95, tracked=True)


def make_frame_with_shadow(tip_xy: tuple[float, float], gap_px: float) -> np.ndarray:
    """A bright synthetic wall with a dark circular "shadow" blob placed
    ``gap_px`` below the fingertip -- shrinking gap_px simulates the finger
    approaching the surface."""
    frame = np.full((H, W, 3), 220, dtype=np.uint8)
    shadow_xy = (int(tip_xy[0]), int(tip_xy[1] + gap_px))
    cv2.circle(frame, shadow_xy, 6, (30, 30, 30), -1)
    return frame


def make_settings(**kw) -> TouchSettings:
    s = TouchSettings()
    s.enabled = True
    s.min_contrast = 15.0
    s.down_threshold, s.up_threshold = 0.2, 0.4
    s.down_frames, s.up_frames = 1, 2
    s.predict_one_frame = False
    for k, v in kw.items():
        setattr(s, k, v)
    return s


def test_shadow_gap_backend_reports_low_metric_when_shadow_is_close():
    backend = ShadowGapFingerBackend()
    backend.configure(make_settings())
    tip = (160.0, 100.0)
    frame = make_frame_with_shadow(tip, gap_px=3.0)
    hand = make_pointing_hand(tip)
    sample = backend.process_frame(frame, [hand], W, H, now=0.0)
    assert sample is not None
    assert sample.contact_metric < 0.3
    assert sample.debug["gap_px"] == pytest.approx(3.0, abs=2.0)


def test_shadow_gap_backend_reports_high_metric_when_shadow_is_far():
    backend = ShadowGapFingerBackend()
    backend.configure(make_settings())
    tip = (160.0, 100.0)
    frame = make_frame_with_shadow(tip, gap_px=40.0)
    hand = make_pointing_hand(tip)
    sample = backend.process_frame(frame, [hand], W, H, now=0.0)
    assert sample is not None
    assert sample.contact_metric > 0.6


def test_shadow_gap_backend_rejects_an_open_palm():
    backend = ShadowGapFingerBackend()
    backend.configure(make_settings())
    tip = (160.0, 100.0)
    frame = make_frame_with_shadow(tip, gap_px=3.0)
    hand = make_pointing_hand(tip)
    # Flip to an open-palm pose by extending every finger.
    hand.landmarks_px[LM_MIDDLE_TIP] = (tip[0], tip[1] + 25.0 - 40.0)
    hand.landmarks_px[LM_RING_TIP] = (tip[0], tip[1] + 25.0 - 40.0)
    hand.landmarks_px[LM_PINKY_TIP] = (tip[0], tip[1] + 25.0 - 40.0)
    hand.landmarks_norm = hand.landmarks_px / np.array([W, H], dtype=np.float32)
    assert backend.process_frame(frame, [hand], W, H, now=0.0) is None


def test_full_approach_produces_down_then_up_on_release():
    detector = SurfaceTouchDetector(ShadowGapFingerBackend(), make_settings())
    tip = (160.0, 100.0)

    events = []
    # Approach: gap shrinks from far to touching.
    for gap in (40.0, 30.0, 20.0, 10.0, 4.0, 2.0):
        frame = make_frame_with_shadow(tip, gap)
        hand = make_pointing_hand(tip)
        events += detector.update(frame, [hand], W, H)

    assert any(e.state == TouchState.DOWN for e in events)

    # Release: the finger lifts back away from the wall.
    for gap in (15.0, 30.0, 45.0, 45.0):
        frame = make_frame_with_shadow(tip, gap)
        hand = make_pointing_hand(tip)
        events += detector.update(frame, [hand], W, H)

    assert any(e.state == TouchState.UP for e in events)


def test_ir_pen_backend_finds_a_bright_spot():
    backend = IRPenBackend()
    backend.configure(make_settings(ir_threshold=200))
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    cv2.circle(frame, (100, 80), 5, (255, 255, 255), -1)
    sample = backend.process_frame(frame, [], W, H, now=0.0)
    assert sample is not None
    assert sample.x_cam_norm == pytest.approx(100.0 / W, abs=0.03)
    assert sample.y_cam_norm == pytest.approx(80.0 / H, abs=0.03)
    assert sample.contact_metric < 0.2


def test_ir_pen_backend_sees_nothing_when_unlit():
    backend = IRPenBackend()
    backend.configure(make_settings(ir_threshold=200))
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    assert backend.process_frame(frame, [], W, H, now=0.0) is None


def test_ir_pen_backend_finds_a_dim_spot_in_a_dark_room():
    """A fixed global brightness cutoff (the old behaviour) would miss a
    genuine LED that never reaches that absolute level in a dim room, even
    though it is clearly the brightest thing in frame. Contrast-vs-local-
    background detection must still catch it."""
    backend = IRPenBackend()
    backend.configure(make_settings(ir_threshold=220))   # old cutoff, unreachable below
    frame = np.full((H, W, 3), 20, dtype=np.uint8)         # a dim room
    cv2.circle(frame, (120, 60), 5, (150, 150, 150), -1)   # LED well under 220 but way above the room
    sample = backend.process_frame(frame, [], W, H, now=0.0)
    assert sample is not None
    assert sample.x_cam_norm == pytest.approx(120.0 / W, abs=0.03)


def test_ir_pen_backend_ignores_glare_even_if_brighter_than_old_cutoff():
    """A uniformly bright/glared frame with no real LED spot must not
    trigger just because it crosses some absolute brightness level -- there
    is no local contrast to justify it."""
    backend = IRPenBackend()
    backend.configure(make_settings(ir_threshold=200))
    frame = np.full((H, W, 3), 230, dtype=np.uint8)   # uniform glare, above the old fixed cutoff
    assert backend.process_frame(frame, [], W, H, now=0.0) is None


def test_color_marker_backend_tracks_a_colored_blob():
    backend = ColorMarkerBackend()
    settings = make_settings()
    settings.color_marker_hsv_low = [40, 100, 100]
    settings.color_marker_hsv_high = [80, 255, 255]
    backend.configure(settings)
    frame = np.full((H, W, 3), 220, dtype=np.uint8)
    cv2.circle(frame, (150, 90), 8, (0, 255, 0), -1)   # pure green -> hue ~60
    cv2.circle(frame, (150, 120), 6, (30, 30, 30), -1)  # shadow below the blob
    sample = backend.process_frame(frame, [], W, H, now=0.0)
    assert sample is not None
    assert sample.x_cam_norm == pytest.approx(150.0 / W, abs=0.05)
    assert sample.y_cam_norm == pytest.approx(90.0 / H, abs=0.05)
