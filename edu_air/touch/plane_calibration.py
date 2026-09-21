"""Touch-plane baseline learning shared by hand-based backends.

The "plan tactile" calibration step reuses the 4 projected corners already
tapped for the homography (see ``edu_air.calibration.STAGE_TOUCH_PLANE``):
the teacher touches each corner for real, and every backend sample seen
during that touch (approach + contact) is handed to :func:`learn_zone_baselines`.

The projected surface is split into a coarse grid ("zones") because both the
shadow-gap offset and the ambient-light contrast can vary across a large
wall (uneven projector throw, side lighting) -- one global constant would
not hold everywhere. Zones with no samples simply fall back to the nearest
learned zone, then to the global default, at lookup time.
"""

from __future__ import annotations

from typing import Optional

DEFAULT_GRID = 3


def zone_key(x_norm: float, y_norm: float, grid: int = DEFAULT_GRID) -> tuple[int, int]:
    gx = min(grid - 1, max(0, int(x_norm * grid)))
    gy = min(grid - 1, max(0, int(y_norm * grid)))
    return (gx, gy)


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def learn_zone_baselines(samples: list, grid: int = DEFAULT_GRID) -> dict:
    """samples: list of ``TouchSample`` collected while the teacher tapped
    the calibration corners (any mix of hover + contact frames is fine).

    Returns a JSON-serializable dict:
        {"grid": 3, "zones": {"0,0": {"dir": [dx, dy], "gap_bias": float,
                                        "n": int}, ...}}
    """
    buckets: dict[tuple[int, int], list] = {}
    for s in samples:
        z = zone_key(s.x_cam_norm, s.y_cam_norm, grid)
        buckets.setdefault(z, []).append(s)

    zones: dict[str, dict] = {}
    for z, group in buckets.items():
        dirs = []
        gaps = []
        for s in group:
            tip_px = s.debug.get("tip_px")
            shadow_px = s.debug.get("shadow_px")
            gap_px = s.debug.get("gap_px")
            if tip_px is not None and shadow_px is not None:
                dx = shadow_px[0] - tip_px[0]
                dy = shadow_px[1] - tip_px[1]
                mag = (dx ** 2 + dy ** 2) ** 0.5
                if mag > 1e-6:
                    dirs.append((dx / mag, dy / mag))
            if gap_px is not None:
                gaps.append(float(gap_px))
        if not dirs and not gaps:
            continue
        mean_dir = (_avg([d[0] for d in dirs]), _avg([d[1] for d in dirs])) if dirs else (0.0, 1.0)
        mag = (mean_dir[0] ** 2 + mean_dir[1] ** 2) ** 0.5 or 1.0
        mean_dir = (mean_dir[0] / mag, mean_dir[1] / mag)
        # The smallest observed gap during a real touch is the closest thing
        # to "true contact" we have -- any residual offset is a systematic
        # camera/projector parallax bias to cancel out at runtime.
        gap_bias = min(gaps) if gaps else 0.0
        zones[f"{z[0]},{z[1]}"] = {
            "dir": [round(mean_dir[0], 4), round(mean_dir[1], 4)],
            "gap_bias": round(gap_bias, 2),
            "n": len(group),
        }
    return {"grid": grid, "zones": zones}


def lookup_zone(data: dict, x_norm: float, y_norm: float) -> Optional[dict]:
    if not data or not data.get("zones"):
        return None
    grid = int(data.get("grid", DEFAULT_GRID))
    z = zone_key(x_norm, y_norm, grid)
    key = f"{z[0]},{z[1]}"
    if key in data["zones"]:
        return data["zones"][key]
    # Fall back to the nearest zone that does have samples.
    best = None
    best_d = None
    for k, v in data["zones"].items():
        gx, gy = (int(p) for p in k.split(","))
        d = (gx - z[0]) ** 2 + (gy - z[1]) ** 2
        if best_d is None or d < best_d:
            best_d, best = d, v
    return best
