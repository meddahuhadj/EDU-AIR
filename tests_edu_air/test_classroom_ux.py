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


def test_offline_voice_settings_round_trip_through_json(tmp_path):
    """offline_voice/vosk_model_path (see edu_air.config.resolve_vosk_model_path)
    persist through the same Settings.save()/load() JSON path as every other
    classroom preference -- same shape as test_touch_settings.py's
    test_settings_load_restores_touch_block."""
    from edu_air.config import Settings

    settings = Settings()
    settings.classroom.offline_voice = True
    settings.classroom.vosk_model_path = "C:/models/vosk-fr"
    path = tmp_path / "config.json"
    settings.save(path)

    restored = Settings()
    restored.load(path)
    assert restored.classroom.offline_voice is True
    assert restored.classroom.vosk_model_path == "C:/models/vosk-fr"


def test_offline_voice_settings_default_when_loading_an_old_config_file(tmp_path):
    """A config.json saved before this feature existed has no offline_voice/
    vosk_model_path keys at all -- loading it must not crash and must fall
    back to the safe defaults (voice stays on Google, no local model)."""
    from edu_air.config import Settings

    path = tmp_path / "config.json"
    path.write_text('{"classroom": {"language": "fr"}}', encoding="utf-8")

    settings = Settings()
    settings.load(path)
    assert settings.classroom.language == "fr"
    assert settings.classroom.offline_voice is False
    assert settings.classroom.vosk_model_path == ""


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


# ---- camera watchdog -------------------------------------------------------------
def test_camera_fallback_marks_honest_env_and_logs_once():
    from edu_air.ui import ClassroomPipeline

    class FakeSession:
        mode = "real"

        def __init__(self):
            self.env_calls = []

        def set_environment(self, **kw):
            self.env_calls.append(kw)

    pipe = ClassroomPipeline(FakeSession())
    emitted = []
    pipe.log_line.connect(emitted.append)
    assert pipe._camera_fallback is False
    sess = pipe.session
    pipe._fallback_from_camera()
    pipe._fallback_from_camera()          # second call is a no-op
    assert pipe._camera_fallback is True
    assert sess.env_calls == [{"hand_visible": False}]
    assert emitted == ["Camera unavailable — synthetic pointer mode. "
                       "Close other apps using the webcam and restart."]


def test_camera_reader_survives_a_hung_read():
    """Regression: cam.read() has no timeout, and some Windows camera
    drivers can block on it forever under contention. That used to run
    straight in the pipeline's main loop, so one stuck read silently froze
    gesture handling, voice routing and the classroom clock together while
    the window kept answering Windows' ping from its own thread — looking
    "responsive" while doing nothing. _CameraReader isolates the blocking
    call so ``latest()`` can report staleness instead of hanging."""
    import threading
    import time
    from edu_air.ui import _CameraReader

    hang = threading.Event()  # never set -> read() blocks like a stuck driver

    class HangingCam:
        def read(self):
            hang.wait()
            return True, "frame-after-hang"

    reader = _CameraReader(HangingCam())
    try:
        # The reader thread is stuck inside read(); no frame has landed yet.
        frame, age = reader.latest()
        assert frame is None
        assert age == float("inf")
        time.sleep(0.1)
        frame, age = reader.latest()
        assert frame is None, "a hung driver must not fabricate a frame"
    finally:
        hang.set()
        reader.stop()


def test_camera_reader_reports_fresh_frames():
    from edu_air.ui import _CameraReader

    class FakeCam:
        def read(self):
            return True, "frame"

    reader = _CameraReader(FakeCam())
    try:
        for _ in range(50):
            frame, age = reader.latest()
            if frame is not None:
                break
        assert frame == "frame"
        assert age < 1.0
    finally:
        reader.stop()


def test_camera_backend_prefers_directshow_on_windows():
    from edu_air.ui import _camera_backend

    class FakeCV:
        CAP_ANY = 0
        CAP_DSHOW = 700

    class FakeLegacyCV:
        CAP_ANY = 0

    assert _camera_backend(FakeCV) == 700        # win32 -> DirectShow
    assert _camera_backend(FakeLegacyCV) == 0    # no DSHOW -> CAP_ANY


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