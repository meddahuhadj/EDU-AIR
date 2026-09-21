"""Offline Vosk model resolution: an explicit path always wins; otherwise a
bundled models/vosk-<lang>/ folder next to the app is auto-detected; nothing
found -> "" (never raises, matches VoskSpeechEngine.available()'s honest
not-available contract, see hadj_no_touch/voice/speech_recognition.py)."""

from __future__ import annotations

import shutil
from pathlib import Path

from edu_air.config import resolve_vosk_model_path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_explicit_path_wins_when_it_is_a_real_directory(tmp_path):
    model_dir = tmp_path / "my-custom-model"
    model_dir.mkdir()
    assert resolve_vosk_model_path("en", str(model_dir)) == str(model_dir)


def test_explicit_path_that_does_not_exist_falls_back_to_auto_detect():
    assert resolve_vosk_model_path("xx-nope", "Z:/does/not/exist") == ""


def test_no_model_anywhere_returns_empty_string_not_an_exception():
    assert resolve_vosk_model_path("xx-nope") == ""


def test_auto_detects_a_bundled_model_folder_next_to_the_app():
    """models/vosk-<lang>/ next to edu_air_main.py, matching the layout
    documented in label.offline_voice_tip and requirements.txt."""
    bundled = PROJECT_ROOT / "models" / "vosk-zz"
    bundled.mkdir(parents=True, exist_ok=True)
    try:
        assert resolve_vosk_model_path("zz") == str(bundled)
        assert resolve_vosk_model_path("zz-ZZ") == str(bundled)  # BCP-47 tag
    finally:
        shutil.rmtree(PROJECT_ROOT / "models" / "vosk-zz")
        # only remove the parent if this test created it and it's now empty
        try:
            (PROJECT_ROOT / "models").rmdir()
        except OSError:
            pass
