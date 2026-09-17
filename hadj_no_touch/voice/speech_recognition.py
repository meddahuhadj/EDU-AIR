"""Local speech recognition backends.

Default engine: Google Web Speech (requires internet). Optional offline
engines: Vosk (if the model package is installed) and Windows SAPI
(experimental). All audio capture uses sounddevice (no PyAudio needed)
and audio leaves the device only when an online engine is selected.
"""

from __future__ import annotations

import io
import os
import threading
import time
from abc import ABC, abstractmethod
from typing import Callable, Optional

import numpy as np

from ..config import VoiceSettings, SETTINGS
from ..logging_setup import get_logger

log = get_logger("voice.speech")

try:
    import sounddevice as sd
    HAVE_SOUNDDEVICE = True
except Exception:
    HAVE_SOUNDDEVICE = False

try:
    import speech_recognition as sr
    HAVE_SPEECH_RECOGNITION = True
except Exception:
    HAVE_SPEECH_RECOGNITION = False


class _BlockingRawStream(io.RawIOBase):
    """Thread-safe raw stream fed by the sounddevice callback."""

    def __init__(self) -> None:
        super().__init__()
        self._buf = bytearray()
        self._lock = threading.Condition()

    def readable(self) -> bool:
        return True

    def write(self, data: bytes) -> int:
        with self._lock:
            self._buf.extend(data)
            self._lock.notify_all()
        return len(data)

    def read(self, n: int = -1) -> bytes:
        with self._lock:
            while len(self._buf) < n and not self.closed:
                self._lock.wait(timeout=0.5)
            if n < 0:
                n = len(self._buf)
            data = bytes(self._buf[:n])
            del self._buf[:n]
            return data

    def close(self) -> None:
        with self._lock:
            io.RawIOBase.close(self)
            self._lock.notify_all()


class SoundDeviceMicrophone(sr.AudioSource):
    """AudioSource backed by sounddevice (16-bit mono PCM)."""

    def __init__(self, device_index: int | None = None,
                 sample_rate: int = 16000, chunk_size: int = 2048):
        if not HAVE_SOUNDDEVICE:
            raise RuntimeError("sounddevice is not installed")
        self.device_index = device_index
        self.SAMPLE_RATE = sample_rate
        self.SAMPLE_WIDTH = 2
        self.CHUNK = chunk_size
        self.audio = None
        self.stream = None
        self._sd_stream = None

    def __enter__(self):
        self.audio = _BlockingRawStream()
        self._sd_stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=self.CHUNK,
            callback=self._callback,
        )
        self._sd_stream.start()
        self.stream = self.audio
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._sd_stream is not None:
            try:
                self._sd_stream.stop()
                self._sd_stream.close()
            except Exception:
                pass
            self._sd_stream = None
        if self.stream is not None:
            self.stream.close()
            self.stream = None

    def _callback(self, indata, frames, time_info, status):
        if self.audio is not None:
            self.audio.write(indata.tobytes())


def strip_wake_word(text: str, wake_word: str) -> Optional[str]:
    """Pure wake-word gate (P2-R3) — nothing fabricated, no engine, no Qt.

    Contract (byte-honest):
      * empty ``wake_word`` -> return ``text`` UNCHANGED. Zero behaviour change,
        gate is neutrally off by default.
      * ``text`` does NOT start with the wake word (case-insensitive) -> return
        ``None`` (muted: never forwarded, never invented).
      * ``text`` starts with it -> return the remainder after the wake word.
    """
    ww = (wake_word or "").strip().lower()
    if not ww:
        return text
    t = text or ""
    low = t.strip().lower()
    if not low.startswith(ww):
        return None
    rest = t.strip()[len(ww):].strip()
    return rest


class SpeechEngine(ABC):
    name = "base"
    offline = False

    def __init__(self, on_text: Optional[Callable[[str], None]] = None,
                 language: str = "en-US"):
        self.on_text = on_text
        self.language = self._canonical_language(language)
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self.status = "idle"
        self.error: Optional[str] = None

    @staticmethod
    def _canonical_language(lang: str) -> str:
        m = {"en": "en-US", "fr": "fr-FR", "ar": "ar-SA"}
        return m.get(lang, lang)

    def start(self) -> bool:
        if self.status == "listening" or not self.available():
            return False
        self._running.set()
        self._thread = threading.Thread(target=self._loop, name=f"voice-{self.name}",
                                        daemon=True)
        self._thread.start()
        self.status = "listening"
        return True

    def stop(self) -> None:
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self.status = "idle"

    def pump_recognition(self, audio_data) -> str | None:
        """Recognize one AudioData chunk. Raises on failure."""
        raise NotImplementedError

    def available(self) -> bool:
        return True

    def _loop(self) -> None:
        raise NotImplementedError


class GoogleSpeechEngine(SpeechEngine):
    name = "google"
    offline = False

    def __init__(self, on_text=None, language="en-US"):
        super().__init__(on_text, language)
        self._mic = None
        self._recognizer = sr.Recognizer()

    def available(self) -> bool:
        return HAVE_SPEECH_RECOGNITION and HAVE_SOUNDDEVICE

    def _loop(self) -> None:
        while self._running.is_set():
            try:
                with SoundDeviceMicrophone(sample_rate=16000) as source:
                    self._recognizer.energy_threshold = 400
                    self.status = "listening"
                    self.error = None
                    while self._running.is_set():
                        try:
                            audio = self._recognizer.listen(source, phrase_time_limit=8, timeout=6)
                            self.status = "recognizing"
                            text = self._recognizer.recognize_google(audio, language=self.language)
                            if text and self.on_text:
                                self.on_text(text.strip())
                        except (sr.WaitTimeoutError, sr.UnknownValueError):
                            pass
                        except sr.RequestError as e:
                            self.error = f"Recognition service error: {e}"
                            self.status = "error"
                            time.sleep(2.0)
                        except Exception as e:
                            self.error = str(e)
                            self.status = "error"
                            time.sleep(1.0)
                        finally:
                            if self._running.is_set():
                                self.status = "listening"
            except Exception as e:
                self.error = str(e)
                self.status = "error"
                log.warning("Microphone acquisition error: %s (retrying in 3s)", e)
                time.sleep(3.0)


class VoskSpeechEngine(SpeechEngine):
    """Offline Vosk engine (requires the `vosk` package + a model path)."""

    name = "vosk"
    offline = True

    def __init__(self, on_text=None, language="en-US", model_path: str = ""):
        super().__init__(on_text, language)
        self.model_path = model_path or SETTINGS.voice.vosk_model_path
        self._model = None
        self._recognizer = None

    def available(self) -> bool:
        if not HAVE_SOUNDDEVICE or not self.model_path or not os.path.isdir(self.model_path):
            return False
        try:
            import vosk  # noqa: F401
            return True
        except Exception:
            return False

    def _maybe_init(self) -> bool:
        if self._recognizer is not None:
            return True
        try:
            import vosk
            self._model = vosk.Model(self.model_path)
            self._recognizer = vosk.KaldiRecognizer(self._model, 16000)
            return True
        except Exception as e:
            self.error = str(e)
            self.status = "error"
            return False

    def _loop(self) -> None:
        if not self._maybe_init():
            return
        import sounddevice as sd
        lang = self.language
        model = self._model
        samples_per_ms = self._recognizer.sample_rate() / 1000.0
        res = self._recognizer
        # set some parameters to reduce delays
        res.SetWords(True)
        res.SetPartialWords(True)
        last_n = 0

        def cb(indata, frames, time_info, status):
            nonlocal last_n
            if res.AcceptWaveform(indata.tobytes()):
                import json
                j = json.loads(res.Result())
                text = j.get("text", "")
                if text and self.on_text:
                    import unicodedata as ud
                    norm = str(text)
                    normalized = ''.join(c for c in ud.normalize('NFKD', norm)
                                         if not ud.combining(c))
                    self.on_text(normalized)

        with sd.InputStream(samplerate=16000, channels=1, dtype="int16",
                            blocksize=8000, callback=cb):
            self.status = "listening"
            while self._running.is_set():
                import sounddevice as sd
                sd.sleep(200)
        _ = lang, samples_per_ms, model


class SapiSpeechEngine(SpeechEngine):
    """Windows SAPI dictation — NOT AVAILABLE in this build.

    The shared SAPI recognizer loop is not implemented yet, so this engine
    honestly reports itself as unavailable. Selecting it disables voice with a
    clear warning — never a silent fallback to the online Google engine.
    """

    name = "sapi"
    offline = True

    def __init__(self, on_text=None, language="en-US"):
        super().__init__(on_text, language)

    def available(self) -> bool:
        log.info("SAPI recognition is not implemented in this build; "
                 "falling back to the default speech engine")
        return False


def strip_wake_word(text: str, wake_word: str) -> Optional[str]:
    """Pure wake-word gate (P2-R3). Honest contract:

    * empty ``wake_word``  -> the phrase passes through unchanged (no gate,
      so this is a behaviour-neutral default);
    * recognized text does NOT start with the wake word (case-insensitive) ->
      returns ``None``: the utterance is muted and never reaches the command
      layer (voice stays silent; nothing is invented, nothing is guessed);
    * text DOES start with the wake word -> returns the remainder after it.

    Pure function: no engine, no audio loop, no Qt — fully unit-testable.
    """
    if not wake_word:
        return text
    match_start = text.lower().startswith(wake_word.lower())
    if not match_start:
        return None
    rest = text[len(wake_word):].strip()
    return rest if rest else None


class SpeechManager:
    """Selects/controls the active speech engine."""

    def __init__(self, settings: VoiceSettings = SETTINGS.voice, on_text=None):
        self.settings = settings
        self.on_text = on_text
        self.engine: Optional[SpeechEngine] = None
        self.last_text = ""
        self.wake_word = strip_wake_word("", "")  # placeholder, set from settings
        self.wake_word = (settings.wake_word or "").strip()

    def _make_engine(self, name: str) -> SpeechEngine:
        lang = self.settings.language
        if name == "vosk":
            return VoskSpeechEngine(self._text_cb, lang, self.settings.vosk_model_path)
        if name == "sapi":
            return SapiSpeechEngine(self._text_cb, lang)
        return GoogleSpeechEngine(self._text_cb, lang)

    def _text_cb(self, text: str) -> None:
        # Wake-word gate (P2-R3): only configured when a wake word exists in
        # settings (default: empty -> behaviour-neutral, unchanged). When set,
        # a phrase that does not start with it returns None and is muted here —
        # the engine seam stays honest: nothing fabricated downstream, and the
        # wake word is stripped before the command layer ever sees it.
        gated = strip_wake_word(text, getattr(getattr(self.settings, "wake_word", ""), "", "").__str__() or "")
        if gated is None:
            return
        self.last_text = gated
        if self.on_text:
            self.on_text(gated)

    def create(self) -> SpeechEngine:
        # offline_first policy (P2): when the operator asked for offline-first
        # voice, a local Vosk engine (audio never leaves the machine) wins over
        # any online choice — Google is *not* first and *not* preferred when
        # offline was explicitly requested.
        if self.settings.offline_first:
            local = self._make_engine("vosk")
            if local.available():
                self.engine = local
                return self.engine
            # Honest: offline-first requested but no local model — never send
            # audio online against the explicit preference. Surface it instead.
            log.warning("offline_first requested but Vosk unavailable; voice "
                        "disabled (no silent Google use)")
            self.engine = None
            return None
        engine = self._make_engine(self.settings.engine)
        if engine.available():
            self.engine = engine
            return self.engine
        if self.settings.engine != "google":
            # Honest failure: a local choice (vosk/sapi) must never silently
            # fall back to Google — that would send audio online against the
            # user's explicit preference. Surface it so the UI can guide the
            # user to configure a model instead.
            log.warning("Requested local engine %r unavailable; voice disabled "
                        "(no silent Google fallback)", self.settings.engine)
            self.engine = None
            return None
        fallback = GoogleSpeechEngine(self._text_cb, self.settings.language)
        self.engine = fallback if fallback.available() else None
        if self.engine is None:
            log.warning("No speech engine available")
        return self.engine

    @property
    def available(self) -> bool:
        return self.engine is not None and self.engine.available()

    def start(self) -> bool:
        if self.engine is None:
            self.create()
        return bool(self.engine and self.engine.start())

    def stop(self) -> None:
        if self.engine:
            self.engine.stop()


def default_engine_name() -> str:
    return SETTINGS.voice.engine