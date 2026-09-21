"""HomographyDriftMonitor: the "calibration no longer fits the room" signal
built from how often mapped touches land outside the projected [0, 1]
rectangle before clamping."""

from __future__ import annotations

from edu_air.touch.drift_monitor import HomographyDriftMonitor


def make_monitor(**kw) -> HomographyDriftMonitor:
    return HomographyDriftMonitor(**kw)


def test_in_bounds_touches_never_trigger_drift():
    m = make_monitor(min_samples=5)
    for _ in range(30):
        assert m.observe(0.4, 0.6) is False
    assert not m.drift_suspected


def test_a_few_edge_touches_do_not_trigger_drift():
    """Real teaching involves genuinely touching near the board's edge --
    a handful of near-boundary or slightly-over readings must not itself
    read as "calibration is broken"."""
    m = make_monitor(min_samples=5, out_of_bounds_ratio=0.35, overflow_margin=0.03)
    samples = [0.5, 0.02, 0.98, 1.02, 0.5, 0.5, 0.5, 0.5]
    for x in samples:
        m.observe(x, 0.5)
    assert not m.drift_suspected


def test_sustained_out_of_bounds_triggers_drift():
    m = make_monitor(min_samples=5, out_of_bounds_ratio=0.35, overflow_margin=0.03)
    for _ in range(20):
        m.observe(1.3, 0.5)   # consistently far outside the board
    assert m.drift_suspected


def test_needs_minimum_samples_before_deciding():
    m = make_monitor(min_samples=10, out_of_bounds_ratio=0.35)
    for _ in range(5):
        m.observe(2.0, 2.0)
    assert not m.drift_suspected   # not enough samples yet to be confident


def test_drift_clears_once_touches_return_in_bounds():
    m = make_monitor(window=10, min_samples=5, out_of_bounds_ratio=0.35)
    for _ in range(10):
        m.observe(1.5, 0.5)
    assert m.drift_suspected
    for _ in range(10):
        m.observe(0.5, 0.5)
    assert not m.drift_suspected


def test_reset_clears_state():
    m = make_monitor(min_samples=3)
    for _ in range(10):
        m.observe(2.0, 2.0)
    assert m.drift_suspected
    m.reset()
    assert not m.drift_suspected
