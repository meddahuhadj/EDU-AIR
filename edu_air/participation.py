"""Participation tally: a manual per-session log the teacher keeps while a
student answers or contributes out loud.

A single teacher-facing webcam has no way to see which student in the room
raised a hand -- that would need a second camera pointed at the class, a
fundamentally different setup than the gesture-control camera this app is
built around. What the teacher *can* do is mark the moment themselves (one
gesture/voice command/keypress) each time a student participates; this
module is the tally that produces, keeping the exact same "pure logic, no
Qt" shape and CSV export style as :mod:`edu_air.quiz`.
"""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParticipationRecord:
    index: int
    elapsed_s: float   # seconds since the tracker's first mark this session


class ParticipationTracker:
    def __init__(self) -> None:
        self.history: list[ParticipationRecord] = []
        self._started_at: float | None = None

    def reset(self) -> None:
        self.history = []
        self._started_at = None

    def mark(self) -> ParticipationRecord:
        now = time.monotonic()
        if self._started_at is None:
            self._started_at = now
        rec = ParticipationRecord(
            index=len(self.history) + 1,
            elapsed_s=round(now - self._started_at, 1),
        )
        self.history.append(rec)
        return rec

    @property
    def count(self) -> int:
        return len(self.history)

    # ---- export --------------------------------------------------------------
    def to_csv_rows(self) -> list[list[str]]:
        rows = [["#", "Time since first mark (s)"]]
        for rec in self.history:
            rows.append([str(rec.index), f"{rec.elapsed_s:.1f}"])
        rows.append([])
        rows.append(["Total participations", str(self.count)])
        return rows

    def export_csv(self, path: str | Path) -> Path:
        p = Path(path)
        with p.open("w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(self.to_csv_rows())
        return p
