"""Camera + gesture + voice pipeline (background thread).

``ClassroomPipeline`` reads the webcam, runs hand tracking / the gesture
engine / the wall-mode touch detector, and feeds the classroom session;
recognized voice arrives through the HADJ ``SpeechManager``. All UI-facing
updates are marshalled through Qt signals so the control dock and the
projector overlay never touch this thread's state directly.

Extracted out of ``edu_air.ui`` (still re-exported there) purely to keep
that module to a readable size; nothing about its behaviour changed.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal

from . import i18n
from .backends import DemoBackend
from .classroom import ClassroomSession


class LowFpsWatchdog:
    """Auto-enables low-CPU mode once per session after the pipeline's FPS
    stays below ``threshold`` for a sustained ``grace_s`` window -- a single
    dip does not count, and this never fires again once triggered (or once
    low-CPU mode is already on for any reason, manual or automatic), so it
    can never fight a teacher who deliberately turns it back off."""

    def __init__(self, threshold: float = 20.0, grace_s: float = 3.0, warmup_s: float = 3.0):
        self.threshold = threshold
        self.grace_s = grace_s
        self.warmup_s = warmup_s
        self._loop_started_at: Optional[float] = None
        self._low_since: Optional[float] = None
        self.triggered = False

    def observe(self, cursor_fps: float, now: float, performance_mode_on: bool) -> bool:
        """Feed the current smoothed FPS. Returns True on the one frame
        sustained-low-FPS is first confirmed (the caller should act on it
        right then -- it will never return True again)."""
        if self.triggered or performance_mode_on:
            return False
        if self._loop_started_at is None:
            self._loop_started_at = now
        if now - self._loop_started_at <= self.warmup_s:
            return False   # cursor_fps' own EMA hasn't settled yet

        if 0.5 < cursor_fps < self.threshold:
            if self._low_since is None:
                self._low_since = now
            elif now - self._low_since >= self.grace_s:
                self.triggered = True
                return True
        else:
            self._low_since = None
        return False


def _camera_backend(cv2_mod) -> int:
    """Pick the video backend: DirectShow fails fast (returns "no frame") on a
    busy/broken webcam instead of hanging forever like MSMF on Windows."""
    if os.name == "nt" and hasattr(cv2_mod, "CAP_DSHOW"):
        return cv2_mod.CAP_DSHOW
    return getattr(cv2_mod, "CAP_ANY", 0)


class _CameraReader:
    """Runs ``cam.read()`` on its own thread.

    DirectShow "fails fast" most of the time, but a contended or flaky
    webcam driver can still make ``read()`` block indefinitely (no timeout
    of its own). That used to happen inside the main pipeline loop, so one
    stuck read froze gesture handling, voice routing and the classroom
    clock together — the window kept answering Windows' ping (different
    thread), which made it look "responsive but doing nothing" instead of
    visibly crashed. Isolating the read here means a hang only ever stales
    the camera frame; the existing 4s watchdog in the pipeline loop still
    detects and recovers from that via ``_fallback_from_camera``.
    """

    def __init__(self, cam) -> None:
        self._cam = cam
        self._lock = threading.Lock()
        self._frame = None
        self._ts = 0.0
        self._running = threading.Event()
        self._running.set()
        self._thread = threading.Thread(
            target=self._loop, name="edu_air_camreader", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while self._running.is_set():
            try:
                ok, frame = self._cam.read()
            except Exception:
                ok, frame = False, None
            if ok and frame is not None:
                with self._lock:
                    self._frame = frame
                    self._ts = time.monotonic()
            else:
                time.sleep(0.01)

    def latest(self):
        """Returns ``(frame_or_None, age_seconds)``."""
        with self._lock:
            frame, ts = self._frame, self._ts
        age = (time.monotonic() - ts) if ts else float("inf")
        return frame, age

    def stop(self) -> None:
        self._running.clear()
        self._thread.join(timeout=1.0)


class ClassroomPipeline(QObject):
    frame_ready = Signal(object)
    voice_ready = Signal(str)
    log_line = Signal(str)
    camera_state = Signal(str)  # "on" | "off" | "demo"

    def __init__(self, session: ClassroomSession, parent=None):
        super().__init__(parent)
        self.session = session
        self._running = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.tracker = None
        self.gesture_engine = None
        self.touch_detector = None
        self._touch_mode_prev = getattr(session, "interaction_mode", "contactless")
        self._drift_warned = False
        self._env_quality = None
        self._last_tracked: list = []
        self._noise_closed = threading.Event()
        self._noise_thread: Optional[threading.Thread] = None
        self._preview_h = 200
        self._last_frame = None
        self._demo_fallback = session.mode == "demo"
        self._camera_fallback = False   # webcam unusable -> synthetic pointer
        self._requested_camera_index: int | None = None
        self._fingertip_capturing = False
        self._fingertip_buffer: list[tuple[float, float]] = []
        self._perf_watchdog = LowFpsWatchdog()   # auto low-CPU mode on sustained low FPS

    # ---- calibration wizard: live fingertip capture ----------------------------
    def begin_fingertip_capture(self) -> None:
        """Start buffering the raw (pre-homography) air-pointer fingertip
        position for the calibration wizard's corner/alignment steps --
        called from the UI thread while ``_loop()`` keeps running on the
        pipeline thread; see ``SurfaceTouchDetector.begin_capture`` for the
        same no-lock rationale already used elsewhere in this codebase."""
        self._fingertip_buffer = []
        self._fingertip_capturing = True

    def end_fingertip_capture(self) -> list[tuple[float, float]]:
        self._fingertip_capturing = False
        buf, self._fingertip_buffer = self._fingertip_buffer, []
        return buf

    def request_camera_index(self, index: int) -> None:
        self._requested_camera_index = index

    # ---- lifecycle ------------------------------------------------------------
    def start(self) -> None:
        if self._thread is not None:
            return
        self._running.set()
        self._thread = threading.Thread(target=self._loop, name="edu_air_pipeline",
                                        daemon=True)
        self._thread.start()
        try:
            self._start_voice()
        except Exception:
            self.log_line.emit("voice unavailable")

    def stop(self) -> None:
        self._running.clear()
        self._noise_closed.set()
        if self._noise_thread is not None:
            self._noise_thread.join(timeout=1.0)
            self._noise_thread = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _start_voice(self) -> None:
        from hadj_no_touch.voice.speech_recognition import SpeechManager
        from hadj_no_touch.config import VoiceSettings
        from .config import resolve_vosk_model_path
        cls = self.session.settings.classroom
        lang = {"en": "en-US", "fr": "fr-FR", "ar": "ar-SA",
                "nl": "nl-NL"} \
            .get(cls.language, "en-US")
        self._voice = SpeechManager(on_text=self.voice_ready.emit)
        self._voice.settings = VoiceSettings(
            language=lang,
            offline_first=cls.offline_voice,
            vosk_model_path=resolve_vosk_model_path(cls.language, cls.vosk_model_path),
        )
        engine = self._voice.create()
        if engine is not None:
            self._voice.start()
            self.log_line.emit(i18n.t("voice.engine", name=engine.name))
        else:
            self.log_line.emit(i18n.t("voice.unavailable"))

        if self._demo_fallback:
            self.session.set_environment(lighting="good", ambient_noise="ok",
                                         hand_visible=True)
        else:
            self._noise_thread = threading.Thread(
                target=self._noise_loop, name="edu_air_noise", daemon=True)
            self._noise_thread.start()

    def _noise_loop(self) -> None:
        """Background ambient-noise meter -> classroom traffic light.

        Backs off when the microphone is busy (e.g. the speech recogniser
        holds it) so the two consumers never fight over the device."""
        from .voice import NoiseProbe
        probe = NoiseProbe()
        state = "unknown"
        misses = 0
        period = 2.0
        while not self._noise_closed.wait(period):
            try:
                v = probe.read(0.4)
            except Exception:
                v = "unknown"
            if v == "unknown":
                misses += 1
                period = 6.0 if misses >= 2 else 2.0
                continue
            misses = 0
            period = 2.0
            state = v
            try:
                self.session.set_environment(ambient_noise=state)
            except Exception:
                pass

    def _fallback_from_camera(self) -> None:
        """Camera open/read watchdog: drop the webcam, keep the class going
        with synthetic pointers and honest "unknown" environment states."""
        if self._camera_fallback:
            return
        self._camera_fallback = True
        try:
            self.camera_state.emit("off")
        except Exception:
            pass
        try:
            self.session.set_environment(hand_visible=False)
        except Exception:
            pass
        self.log_line.emit(
            "Camera unavailable — synthetic pointer mode. "
            "Close other apps using the webcam and restart.")

    # ---- main loop --------------------------------------------------------------
    def _loop(self) -> None:
        try:
            import cv2
        except Exception:
            cv2 = None
        from hadj_no_touch.performance import EnvironmentQuality
        from hadj_no_touch.vision.hand_tracking import HandTracker
        from hadj_no_touch.gestures import gesture_engine as ge
        self._env_quality = EnvironmentQuality()

        cam = None
        cap_w, cap_h = self.session.settings.classroom.capture_size()
        if not self._demo_fallback and cv2 is not None:
            try:
                from hadj_no_touch.camera.camera_config import resolve_camera, apply_exposure
                cam_idx, backend = resolve_camera(preferred=0, max_index=4)
                if cam_idx >= 0:
                    backend_arg = backend if backend is not None else _camera_backend(cv2)
                    cam = cv2.VideoCapture(cam_idx, backend_arg)
                    if cam.isOpened():
                        cam.set(cv2.CAP_PROP_FRAME_WIDTH, cap_w)
                        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, cap_h)
                        apply_exposure(cam)
                        ok_test, test_frame = cam.read()
                        if not ok_test or test_frame is None or test_frame.size == 0:
                            # Re-open at native resolution if resolution change broke output
                            cam.release()
                            cam = cv2.VideoCapture(cam_idx, backend_arg)
                            apply_exposure(cam)
            except Exception:
                try:
                    if cam is not None:
                        cam.release()
                except Exception:
                    pass
                cam = None

            if (cam is None or not cam.isOpened()) and cv2 is not None:
                try:
                    cam = cv2.VideoCapture(0, _camera_backend(cv2))
                    if cam.isOpened():
                        cam.set(cv2.CAP_PROP_FRAME_WIDTH, cap_w)
                        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, cap_h)
                except Exception:
                    try:
                        if cam is not None:
                            cam.release()
                    except Exception:
                        pass
                    cam = None

        if self._demo_fallback:
            self.camera_state.emit("demo")
        else:
            self.camera_state.emit(
                "on" if cam is not None and cam.isOpened() else "off")

        self.tracker = HandTracker()
        self.gesture_engine = ge.GestureEngine()
        from .touch import SurfaceTouchDetector, build_backend
        self.touch_detector = SurfaceTouchDetector(
            build_backend(self.session.settings.touch.backend), self.session.settings.touch)
        self.touch_detector.set_calibration(self.session.pointer.mapping)
        self.touch_detector.load_plane_calibration(
            (self.session.settings.calibration or {}).get("touch_plane", {}))

        # cam.read() itself has no timeout, and some Windows camera drivers
        # (DirectShow included, under contention) can stall on it forever.
        # Isolate the read on its own thread so a stuck driver only ever
        # stales the frame instead of freezing gestures/voice/the classroom
        # clock — see _CameraReader.
        reader = _CameraReader(cam) if cam is not None else None

        cursor_fps = 0.0
        t0 = time.monotonic()
        frame_idx = 0
        tracked: list = []
        camera_dead_at: float | None = None
        while self._running.is_set():
            now = time.monotonic()
            dt = now - t0
            t0 = now
            if dt > 0.001:
                cursor_fps = cursor_fps * 0.9 + (1.0 / dt) * 0.1
            frame_idx += 1
            every = self.session.settings.classroom.tracking_interval()

            real_hands: list = []
            if reader is not None:
                frame, age = reader.latest()
                if frame is not None and age < 4.0:
                    camera_dead_at = None
                    self._last_frame = frame
                    if frame_idx % every == 0:
                        tracked = self.tracker.detect(frame, cap_w, cap_h)
                        env = self._env_quality.estimate(frame)
                        if env is not None:
                            self.session.set_environment(lighting=env.lighting)
                    real_hands = list(tracked)
                    debug = (self.touch_detector.last_debug
                            if (self.touch_detector is not None
                                and self.session.settings.touch.debug_visual
                                and self.session.interaction_mode == "wall") else None)
                    self._emit_preview(frame, debug)
                else:
                    if camera_dead_at is None:
                        camera_dead_at = now
                    elif now - camera_dead_at >= 4.0:
                        self._fallback_from_camera()
                        reader.stop()
                        reader = None
                        if cam is not None:
                            cam.release()
                        cam = None
            elif self._demo_fallback:
                real_hands = self._synthetic_hands(now)

            hands = real_hands
            if self._demo_fallback or not hands:
                if not hands:
                    hands = self._synthetic_hands(now)
            self.session.set_environment(
                hand_visible=bool(real_hands) or self._demo_fallback)

            pointer_norm = None
            if hands:
                tip = hands[0].landmarks_norm[8]
                pointer_norm = (float(tip[0]), float(tip[1]))
            self.session.update_pointer(pointer_norm)

            if self._fingertip_capturing and self._last_frame is not None and real_hands:
                # Genuine camera-tracked fingertip only. Despite its name,
                # ``real_hands`` in demo mode holds the *synthetic* demo
                # hand once no reader is attached (see above) -- gating on
                # ``self._last_frame`` too (only ever set from a live
                # reader frame) is what actually keeps a synthetic hand
                # from silently "calibrating" against nothing.
                real_tip = real_hands[0].landmarks_norm[8]
                self._fingertip_buffer.append((float(real_tip[0]), float(real_tip[1])))

            events = self.gesture_engine.update(hands, None, cap_w, cap_h)
            for ev in events:
                log = self.log_line
                try:
                    self.session.handle_gesture(ev)
                except Exception:
                    pass

            if self.session.interaction_mode != self._touch_mode_prev:
                # Mode just toggled: drop any stale stroke/hysteresis state
                # instead of leaving a stroke hanging DOWN forever.
                self.touch_detector.reset()
                if self._touch_mode_prev == "wall":
                    self.session.annotation.finish()
                    if self._drift_warned:
                        self._drift_warned = False
                        self.session.set_calibration_drift(False)
                self._touch_mode_prev = self.session.interaction_mode

            if self.session.interaction_mode == "wall" and self._last_frame is not None:
                # Called even with an empty hand list (tracking briefly lost)
                # so ContactStateMachine's own lost-frame grace period can
                # still tick and force-lift a stroke instead of leaving it
                # hanging DOWN until the hand happens to reappear.
                try:
                    touch_events = self.touch_detector.update(
                        self._last_frame, real_hands, cap_w, cap_h)
                    for tev in touch_events:
                        self.session.handle_touch_event(tev)
                    palm_pos = self.touch_detector.update_palm_erase(
                        self._last_frame, real_hands, cap_w, cap_h)
                    if palm_pos is not None:
                        self.session.handle_palm_wipe(palm_pos)
                    drift_now = self.touch_detector.drift.drift_suspected
                    if drift_now != self._drift_warned:
                        self._drift_warned = drift_now
                        self.session.set_calibration_drift(drift_now)
                        if drift_now:
                            self.log_line.emit(
                                "Wall-mode calibration looks off (touches landing outside "
                                "the board) — recalibrate when you get a chance.")
                except Exception:
                    pass

            self.session._fps = cursor_fps
            self.session.tick(dt)
            if dt >= 0.5:
                self.log_line.emit(f"fps {cursor_fps:.1f} hands {len(hands)}")

            if self._perf_watchdog.observe(
                    cursor_fps, now, self.session.settings.classroom.performance_mode):
                self.session.set_performance(True)
                self.log_line.emit(
                    f"FPS below {self._perf_watchdog.threshold:.0f} for "
                    f"{self._perf_watchdog.grace_s:.0f}s — switched to low-CPU mode "
                    "automatically (lighter tracking cadence). Turn it back off "
                    "in Réglages if you'd rather keep full quality.")

            # keep the loop gentle on CPU: ~30 fps (or ~15 in performance mode)
            time.sleep(0.033 if every == 1 else 0.066)

        if reader is not None:
            reader.stop()
        if cam is not None:
            cam.release()
        self.tracker.close()

    def _synthetic_hands(self, now: float):
        from .demo import synthetic_hand, moving_point
        import math
        t = now
        g = "point"
        if self.session.quiz.active and int(t) % 6 == 0:
            g = "palm"
        pos = moving_point(t)
        return [synthetic_hand(g, pos)]

    def _emit_preview(self, frame, touch_debug: dict | None = None) -> None:
        try:
            import cv2
            if touch_debug:
                frame = frame.copy()
                self._draw_touch_debug(cv2, frame, touch_debug)
            h0, w0 = frame.shape[:2]
            scale = self._preview_h / h0
            small = cv2.resize(frame, (int(w0 * scale), self._preview_h))
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            self.frame_ready.emit(rgb)
        except Exception:
            pass

    @staticmethod
    def _draw_touch_debug(cv2, frame, debug: dict) -> None:
        """Wall-mode tuning aid: fingertip, shadow, measured gap and the
        current contact/hover state, drawn straight onto the teacher-facing
        camera preview (never onto the projector overlay the class sees)."""
        touching = bool(debug.get("touching"))
        color = (60, 220, 60) if touching else (60, 170, 255)
        tip_px = debug.get("tip_px") or debug.get("blob_px")
        if tip_px is not None:
            p = (int(tip_px[0]), int(tip_px[1]))
            cv2.circle(frame, p, 8, color, 2)
        shadow_px = debug.get("shadow_px")
        if tip_px is not None and shadow_px is not None:
            s = (int(shadow_px[0]), int(shadow_px[1]))
            cv2.line(frame, p, s, (0, 165, 255), 1)
            cv2.circle(frame, s, 5, (0, 165, 255), 1)
        label_parts = ["TOUCH" if touching else "HOVER"]
        gap_px = debug.get("gap_px")
        if gap_px is not None:
            label_parts.append(f"gap={gap_px:.0f}px")
        metric = debug.get("contact_metric")
        if metric is not None:
            label_parts.append(f"metric={metric:.2f}")
        origin = (int(tip_px[0]) + 12, int(tip_px[1]) - 12) if tip_px is not None else (10, 20)
        cv2.putText(frame, " ".join(label_parts), origin,
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
