"""P2-R3 wake-word gate — tests against the REAL strip_wake_word (318),
the original, pre-existing function. My earlier duplicate def (116) has been
removed; only this one binds. Pure string gate: no engine, no audio loop,
no Qt. Tests animate the exact byte-verified contract in
voice/speech_recognition.py:318-336.
"""

import pytest

from hadj_no_touch.voice.speech_recognition import strip_wake_word


def test_empty_wake_word_is_behaviour_neutral():
    # byte-contract: empty wake word -> pass phrase through UNCHANGED.
    assert strip_wake_word("open chrome", "") == "open chrome"
    assert strip_wake_word("", "") == ""


def test_no_prefix_is_muted():
    assert strip_wake_word("open chrome", "hey hadj") is None


def test_prefix_stripped_keeps_remainder():
    assert strip_wake_word("hey hadj open chrome", "hey hadj") == "open chrome"


def test_prefix_stripped_case_insensitive():
    assert strip_wake_word("HEY HADJ open chrome", "hey hadj") == "open chrome"


def test_wake_word_alone_yields_none_muted():
    # Canonical 318 contract (byte-read): starts-with-ww + rest empty ->
    # return None (muted: nothing to forward, nothing invented).
    assert strip_wake_word("hey hadj", "hey hadj") is None
