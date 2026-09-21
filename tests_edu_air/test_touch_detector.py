"""SurfaceTouchDetector: calibration mapping, smoothing and the
enabled/backend-swap plumbing -- backend-agnostic, driven by a fake
backend so these tests do not need a camera or MediaPipe."""

from __future__ import annotations

import pytest

from edu_air.config import TouchSettings
from edu_air.touch.backends.base import SurfaceTouchBackend, TouchSample
from edu_air.touch.detector import SurfaceTouchDetector
from edu_air.touch.events import TouchState


class ScriptedBackend(SurfaceTouchBackend):
    name = "scripted"

    def __init__(self, script: list):
        self.script = list(script)
        self.settings = None
        self.reset_calls = 0
        self.loaded_plane: dict = {}

    def configure(self, settings) -> None:
        self.settings = settings

    def process_frame(self, bgr_frame, hands, frame_w, frame_h, now):
        return self.script.pop(0) if self.script else None

    def reset(self) -> None:
        self.reset_calls += 1

    def load_plane_calibration(self, data: dict) -> None:
        self.loaded_plane = data or {}


def sample(x, y, metric, confidence=1.0):
    return TouchSample(x_cam_norm=x, y_cam_norm=y, contact_metric=metric, confidence=confidence)


def make_detector(script, **kw):
    settings = TouchSettings()
    settings.enabled = True
    settings.down_threshold, settings.up_threshold = 0.2, 0.4
    settings.down_frames, settings.up_frames = 1, 1
    settings.predict_one_frame = False
    for k, v in kw.items():
        setattr(settings, k, v)
    backend = ScriptedBackend(script)
    return SurfaceTouchDetector(backend, settings), backend


def test_disabled_detector_returns_nothing():
    det, _ = make_detector([sample(0.5, 0.5, 0.1)], enabled=False)
    assert det.update(None, [], 100, 100) == []


def test_no_mapping_passes_camera_coords_through():
    det, _ = make_detector([sample(0.3, 0.7, 0.1)])
    events = det.update(None, [], 100, 100)
    assert len(events) == 1
    assert events[0].state == TouchState.DOWN
    assert events[0].x == pytest.approx(0.3, abs=0.05)
    assert events[0].y == pytest.approx(0.7, abs=0.05)


def test_calibration_mapping_is_applied():
    det, _ = make_detector([sample(0.5, 0.5, 0.1)])
    det.set_calibration(lambda xy: (xy[0] * 0.5, xy[1] * 0.5))
    events = det.update(None, [], 100, 100)
    assert events[0].x == pytest.approx(0.25, abs=0.05)
    assert events[0].y == pytest.approx(0.25, abs=0.05)


def test_move_smooths_toward_target_over_frames(monkeypatch):
    # OneEuroFilter's alpha is dt-driven, so convergence needs realistic
    # frame spacing -- fake a steady 30fps clock instead of relying on
    # however fast the test loop itself happens to run.
    clock = {"t": 0.0}

    def fake_monotonic():
        clock["t"] += 1.0 / 30.0
        return clock["t"]

    monkeypatch.setattr("edu_air.touch.detector.time.monotonic", fake_monotonic)

    script = [sample(0.1, 0.1, 0.1)] + [sample(0.9, 0.9, 0.1) for _ in range(200)]
    det, _ = make_detector(script, smoothing_min_cutoff=1.0, smoothing_beta=0.0)
    last = None
    for _ in range(201):
        evs = det.update(None, [], 100, 100)
        if evs:
            last = evs[0]
    assert last is not None
    assert last.x == pytest.approx(0.9, abs=0.05)
    assert last.y == pytest.approx(0.9, abs=0.05)


def test_up_keeps_last_smoothed_position():
    script = [sample(0.5, 0.5, 0.1), sample(0.5, 0.5, 0.1), sample(0.9, 0.9, 0.9)]
    det, _ = make_detector(script)
    d1 = det.update(None, [], 100, 100)[0]   # DOWN
    d2 = det.update(None, [], 100, 100)[0]   # MOVE
    up = det.update(None, [], 100, 100)[0]   # UP -> should not jump to (0.9, 0.9)
    assert up.state == TouchState.UP
    assert up.x == pytest.approx(d2.x, abs=1e-6)
    assert up.y == pytest.approx(d2.y, abs=1e-6)


def test_reset_clears_backend_and_smoother():
    det, backend = make_detector([sample(0.5, 0.5, 0.1)])
    det.update(None, [], 100, 100)
    det.reset()
    assert backend.reset_calls == 1


def test_set_backend_reconfigures_and_resets():
    det, backend = make_detector([sample(0.5, 0.5, 0.1)])
    new_backend = ScriptedBackend([sample(0.2, 0.2, 0.1)])
    det.set_backend(new_backend)
    assert new_backend.settings is det.settings
    assert det.backend is new_backend


def test_capture_buffers_raw_samples_for_the_touch_plane_wizard():
    """begin_capture()/end_capture() feed the "plan tactile" step: every
    raw sample the backend produces while capturing is collected, hover
    included -- unlike TouchEvent, which only fires on state changes."""
    script = [sample(0.5, 0.5, 0.9), sample(0.5, 0.5, 0.9), sample(0.5, 0.5, 0.9)]
    det, _ = make_detector(script)
    det.begin_capture()
    for _ in range(3):
        det.update(None, [], 100, 100)
    captured = det.end_capture()
    assert len(captured) == 3
    assert all(s.contact_metric == pytest.approx(0.9) for s in captured)


def test_capture_stops_when_ended():
    script = [sample(0.5, 0.5, 0.9)] * 5
    det, _ = make_detector(script)
    det.begin_capture()
    det.update(None, [], 100, 100)
    det.end_capture()
    det.update(None, [], 100, 100)   # after end_capture -- must not be buffered
    assert det.end_capture() == []


def test_capture_skips_frames_with_no_sample():
    script = [sample(0.5, 0.5, 0.9), None, sample(0.5, 0.5, 0.9)]
    det, backend = make_detector([])
    backend.script = script
    det.begin_capture()
    for _ in range(3):
        det.update(None, [], 100, 100)
    assert len(det.end_capture()) == 2


def test_switching_backend_then_reloading_plane_restores_calibration():
    """Mirrors ClassroomWindow._change_touch_backend: set_backend() alone
    starts the new backend blank -- the caller must re-push the persisted
    touch-plane baseline right after, or a teacher who calibrated and then
    merely previews a different backend loses that work even coming straight
    back to the backend they calibrated."""
    det, backend = make_detector([sample(0.5, 0.5, 0.1)])
    learned_plane = {"grid": 3, "zones": {"0,0": {"dir": [0.0, 1.0], "gap_bias": 4.0, "n": 5}}}
    det.load_plane_calibration(learned_plane)
    assert backend.loaded_plane == learned_plane

    new_backend = ScriptedBackend([sample(0.2, 0.2, 0.1)])
    det.set_backend(new_backend)
    assert new_backend.loaded_plane == {}   # blank until reloaded, as set_backend leaves it

    det.load_plane_calibration(learned_plane)
    assert new_backend.loaded_plane == learned_plane


def test_drift_monitor_observes_the_unclamped_mapped_position():
    """A homography that consistently pushes touches outside the board
    must be visible on detector.drift, using the *pre-clamp* mapped
    position -- not the [0,1]-clamped event.x/y the ink pipeline sees."""
    script = [sample(0.5, 0.5, 0.1) for _ in range(20)]
    det, _ = make_detector(script, down_frames=1, up_frames=1,
                           down_threshold=0.6, up_threshold=0.9)
    det.set_calibration(lambda xy: (xy[0] + 1.0, xy[1]))  # always far out of bounds
    for _ in range(20):
        det.update(None, [], 100, 100)
    assert det.drift.drift_suspected


def test_set_calibration_resets_drift_flag():
    script = [sample(0.5, 0.5, 0.1) for _ in range(20)]
    det, _ = make_detector(script, down_frames=1, up_frames=1,
                           down_threshold=0.6, up_threshold=0.9)
    det.set_calibration(lambda xy: (xy[0] + 1.0, xy[1]))
    for _ in range(20):
        det.update(None, [], 100, 100)
    assert det.drift.drift_suspected
    det.set_calibration(lambda xy: xy)   # recalibrating clears the flag
    assert not det.drift.drift_suspected
