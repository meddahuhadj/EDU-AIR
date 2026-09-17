"""Projector calibration: homography fitting, stage lifecycle and report."""

from __future__ import annotations

import pytest

from edu_air.calibration import (
    ProjectorCalibration, fit_homography, linear_mapping,
    STAGE_CAMERA, STAGE_PROJECTION, STAGE_CORNERS,
    STAGE_ALIGNMENT, STAGE_GESTURES, STAGE_ORDER,
    STATUS_DONE, STATUS_SKIPPED, STATUS_FAILED, STATUS_PARTIAL,
)


def test_fit_homography_maps_corners_back():
    src = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
    dst = [(0.03, 0.03), (0.97, 0.03), (0.97, 0.97), (0.03, 0.97)]
    m = fit_homography(src, dst)
    assert m is not None
    out = m((0.5, 0.5))
    assert out == pytest.approx((0.5, 0.5), abs=0.05)


def test_homography_needs_4_points():
    assert fit_homography([(0.1, 0.1)], [(0.03, 0.03)]) is None


def test_linear_mapping_fallback():
    src = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.5, 0.5)]
    dst = [(0.03, 0.03), (0.97, 0.03), (0.97, 0.97), (0.5, 0.5)]
    m = linear_mapping(src, dst)
    assert m is not None
    x, y = m((0.5, 0.5))
    assert x == pytest.approx(0.5, abs=0.1)


def test_stage_order_and_navigation():
    cal = ProjectorCalibration()
    assert cal.stage == STAGE_CAMERA
    assert cal.advance()
    assert cal.stage == STAGE_PROJECTION
    for _ in range(5):
        cal.advance()
    assert cal.done


def test_full_wizard_produces_done_report():
    cal = ProjectorCalibration()
    cal.step_camera(True)
    cal.step_projection(True)
    cal.finish_corners([(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)])
    for target in [[(0.15, 0.20), (0.85, 0.20), (0.85, 0.80), (0.15, 0.80), (0.5, 0.5)]][0]:
        cal.add_alignment(target, target)
    cal.finish_alignment()
    for g in ("swipe_left", "point", "pinch", "palm"):
        cal.observe_gesture(g)
    cal.finish_gestures()
    cal.stage_index = len(STAGE_ORDER)
    rep = cal.complete()
    assert rep.calibrated
    assert rep.stages[STAGE_CORNERS].status == STATUS_DONE
    assert rep.stages[STAGE_GESTURES].status == STATUS_DONE
    assert rep.completed


def test_estimated_corners_are_reported_as_estimated():
    cal = ProjectorCalibration()
    cal.step_camera(True)
    cal.step_projection(True)
    st = cal.finish_corners(corner_list=None)
    assert st.status == STATUS_SKIPPED
    cal.stage_index = len(STAGE_ORDER)
    rep = cal.complete()
    assert STAGE_CORNERS in rep.estimated
    assert rep.calibrated is False


def test_partial_gesture_test_flagged():
    cal = ProjectorCalibration()
    cal.observe_gesture("swipe_left")
    st = cal.finish_gestures()
    assert st.status == STATUS_PARTIAL
    assert "missing" in st.detail


def test_camera_failure_and_reset():
    cal = ProjectorCalibration()
    assert cal.step_camera(False).status == STATUS_FAILED
    cal.reset()
    assert cal.stage == STAGE_CAMERA
    assert cal.report.stages[STAGE_CAMERA].status == "pending"
    assert cal.report.stages[STAGE_ALIGNMENT].status == "pending"