"""ContactStateMachine: hysteresis, debounce and lost-tracking recovery --
the anti-flicker core every touch backend shares."""

from __future__ import annotations

import pytest

from edu_air.config import TouchSettings
from edu_air.touch.backends.base import TouchSample
from edu_air.touch.events import TouchState
from edu_air.touch.state_machine import ContactStateMachine


def make_machine(**kw) -> ContactStateMachine:
    s = TouchSettings()
    for k, v in kw.items():
        setattr(s, k, v)
    return ContactStateMachine(s)


def sample(metric: float, confidence: float = 1.0) -> TouchSample:
    return TouchSample(x_cam_norm=0.5, y_cam_norm=0.5, contact_metric=metric,
                       confidence=confidence)


def test_no_event_until_down_frames_confirmed():
    m = make_machine(down_threshold=0.2, down_frames=3)
    assert m.step(sample(0.1), 0.0) is None
    assert m.step(sample(0.1), 0.01) is None
    ev = m.step(sample(0.1), 0.02)
    assert ev is not None and ev.state == TouchState.DOWN


def test_hysteresis_dead_band_holds_move_without_flicker():
    m = make_machine(down_threshold=0.2, up_threshold=0.4, down_frames=1, up_frames=2)
    down = m.step(sample(0.1), 0.0)
    assert down.state == TouchState.DOWN
    # sits in the dead band (between down and up threshold): must stay MOVE.
    for i in range(5):
        ev = m.step(sample(0.3), 0.01 * i)
        assert ev.state == TouchState.MOVE


def test_up_requires_sustained_frames_above_threshold():
    m = make_machine(down_threshold=0.2, up_threshold=0.4, down_frames=1, up_frames=3)
    m.step(sample(0.1), 0.0)
    ev1 = m.step(sample(0.5), 0.01)
    ev2 = m.step(sample(0.5), 0.02)
    ev3 = m.step(sample(0.5), 0.03)
    assert ev1.state == TouchState.MOVE
    assert ev2.state == TouchState.MOVE
    assert ev3.state == TouchState.UP


def test_up_debounce_resets_on_dip_back_below_threshold():
    m = make_machine(down_threshold=0.2, up_threshold=0.4, down_frames=1, up_frames=2)
    m.step(sample(0.1), 0.0)
    m.step(sample(0.5), 0.01)          # 1st "above" frame
    ev = m.step(sample(0.1), 0.02)     # dips back into contact -> counter resets
    assert ev.state == TouchState.MOVE
    ev2 = m.step(sample(0.5), 0.03)    # only the 1st "above" frame again
    assert ev2.state == TouchState.MOVE


def test_low_confidence_sample_is_treated_as_no_sample():
    m = make_machine(down_threshold=0.2, down_frames=1, min_confidence=0.5)
    ev = m.step(sample(0.05, confidence=0.1), 0.0)
    assert ev is None
    assert not m.touching


def test_lost_tracking_force_lifts_a_live_stroke():
    m = make_machine(down_threshold=0.2, down_frames=1, lost_frames_up=2)
    down = m.step(sample(0.1), 0.0)
    assert down.state == TouchState.DOWN
    assert m.step(None, 0.01) is None        # 1st missing frame: grace period
    ev = m.step(None, 0.02)                  # 2nd missing frame: force UP
    assert ev is not None and ev.state == TouchState.UP
    assert not m.touching


def test_reset_clears_touching_state():
    m = make_machine(down_threshold=0.2, down_frames=1)
    m.step(sample(0.1), 0.0)
    assert m.touching
    m.reset()
    assert not m.touching


def test_track_id_increments_across_strokes():
    m = make_machine(down_threshold=0.2, up_threshold=0.4, down_frames=1, up_frames=1)
    down1 = m.step(sample(0.1), 0.0)
    up1 = m.step(sample(0.5), 0.01)
    down2 = m.step(sample(0.1), 0.02)
    assert down1.track_id == up1.track_id
    assert down2.track_id == down1.track_id + 1
