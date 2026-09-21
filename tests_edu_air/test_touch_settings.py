"""TouchSettings: sensitivity presets and round-trip through Settings.to_dict()
(the same JSON persistence path as pointer/annotation settings)."""

from __future__ import annotations

import json

import pytest

from edu_air.config import Settings, TouchSettings


def test_default_backend_is_shadow_gap_and_disabled_by_default():
    s = TouchSettings()
    assert s.backend == "shadow_gap"
    assert s.enabled is False


def test_sensitivity_presets_tighten_hysteresis_as_sensitivity_rises():
    low, med, high = TouchSettings(sensitivity="low"), TouchSettings(sensitivity="medium"), \
        TouchSettings(sensitivity="high")
    for s in (low, med, high):
        s.apply_sensitivity()
    assert high.down_threshold > med.down_threshold > low.down_threshold
    assert high.down_frames < med.down_frames < low.down_frames


def test_invalid_sensitivity_falls_back_to_medium():
    s = TouchSettings(sensitivity="ultra")
    s.apply_sensitivity()
    assert s.sensitivity == "medium"


def test_settings_to_dict_includes_touch_block_and_is_json_serializable():
    settings = Settings()
    settings.touch.backend = "ir_pen"
    settings.touch.enabled = True
    d = settings.to_dict()
    assert "touch" in d
    assert d["touch"]["backend"] == "ir_pen"
    assert d["touch"]["enabled"] is True
    json.dumps(d)  # must not raise


def test_settings_load_restores_touch_block(tmp_path):
    settings = Settings()
    settings.touch.backend = "color_marker"
    settings.touch.sensitivity = "high"
    path = tmp_path / "config.json"
    settings.save(path)

    restored = Settings()
    restored.load(path)
    assert restored.touch.backend == "color_marker"
    assert restored.touch.sensitivity == "high"
