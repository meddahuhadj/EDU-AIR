"""UX-classroom desktop improvements: performance preset round-trips,
external whiteboard-app presets + launch guarding, environment traffic-light
status carry-over, camera/detection pacing, estimated calibration corners,
NoiseProbe fallback and the new i18n catalogue."""

from __future__ import annotations

import pytest

import edu_air.i18n as i18n
import edu_air.presentation as presentation_mod
from edu_air.calibration import (ProjectorCalibration, STAGE_CORNERS,
                                 STATUS_SKIPPED)
from edu_air.classroom import ClassroomSession, RecordingBackend
from edu_air.config import (EXTERNAL_APP_OPTIONS, PROJECTOR_PRESETS,
                            ClassroomSettings, PresentationSettings)
from edu_air.presentation import PresentationController, RecordingDriver
from edu_air.voice import NoiseProbe


# ---- config round-trip ------------------------------------------------------
def test_classroom_performance_settings_round_trip(tmp_path):
    settings = ClassroomSettings()
    settings.performance_mode = True
    assert settings.capture_size() == (320, 240)
    assert settings.tracking_interval() == 2
    settings.performance_mode = False
    assert settings.capture_size() == (640, 480)
    assert settings.tracking_interval() == 1
    body = settings.asdict() if hasattr(settings, "asdict") else settings.__dict__
    restored = ClassroomSettings(**body)
    assert restored.performance_mode is False
    assert restored.camera_width == 640


def test_classroom_ux_catalog_choices():
    assert "1920x1080" in PROJECTOR_PRESETS
    assert "1280x800" in PROJECTOR_PRESETS
    assert "1024x768" in PROJECTOR_PRESETS
    assert set(EXTERNAL_APP_OPTIONS) == {"none", "openboard", "xournalpp"}
    assert ClassroomSettings().calibration_resolution in PROJECTOR_PRESETS


def test_presentation_settings_external_app_defaults():
    s = PresentationSettings()
    assert s.external_app == "none"
    assert s.launch_command == ""


# ---- external whiteboard app presets -----------------------------------------
def test_apply_external_app_merges_keymap():
    ctl, _ = make_ctl()
    ctl.apply_external_app("openboard")
    assert ctl.settings.external_app == "openboard"
    assert ctl.settings.keymap.get("start") == "F2"
    assert ctl.settings.keymap.get("stop") == "ESC"
    ctl.apply_external_app("xournalpp")
    assert ctl.settings.keymap.get("start") == "F5"
    assert "CTRL" in ctl.settings.keymap.get("zoom_in_mods")


def test_start_sends_preset_key_and_launch_suppressed_in_demo():
    ctl, driver = make_ctl()
    ctl.apply_external_app("openboard")
    ctl.suppress_launch = True
    r = ctl.start()
    assert driver.key_sequence == ["F2"]
    assert "suppressed" in r.note


def test_launch_popen_is_invoked_when_allowed(monkeypatch):
    calls: list[list[str]] = []

    class FakePopen:
        def __init__(self, cmd, *a, **k):
            calls.append(cmd)

    ctl, _ = make_ctl()
    ctl.settings.external_app = "openboard"
    ctl.settings.launch_command = ""
    monkeypatch.setattr(presentation_mod.subprocess, "Popen", FakePopen)
    ctl.suppress_launch = False
    ctl.start()
    assert any("openboard" in str(c) for c in calls)


def test_unknown_external_app_is_noop():
    ctl, driver = make_ctl()
    before = dict(ctl.settings.keymap)
    ctl.apply_external_app("no-such-app")
    assert ctl.settings.keymap == before
    assert driver.key_sequence == []


def make_ctl() -> "tuple[PresentationController, RecordingDriver]":
    ctl = PresentationController(driver=RecordingDriver(),
                                 settings=PresentationSettings())
    return ctl, ctl.driver


# ---- environment status -------------------------------------------------------
def test_set_environment_persists_through_snapshot():
    sess, _ = make_session()
    sess.set_environment(lighting="low", ambient_noise="loud",
                         hand_visible=True)
    st = sess.status
    assert st.lighting == "low"
    assert st.ambient_noise == "loud"
    assert st.hand_visible is True
    sess.tick(0.5)
    st = sess.status  # snapshot rebuilt every tick
    assert st.lighting == "low"
    assert st.ambient_noise == "loud"
    assert st.hand_visible is True


def test_set_performance_updates_settings_and_status():
    sess, _ = make_session()
    sess.set_performance(True)
    assert sess.settings.classroom.performance_mode is True
    assert sess.status.performance_mode is True
    sess.set_performance(False)
    assert sess.status.performance_mode is False


def test_demo_session_keeps_healthy_env():
    sess, _ = make_session("demo")
    assert sess.presentation.suppress_launch is True
    sess.set_environment(lighting="good", ambient_noise="ok", hand_visible=True)
    assert sess.status.lighting == "good"


def make_session(mode: str = "demo") -> "tuple[ClassroomSession, RecordingBackend]":
    backend = RecordingBackend()
    pres = PresentationController(driver=RecordingDriver(),
                                  settings=PresentationSettings())
    sess = ClassroomSession(backend=backend, presentation=pres)
    sess.set_mode(mode)
    return sess, backend


# ---- estimated calibration ------------------------------------------------------
def test_estimate_corners_builds_mapping_and_marks_estimated():
    cal = ProjectorCalibration()
    st = cal.estimate_corners("1280x800")
    assert len(cal.corners_camera) == 4
    assert cal.report.mapping is not None
    assert st.status == STATUS_SKIPPED
    assert STAGE_CORNERS in cal.report.estimated
    assert cal.settings.calibration.get("resolution") == "1280x800"
    mapped = cal.report.mapping((0.5, 0.5))
    assert 0.0 <= mapped[0] <= 1.0 and 0.0 <= mapped[1] <= 1.0


def test_estimate_then_complete_still_reports_calibrated():
    cal = ProjectorCalibration()
    cal.step_camera(True)
    cal.step_projection(True)
    cal.estimate_corners("1920x1080")
    cal.finish_alignment(1)
    cal.observe_gesture("point")
    cal.observe_gesture("pinch")
    cal.observe_gesture("swipe")
    cal.observe_gesture("palm")
    cal.finish_gestures()
    report = cal.complete()
    assert report.calibrated is True
    assert report.stage_ok(STAGE_CORNERS) is True  # estimated counts as ok


# ---- NoiseProbe ----------------------------------------------------------------
def test_noise_probe_degrades_to_unknown():
    probe = NoiseProbe()
    verdict = probe.read(duration=0.05)
    assert verdict in ("ok", "loud", "unknown")


# ---- i18n ----------------------------------------------------------------------
def test_new_ux_keys_exist_in_all_languages():
    keys = [
        "status.lighting", "status.noise", "status.hand",
        "env.dark", "env.low", "env.good", "env.bright",
        "env.ok", "env.loud", "hand.seen", "hand.lost",
        "label.performance", "label.external_app",
        "extapp.none", "extapp.openboard", "extapp.xournalpp",
    ]
    for key in keys:
        entry = i18n.STRINGS.get(key, {})
        assert set(entry) >= {"en", "fr", "ar", "nl"}, f"missing lang for {key}"
        for lang in ("en", "fr", "ar", "nl"):
            assert entry[lang].strip(), f"empty {key}[{lang}]"
        assert i18n.t(key) != f"{key}", f"fallback exposed for {key}"