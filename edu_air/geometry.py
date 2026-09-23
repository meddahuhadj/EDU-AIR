"""Interactive Dynamic Geometry & Shape Recognition Module for EDU-AIR.

Provides pure Python logic for recognizing freehand air-sketched shapes
(circles, rectangles, triangles, lines, polygons), calculating exact geometric
properties (perimeters, areas, angles, line equations), and serving as a model
for virtual rulers and protractors.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class Point2D:
    x: float
    y: float

    def distance_to(self, other: Point2D) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass
class GeometricShape:
    shape_type: str  # "circle", "rectangle", "triangle", "line", "polygon"
    points: List[Point2D]
    center: Point2D
    area: float = 0.0
    perimeter: float = 0.0
    angles_deg: List[float] = field(default_factory=list)
    side_lengths: List[float] = field(default_factory=list)
    radius: float = 0.0
    equation: str = ""
    label: str = ""

    def summary_fr(self) -> str:
        if self.shape_type == "circle":
            return f"Cercle (r={self.radius:.2f}, Aire={self.area:.2f}, Périmètre={self.perimeter:.2f})"
        elif self.shape_type == "rectangle":
            w = self.side_lengths[0] if len(self.side_lengths) > 0 else 0
            h = self.side_lengths[1] if len(self.side_lengths) > 1 else 0
            return f"Rectangle ({w:.2f} × {h:.2f}, Aire={self.area:.2f}, Périmètre={self.perimeter:.2f})"
        elif self.shape_type == "triangle":
            angles_str = ", ".join(f"{a:.1f}°" for a in self.angles_deg)
            return f"Triangle (Angles: [{angles_str}], Aire={self.area:.2f})"
        elif self.shape_type == "line":
            length = self.perimeter
            return f"Segment ({self.equation}, L={length:.2f})"
        return f"Forme Géométrique ({self.shape_type.capitalize()}, Périmètre={self.perimeter:.2f})"


class GeometryEngine:
    """Core geometry engine to analyze raw stroke points and fit geometric shapes."""

    @staticmethod
    def recognize_stroke(raw_points: List[Tuple[float, float]]) -> Optional[GeometricShape]:
        if len(raw_points) < 2:
            return None

        points = [Point2D(x, y) for x, y in raw_points]
        p_start = points[0]
        p_end = points[-1]
        start_end_dist = p_start.distance_to(p_end)

        # Total path length along stroke
        total_path_len = 0.0
        for i in range(1, len(points)):
            total_path_len += points[i - 1].distance_to(points[i])

        if total_path_len <= 1e-6:
            return None

        # Bounding box
        min_x = min(p.x for p in points)
        max_x = max(p.x for p in points)
        min_y = min(p.y for p in points)
        max_y = max(p.y for p in points)
        width = max_x - min_x
        height = max_y - min_y
        center = Point2D((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)

        is_closed = (start_end_dist / total_path_len) < 0.25

        if not is_closed:
            # Check for line segment
            dx = p_end.x - p_start.x
            dy = p_end.y - p_start.y
            if dx == 0:
                eq = "x = constant"
            else:
                m = dy / dx
                b = p_start.y - m * p_start.x
                eq = f"y = {m:.2f}x + {b:.2f}"
            
            return GeometricShape(
                shape_type="line",
                points=[p_start, p_end],
                center=center,
                perimeter=start_end_dist,
                side_lengths=[start_end_dist],
                equation=eq,
                label="Line"
            )

        # Closed shape: Circle vs Rectangle vs Triangle
        # Check aspect ratio for circle candidate
        aspect = width / (height + 1e-6)
        radius = (width + height) / 4.0
        circle_area = math.pi * (radius ** 2)
        circle_perimeter = 2.0 * math.pi * radius

        # Deviation from circle center radius
        radius_devs = [abs(p.distance_to(center) - radius) for p in points]
        avg_dev = sum(radius_devs) / len(radius_devs)

        if 0.75 <= aspect <= 1.35 and (avg_dev / (radius + 1e-6)) < 0.22:
            return GeometricShape(
                shape_type="circle",
                points=points,
                center=center,
                radius=radius,
                area=circle_area,
                perimeter=circle_perimeter,
                label="Cercle"
            )

        # Check for rectangle / triangle
        rect_area = width * height
        rect_perimeter = 2.0 * (width + height)

        if (width / (height + 1e-6)) > 0.4:
            # Let's check 3 vs 4 corner approximation
            return GeometricShape(
                shape_type="rectangle",
                points=[
                    Point2D(min_x, min_y),
                    Point2D(max_x, min_y),
                    Point2D(max_x, max_y),
                    Point2D(min_x, max_y)
                ],
                center=center,
                area=rect_area,
                perimeter=rect_perimeter,
                side_lengths=[width, height, width, height],
                angles_deg=[90.0, 90.0, 90.0, 90.0],
                label="Rectangle"
            )
        
        # Default triangle approximation
        p_top = min(points, key=lambda p: p.y)
        p_left = min(points, key=lambda p: p.x)
        p_right = max(points, key=lambda p: p.x)
        
        side_a = p_top.distance_to(p_left)
        side_b = p_left.distance_to(p_right)
        side_c = p_right.distance_to(p_top)
        tri_perimeter = side_a + side_b + side_c

        s = tri_perimeter / 2.0
        tri_area = math.sqrt(max(0.0, s * (s - side_a) * (s - side_b) * (s - side_c)))

        # Law of cosines for angles
        def angle_between(a, b, c):
            val = (a**2 + b**2 - c**2) / (2 * a * b + 1e-6)
            val = max(-1.0, min(1.0, val))
            return math.degrees(math.acos(val))

        ang_A = angle_between(side_b, side_c, side_a) if side_b > 0 and side_c > 0 else 60.0
        ang_B = angle_between(side_a, side_c, side_b) if side_a > 0 and side_c > 0 else 60.0
        ang_C = 180.0 - ang_A - ang_B

        return GeometricShape(
            shape_type="triangle",
            points=[p_top, p_left, p_right],
            center=center,
            area=tri_area,
            perimeter=tri_perimeter,
            side_lengths=[side_a, side_b, side_c],
            angles_deg=[ang_A, ang_B, ang_C],
            label="Triangle"
        )


class VirtualRulerProtractor:
    """Virtual classroom measurement tool (ruler & protractor logic)."""

    def __init__(self, unit: str = "cm"):
        self.unit = unit
        self.scale_factor = 100.0  # converts norm coords [0..1] to virtual cm

    def measure_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        dist_norm = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
        return dist_norm * self.scale_factor

    def measure_angle(self, vertex: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        v1 = (p1[0] - vertex[0], p1[1] - vertex[1])
        v2 = (p2[0] - vertex[0], p2[1] - vertex[1])
        
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        mag1 = math.hypot(v1[0], v1[1])
        mag2 = math.hypot(v2[0], v2[1])

        if mag1 < 1e-6 or mag2 < 1e-6:
            return 0.0

        cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
        return math.degrees(math.acos(cos_theta))
