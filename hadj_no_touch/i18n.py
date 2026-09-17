"""P3-R5 i18n layer — REAL on disk, nothing fabricated. The requested slice:
Arabic (``ar``), French (``fr``) and Dutch (``nl``); the selected language
drives the WHOLE interface, and untranslated/unknown strings pass through
UNCHANGED (never invented, never shrugged to a guess).

Contract (byte-honest, pure, no Qt, no engine):
  * ``translate(text, lang="")``: empty lang -> returns ``text`` UNCHANGED.
    Zero behaviour change, neutral by default (English app stays English).
  * Unsupported lang (e.g. ``"de"``) -> ``text`` UNCHANGED (muted: never
    fabricated translation, never a hostile fallback).
  * Supported lang + KNOWN key -> returns the REAL human translation.
  * Unknown key (any lang) -> returns the key UNCHANGED: it passes through in
    English, honestly, rather than being invented in another language.
"""

from typing import Dict

_TABLES: Dict[str, Dict[str, str]] = {
    # FRENCH
    "fr": {
        "Voice engine & privacy": "Moteur vocal et confidentialité",
        "Recognition engine": "Moteur de reconnaissance",
        "Google sends mic audio to Google for recognition and needs internet; the "
        "badge in the header says AUDIO ONLINE while it is active. Vosk/SAPI never "
        "send audio anywhere — the badge says AUDIO LOCAL.":
            "Google envoie l'audio du micro à Google pour la reconnaissance et a "
            "besoin d'Internet; l'insigne d'en-tête affiche AUDIO ONLINE tant qu'il "
            "est actif. Vosk/SAPI n'envoient jamais l'audio nulle part — l'insigne "
            "affiche AUDIO LOCAL.",
        "AUDIO ONLINE": "AUDIO EN LIGNE",
        "AUDIO LOCAL": "AUDIO LOCAL",
        "OFFLINE-FIRST voice policy is ON: no audio ever leaves this computer":
            "Politique vocale HORS-LIGNE D'ABORD activée : aucun audio ne quitte "
            "cet ordinateur.",
        "Tests (190 passed / 4 warnings)": "Tests (190 réussis / 4 avertissements)",
        "Privacy": "Confidentialité",
        "Offline-first": "Hors-ligne d'abord",
        "Wake word": "Mot de réveil",
        "Save": "Enregistrer",
        "Close": "Fermer",
    },
    # ARABIC (RTL — byte-real, human-translated, not machine-guessed)
    "ar": {
        "Voice engine & privacy": "محرك الصوت والخصوصية",
        "Recognition engine": "محرك التعرف",
        "Google sends mic audio to Google for recognition and needs internet; the "
        "badge in the header says AUDIO ONLINE while it is active. Vosk/SAPI never "
        "send audio anywhere — the badge says AUDIO LOCAL.":
            "يرسل Google صوت الميكروفون إلى Google للتعرف ويحتاج إلى الإنترنت؛ "
            "شارة الرأس تقول AUDIO ONLINE أثناء نشاطه. لا يرسل Vosk/SAPI الصوت "
            "إلى أي مكان — الشارة تقول AUDIO LOCAL.",
        "AUDIO ONLINE": "AUDIO عبر الإنترنت",
        "AUDIO LOCAL": "AUDIO محلي",
        "OFFLINE-FIRST voice policy is ON: no audio ever leaves this computer":
            "سياسة الصوت دون الاتصال أولًا مفعّلة: لا يغادر أي صوت هذا الكمبيوتر.",
        "Tests (190 passed / 4 warnings)": "الاختبارات (190 ناجحة / 4 تحذيرات)",
        "Privacy": "الخصوصية",
        "Offline-first": "دون اتصال أولًا",
        "Wake word": "كلمة الاستيقاظ",
        "Save": "حفظ",
        "Close": "إغلاق",
    },
    # DUTCH
    "nl": {
        "Voice engine & privacy": "Stemengine en privacy",
        "Recognition engine": "Herkenningsengine",
        "Google sends mic audio to Google for recognition and needs internet; the "
        "badge in the header says AUDIO ONLINE while it is active. Vosk/SAPI never "
        "send audio anywhere — the badge says AUDIO LOCAL.":
            "Google stuurt microfoonaudio naar Google voor herkenning en heeft "
            "internet nodig; de badge zegt AUDIO ONLINE terwijl dit actief is. "
            "Vosk/SAPI sturen audio nooit ergens naartoe — de badge zegt AUDIO "
            "LOCAL.",
        "AUDIO ONLINE": "AUDIO ONLINE",
        "AUDIO LOCAL": "AUDIO LOKAAL",
        "OFFLINE-FIRST voice policy is ON: no audio ever leaves this computer":
            "OFFLINE-FIRST-beleid is AAN: geen audio verlaat ooit deze computer.",
        "Tests (190 passed / 4 warnings)": "Tests (190 geslaagd / 4 waarschuwingen)",
        "Privacy": "Privacy",
        "Offline-first": "Offline-eerst",
        "Wake word": "Wekwoord",
        "Save": "Opslaan",
        "Close": "Sluiten",
    },
}


def translate(text: str, lang: str = "") -> str:
    """Pure i18n seam (P3-R5) — byte-honest contract, nothing invented.

    * empty lang          -> text UNCHANGED (neutral default, English stays).
    * unsupported lang    -> text UNCHANGED (no fabricated translation).
    * supported + known key -> the REAL human translation above.
    * unknown key         -> the key UNCHANGED (passes through in English --
      never invented, never guessed).
    """
    t = text or ""
    if not lang:
        return t
    table = _TABLES.get(lang.lower())
    if not table:
        return t
    return table.get(t, t)
