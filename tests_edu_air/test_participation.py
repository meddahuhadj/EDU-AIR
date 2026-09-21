"""ParticipationTracker: a manual per-mark tally + CSV export, mirroring
VoiceQuiz's export shape (edu_air.quiz)."""

from __future__ import annotations

import csv

from edu_air.participation import ParticipationTracker


def test_starts_empty():
    t = ParticipationTracker()
    assert t.count == 0
    assert t.history == []


def test_mark_increments_count_and_indexes_sequentially():
    t = ParticipationTracker()
    r1 = t.mark()
    r2 = t.mark()
    r3 = t.mark()
    assert t.count == 3
    assert [r.index for r in (r1, r2, r3)] == [1, 2, 3]


def test_elapsed_s_is_relative_to_the_first_mark():
    t = ParticipationTracker()
    r1 = t.mark()
    assert r1.elapsed_s == 0.0
    r2 = t.mark()
    assert r2.elapsed_s >= 0.0


def test_reset_clears_history_and_timer():
    t = ParticipationTracker()
    t.mark()
    t.mark()
    t.reset()
    assert t.count == 0
    assert t.history == []
    r = t.mark()
    assert r.index == 1
    assert r.elapsed_s == 0.0   # timer restarted too, not just the list


def test_csv_rows_header_and_body():
    t = ParticipationTracker()
    t.mark()
    t.mark()
    rows = t.to_csv_rows()
    assert rows[0] == ["#", "Time since first mark (s)"]
    assert rows[1][0] == "1"
    assert rows[2][0] == "2"


def test_csv_rows_include_total_footer():
    t = ParticipationTracker()
    t.mark()
    t.mark()
    t.mark()
    rows = t.to_csv_rows()
    footer = {r[0]: r[1] for r in rows if len(r) == 2 and r[0] != "#"}
    assert footer["Total participations"] == "3"


def test_empty_export_still_has_a_zeroed_footer():
    t = ParticipationTracker()
    rows = t.to_csv_rows()
    footer = {r[0]: r[1] for r in rows if len(r) == 2 and r[0] != "#"}
    assert footer["Total participations"] == "0"


def test_export_csv_writes_a_real_readable_file(tmp_path):
    t = ParticipationTracker()
    t.mark()
    t.mark()
    out = tmp_path / "participation.csv"
    written = t.export_csv(out)
    assert written == out
    assert out.exists()
    with out.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0][0] == "#"
    assert rows[1][0] == "1"
    assert rows[2][0] == "2"
