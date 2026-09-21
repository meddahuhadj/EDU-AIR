"""shape_recognition.recognize_and_clean(): "ink to shape" for the draw
tool -- conservative circle/rectangle detection that must never touch
genuine freehand drawing (scribbles, handwriting, an intentional ellipse
or triangle, an unclosed curve)."""

from __future__ import annotations

import math
import random

import pytest

from edu_air.shape_recognition import MAX_POINTS, MIN_POINTS, recognize_and_clean


def synth_circle(cx, cy, r, n=60, noise=0.01, rng=random):
    pts = []
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        pts.append((cx + r * math.cos(a) + rng.uniform(-noise, noise),
                    cy + r * math.sin(a) + rng.uniform(-noise, noise)))
    return pts


def synth_ellipse(cx, cy, rx, ry, n=60, noise=0.01, rng=random):
    pts = []
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        pts.append((cx + rx * math.cos(a) + rng.uniform(-noise, noise),
                    cy + ry * math.sin(a) + rng.uniform(-noise, noise)))
    return pts


def synth_rect(x0, y0, x1, y1, per_side=15, noise=0.01, rng=random):
    pts = []
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    for i in range(4):
        a, b = corners[i], corners[i + 1]
        for t in range(per_side):
            f = t / per_side
            pts.append((a[0] + (b[0] - a[0]) * f + rng.uniform(-noise, noise),
                        a[1] + (b[1] - a[1]) * f + rng.uniform(-noise, noise)))
    pts.append(corners[0])
    return pts


def synth_rotated_square(cx, cy, half, deg, per_side=15, noise=0.01, rng=random):
    ang = math.radians(deg)
    base = [(-half, -half), (half, -half), (half, half), (-half, half), (-half, -half)]
    corners = [(cx + x * math.cos(ang) - y * math.sin(ang),
               cy + x * math.sin(ang) + y * math.cos(ang)) for x, y in base]
    pts = []
    for i in range(4):
        a, b = corners[i], corners[i + 1]
        for t in range(per_side):
            f = t / per_side
            pts.append((a[0] + (b[0] - a[0]) * f + rng.uniform(-noise, noise),
                        a[1] + (b[1] - a[1]) * f + rng.uniform(-noise, noise)))
    pts.append(corners[0])
    return pts


def synth_triangle(p1, p2, p3, per_side=15, noise=0.01, rng=random):
    pts = []
    corners = [p1, p2, p3, p1]
    for i in range(3):
        a, b = corners[i], corners[i + 1]
        for t in range(per_side):
            f = t / per_side
            pts.append((a[0] + (b[0] - a[0]) * f + rng.uniform(-noise, noise),
                        a[1] + (b[1] - a[1]) * f + rng.uniform(-noise, noise)))
    pts.append(corners[0])
    return pts


def synth_scribble(n=40, rng=random):
    pts = [(0.5, 0.5)]
    for _ in range(n):
        pts.append((pts[-1][0] + rng.uniform(-0.03, 0.03),
                    pts[-1][1] + rng.uniform(-0.03, 0.03)))
    return pts


@pytest.fixture
def rng():
    return random.Random(1234)


def test_a_noisy_hand_drawn_circle_is_recognised(rng):
    pts = synth_circle(0.5, 0.5, 0.15, rng=rng)
    cleaned = recognize_and_clean(pts)
    assert cleaned is not None
    assert len(cleaned) > 10  # a redrawn circle, not a 4/5-point polygon


def test_a_cleaned_circle_is_actually_round():
    pts = synth_circle(0.5, 0.5, 0.15, noise=0.005)
    cleaned = recognize_and_clean(pts)
    assert cleaned is not None
    cx = sum(p[0] for p in cleaned) / len(cleaned)
    cy = sum(p[1] for p in cleaned) / len(cleaned)
    radii = [math.hypot(p[0] - cx, p[1] - cy) for p in cleaned]
    assert max(radii) - min(radii) < 0.01  # near-perfect circle, no wobble left


def test_a_noisy_hand_drawn_rectangle_is_recognised_as_a_4_corner_polygon(rng):
    pts = synth_rect(0.2, 0.2, 0.7, 0.6, rng=rng)
    cleaned = recognize_and_clean(pts)
    assert cleaned is not None
    assert len(cleaned) == 5  # 4 corners + closing point back to the first


def test_a_square_is_recognised(rng):
    pts = synth_rect(0.3, 0.3, 0.6, 0.6, rng=rng)
    cleaned = recognize_and_clean(pts)
    assert cleaned is not None
    assert len(cleaned) == 5


def test_a_rotated_square_is_still_recognised(rng):
    pts = synth_rotated_square(0.5, 0.5, 0.15, 30, rng=rng)
    cleaned = recognize_and_clean(pts)
    assert cleaned is not None
    assert len(cleaned) == 5


def test_cleaned_rectangle_corners_are_actually_right_angles(rng):
    pts = synth_rect(0.2, 0.2, 0.7, 0.5, rng=rng)
    cleaned = recognize_and_clean(pts)
    assert cleaned is not None
    corners = cleaned[:-1]
    for i in range(4):
        prev_pt, corner, next_pt = corners[i - 1], corners[i], corners[(i + 1) % 4]
        v1 = (prev_pt[0] - corner[0], prev_pt[1] - corner[1])
        v2 = (next_pt[0] - corner[0], next_pt[1] - corner[1])
        n1, n2 = math.hypot(*v1), math.hypot(*v2)
        cos_a = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
        angle = math.degrees(math.acos(max(-1.0, min(1.0, cos_a))))
        assert abs(angle - 90.0) < 5.0  # cleaned up to a real right angle


def test_a_freehand_scribble_is_never_touched(rng):
    pts = synth_scribble(rng=rng)
    assert recognize_and_clean(pts) is None


def test_a_wide_intentional_ellipse_is_left_alone(rng):
    """A 2:1 ellipse is not "close enough" to a circle -- forcing it round
    would fight the teacher's actual intent."""
    pts = synth_ellipse(0.5, 0.5, 0.25, 0.12, rng=rng)
    assert recognize_and_clean(pts) is None


def test_a_triangle_is_left_alone_not_misfit_to_a_rectangle(rng):
    pts = synth_triangle((0.3, 0.6), (0.5, 0.2), (0.7, 0.6), rng=rng)
    assert recognize_and_clean(pts) is None


def test_an_open_unclosed_curve_is_left_alone(rng):
    pts = synth_circle(0.5, 0.5, 0.15, n=60, rng=rng)[:-20]  # never comes back to the start
    assert recognize_and_clean(pts) is None


def test_a_tiny_shape_below_the_size_floor_is_left_alone(rng):
    pts = synth_circle(0.5, 0.5, 0.01, rng=rng)  # a dot-sized loop, not a deliberate circle
    assert recognize_and_clean(pts) is None


def test_too_few_points_is_left_alone():
    assert recognize_and_clean([(0.1, 0.1), (0.2, 0.2), (0.1, 0.1)]) is None
    assert len([(0.1, 0.1)] * (MIN_POINTS - 1)) < MIN_POINTS  # sanity on the fixture itself


def test_never_mutates_the_input_list(rng):
    pts = synth_circle(0.5, 0.5, 0.15, rng=rng)
    original = list(pts)
    recognize_and_clean(pts)
    assert pts == original


def test_an_extremely_long_stroke_is_skipped_not_crawled(rng):
    """RDP is worst-case O(n^2); recognize_and_clean must bail out fast on
    a pathologically long stroke instead of hanging the UI thread."""
    pts = synth_circle(0.5, 0.5, 0.15, n=MAX_POINTS + 50, rng=rng)
    assert recognize_and_clean(pts) is None
