"""STAGE_TOUCH_PLANE: the wall-mode contact-baseline step added to the
existing projector calibration wizard -- reuses the 4 corners already
tapped for the homography, and must stay fully optional (default-skips)
so callers unaware of wall mode still get a coherent, completable report."""

from __future__ import annotations

import pytest

from edu_air.calibration import (
    ProjectorCalibration, STAGE_TOUCH_PLANE, STAGE_ORDER,
    STATUS_DONE, STATUS_SKIPPED,
)
from edu_air.touch.backends.base import TouchSample
from edu_air.touch.backends.shadow_gap import ShadowGapFingerBackend
from edu_air.config import TouchSettings


def test_touch_plane_is_in_stage_order_after_corners():
    from edu_air.calibration import STAGE_CORNERS
    assert STAGE_TOUCH_PLANE in STAGE_ORDER
    assert STAGE_ORDER.index(STAGE_TOUCH_PLANE) == STAGE_ORDER.index(STAGE_CORNERS) + 1


def test_finish_touch_plane_without_backend_is_skipped_and_estimated():
    cal = ProjectorCalibration()
    st = cal.finish_touch_plane(backend=None)
    assert st.status == STATUS_SKIPPED
    assert STAGE_TOUCH_PLANE in cal.report.estimated


def test_complete_auto_skips_touch_plane_when_never_touched():
    cal = ProjectorCalibration()
    cal.step_camera(True)
    cal.step_projection(True)
    cal.finish_corners([(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)])
    cal.add_alignment((0.5, 0.5), (0.5, 0.5))
    cal.finish_alignment(1)
    for g in ("point", "pinch", "swipe_left", "palm"):
        cal.observe_gesture(g)
    cal.finish_gestures()
    rep = cal.complete()
    assert rep.stages[STAGE_TOUCH_PLANE].status == STATUS_SKIPPED
    assert rep.completed


def test_finish_touch_plane_learns_baseline_from_real_samples():
    cal = ProjectorCalibration()
    backend = ShadowGapFingerBackend()
    backend.configure(TouchSettings())
    cal.add_touch_sample(0, TouchSample(
        x_cam_norm=0.1, y_cam_norm=0.1, contact_metric=0.0, confidence=1.0,
        debug={"tip_px": (100.0, 100.0), "shadow_px": (100.0, 108.0), "gap_px": 8.0}))
    cal.add_touch_sample(0, TouchSample(
        x_cam_norm=0.1, y_cam_norm=0.1, contact_metric=0.0, confidence=1.0,
        debug={"tip_px": (100.0, 100.0), "shadow_px": (100.0, 103.0), "gap_px": 3.0}))
    st = cal.finish_touch_plane(backend=backend)
    assert st.status == STATUS_DONE
    assert cal.touch_plane["zones"]
    assert cal.settings.calibration.get("touch_plane") == cal.touch_plane


def test_reset_clears_touch_samples():
    cal = ProjectorCalibration()
    cal.add_touch_sample(0, TouchSample(x_cam_norm=0.1, y_cam_norm=0.1,
                                        contact_metric=0.0, confidence=1.0))
    cal.reset()
    assert cal.touch_samples == {}
    assert cal.touch_plane == {}
