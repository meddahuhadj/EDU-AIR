"""i18n layer gate — byte-honest. Tests the REAL translate("...") seam.

Contract under test (nothing fabricated, nothing invented):
  * empty lang                    -> text UNCHANGED (zero behaviour change, no
                                    pedigree invention)
  * unsupported lang ("de","xx")  -> text UNCHANGED
  * SUPPORTED lang (fr/ar/nl) + a key THAT EXISTS in the table -> the real
    translation (byte-real, human, from the table on disk)
  * any lang + a key that does NOT exist -> text UNCHANGED (never invented,
    unknown strings pass through honestly)
All pure: no Qt, no engine, no setting mutation.
"""

from hadj_no_touch.i18n import translate

_FR_KEY = "Voice engine & privacy"
_AR_KEY = "Offline-first"


def test_empty_lang_is_neutral():
    assert translate("Voice engine & privacy", "") == "Voice engine & privacy"


def test_unsupported_lang_is_neutral():
    assert translate("Voice engine & privacy", "de") == "Voice engine & privacy"
    assert translate("Voice engine & privacy", "xx") == "Voice engine & privacy"


def test_fr_translates_a_real_key():
    v = translate(_FR_KEY, "fr")
    assert v == "Moteur vocal et confidentialité"
    assert isinstance(v, str) and v


def test_ar_translates_a_real_key():
    v = translate(_AR_KEY, "ar")
    assert v == "دون اتصال أولًا"
    assert isinstance(v, str) and v


def test_unknown_key_passes_through_never_invented():
    for lang in ("fr", "ar", "nl", ""):
        assert translate("This is NOT a known UI key at all", lang) == \
            "This is NOT a known UI key at all"


def test_case_sensitive_keys_are_not_guessed():
    # "voice engine & privacy" (lowercase v) is NOT the same byte token as the
    # canonical key -> must NOT translate (no case guessing).
    assert translate("voice engine & privacy", "fr") == "voice engine & privacy"
