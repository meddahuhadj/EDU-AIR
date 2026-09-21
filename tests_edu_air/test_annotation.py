"""AirAnnotation: stroke lifecycle, tools, erase, clear and undo."""

from __future__ import annotations

import pytest

from edu_air.annotation import (
    AnnotationModel, TOOL_DRAW, TOOL_HIGHLIGHT, TOOL_POINT, TOOL_ERASE,
)
from edu_air.config import AnnotationSettings


def make_model(**kw) -> AnnotationModel:
    s = AnnotationSettings()
    for k, v in kw.items():
        setattr(s, k, v)
    return AnnotationModel(s)


def test_draw_stroke_lifecycle():
    m = make_model(default_tool=TOOL_DRAW)
    m.set_tool(TOOL_DRAW)
    s = m.begin((0.1, 0.1))
    assert s is not None and m.drawing
    m.move((0.2, 0.2))
    m.move((0.3, 0.3))
    m.finish()
    assert not m.drawing
    assert m.count == 1
    assert len(m.strokes[0].points) == 3
    assert all(0 <= x <= 1 and 0 <= y <= 1 for x, y in m.strokes[0].points)


def test_highlight_tool_honours_highlight_flag():
    m = make_model(default_tool=TOOL_HIGHLIGHT)
    m.set_tool(TOOL_HIGHLIGHT)
    s = m.begin((0.5, 0.5))
    m.finish()
    assert m.strokes[0].highlight
    assert m.strokes[0].width > 3


def test_point_drops_single_point_stroke():
    m = make_model(default_tool=TOOL_POINT)
    m.set_tool(TOOL_POINT)
    s = m.dot((0.25, 0.25))
    assert s is not None
    assert m.count == 1
    assert m.strokes[0].tool == TOOL_POINT


def test_erase_removes_only_touching_stroke():
    m = make_model(default_tool=TOOL_DRAW)
    m.set_tool(TOOL_DRAW)
    m.begin((0.1, 0.1))
    m.finish()
    m.set_tool(TOOL_DRAW)
    m.begin((0.8, 0.8))
    m.finish()
    assert m.count == 2
    m.set_tool(TOOL_ERASE)
    removed = m.erase_at((0.1, 0.1), radius_norm=0.1)
    assert removed == 1
    assert m.count == 1
    assert m.strokes[0].points[0] == pytest.approx((0.8, 0.8))


def test_clear_and_undo():
    m = make_model(default_tool=TOOL_DRAW)
    m.set_tool(TOOL_DRAW)
    m.begin((0.1, 0.1))
    m.finish()
    m.set_tool(TOOL_DRAW)
    m.begin((0.2, 0.2))
    m.finish()
    assert m.count == 2
    popped = m.undo()
    assert popped is not None and m.count == 1
    assert m.clear() == 1
    assert m.count == 0


def test_max_strokes_trim():
    m = make_model(default_tool=TOOL_DRAW, max_strokes=3)
    m.set_tool(TOOL_DRAW)
    for i in range(10):
        m.begin((i / 10.0, 0.5))
        m.finish()
    assert m.count == 3


def test_geometry_returns_pixel_data():
    m = make_model(default_tool=TOOL_DRAW)
    m.set_tool(TOOL_DRAW)
    m.begin((0.1, 0.1))
    m.move((0.2, 0.2))
    m.finish()
    geo = m.geometry(1280, 720)
    assert len(geo) == 1
    assert geo[0]["points"] == [(128, 72), (256, 144)]
    assert geo[0]["color"].startswith("#")
    assert geo[0]["width"] > 0


def test_move_in_point_tool_is_noop():
    m = make_model(default_tool=TOOL_POINT)
    m.set_tool(TOOL_POINT)
    s = m.move((0.5, 0.5))
    assert s is None
    assert not m.drawing
    assert m.count == 0


# ---- shape correction ("ink to shape", see edu_air.shape_recognition) -----
def _draw_noisy_circle(m, cx=0.5, cy=0.5, r=0.15, n=60):
    """Draws with whatever tool is already selected on ``m`` -- callers
    that want to test a specific tool set it themselves first."""
    import math
    import random
    rng = random.Random(7)
    m.begin((cx + r, cy))
    for i in range(1, n + 1):
        a = 2 * math.pi * i / n
        m.move((cx + r * math.cos(a) + rng.uniform(-0.01, 0.01),
               cy + r * math.sin(a) + rng.uniform(-0.01, 0.01)))
    m.finish()


def test_a_hand_drawn_circle_is_cleaned_up_on_finish():
    m = make_model(default_tool=TOOL_DRAW, shape_correction=True)
    _draw_noisy_circle(m)
    assert m.count == 1
    assert len(m.strokes[0].points) > 10  # replaced by a redrawn circle polygon


def test_shape_correction_can_be_turned_off():
    m = make_model(default_tool=TOOL_DRAW, shape_correction=False)
    _draw_noisy_circle(m)
    assert m.count == 1
    assert len(m.strokes[0].points) == 61  # left exactly as drawn (60 moves + begin)


def test_shape_correction_never_touches_the_highlighter():
    """The highlighter is meant to underline/emphasize existing content,
    not become a shape -- only the draw tool gets "ink to shape"."""
    m = make_model(default_tool=TOOL_HIGHLIGHT, shape_correction=True)
    m.set_tool(TOOL_HIGHLIGHT)
    _draw_noisy_circle(m)
    assert m.count == 1
    assert len(m.strokes[0].points) == 61


def test_a_genuine_freeform_stroke_keeps_its_original_points():
    m = make_model(default_tool=TOOL_DRAW, shape_correction=True)
    m.set_tool(TOOL_DRAW)
    m.begin((0.1, 0.1))
    m.move((0.15, 0.4))
    m.move((0.4, 0.2))
    m.move((0.6, 0.6))
    m.finish()
    assert m.strokes[0].points == [(0.1, 0.1), (0.15, 0.4), (0.4, 0.2), (0.6, 0.6)]


def test_cleaned_shape_keeps_the_strokes_color_and_width():
    m = make_model(default_tool=TOOL_DRAW, shape_correction=True, draw_color="#00ff00", draw_width=5)
    _draw_noisy_circle(m)
    assert m.strokes[0].color == "#00ff00"
    assert m.strokes[0].width == 5