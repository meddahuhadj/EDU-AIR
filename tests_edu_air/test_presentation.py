"""PresentationController state machine with a recording driver."""

from __future__ import annotations

import pytest

from edu_air.config import PresentationSettings
from edu_air.presentation import PresentationController, RecordingDriver


def make_presentation(total_slides: int = 10) -> "tuple[PresentationController, RecordingDriver]":
    driver = RecordingDriver()
    settings = PresentationSettings()
    settings.total_slides = total_slides
    ctl = PresentationController(driver=driver, settings=settings)
    return ctl, driver


def test_idle_commands_are_ignored():
    ctl, _ = make_presentation()
    assert ctl.state == ctl.IDLE
    r = ctl.next_slide()
    assert r.note.startswith("ignored")
    assert r.key == ""
    ctl.prev_slide()
    ctl.pause()
    assert ctl.slide_index == 0


def test_start_sends_f5_and_marks_active():
    ctl, driver = make_presentation()
    ctl.start()
    assert ctl.state == ctl.ACTIVE
    assert driver.key_sequence == ["F5"]


def test_next_prev_clamp_at_edges():
    ctl, _ = make_presentation(total_slides=3)
    ctl.start()
    ctl.prev_slide()
    assert ctl.slide_index == 0
    ctl.next_slide()
    ctl.next_slide()
    ctl.next_slide()
    assert ctl.slide_index == 2  # clamped at total_slides - 1


def test_stop_returns_to_idle():
    ctl, driver = make_presentation()
    ctl.start()
    ctl.stop()
    assert ctl.state == ctl.IDLE
    assert driver.key_sequence == ["F5", "ESC"]


def test_pause_toggles_state():
    ctl, driver = make_presentation()
    ctl.start()
    ctl.pause()
    assert ctl.state == ctl.PAUSED
    assert driver.key_sequence[-1] == "B"
    ctl.resume()
    assert ctl.state == ctl.ACTIVE


def test_zoom_sends_ctrl_plus_minus():
    ctl, driver = make_presentation()
    ctl.zoom_in()
    assert driver.keys[-1] == ("PLUS", ["CTRL"])
    ctl.zoom_out()
    assert driver.keys[-1] == ("MINUS", ["CTRL"])


def test_scroll_uses_page_keys():
    ctl, driver = make_presentation()
    ctl.scroll_down()
    assert driver.key_sequence[-1] == "PAGEDOWN"
    ctl.scroll_up()
    assert driver.key_sequence[-1] == "PAGEUP"


def test_go_to_emits_relative_advance():
    ctl, driver = make_presentation(total_slides=10)
    ctl.start()
    ctl.go_to(4)
    assert ctl.slide_index == 4
    # repeated go-to on the same slide sends no extra key
    n = len(driver.keys)
    ctl.go_to(4)
    assert len(driver.keys) == n


def test_history_and_on_record_callback():
    ctl, driver = make_presentation()
    records = []
    ctl.on_record = records.append
    ctl.start()
    ctl.next_slide()
    assert len(records) == 2
    assert records[0].command == "start"
    assert records[1].command == "next_slide"
    assert len(ctl.history) == 2