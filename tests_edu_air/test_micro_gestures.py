"""Tests for MicroGestureMapper, OneEuroFilter, Shape Fitting and Lesson Canvas Export."""

from __future__ import annotations

import os
import tempfile
from edu_air.pointer import InteractivePointer, OneEuroFilter, MicroGestureMapper
from edu_air.annotation import AnnotationModel, Stroke, fit_shape, TOOL_SHAPE


def test_one_euro_filter() -> None:
    f = OneEuroFilter(min_cutoff=1.0, beta=0.05)
    p1 = f.filter((100.0, 100.0), 0.0)
    assert p1 == (100.0, 100.0)

    # Slow movement -> heavy smoothing
    p2 = f.filter((101.0, 101.0), 0.033)
    assert abs(p2[0] - 100.0) < 1.0  # smoothed

    # Reset
    f.reset()
    assert f.x_prev is None


def test_micro_gesture_mapper() -> None:
    mapper = MicroGestureMapper(roi_center=(0.5, 0.5), roi_size=(0.4, 0.4), enabled=True)
    # Center of ROI (0.5, 0.5) should map to screen center (0.5, 0.5)
    res_center = mapper.map((0.5, 0.5))
    assert abs(res_center[0] - 0.5) < 1e-5
    assert abs(res_center[1] - 0.5) < 1e-5

    # Top-left of ROI (0.3, 0.3) should map to (0.0, 0.0)
    res_tl = mapper.map((0.3, 0.3))
    assert abs(res_tl[0] - 0.0) < 1e-5
    assert abs(res_tl[1] - 0.0) < 1e-5


def test_pointer_with_micro_gestures() -> None:
    pointer = InteractivePointer(1000, 1000)
    pointer.micro_gesture_mapper.enabled = True
    pos = pointer.raw_to_screen((0.5, 0.5))
    assert abs(pos[0] - 0.5) < 1e-5


def test_shape_fitting_circle() -> None:
    import math
    # Generate points forming a rough circle around (0.5, 0.5) with radius 0.1
    pts = []
    num_pts = 20
    for i in range(num_pts):
        ang = (2.0 * math.pi * i) / num_pts
        pts.append((0.5 + 0.1 * math.cos(ang), 0.5 + 0.1 * math.sin(ang)))
    pts.append(pts[0])  # close loop

    raw_stroke = Stroke(tool=TOOL_SHAPE, points=pts)
    fitted = fit_shape(raw_stroke)
    assert fitted.shape_type == "circle"
    assert len(fitted.points) > 20


def test_shape_fitting_line() -> None:
    # Straight open stroke
    pts = [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3), (0.4, 0.4), (0.5, 0.5), (0.6, 0.6)]
    raw_stroke = Stroke(tool=TOOL_SHAPE, points=pts)
    fitted = fit_shape(raw_stroke)
    assert fitted.shape_type == "line"
    assert len(fitted.points) == 2


def test_canvas_export() -> None:
    model = AnnotationModel()
    model.set_tool("draw")
    model.begin((0.1, 0.1))
    model.move((0.5, 0.5))
    model.finish()

    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "test_lesson.png")
        success = model.export_canvas(out_file, 400, 300)
        assert success is True
        assert os.path.exists(out_file)
        assert os.path.getsize(out_file) > 100
