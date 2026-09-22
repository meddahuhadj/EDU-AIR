"""Unit tests for EDU-AIR practical ergonomics additions.

Covers:
- Dwell clicking & progress computation
- Rest zone detection
- Sensitivity & smoothing presets
- 1-point recenter offset
- Auto-profile window title detection
"""

import time
import pytest
from edu_air.pointer import InteractivePointer
from edu_air.intent import AutoProfileManager
from edu_air.classroom import ClassroomSession, DemoBackend


def test_pointer_presets():
    p = InteractivePointer(1000, 1000)
    assert p.active_preset == "normal"

    p.apply_preset("smooth")
    assert p.active_preset == "smooth"
    assert p.settings.smoothing == 0.25

    p.apply_preset("fast")
    assert p.active_preset == "fast"
    assert p.settings.smoothing == 0.80


def test_rest_zone_pause():
    p = InteractivePointer(1000, 1000)
    p.rest_zone_enabled = True
    p.update((0.5, 0.5))
    assert not p.in_rest_zone
    pos_active = p.position

    # Hand lowered near bottom edge (y > 0.88)
    p.update((0.5, 0.95))
    assert p.in_rest_zone
    # Position should be held at previous position to avoid jump or stray clicks
    assert p.position == pos_active


def test_recenter_offset():
    p = InteractivePointer(1000, 1000)
    p.update((0.3, 0.3))
    curr_pos = p.position
    assert curr_pos is not None

    # Recenter to center of screen (500, 500)
    p.recenter_offset()
    # Next sample at the same raw position should be offset towards center
    p.update((0.3, 0.3))
    new_pos = p.position
    assert new_pos is not None
    assert abs(new_pos[0] - 500.0) < abs(curr_pos[0] - 500.0) or abs(new_pos[0] - 500.0) < 50.0


def test_dwell_clicking():
    clicks = []
    p = InteractivePointer(1000, 1000)
    p.dwell_enabled = True
    p.dwell_delay = 0.05  # fast for testing
    p.on_dwell_click = lambda pos: clicks.append(pos)

    # First update sets anchor
    p.update((0.5, 0.5))
    assert p.dwell_progress == 0.0
    assert len(clicks) == 0

    # Wait for dwell delay
    time.sleep(0.07)
    p.update((0.5, 0.5))
    assert p.dwell_progress >= 1.0
    assert len(clicks) == 1


def test_auto_profile_manager():
    mgr = AutoProfileManager(enabled=True)
    assert mgr.detect_profile("Presentation.pptx - PowerPoint") == "presentation"
    assert mgr.detect_profile("Document1.pdf - Adobe Acrobat Reader") == "presentation"
    assert mgr.detect_profile("Summer Playlist - Spotify") == "media"
    assert mgr.detect_profile("Awesome Video - YouTube - Google Chrome") in ("media", "web")
    assert mgr.detect_profile("Untitled - Paint") == "annotation"
    assert mgr.detect_profile("Classroom Whiteboard") == "annotation"
    assert mgr.detect_profile("Wikipedia - Mozilla Firefox") == "web"
    assert mgr.detect_profile("Random Tool") == "general"


def test_classroom_session_dwell_and_profile():
    session = ClassroomSession(backend=DemoBackend())
    session.pointer.dwell_delay = 0.02
    session.update_pointer((0.5, 0.5))
    time.sleep(0.04)
    session.update_pointer((0.5, 0.5))

    # Verify dwell click was logged
    interactions = [item[1] for item in session.interaction_log]
    assert "DWELL_CLICK" in interactions
