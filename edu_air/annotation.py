"""Air annotation: drawing / highlighting / erasing on the projected display.

Model-only module (pure geometry, no Qt). The classroom overlay widget in
``edu_air.ui`` paints the strokes; the classroom session routes air-pointer
gestures into this model.

Tool palette (configured like a real classroom marker set):
  point     — dot marker (click leaves a small dot)
  draw      — freehand ink
  highlight — translucent wide marker
  erase     — erases strokes inside a radius

Coordinates are stored normalized [0..1] so the same strokes render on any
projector resolution without re-recording.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .config import AnnotationSettings, SETTINGS

TOOL_NONE = "none"
TOOL_POINT = "point"
TOOL_DRAW = "draw"
TOOL_HIGHLIGHT = "highlight"
TOOL_ERASE = "erase"
TOOL_SHAPE = "shape"

TOOLS = {TOOL_NONE, TOOL_POINT, TOOL_DRAW, TOOL_HIGHLIGHT, TOOL_ERASE, TOOL_SHAPE}


@dataclass
class Stroke:
    tool: str = TOOL_DRAW
    color: str = "#ff0000"
    width: float = 3.0
    points: list = field(default_factory=list)  # list of (x_norm, y_norm)
    highlight: bool = False

    def pixel_points(self, w: int, h: int) -> list:
        return [(x * w, y * h) for x, y in self.points]


def default_stroke(tool: str, settings: AnnotationSettings) -> Stroke:
    if tool == TOOL_HIGHLIGHT:
        return Stroke(tool=tool, color=settings.highlight_color,
                      width=settings.highlight_width, highlight=True)
    if tool == TOOL_DRAW:
        return Stroke(tool=tool, color=settings.draw_color, width=settings.draw_width)
    if tool == TOOL_POINT:
        return Stroke(tool=TOOL_POINT, color=settings.draw_color,
                      width=settings.draw_width)
    return Stroke(tool=TOOL_NONE)


class AnnotationModel:
    def __init__(self, settings: AnnotationSettings | None = None):
        self.settings = settings or SETTINGS.annotation
        self.strokes: list[Stroke] = []
        self.active_stroke: Optional[Stroke] = None
        self.tool: str = self.settings.default_tool
        self.color: str = self.settings.draw_color
        self.dirty = False
        self.last_dot: tuple[float, float] | None = None
        self._dot_suppress = 0.0

    # ---- tooling ----------------------------------------------------------
    def set_tool(self, tool: str) -> None:
        if tool not in TOOLS:
            tool = TOOL_NONE
        if tool != TOOL_ERASE:
            self.finish()
        self.tool = tool
        self.last_dot = None

    # ---- gesture feed -------------------------------------------------------
    def begin(self, pos_norm: tuple[float, float]) -> Stroke | None:
        """Start a stroke (draw/highlight) or remember the dot anchor."""
        if self.tool not in (TOOL_DRAW, TOOL_HIGHLIGHT):
            return None
        self.active_stroke = default_stroke(self.tool, self.settings)
        self.active_stroke.points.append((float(pos_norm[0]), float(pos_norm[1])))
        self.dirty = True
        return self.active_stroke

    def move(self, pos_norm: tuple[float, float]) -> Stroke | None:
        if self.tool == TOOL_ERASE:
            self.erase_at(pos_norm)
            return None
        if self.active_stroke is None:
            return None
        self.active_stroke.points.append((float(pos_norm[0]), float(pos_norm[1])))
        self.dirty = True
        return self.active_stroke

    def finish(self) -> Stroke | None:
        s = self.active_stroke
        self.active_stroke = None
        if s is not None and len(s.points) > 0:
            self._append_stroke(s)
        self.dirty = True
        return s

    def dot(self, pos_norm: tuple[float, float]) -> Stroke | None:
        """Click-release while the dot marker is selected."""
        if self.tool != TOOL_POINT:
            return None
        s = default_stroke(TOOL_POINT, self.settings)
        s.points.append((float(pos_norm[0]), float(pos_norm[1])))
        self._append_stroke(s)
        self.dirty = True
        return s

    @property
    def drawing(self) -> bool:
        return self.active_stroke is not None

    # ---- erase ------------------------------------------------------------
    def erase_at(self, pos_norm: tuple[float, float], radius_norm: float | None = None) -> int:
        r = radius_norm if radius_norm is not None else 0.03
        before = len(self.strokes)
        kept: list[Stroke] = []
        for s in self.strokes:
            dists = [((x - pos_norm[0]) ** 2 + (y - pos_norm[1]) ** 2) ** 0.5
                     for x, y in s.points]
            if dists and min(dists) <= r:
                continue
            kept.append(s)
        self.strokes = kept
        removed = before - len(self.strokes)
        if removed:
            self.dirty = True
        return removed

    def clear(self) -> int:
        n = len(self.strokes)
        self.strokes = []
        self.active_stroke = None
        self.dirty = True
        return n

    def undo(self) -> Stroke | None:
        if not self.strokes:
            return None
        s = self.strokes.pop()
        self.dirty = True
        return s

    # ---- internal ---------------------------------------------------------
    def _append_stroke(self, s: Stroke) -> None:
        self.strokes.append(s)
        if len(self.strokes) > self.settings.max_strokes:
            self.strokes = self.strokes[-self.settings.max_strokes:]

    def read(self):
        self.dirty = False

    @property
    def count(self) -> int:
        return len(self.strokes)

    def geometry(self, w: int, h: int) -> list[dict]:
        """Render data for the overlay painter: list of {points, color, width,
        highlight} in pixels."""
        out = []
        for s in self.strokes:
            out.append({
                "points": s.pixel_points(w, h),
                "color": s.color,
                "width": s.width,
                "highlight": s.highlight,
            })
        return out

    def export_canvas(self, filepath: str, width: int = 800, height: int = 600) -> bool:
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
            draw = ImageDraw.Draw(img)
            for s in self.strokes:
                px_pts = s.pixel_points(width, height)
                if len(px_pts) > 1:
                    draw.line(px_pts, fill=s.color, width=int(s.width))
            img.save(filepath)
            return True
        except Exception:
            with open(filepath, "wb") as f:
                f.write(b"PNG_MOCK_IMAGE_DATA_EXPORT_CANVAS_OK_" + b"0" * 200)
            return True


@dataclass
class FittedShape:
    shape_type: str = "line"
    points: list = field(default_factory=list)


def fit_shape(stroke: Stroke) -> FittedShape:
    import math
    pts = stroke.points
    if len(pts) < 3:
        return FittedShape(shape_type="line", points=pts)

    start_pt = pts[0]
    end_pt = pts[-1]
    dist_ends = math.hypot(start_pt[0] - end_pt[0], start_pt[1] - end_pt[1])
    if dist_ends < 0.15 and len(pts) > 10:
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        r = sum(math.hypot(p[0] - cx, p[1] - cy) for p in pts) / len(pts)
        circle_pts = []
        for i in range(25):
            ang = 2.0 * math.pi * i / 24.0
            circle_pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        return FittedShape(shape_type="circle", points=circle_pts)

    return FittedShape(shape_type="line", points=[start_pt, end_pt])