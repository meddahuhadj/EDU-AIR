"""InteractivePointer geometry: spike rejection, dead zone, smoothing,
sensitivity presets and the calibration hook."""

from __future__ import annotations

import pytest

from edu_air.config import PointerSettings
from edu_air.pointer import InteractivePointer


def make_pointer(**kw) -> InteractivePointer:
    settings = PointerSettings()
    settings.sensitivity = kw.pop("sensitivity", "medium")
    settings.apply_sensitivity()
    for k, v in kw.items():
        setattr(settings, k, v)
    return InteractivePointer(1280, 720, settings)


def test_first_sample_sets_position():
    p = make_pointer(mirror_x=False)
    pos = p.update((0.5, 0.5))
    assert pos is not None
    assert 0 <= pos[0] <= 1280 and 0 <= pos[1] <= 720


def test_mirror_x_flips_horizontal():
    p = make_pointer(mirror_x=True)
    p.update((0.2, 0.5))
    p.update((0.2, 0.5))
    raw = p.raw_to_screen((0.2, 0.5))
    assert raw[0] == pytest.approx(0.8)


def test_dead_zone_holds_position():
    p = make_pointer(dead_zone=0.01, smoothing=1.0, speed=1.0, mirror_x=False)
    p.update((0.5, 0.5))
    p.update((0.5, 0.5))
    a = p.position
    p.update((0.5, 0.508))
    b = p.position
    assert b == a  # movement within dead zone is ignored


def test_spike_is_rejected():
    p = make_pointer(max_jump_ratio=0.10, mirror_x=False)
    p.update((0.5, 0.5))
    a = p.position
    p.update((0.99, 0.99))  # a wild single-frame jump
    b = p.position
    assert b == a
    assert p.metrics.spikes_rejected == 1


def test_sensitivity_presets_apply():
    low = make_pointer(sensitivity="low", mirror_x=False)
    med = make_pointer(sensitivity="medium", mirror_x=False)
    high = make_pointer(sensitivity="high", mirror_x=False)
    assert med.settings.dead_zone < low.settings.dead_zone
    assert high.settings.dead_zone < med.settings.dead_zone
    assert high.settings.speed > med.settings.speed > low.settings.speed
    assert high.settings.smoothing < med.settings.smoothing < low.settings.smoothing


def test_sensitivity_invalid_falls_back_to_medium():
    p = make_pointer(sensitivity="turbo")
    assert p.settings.sensitivity == "medium"


def test_ema_smoothing_converges_to_target():
    p = make_pointer(smoothing=0.5, speed=1.0, dead_zone=0.0,
                     max_jump_ratio=2.0, mirror_x=False)
    p.update((0.1, 0.1))
    for _ in range(200):
        p.update((0.9, 0.9))
    x, y = p.position
    assert x == pytest.approx(0.9 * 1280, abs=1.0)
    assert y == pytest.approx(0.9 * 720, abs=1.0)


def test_disabled_pointer_returns_last_pos():
    p = make_pointer(mirror_x=False)
    p.update((0.5, 0.5))
    a = p.position
    p.set_enabled(False)
    pos = p.update((0.9, 0.9))
    assert pos == a
    assert not p.visible


def test_calibration_mapping_applied():
    p = make_pointer(mirror_x=False)
    p.set_calibration(lambda xy: (xy[0] * 0.5, xy[1] * 0.5))
    assert p.raw_to_screen((0.8, 0.8)) == pytest.approx((0.4, 0.4))
    p.set_calibration(None)
    assert p.raw_to_screen((0.8, 0.8)) == pytest.approx((0.8, 0.8))


def test_reset_clears_state():
    p = make_pointer(mirror_x=False)
    p.update((0.5, 0.5))
    p.update((0.6, 0.5))
    p.reset()
    assert p.position is None
    assert p.metrics.tremor_px == 0.0