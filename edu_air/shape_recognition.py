"""Shape correction ("ink to shape") for the draw tool.

A stroke that looks like an intentional circle or rectangle is replaced
with a clean geometric redraw instead of the wobbly freehand points -- the
same idea as PowerPoint/OneNote's "Ink to Shape". Pure geometry, no Qt, so
it is exercised identically from a unit test and from the live annotation
pipeline (see ``AnnotationModel.finish()`` in ``annotation.py``).

Conservative by design: thresholds are tight enough that genuine freehand
drawing (a face, a diagram, handwriting, an intentional oval or scribble)
is essentially never touched -- only a stroke that is clearly *closed* and
clearly circle/rectangle-shaped gets cleaned up. Anything else is returned
completely unchanged (``None``), and the caller keeps the original points.
"""

from __future__ import annotations

import math
from typing import Optional

Point = tuple[float, float]

MIN_POINTS = 10
MAX_POINTS = 800                    # RDP is worst-case O(n^2); a stroke this long is not a simple shape anyway
MIN_SIZE = 0.03                     # bounding box must span at least this much (normalized)
CLOSE_GAP_RATIO = 0.28              # first/last points within this fraction of the bbox diagonal counts as "closed"
CIRCLE_CV_MAX = 0.16                # radius coefficient of variation ceiling
CIRCLE_ASPECT_RANGE = (0.55, 1.80)  # bbox width/height ratio allowed for "roughly round"
CIRCLE_POINTS = 48
RDP_EPSILON_RATIO = 0.045           # simplification tolerance, relative to the bbox diagonal
RECT_ANGLE_TOLERANCE_DEG = 28.0
RECT_MIN_SIDE_RATIO = 0.12          # reject a sliver "rectangle" where one side is near zero


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _bbox(points: list[Point]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _is_closed(points: list[Point]) -> bool:
    x0, y0, x1, y1 = _bbox(points)
    diag = math.hypot(x1 - x0, y1 - y0)
    if diag <= 1e-6:
        return False
    return _dist(points[0], points[-1]) <= CLOSE_GAP_RATIO * diag


def _fit_circle(points: list[Point]) -> Optional[list[Point]]:
    x0, y0, x1, y1 = _bbox(points)
    w, h = x1 - x0, y1 - y0
    if w <= 1e-6 or h <= 1e-6:
        return None
    aspect = w / h
    if not (CIRCLE_ASPECT_RANGE[0] <= aspect <= CIRCLE_ASPECT_RANGE[1]):
        return None
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    radii = [_dist(p, (cx, cy)) for p in points]
    mean_r = sum(radii) / len(radii)
    if mean_r <= 1e-6:
        return None
    variance = sum((r - mean_r) ** 2 for r in radii) / len(radii)
    cv = math.sqrt(variance) / mean_r
    if cv > CIRCLE_CV_MAX:
        return None
    start_angle = math.atan2(points[0][1] - cy, points[0][0] - cx)
    out = []
    for i in range(CIRCLE_POINTS + 1):
        a = start_angle + 2 * math.pi * i / CIRCLE_POINTS
        out.append((cx + mean_r * math.cos(a), cy + mean_r * math.sin(a)))
    return out


def _point_segment_distance(p: Point, a: Point, b: Point, ab: float) -> float:
    if ab <= 1e-9:
        return _dist(p, a)
    t = ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / (ab * ab)
    t = max(0.0, min(1.0, t))
    proj = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    return _dist(p, proj)


def _rdp(points: list[Point], epsilon: float) -> list[Point]:
    """Ramer-Douglas-Peucker polyline simplification (iterative -- no
    recursion-depth surprises on a long stroke)."""
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        if end <= start + 1:
            continue
        a, b = points[start], points[end]
        ab = _dist(a, b)
        best_i, best_d = -1, -1.0
        for i in range(start + 1, end):
            d = _point_segment_distance(points[i], a, b, ab)
            if d > best_d:
                best_d, best_i = d, i
        if best_d > epsilon:
            keep[best_i] = True
            stack.append((start, best_i))
            stack.append((best_i, end))
    return [p for p, k in zip(points, keep) if k]


def _angle_deg(prev_pt: Point, corner: Point, next_pt: Point) -> float:
    v1 = (prev_pt[0] - corner[0], prev_pt[1] - corner[1])
    v2 = (next_pt[0] - corner[0], next_pt[1] - corner[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 <= 1e-9 or n2 <= 1e-9:
        return 0.0
    cos_a = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
    cos_a = max(-1.0, min(1.0, cos_a))
    return math.degrees(math.acos(cos_a))


def _fit_rectangle(points: list[Point]) -> Optional[list[Point]]:
    x0, y0, x1, y1 = _bbox(points)
    diag = math.hypot(x1 - x0, y1 - y0)
    if diag <= 1e-6:
        return None
    simplified = _rdp(points, RDP_EPSILON_RATIO * diag)
    # A closed loop's RDP output repeats the (forced-kept) start point at
    # the end -- drop that duplicate before counting corners. The two
    # copies are rarely bit-identical (real freehand noise puts the first
    # and last raw samples a little apart even when the teacher meant to
    # close the shape exactly), so this uses the same relative tolerance
    # as the simplification itself rather than an exact-equality check.
    if len(simplified) > 1 and _dist(simplified[0], simplified[-1]) < RDP_EPSILON_RATIO * diag:
        corners = simplified[:-1]
    else:
        corners = simplified
    if len(corners) != 4:
        return None
    n = len(corners)
    sides = [_dist(corners[i], corners[(i + 1) % n]) for i in range(n)]
    if min(sides) < RECT_MIN_SIDE_RATIO * max(sides):
        return None
    for i in range(n):
        angle = _angle_deg(corners[(i - 1) % n], corners[i], corners[(i + 1) % n])
        if abs(angle - 90.0) > RECT_ANGLE_TOLERANCE_DEG:
            return None
    return corners + [corners[0]]


def recognize_and_clean(points: list[Point]) -> Optional[list[Point]]:
    """Try to recognize ``points`` (a just-finished freehand stroke) as a
    circle or a rectangle and, if so, return a clean redraw ready to
    replace the wobbly freehand points. Returns ``None`` (never mutates
    the input) when nothing matches -- the caller keeps the original
    stroke untouched."""
    if len(points) < MIN_POINTS or len(points) > MAX_POINTS:
        return None
    x0, y0, x1, y1 = _bbox(points)
    if max(x1 - x0, y1 - y0) < MIN_SIZE:
        return None
    if not _is_closed(points):
        return None
    # Rectangle first: its RDP simplification has a sharp, unambiguous
    # signature (exactly 4 dominant corners) that a real circle's smooth
    # curve never produces, whereas a circle's radius-variation test can
    # be lenient enough to also accept a rounded-corner rectangle -- so
    # checking rectangle first avoids that one-way misclassification.
    rectangle = _fit_rectangle(points)
    if rectangle is not None:
        return rectangle
    return _fit_circle(points)
