"""Class journal: one line per class session (date, time, board pages
used, teacher notes) -- the same "pure logic, no Qt" shape as
participation.py/quiz.py's CSV export.

Kept deliberately separate from the per-session ParticipationTracker/
VoiceQuiz stats, which reset every time the app restarts: the journal is
meant to accumulate across a whole term, so it persists as JSON the same
way the whiteboard notebook does (see ``board.py``'s ``save_nb``/
``load_nb`` and ``ui.py``'s ``_restore_board``/``_persist_board`` --
``_restore_journal``/``_persist_journal`` mirror that pattern).
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class JournalEntry:
    date: str          # "YYYY-MM-DD"
    time: str           # "HH:MM"
    board_pages: int
    notes: str = ""


class ClassJournal:
    def __init__(self) -> None:
        self.entries: list[JournalEntry] = []

    def log(self, board_pages: int, notes: str = "",
            when: Optional[datetime] = None) -> JournalEntry:
        """Append one line for the class that just happened."""
        dt = when or datetime.now()
        entry = JournalEntry(date=dt.strftime("%Y-%m-%d"), time=dt.strftime("%H:%M"),
                             board_pages=max(0, int(board_pages)), notes=notes or "")
        self.entries.append(entry)
        return entry

    @property
    def count(self) -> int:
        return len(self.entries)

    # ---- CSV export (same shape as quiz.py/participation.py) -----------------
    def to_csv_rows(self) -> list[list[str]]:
        rows = [["Date", "Time", "Board pages", "Notes"]]
        for e in self.entries:
            rows.append([e.date, e.time, str(e.board_pages), e.notes])
        return rows

    def export_csv(self, path) -> Path:
        p = Path(path)
        with p.open("w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(self.to_csv_rows())
        return p

    # ---- persistence (same shape as board.py's notebook) ---------------------
    def as_dict(self) -> dict:
        return {"entries": [{"date": e.date, "time": e.time,
                             "board_pages": e.board_pages, "notes": e.notes}
                            for e in self.entries]}

    def load_dict(self, data: dict) -> None:
        data = data or {}
        entries = []
        for raw in data.get("entries") or []:
            entries.append(JournalEntry(
                date=str(raw.get("date", "")),
                time=str(raw.get("time", "")),
                board_pages=int(raw.get("board_pages", 0) or 0),
                notes=str(raw.get("notes", "")),
            ))
        self.entries = entries

    def save_json(self, path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.as_dict(), ensure_ascii=False, indent=1),
                     encoding="utf-8")
        return p

    def load_json(self, path) -> bool:
        """Restore a journal saved with :meth:`save_json`. Returns False
        when the file is missing or unreadable (the journal is then left
        untouched) -- guards the same "syntactically valid JSON, malformed
        field" crash class fixed in lesson.py/board.py earlier."""
        p = Path(path)
        if not p.is_file():
            return False
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "entries" not in data:
                return False
            self.load_dict(data)
        except (ValueError, OSError, TypeError):
            return False
        return True
