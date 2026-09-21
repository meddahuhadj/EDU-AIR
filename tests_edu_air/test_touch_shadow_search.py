"""find_shadow(): the pixel-level darkest-point-vs-local-background search
shared by ShadowGapFingerBackend and ColorMarkerBackend. Exercised directly
against synthetic grayscale arrays so it needs no camera or MediaPipe."""

from __future__ import annotations

import numpy as np
import pytest

from edu_air.touch.shadow_search import find_shadow


def make_gray(w=200, h=200, background=200) -> np.ndarray:
    return np.full((h, w), background, dtype=np.uint8)


def test_finds_dark_pixel_along_the_search_direction():
    gray = make_gray(background=220)
    gray[130, 100] = 40   # a dark pixel 30px below the tip at (100, 100)
    gap_px, shadow_px, contrast = find_shadow(
        gray, (100.0, 100.0), direction=(0.0, 1.0), search_len=60,
        scale_px=50.0, min_contrast=20.0, np=np)
    assert shadow_px is not None
    assert shadow_px == pytest.approx((100.0, 130.0), abs=3.0)
    assert gap_px == pytest.approx(30.0, abs=3.0)
    assert contrast > 20.0


def test_no_shadow_when_contrast_too_low():
    gray = make_gray(background=200)
    gray[130, 100] = 190   # barely darker than background: not a real shadow
    gap_px, shadow_px, contrast = find_shadow(
        gray, (100.0, 100.0), direction=(0.0, 1.0), search_len=60,
        scale_px=50.0, min_contrast=20.0, np=np)
    assert shadow_px is None
    assert gap_px is None


def test_direction_is_normalized_regardless_of_input_magnitude():
    gray = make_gray(background=220)
    gray[100, 130] = 40   # dark pixel 30px to the right of the tip
    gap_px, shadow_px, _ = find_shadow(
        gray, (100.0, 100.0), direction=(5.0, 0.0), search_len=60,
        scale_px=50.0, min_contrast=20.0, np=np)
    assert shadow_px is not None
    assert shadow_px == pytest.approx((130.0, 100.0), abs=3.0)


def test_search_corridor_clipped_to_frame_bounds_returns_none_gracefully():
    gray = make_gray(w=20, h=20, background=220)
    gap_px, shadow_px, contrast = find_shadow(
        gray, (1.0, 1.0), direction=(0.0, -1.0), search_len=60,
        scale_px=50.0, min_contrast=20.0, np=np)
    assert shadow_px is None
    assert contrast == 0.0


def test_finger_sized_shadow_blob_is_accepted():
    """A real fingertip shadow isn't a single pixel -- a small, roughly
    finger-width dark blob must still be accepted. The corridor search
    reports the *near* edge of the blob (where it first crosses into
    shadow), not its center."""
    import cv2
    gray = make_gray(w=300, h=300, background=220)
    cv2.circle(gray, (100, 130), 6, 40, -1)
    gap_px, shadow_px, contrast = find_shadow(
        gray, (100.0, 100.0), direction=(0.0, 1.0), search_len=60,
        scale_px=50.0, min_contrast=20.0, np=np)
    assert shadow_px is not None
    assert shadow_px[1] == pytest.approx(124.0, abs=4.0)


def test_body_shadow_is_rejected_despite_high_contrast():
    """A large dark region the search corridor happens to walk into (the
    teacher's own arm/body shadow, not their fingertip's) must be rejected
    even though the contrast against the lit background next to the
    fingertip is high -- contrast alone is not enough evidence."""
    gray = make_gray(w=300, h=300, background=220)
    gray[110:300, :] = 40   # a wide dark band well below the fingertip
    gap_px, shadow_px, contrast = find_shadow(
        gray, (150.0, 100.0), direction=(0.0, 1.0), search_len=60,
        scale_px=50.0, min_contrast=20.0, np=np)
    assert shadow_px is None
    assert contrast > 20.0   # contrast alone would have accepted it
