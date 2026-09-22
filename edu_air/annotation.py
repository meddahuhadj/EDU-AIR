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
    shape_type: str | None = None  # None, "circle", "rectangle", "line", "arrow"

    def pixel_points(self, w: int, h: int) -> list:
        return [(x * w, y * h) for x, y in self.points]


def default_stroke(tool: str, settings: AnnotationSettings) -> Stroke:
    if tool == TOOL_HIGHLIGHT:
        return Stroke(tool=tool, color=settings.highlight_color,
                      width=settings.highlight_width, highlight=True)
    if tool in (TOOL_DRAW, TOOL_SHAPE):
        return Stroke(tool=tool, color=settings.draw_color, width=settings.draw_width)
    if tool == TOOL_POINT:
        return Stroke(tool=TOOL_POINT, color=settings.draw_color,
                      width=settings.draw_width)
    return Stroke(tool=TOOL_NONE)


def fit_shape(stroke: Stroke) -> Stroke:
    """Classify and fit a raw stroke into a clean geometric shape
    (circle, rectangle, or straight line). Returns a new fitted Stroke.
    """
    pts = stroke.points
    if len(pts) < 5:
        return stroke

    import math

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w_box = max_x - min_x
    h_box = max_y - min_y

    start = pts[0]
    end = pts[-1]
    dist_start_end = math.hypot(end[0] - start[0], end[1] - start[1])
    diag_box = math.hypot(w_box, h_box)

    # Closed loop check: start and end are close relative to bounding box
    if diag_box > 0.04 and dist_start_end < 0.4 * diag_box:
        aspect = w_box / h_box if h_box > 0 else 1.0
        # Circle / Ellipse
        if 0.6 <= aspect <= 1.6:
            cx = (min_x + max_x) / 2.0
            cy = (min_y + max_y) / 2.0
            rx = w_box / 2.0
            ry = h_box / 2.0
            fitted_pts = []
            num_samples = 32
            for i in range(num_samples + 1):
                angle = (2.0 * math.pi * i) / num_samples
                px = cx + rx * math.cos(angle)
                py = cy + ry * math.sin(angle)
                fitted_pts.append((px, py))
            return Stroke(
                tool=stroke.tool,
                color=stroke.color,
                width=stroke.width,
                points=fitted_pts,
                highlight=stroke.highlight,
                shape_type="circle"
            )
        else:
            # Rectangle
            fitted_pts = [
                (min_x, min_y),
                (max_x, min_y),
                (max_x, max_y),
                (min_x, max_y),
                (min_x, min_y)
            ]
            return Stroke(
                tool=stroke.tool,
                color=stroke.color,
                width=stroke.width,
                points=fitted_pts,
                highlight=stroke.highlight,
                shape_type="rectangle"
            )

    # Open line check: fit straight line between start and end
    if diag_box > 0.05:
        fitted_pts = [start, end]
        return Stroke(
            tool=stroke.tool,
            color=stroke.color,
            width=stroke.width,
            points=fitted_pts,
            highlight=stroke.highlight,
            shape_type="line"
        )

    return stroke


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
        """Start a stroke (draw/highlight/shape) or remember the dot anchor."""
        if self.tool not in (TOOL_DRAW, TOOL_HIGHLIGHT, TOOL_SHAPE):
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
            if s.tool == TOOL_SHAPE:
                s = fit_shape(s)
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

    def export_canvas(self, filepath: str, width: int = 1920, height: int = 1080,
                      bg_color: str = "#060912") -> bool:
        """Export all strokes to a high-resolution PNG image file."""
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGBA", (width, height), bg_color)
            draw = ImageDraw.Draw(img)

            for s in self.strokes:
                pxs = s.pixel_points(width, height)
                if len(pxs) < 2:
                    if len(pxs) == 1:
                        x, y = pxs[0]
                        r = s.width * 2
                        draw.ellipse([x - r, y - r, x + r, y + r], fill=s.color)
                    continue

                w_px = int(max(1.0, s.width * 2))
                if s.highlight:
                    draw.line(pxs, fill=s.color, width=w_px + 8, joint="round")
                else:
                    draw.line(pxs, fill=s.color, width=w_px, joint="round")

            img.save(filepath, "PNG")
            return True
        except Exception:
            return False

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
                "shape_type": s.shape_type,
            })
        return out