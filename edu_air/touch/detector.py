"""SurfaceTouchDetector -- the single entry point the UI loop talks to.

Owns everything that is common to *every* backend so backends stay tiny and
swappable: the calibration mapping (camera space -> projector space, reused
from :class:`edu_air.calibration.ProjectorCalibration`, never reinvented),
the DOWN/MOVE/UP hysteresis (:class:`~edu_air.touch.state_machine.ContactStateMachine`),
and the stroke-smoothing One-Euro filter already used by the contactless
pointer (:class:`edu_air.pointer.OneEuroFilter`).

Call once per camera frame with whatever the frame produced (the raw BGR
image and the MediaPipe hands for this frame); get back zero or one
:class:`~edu_air.touch.events.TouchEvent` already in projector-normalized
coordinates, ready to feed straight into the ink pipeline.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

from ..pointer import OneEuroFilter
from .backends.base import SurfaceTouchBackend, TouchSample
from .drift_monitor import HomographyDriftMonitor
from .events import TouchEvent, TouchState
from .palm_eraser import PalmEraseDetector
from .state_machine import ContactStateMachine

Mapping = Callable[[tuple[float, float]], tuple[float, float]]


def _clip01(v: float) -> float:
    return max(0.0, min(1.0, v))


class SurfaceTouchDetector:
    def __init__(self, backend: SurfaceTouchBackend, settings):
        self.backend = backend
        self.settings = settings
        self.backend.configure(settings)
        self._state = ContactStateMachine(settings)
        self._smoother = OneEuroFilter(min_cutoff=settings.smoothing_min_cutoff,
                                       beta=settings.smoothing_beta)
        self.mapping: Optional[Mapping] = None
        self._prev_smoothed: Optional[tuple[float, float]] = None
        self._last_debug: dict = {}
        self.drift = HomographyDriftMonitor()
        self._capturing = False
        self._capture_buffer: list[TouchSample] = []
        self._palm_eraser = PalmEraseDetector(settings)

    # ---- configuration --------------------------------------------------------
    def set_calibration(self, mapping: Optional[Mapping]) -> None:
        """Attach the same homography callable the contactless pointer
        uses (see ``ProjectorCalibration.report.mapping`` /
        ``InteractivePointer.set_calibration``). None restores identity.
        A fresh mapping clears any prior drift flag -- recalibrating IS the
        fix the monitor was asking for."""
        self.mapping = mapping
        self.drift.reset()

    def load_plane_calibration(self, data: dict) -> None:
        self.backend.load_plane_calibration(data or {})

    def set_backend(self, backend: SurfaceTouchBackend) -> None:
        self.backend = backend
        self.backend.configure(self.settings)
        self.reset()

    def reset(self) -> None:
        self._state.reset()
        self._smoother.reset()
        self.backend.reset()
        self._prev_smoothed = None
        self._last_debug = {}
        self.drift.reset()
        self._palm_eraser.reset()

    @property
    def last_debug(self) -> dict:
        """Per-frame raw debug info (tip/shadow px, gap, contrast, contact
        state) for the classroom debug overlay -- populated even on frames
        that do not produce a TouchEvent (plain hover)."""
        return self._last_debug

    # ---- touch-plane calibration capture ---------------------------------------
    def begin_capture(self) -> None:
        """Start buffering raw ``TouchSample`` frames (hover *and* contact,
        whatever the backend actually sees) for the "plan tactile" wizard
        step -- called from the UI thread while ``update()`` keeps running
        on the pipeline thread; a plain list append/swap is enough given
        this codebase's existing threading model (GIL-backed, no locks
        elsewhere around shared pipeline/detector state either)."""
        self._capture_buffer = []
        self._capturing = True

    def end_capture(self) -> list[TouchSample]:
        self._capturing = False
        buf, self._capture_buffer = self._capture_buffer, []
        return buf

    # ---- per-frame update -------------------------------------------------------
    def update(self, bgr_frame, hands: list, frame_w: int, frame_h: int) -> list[TouchEvent]:
        if not self.settings.enabled:
            return []
        now = time.monotonic()
        sample = self.backend.process_frame(bgr_frame, hands, frame_w, frame_h, now)

        if self._capturing and sample is not None:
            self._capture_buffer.append(sample)

        if sample is not None:
            debug = dict(sample.debug)
            debug["contact_metric"] = sample.contact_metric
            debug["confidence"] = sample.confidence
        else:
            debug = {}
        debug["touching"] = self._state.touching
        self._last_debug = debug

        raw = self._state.step(sample, now)
        if raw is None:
            return []
        return [self._finalize(raw, now)]

    def update_palm_erase(self, bgr_frame, hands: list, frame_w: int,
                          frame_h: int) -> Optional[tuple[float, float]]:
        """Projector-normalized position to erase at this frame if (and
        only if) an open palm is mid-wipe -- see ``PalmEraseDetector``.
        Runs independently of ``update()``'s fingertip pipeline; a frame
        can report a palm-erase position while also reporting no ink
        TouchEvent, since a palm is never a drawing candidate."""
        if not self.settings.enabled:
            return None
        pos = self._palm_eraser.update(bgr_frame, hands, frame_w, frame_h)
        if pos is None:
            return None
        if self.mapping is not None:
            try:
                pos = self.mapping(pos)
            except Exception:
                return None
        return (_clip01(pos[0]), _clip01(pos[1]))

    def _finalize(self, raw: TouchEvent, now: float) -> TouchEvent:
        x, y = raw.x, raw.y
        if self.mapping is not None:
            try:
                x, y = self.mapping((x, y))
            except Exception:
                pass
            else:
                self.drift.observe(x, y)
        x, y = _clip01(x), _clip01(y)

        if raw.state == TouchState.DOWN:
            self._smoother.reset()
            x, y = self._smoother.filter((x, y), now)
        elif raw.state == TouchState.MOVE:
            x, y = self._smoother.filter((x, y), now)
            if self.settings.predict_one_frame and self._prev_smoothed is not None:
                px, py = self._prev_smoothed
                x = _clip01(x + (x - px))
                y = _clip01(y + (y - py))
        elif self._prev_smoothed is not None:
            # UP: keep the last good smoothed position instead of
            # re-filtering a possibly-degraded release sample, so the
            # stroke does not jump right as the pen lifts.
            x, y = self._prev_smoothed

        self._prev_smoothed = (x, y)
        return TouchEvent(x=x, y=y, state=raw.state, confidence=raw.confidence,
                          tool_id=raw.tool_id, track_id=raw.track_id, gap=raw.gap, ts=now)
