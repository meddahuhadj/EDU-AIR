"""Shared "find the shadow near a point" routine.

Used by both :class:`~edu_air.touch.backends.shadow_gap.ShadowGapFingerBackend`
(shadow relative to the bare fingertip) and
:class:`~edu_air.touch.backends.color_marker.ColorMarkerBackend` (shadow
relative to the colored marker tip) -- the pixel-level search is identical,
only the tracked point differs.
"""

from __future__ import annotations

from typing import Optional

# A fingertip's own shadow has a bounded silhouette; darkness that keeps
# going for longer than this, as a fraction of the hand/blob scale, along
# the same corridor is treated as the teacher's arm/body shadow sweeping
# through rather than a fingertip's -- see the consecutive-dark-run check
# in ``find_shadow``.
BODY_SHADOW_RUN_RATIO = 0.8


def find_shadow(gray, point_px, direction: tuple[float, float], search_len: int,
                scale_px: float, min_contrast: float, np) -> tuple[Optional[float], Optional[tuple], float]:
    """Walk a short corridor from ``point_px`` along ``direction`` looking
    for the darkest pixel, and compare it against the local background
    sampled off to the side (adaptive contrast, no fixed brightness
    constant -- robust to ambient light / projector glare).

    A candidate is rejected when the darkness keeps going for longer than a
    fingertip's own shadow plausibly could (see ``BODY_SHADOW_RUN_RATIO``)
    -- most often the teacher's arm or body shadow sweeping across the
    corridor, which must never read as contact.

    Returns (gap_px, shadow_px, contrast) -- gap_px/shadow_px are None when
    no credible, finger-sized shadow was found."""
    h, w = gray.shape[:2]
    dx, dy = direction
    mag = (dx ** 2 + dy ** 2) ** 0.5 or 1.0
    dx, dy = dx / mag, dy / mag
    step = max(1, int(scale_px * 0.06))

    samples = []
    for r in range(step, search_len, step):
        x = int(point_px[0] + dx * r)
        y = int(point_px[1] + dy * r)
        if 0 <= x < w and 0 <= y < h:
            samples.append((r, x, y, float(gray[y, x])))
    if len(samples) < 3:
        return None, None, 0.0

    perp = (-dy, dx)
    bg_samples = []
    for r in range(step, search_len, step):
        for side in (-1, 1):
            x = int(point_px[0] + perp[0] * scale_px * 0.5 * side)
            y = int(point_px[1] + perp[1] * scale_px * 0.5 * side)
            if 0 <= x < w and 0 <= y < h:
                bg_samples.append(float(gray[y, x]))
    background = float(np.median(bg_samples)) if bg_samples else float(np.median([s[3] for s in samples]))

    r_min, x_min, y_min, val_min = min(samples, key=lambda s: s[3])
    contrast = background - val_min
    if contrast < min_contrast:
        return None, None, contrast

    # How far the darkness continues past r_min, along the same corridor.
    # A compact fingertip shadow ends quickly; a body/arm shadow the
    # corridor walked into keeps going for much longer.
    dark_level = background - contrast * 0.5
    run_px = 0.0
    for r, _, _, val in samples:
        if r < r_min or val > dark_level:
            continue
        run_px = max(run_px, r - r_min)
    if run_px > scale_px * BODY_SHADOW_RUN_RATIO:
        return None, None, contrast

    return float(r_min), (float(x_min), float(y_min)), contrast
