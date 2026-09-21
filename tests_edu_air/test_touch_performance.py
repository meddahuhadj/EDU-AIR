"""Wall-clock budget check for the touch pipeline.

The acceptance target is contact->ink latency under 60-80ms. That budget
covers camera capture + one or two hysteresis-debounce frames + processing;
this test isolates just the *processing* half (backend.process_frame +
SurfaceTouchDetector.update) on a realistic frame size, so a regression
that makes the per-frame math slow shows up here long before anyone has to
notice it "feels laggy" on real hardware. Thresholds are generous (not a
tight microbenchmark) to stay stable on a loaded CI machine while still
catching a real regression (e.g. an accidental O(w*h) full-frame scan
where the design calls for a short localized corridor)."""

from __future__ import annotations

import time

import cv2
import numpy as np

from edu_air.config import TouchSettings
from edu_air.touch.backends.color_marker import ColorMarkerBackend
from edu_air.touch.backends.ir_pen import IRPenBackend
from edu_air.touch.backends.shadow_gap import ShadowGapFingerBackend
from edu_air.touch.detector import SurfaceTouchDetector
from hadj_no_touch.vision.hand_tracking import (
    HandData, LM_WRIST, LM_THUMB_TIP, LM_INDEX_PIP, LM_INDEX_TIP,
    LM_MIDDLE_MCP, LM_MIDDLE_PIP, LM_MIDDLE_TIP, LM_RING_PIP, LM_RING_TIP,
    LM_PINKY_PIP, LM_PINKY_TIP,
)

W, H = 640, 480
FRAME_BUDGET_MS = 33.0    # 30fps camera cadence
# Processing is one small slice of the 60-80ms end-to-end target (camera
# capture + debounce frames eat the rest) -- a generous per-frame ceiling
# that still catches an accidental full-frame-scan-style regression.
PER_FRAME_CEILING_MS = 20.0
N_FRAMES = 60


def make_pointing_hand(tip_xy: tuple[float, float]) -> HandData:
    px = np.zeros((21, 2), dtype=np.float32)
    wrist = (tip_xy[0], tip_xy[1] + 60.0)
    middle_mcp = (tip_xy[0], tip_xy[1] + 30.0)
    px[LM_WRIST] = wrist
    px[LM_MIDDLE_MCP] = middle_mcp
    px[LM_THUMB_TIP] = (tip_xy[0] - 20.0, tip_xy[1] + 50.0)

    def place(pip_idx, tip_idx, x, extended):
        px[pip_idx] = (x, tip_xy[1] + 15.0)
        px[tip_idx] = (x, tip_xy[1] - 5.0) if extended else (x, tip_xy[1] + 25.0)

    place(LM_INDEX_PIP, LM_INDEX_TIP, tip_xy[0], True)
    place(LM_MIDDLE_PIP, LM_MIDDLE_TIP, tip_xy[0] + 5, False)
    place(LM_RING_PIP, LM_RING_TIP, tip_xy[0] + 10, False)
    place(LM_PINKY_PIP, LM_PINKY_TIP, tip_xy[0] + 15, False)
    norm = px / np.array([W, H], dtype=np.float32)
    return HandData(landmarks_norm=norm, landmarks_px=px, handedness="Right",
                    confidence=0.95, tracked=True)


def make_settings() -> TouchSettings:
    s = TouchSettings()
    s.enabled = True
    s.min_contrast = 15.0
    return s


def timed_frames(fn, n=N_FRAMES) -> list[float]:
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000.0)
    return times


def assert_within_budget(times: list[float], label: str) -> None:
    """Median is the meaningful number for "does this fit the frame
    budget" -- it reflects the algorithm's actual cost and is what
    determines whether real-time contact detection feels responsive.
    A single wildly slow frame is checked too, but with a loose ceiling:
    on a busy shared dev machine, OS scheduling jitter alone can stall any
    Python process for tens of milliseconds on a rare frame -- that is not
    a defect in this code, and a tight tail-latency assertion here would
    just be flaky. It only needs to catch a *sustained*, pathological
    regression (e.g. an accidental O(w*h) full-frame scan)."""
    times_sorted = sorted(times)
    p50 = times_sorted[len(times_sorted) // 2]
    worst = times_sorted[-1]
    assert p50 < PER_FRAME_CEILING_MS, f"{label}: p50 {p50:.2f}ms exceeds {PER_FRAME_CEILING_MS}ms"
    assert worst < PER_FRAME_CEILING_MS * 15, (
        f"{label}: worst frame {worst:.2f}ms exceeds {PER_FRAME_CEILING_MS * 15}ms "
        "-- likely a real regression, not scheduler noise")


def test_shadow_gap_process_frame_stays_within_frame_budget():
    backend = ShadowGapFingerBackend()
    backend.configure(make_settings())
    tip = (320.0, 200.0)
    frame = np.full((H, W, 3), 220, dtype=np.uint8)
    cv2.circle(frame, (int(tip[0]), int(tip[1] + 15)), 6, (40, 40, 40), -1)
    hand = make_pointing_hand(tip)

    times = timed_frames(lambda: backend.process_frame(frame, [hand], W, H, now=0.0))
    assert_within_budget(times, "ShadowGapFingerBackend.process_frame")


def test_ir_pen_process_frame_stays_within_frame_budget():
    backend = IRPenBackend()
    backend.configure(make_settings())
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    cv2.circle(frame, (300, 220), 5, (255, 255, 255), -1)

    times = timed_frames(lambda: backend.process_frame(frame, [], W, H, now=0.0))
    assert_within_budget(times, "IRPenBackend.process_frame")


def test_color_marker_process_frame_stays_within_frame_budget():
    backend = ColorMarkerBackend()
    settings = make_settings()
    settings.color_marker_hsv_low = [40, 100, 100]
    settings.color_marker_hsv_high = [80, 255, 255]
    backend.configure(settings)
    frame = np.full((H, W, 3), 220, dtype=np.uint8)
    cv2.circle(frame, (300, 200), 8, (0, 255, 0), -1)
    cv2.circle(frame, (300, 225), 6, (40, 40, 40), -1)

    times = timed_frames(lambda: backend.process_frame(frame, [], W, H, now=0.0))
    assert_within_budget(times, "ColorMarkerBackend.process_frame")


def test_full_detector_update_stays_within_frame_budget():
    """The whole per-frame path an actual camera loop calls: backend +
    hysteresis + calibration mapping + One-Euro smoothing."""
    detector = SurfaceTouchDetector(ShadowGapFingerBackend(), make_settings())
    detector.set_calibration(lambda xy: (xy[0], xy[1]))
    tip = (320.0, 200.0)
    frame = np.full((H, W, 3), 220, dtype=np.uint8)
    cv2.circle(frame, (int(tip[0]), int(tip[1] + 10)), 6, (40, 40, 40), -1)
    hand = make_pointing_hand(tip)

    times = timed_frames(lambda: detector.update(frame, [hand], W, H))
    assert_within_budget(times, "SurfaceTouchDetector.update (shadow_gap)")
