"""ClassJournal: one line per class session + CSV export, mirroring
participation.py's shape, and JSON persistence mirroring board.py's
notebook (including the malformed-file robustness fix applied there and
in lesson.py earlier this session)."""

from __future__ import annotations

import csv
from datetime import datetime

from edu_air.journal import ClassJournal, JournalEntry


def test_starts_empty():
    j = ClassJournal()
    assert j.count == 0
    assert j.entries == []


def test_log_appends_an_entry_with_date_and_time():
    j = ClassJournal()
    when = datetime(2026, 3, 5, 9, 30)
    entry = j.log(board_pages=3, notes="Fractions", when=when)
    assert entry.date == "2026-03-05"
    assert entry.time == "09:30"
    assert entry.board_pages == 3
    assert entry.notes == "Fractions"
    assert j.count == 1


def test_log_defaults_notes_to_empty_string():
    j = ClassJournal()
    entry = j.log(board_pages=1)
    assert entry.notes == ""


def test_log_clamps_negative_page_counts_to_zero():
    j = ClassJournal()
    entry = j.log(board_pages=-5)
    assert entry.board_pages == 0


def test_multiple_logs_accumulate_in_order():
    j = ClassJournal()
    j.log(1, "A", when=datetime(2026, 1, 1))
    j.log(2, "B", when=datetime(2026, 1, 2))
    j.log(3, "C", when=datetime(2026, 1, 3))
    assert j.count == 3
    assert [e.notes for e in j.entries] == ["A", "B", "C"]


def test_csv_rows_header_and_body():
    j = ClassJournal()
    j.log(2, "First class", when=datetime(2026, 3, 5, 9, 0))
    rows = j.to_csv_rows()
    assert rows[0] == ["Date", "Time", "Board pages", "Notes"]
    assert rows[1] == ["2026-03-05", "09:00", "2", "First class"]


def test_export_csv_writes_a_real_readable_file(tmp_path):
    j = ClassJournal()
    j.log(1, "Intro", when=datetime(2026, 3, 5, 9, 0))
    j.log(2, "Follow-up", when=datetime(2026, 3, 6, 9, 0))
    out = tmp_path / "journal.csv"
    written = j.export_csv(out)
    assert written == out
    with out.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0][0] == "Date"
    assert rows[1][3] == "Intro"
    assert rows[2][3] == "Follow-up"


def test_save_and_load_json_round_trip(tmp_path):
    j = ClassJournal()
    j.log(2, "Fractions", when=datetime(2026, 3, 5, 9, 0))
    j.log(1, "Recap", when=datetime(2026, 3, 6, 10, 15))
    path = j.save_json(tmp_path / "journal.json")
    assert path.exists()

    loaded = ClassJournal()
    assert loaded.load_json(path) is True
    assert loaded.count == 2
    assert loaded.entries[0].notes == "Fractions"
    assert loaded.entries[1].time == "10:15"


def test_load_json_missing_file_returns_false_and_leaves_journal_untouched():
    j = ClassJournal()
    j.log(1, "Keep me")
    assert j.load_json("Z:/does/not/exist.json") is False
    assert j.count == 1
    assert j.entries[0].notes == "Keep me"


def test_load_json_corrupt_file_is_ignored(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    j = ClassJournal()
    j.log(1, "Keep me")
    assert j.load_json(bad) is False
    assert j.count == 1


def test_load_json_wrong_shape_is_rejected(tmp_path):
    wrong = tmp_path / "wrong.json"
    wrong.write_text('{"not_entries": []}', encoding="utf-8")
    j = ClassJournal()
    j.log(1, "Keep me")
    assert j.load_json(wrong) is False
    assert j.count == 1


def test_load_json_with_a_non_numeric_page_count_does_not_crash(tmp_path):
    """Syntactically valid JSON with a malformed field (a hand-edited
    board_pages that isn't a number) must not crash the app -- same class
    of bug fixed in board.py/lesson.py earlier this session."""
    bad = tmp_path / "typo.json"
    bad.write_text('{"entries": [{"date": "2026-01-01", "time": "09:00", '
                    '"board_pages": "many", "notes": "x"}]}', encoding="utf-8")
    j = ClassJournal()
    j.log(1, "Keep me")
    assert j.load_json(bad) is False
    assert j.count == 1
    assert j.entries[0].notes == "Keep me"
