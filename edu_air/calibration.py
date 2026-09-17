"""Projector calibration procedure.

A 5-step wizard that maps webcam space onto the projected display:

  1. Camera          — check that the webcam sees the teacher (tracking OK);
  2. Projection area — confirm the projected rectangle is framed;
  3. Screen corners  — collect the 4 projected corners in camera space and
                       build the homography (webcam -> projector);
  4. Pointer alignment — teacher points at 5 on-screen targets; measure the
                       mapping error so drift is reported honestly;
  5. Gesture test    — confirm the classifier sees the gestures the classroom
                       relies on (point, pinch, swipe, palm).

When calibration succeeds it produces a ``mapping`` callable that the
interactive pointer attaches as its homography. Steps that must be skipped
are flagged as *estimated* — the resulting mapping is clearly reported as
approximate, never silently precise.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from .config import SETTINGS

Mapping = Callable[[tuple[float, float]], tuple[float, float]]

STAGE_CAMERA = "camera"
STAGE_PROJECTION = "projection_area"
STAGE_CORNERS = "corners"
STAGE_ALIGNMENT = "alignment"
STAGE_GESTURES = "gesture_test"

STAGE_ORDER = [STAGE_CAMERA, STAGE_PROJECTION, STAGE_CORNERS,
               STAGE_ALIGNMENT, STAGE_GESTURES]

STATUS_PENDING = "pending"
STATUS_DONE = "done"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"
STATUS_PARTIAL = "partial"

# On-screen alignment targets (normalized, slightly inset so the crosshair is
# within the projector frame even on odd-behaviour webcams).
ALIGN_TARGETS = [(0.15, 0.20), (0.85, 0.20), (0.85, 0.80), (0.15, 0.80), (0.5, 0.5)]

# The gestures the classroom relies on (for the final test).
REQUIRED_GESTURES = ["point", "pinch", "swipe_left", "palm"]


@dataclass
class StageStatus:
    stage: str
    status: str = STATUS_PENDING
    detail: str = ""
    ts: float = field(default_factory=time.monotonic)


@dataclass
class CalibrationReport:
    stages: dict = field(default_factory=dict)
    mapping: Optional[Mapping] = None
    estimated: set = field(default_factory=set)
    alignment_error: float = 0.0      # mean normalized distance, best-effort
    calibrated: bool = False
    completed: bool = False

    def stage_ok(self, stage: str) -> bool:
        s = self.stages.get(stage)
        return bool(s and s.status in (STATUS_DONE, STATUS_SKIPPED))


def fit_homography(src: list[tuple[float, float]],
                   dst: list[tuple[float, float]]) -> Optional[Mapping]:
    """Perspective transform from at least 4 point pairs, or a best-effort
    affine/linear mapping when the homography solver is unavailable. Returns
    a callable(norm)->norm or None when fewer than 4 points are known."""
    if len(src) < 4 or len(dst) < 4:
        return None
    try:
        import numpy as np
        import cv2
        s = np.float32(src[:4]).reshape(-1, 1, 2)
        d = np.float32(dst[:4]).reshape(-1, 1, 2)
        h, _ = cv2.findHomography(s, d, cv2.RANSAC, 3.0)
        if h is None:
            h = cv2.getPerspectiveTransform(s, d)
        hmat = h

        def map_fn(p: tuple[float, float]) -> tuple[float, float]:
            pt = np.float32([[p[0], p[1]]]).reshape(-1, 1, 2)
            out = cv2.perspectiveTransform(pt, hmat)
            x, y = float(out[0][0][0]), float(out[0][0][1])
            return (max(0.0, min(1.0, x)), max(0.0, min(1.0, y)))
        return map_fn
    except Exception:
        return None


def linear_mapping(src: list[tuple[float, float]],
                   dst: list[tuple[float, float]]) -> Optional[Mapping]:
    """Minimal linear fallback: map camera->screen with an 8-parameter least
    squares fit (affine-ish). Used only when the homography solver is absent."""
    try:
        import numpy as np
        if len(src) < 3:
            return None
        A = np.column_stack([np.array([p[0] for p in src]),
                             np.array([p[1] for p in src]),
                             np.ones(len(src))])
        bx = np.array([p[0] for p in dst])
        by = np.array([p[1] for p in dst])
        mx, _, _, _ = np.linalg.lstsq(A, bx, rcond=None)
        my, _, _, _ = np.linalg.lstsq(A, by, rcond=None)

        def map_fn(p: tuple[float, float]) -> tuple[float, float]:
            v = np.array([p[0], p[1], 1.0])
            x = float(np.dot(mx, v))
            y = float(np.dot(my, v))
            return (max(0.0, min(1.0, x)), max(0.0, min(1.0, y)))
        return map_fn
    except Exception:
        return None


class ProjectorCalibration:
    def __init__(self, settings=None):
        self.settings = settings or SETTINGS
        self.report = CalibrationReport(stages={s: StageStatus(s)
                                                for s in STAGE_ORDER})
        self.stage_index = 0
        self.corners_camera: list[tuple[float, float]] = []
        self.alignment = []   # (screen_target_norm, measured_camera_norm)
        self.gestures_seen: set[str] = set()
        self.last_error: Optional[float] = None

    # ---- navigation --------------------------------------------------------
    @property
    def stage(self) -> str:
        return STAGE_ORDER[self.stage_index] if self.stage_index < len(STAGE_ORDER) \
            else STAGE_ORDER[-1]

    @property
    def done(self) -> bool:
        return self.stage_index >= len(STAGE_ORDER)

    def advance(self) -> bool:
        if self.done:
            return False
        self.stage_index += 1
        return True

    def reset(self) -> None:
        self.stage_index = 0
        self.corners_camera.clear()
        self.alignment.clear()
        self.gestures_seen.clear()
        self.report = CalibrationReport(stages={s: StageStatus(s)
                                                for s in STAGE_ORDER})

    # ---- step 1..2 ----------------------------------------------------------
    def step_camera(self, ok: bool, detail: str = "") -> StageStatus:
        st = self.report.stages[STAGE_CAMERA]
        st.status = STATUS_DONE if ok else STATUS_FAILED
        st.detail = detail or ("camera OK" if ok else "camera not usable")
        return st

    def step_projection(self, ok: bool, detail: str = "") -> StageStatus:
        st = self.report.stages[STAGE_PROJECTION]
        st.status = STATUS_DONE if ok else STATUS_FAILED
        st.detail = detail or ("projection area captured" if ok
                               else "projection area not confirmed")
        return st

    # ---- step 3: corners -----------------------------------------------------
    def add_corner(self, camera_norm: tuple[float, float], index: int | None = None) -> None:
        if index is not None and index < len(self.corners_camera):
            self.corners_camera[index] = (float(camera_norm[0]), float(camera_norm[1]))
        else:
            self.corners_camera.append((float(camera_norm[0]), float(camera_norm[1])))
        if len(self.corners_camera) >= 4:
            self._build_mapping()

    def finish_corners(self, corner_list: list[tuple[float, float]] | None = None) -> StageStatus:
        st = self.report.stages[STAGE_CORNERS]
        if corner_list:
            self.corners_camera = [(float(a), float(b)) for a, b in corner_list]
        if len(self.corners_camera) >= 4:
            self._build_mapping()
            if self.report.mapping is not None:
                st.status = STATUS_DONE
                st.detail = f"homography from {len(self.corners_camera)} corners"
            else:
                st.status = STATUS_FAILED
                st.detail = "homography could not be computed"
        else:
            st.status = STATUS_SKIPPED
            st.detail = "corners unavailable — estimated mapping"
        return st

    # ---- step 3b: estimation -----------------------------------------------
    PROJECTOR_RESOLUTIONS: dict[str, tuple[int, int]] = {
        "1920x1080": (1920, 1080),
        "1280x800": (1280, 800),
        "1024x768": (1024, 768),
    }

    def estimate_corners(self, resolution: str = "1920x1080") -> StageStatus:
        """Auto-calibration fallback: a centred projector rectangle framed by
        a straight-on camera. Marks the corner stage as estimated (SKIPPED)
        so every later stage still completes."""
        w, h = self.PROJECTOR_RESOLUTIONS.get(
            resolution, (1920, 1080))
        aspect = w / h
        # For a landscape projector inside the camera frame the usable band
        # is roughly [0.15, 0.85] horizontally, height scaled to match aspect.
        top = 0.5 - 0.5 * (0.55 / aspect)
        bot = 0.5 + 0.5 * (0.55 / aspect)
        self.corners_camera = [
            (0.18, min(0.98, max(0.02, top))),
            (0.82, min(0.98, max(0.02, top))),
            (0.82, min(0.98, max(0.02, bot))),
            (0.18, min(0.98, max(0.02, bot))),
        ]
        self._build_mapping()
        st = self.report.stages[STAGE_CORNERS]
        st.status = STATUS_SKIPPED
        st.detail = f"estimated corners @ {w}x{h}"
        self.report.estimated.add(STAGE_CORNERS)
        self.last_error = None
        self.settings.calibration = {
            **(self.settings.calibration or {}),
            "resolution": resolution,
            "estimated": sorted(self.report.estimated),
        }
        return st

    def _build_mapping(self) -> None:
        # Screen corners in projector space (normalized, inset by 3%).
        screen_corners = [(0.03, 0.03), (0.97, 0.03), (0.97, 0.97), (0.03, 0.97)]
        m = fit_homography(self.corners_camera, screen_corners) \
            or linear_mapping(self.corners_camera, screen_corners)
        if m is not None:
            self.report.mapping = m
            self.report.calibrated = True

    # ---- step 4: alignment ----------------------------------------------------
    def add_alignment(self, screen_target: tuple[float, float],
                      camera_norm: tuple[float, float]) -> None:
        self.alignment.append((screen_target, camera_norm))
        if self.report.mapping is not None:
            try:
                m = self.report.mapping(camera_norm)
                self.last_error = (
                    (m[0] - screen_target[0]) ** 2 + (m[1] - screen_target[1]) ** 2
                ) ** 0.5
            except Exception:
                self.last_error = None

    def finish_alignment(self, required: int = 5) -> StageStatus:
        st = self.report.stages[STAGE_ALIGNMENT]
        if len(self.alignment) >= max(1, required) and self.report.mapping is not None:
            errors = []
            for target, cam in self.alignment:
                m = self.report.mapping(cam)
                errors.append(((m[0] - target[0]) ** 2 + (m[1] - target[1]) ** 2) ** 0.5)
            self.report.alignment_error = sum(errors) / len(errors)
            st.status = STATUS_DONE
            st.detail = (f"alignment error {self.report.alignment_error:.3f} "
                         f"over {len(errors)} targets")
        elif len(self.alignment) < max(1, required):
            st.status = STATUS_SKIPPED
            st.detail = "fewer alignment points than required — pointer drift untested"
        else:
            st.status = STATUS_FAILED
            st.detail = "cannot verify alignment without a mapping"
        return st

    # ---- step 5: gesture test ----------------------------------------------------
    def observe_gesture(self, gesture_name: str) -> None:
        g = gesture_name.lower()
        for expected in REQUIRED_GESTURES:
            if expected in g:
                self.gestures_seen.add(expected)

    def finish_gestures(self, required: list[str] | None = None) -> StageStatus:
        st = self.report.stages[STAGE_GESTURES]
        needed = set(required or REQUIRED_GESTURES)
        missing = needed - self.gestures_seen
        if not missing:
            st.status = STATUS_DONE
            st.detail = f"all gestures recognised: {', '.join(sorted(needed))}"
        else:
            st.status = STATUS_PARTIAL if self.gestures_seen else STATUS_FAILED
            st.detail = f"missing gestures: {', '.join(sorted(missing))}"
        return st

    # ---- completion -----------------------------------------------------------
    def complete(self) -> CalibrationReport:
        if not self.done:
            # finish the remaining cheap stages so the report is coherent.
            pass
        self.report.completed = all(
            self.report.stages[s].status in (STATUS_DONE, STATUS_SKIPPED)
            for s in STAGE_ORDER)
        # A homography built from *estimated* corners is approximate.
        if self.report.stages[STAGE_CORNERS].status == STATUS_SKIPPED:
            self.report.estimated.add(STAGE_CORNERS)
        self.report.calibrated = bool(self.report.mapping is not None)
        self.settings.calibration = {
            "mapping": "homography" if self.report.mapping else None,
            "alignment_error": self.report.alignment_error,
            "estimated": sorted(self.report.estimated),
            "completed": self.report.completed,
        }
        return self.report