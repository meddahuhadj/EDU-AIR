"""_median_point(): the noise-robust averaging used by the calibration
wizard's live corner/alignment capture windows."""

from __future__ import annotations

import pytest

from edu_air.ui import _median_point


def test_empty_samples_returns_none():
    assert _median_point([]) is None


def test_single_sample_returns_itself():
    assert _median_point([(0.3, 0.4)]) == (0.3, 0.4)


def test_median_ignores_a_single_outlier():
    samples = [(0.50, 0.50)] * 9 + [(0.99, 0.01)]   # one wild tracking glitch
    x, y = _median_point(samples)
    assert x == pytest.approx(0.50)
    assert y == pytest.approx(0.50)


def test_median_of_even_count_picks_the_upper_middle():
    samples = [(0.1, 0.1), (0.2, 0.2), (0.3, 0.3), (0.4, 0.4)]
    # sorted -> index len//2 == 2 -> (0.3, 0.3), matching the implementation's
    # simple "no numpy for a tiny list" choice (not an interpolated median).
    assert _median_point(samples) == (0.3, 0.3)


def test_x_and_y_are_computed_independently():
    samples = [(0.1, 0.9), (0.5, 0.5), (0.9, 0.1)]
    assert _median_point(samples) == (0.5, 0.5)
