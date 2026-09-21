"""Touch-plane baseline learning: zone bucketing, direction averaging and
gap-bias extraction from a batch of touch samples collected during the
"plan tactile" calibration step."""

from __future__ import annotations

import pytest

from edu_air.touch import plane_calibration as plane
from edu_air.touch.backends.base import TouchSample


def make_sample(x, y, tip_px, shadow_px, gap_px):
    return TouchSample(
        x_cam_norm=x, y_cam_norm=y, contact_metric=0.0, confidence=1.0,
        debug={"tip_px": tip_px, "shadow_px": shadow_px, "gap_px": gap_px},
    )


def test_zone_key_buckets_corners_into_distinct_cells():
    assert plane.zone_key(0.05, 0.05, grid=3) == (0, 0)
    assert plane.zone_key(0.95, 0.05, grid=3) == (2, 0)
    assert plane.zone_key(0.05, 0.95, grid=3) == (0, 2)
    assert plane.zone_key(0.95, 0.95, grid=3) == (2, 2)


def test_zone_key_clamps_out_of_range_values():
    assert plane.zone_key(-0.5, 1.5, grid=3) == (0, 2)


def test_learn_zone_baselines_averages_direction_and_takes_min_gap():
    samples = [
        make_sample(0.1, 0.1, (100, 100), (100, 110), 10.0),   # shadow straight below
        make_sample(0.1, 0.1, (100, 100), (100, 106), 6.0),
        make_sample(0.1, 0.1, (100, 100), (100, 102), 2.0),
    ]
    result = plane.learn_zone_baselines(samples, grid=3)
    zone = result["zones"]["0,0"]
    assert zone["dir"] == pytest.approx([0.0, 1.0], abs=1e-6)
    assert zone["gap_bias"] == pytest.approx(2.0)
    assert zone["n"] == 3


def test_learn_zone_baselines_keeps_zones_separate():
    samples = [
        make_sample(0.05, 0.05, (10, 10), (10, 20), 10.0),
        make_sample(0.95, 0.95, (300, 300), (310, 300), 10.0),
    ]
    result = plane.learn_zone_baselines(samples, grid=3)
    assert set(result["zones"].keys()) == {"0,0", "2,2"}
    assert result["zones"]["2,2"]["dir"] == pytest.approx([1.0, 0.0], abs=1e-6)


def test_lookup_zone_exact_match():
    data = plane.learn_zone_baselines(
        [make_sample(0.1, 0.1, (0, 0), (0, 10), 10.0)], grid=3)
    z = plane.lookup_zone(data, 0.1, 0.1)
    assert z is not None
    assert z["gap_bias"] == pytest.approx(10.0)


def test_lookup_zone_falls_back_to_nearest_when_empty():
    data = plane.learn_zone_baselines(
        [make_sample(0.05, 0.05, (0, 0), (0, 10), 10.0)], grid=3)
    # (2,2) has no samples -> nearest populated zone (0,0) should be used.
    z = plane.lookup_zone(data, 0.95, 0.95)
    assert z is not None
    assert z["gap_bias"] == pytest.approx(10.0)


def test_lookup_zone_none_when_no_data():
    assert plane.lookup_zone({}, 0.5, 0.5) is None
    assert plane.lookup_zone({"grid": 3, "zones": {}}, 0.5, 0.5) is None
