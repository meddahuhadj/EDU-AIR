"""ContactStateMachine -- the anti-flicker core of the wall mode.

A single webcam cannot measure depth, so every backend can only report a
noisy, continuous "how close to the surface" metric per frame
(``TouchSample.contact_metric``, 0 = touching .. 1 = hovering). Turning that
noisy signal into a clean DOWN/MOVE/UP stream needs hysteresis: two
different thresholds for "went down" and "came up", each confirmed over a
few consecutive frames, so a value hovering right at the boundary does not
toggle the pen every other frame::

    1.0 |                      HOVER
        |    up_threshold  ----------------  crossing this (sustained) -> UP
        |
        |         dead band (no state change here)
        |
        |    down_threshold ----------------  crossing this (sustained) -> DOWN
    0.0 |                      TOUCH

This class is backend-agnostic: it only ever sees ``TouchSample``.
"""

from __future__ import annotations

from typing import Optional

from .backends.base import TouchSample
from .events import TouchEvent, TouchState


class ContactStateMachine:
    def __init__(self, settings):
        self.settings = settings
        self._touching = False
        self._below_count = 0
        self._above_count = 0
        self._lost_count = 0
        self._track_id = 0
        self._last_xy: Optional[tuple[float, float]] = None
        self._last_tool = "finger"

    def reset(self) -> None:
        self._touching = False
        self._below_count = 0
        self._above_count = 0
        self._lost_count = 0
        self._last_xy = None

    def step(self, sample: Optional[TouchSample], now: float) -> Optional[TouchEvent]:
        s = self.settings

        if sample is None or sample.confidence < s.min_confidence:
            return self._on_missing_sample()

        self._lost_count = 0
        self._last_xy = (sample.x_cam_norm, sample.y_cam_norm)
        self._last_tool = sample.tool_id

        below = sample.contact_metric <= s.down_threshold
        above = sample.contact_metric >= s.up_threshold

        if not self._touching:
            self._below_count = self._below_count + 1 if below else 0
            if self._below_count < s.down_frames:
                return None
            self._touching = True
            self._below_count = 0
            return TouchEvent(x=sample.x_cam_norm, y=sample.y_cam_norm, state=TouchState.DOWN,
                              confidence=sample.confidence, tool_id=sample.tool_id,
                              track_id=self._track_id, gap=sample.contact_metric)

        self._above_count = self._above_count + 1 if above else 0
        if self._above_count >= s.up_frames:
            self._touching = False
            self._above_count = 0
            ev = TouchEvent(x=sample.x_cam_norm, y=sample.y_cam_norm, state=TouchState.UP,
                            confidence=sample.confidence, tool_id=sample.tool_id,
                            track_id=self._track_id, gap=sample.contact_metric)
            self._track_id += 1
            return ev

        return TouchEvent(x=sample.x_cam_norm, y=sample.y_cam_norm, state=TouchState.MOVE,
                          confidence=sample.confidence, tool_id=sample.tool_id,
                          track_id=self._track_id, gap=sample.contact_metric)

    def _on_missing_sample(self) -> Optional[TouchEvent]:
        """No usable sample this frame (hand left the frame, tracking lost,
        low confidence). A stroke in progress must still be lifted after a
        short grace window instead of hanging forever with the pen "down"."""
        self._below_count = 0
        if not self._touching:
            return None
        self._lost_count += 1
        if self._lost_count < self.settings.lost_frames_up or self._last_xy is None:
            return None
        self._touching = False
        self._lost_count = 0
        x, y = self._last_xy
        ev = TouchEvent(x=x, y=y, state=TouchState.UP, confidence=0.0,
                        tool_id=self._last_tool, track_id=self._track_id, gap=1.0)
        self._track_id += 1
        return ev

    @property
    def touching(self) -> bool:
        return self._touching
