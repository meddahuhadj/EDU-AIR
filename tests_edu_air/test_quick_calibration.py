"""quick_calibrate(): the 3-tap pointer touch-up alternative to the full
corner/touch-plane/alignment wizard (see ui.py::_quick_calibrate_pointer)."""

from __future__ import annotations

from edu_air.calibration import QUICK_CALIB_TARGETS, quick_calibrate


def test_fewer_than_three_points_returns_none():
    assert quick_calibrate([]) is None
    assert quick_calibrate([(0.1, 0.1)]) is None
    assert quick_calibrate([(0.1, 0.1), (0.5, 0.5)]) is None


def test_three_points_produce_a_mapping_that_reproduces_the_targets():
    # Any invertible affine relationship between camera and screen space --
    # a linear fit from exactly 3 non-collinear correspondences should
    # reproduce them with (near) zero residual.
    camera_points = [(x * 0.5 + 0.1, y * 0.5 + 0.05) for x, y in QUICK_CALIB_TARGETS]
    mapping = quick_calibrate(camera_points)
    assert mapping is not None
    for cam_pt, target in zip(camera_points, QUICK_CALIB_TARGETS):
        mapped = mapping(cam_pt)
        assert abs(mapped[0] - target[0]) < 1e-6
        assert abs(mapped[1] - target[1]) < 1e-6


def test_a_fourth_point_is_ignored_not_averaged_in():
    camera_points = [(x * 0.5 + 0.1, y * 0.5 + 0.05) for x, y in QUICK_CALIB_TARGETS]
    exact_mapping = quick_calibrate(camera_points)
    with_extra = quick_calibrate(camera_points + [(0.99, 0.01)])
    assert with_extra is not None
    probe = (0.4, 0.3)
    a = exact_mapping(probe)
    b = with_extra(probe)
    assert abs(a[0] - b[0]) < 1e-6
    assert abs(a[1] - b[1]) < 1e-6


def test_targets_form_a_wide_non_collinear_triangle():
    """A degenerate (near-collinear) target set would make the affine fit
    ill-conditioned -- guard the geometry itself, not just the happy path."""
    (x0, y0), (x1, y1), (x2, y2) = QUICK_CALIB_TARGETS
    area2 = abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))
    assert area2 > 0.1  # well clear of collinear
