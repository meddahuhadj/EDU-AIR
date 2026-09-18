"""EDU-AIR user-interface translations (English / French / Arabic / Dutch).

Every user-facing string in the control dock, the projection overlay (HUD,
quiz panel) and the demo script is looked up through ``t()``. Missing keys
fall back to English, then to the key itself, so the classroom always renders
something readable even when a translation is incomplete.

Activations are intentionally decoupled from the voice-recognition language
so a teacher can, e.g., keep the UI in English while giving voice commands in
Arabic — or translate both together via the language combo box.

RTL support: choose Arabic and the ``is_rtl()`` flag mirrors the layout.
"""

from __future__ import annotations

from .config import SETTINGS

# Canonical order shown in the language selector.
SUPPORTED = ("en", "fr", "ar", "nl")
LANG_NAMES = {"en": "English", "fr": "Français", "ar": "العربية", "nl": "Nederlands"}
RTL_LANGS = {"ar"}

_current_lang = ""  # resolved lazily from SETTINGS on first access


def set_language(lang: str) -> None:
    """Set the current UI language (binds to persisted settings too)."""
    global _current_lang
    _current_lang = lang if lang in SUPPORTED else "en"
    if SETTINGS is not None:
        SETTINGS.classroom.language = _current_lang


def current_language() -> str:
    global _current_lang
    if _current_lang not in SUPPORTED:
        _current_lang = SETTINGS.classroom.language if SETTINGS is not None else "en"
    if _current_lang not in SUPPORTED:
        _current_lang = "en"
    return _current_lang


def is_rtl(lang: str | None = None) -> bool:
    """True when the given (or current) language is written right-to-left."""
    return (lang or current_language()) in RTL_LANGS


# ---------------------------------------------------------------------------
# String catalogue: STRINGS[key][lang] = translated text.
# Keys may contain {placeholders} filled by ``t(key, **fmt)``.
# ---------------------------------------------------------------------------
STRINGS: dict[str, dict[str, str]] = {
    # ---- window -----------------------------------------------------------
    "window.title": {
        "en": "EDU-AIR — Contactless Interactive Classroom",
        "fr": "EDU-AIR — Classe interactive sans contact",
        "ar": "إيدو-إير — فصل تفاعلي بدون لمس",
        "nl": "EDU-AIR — Contactloze interactieve klas",
    },
    "window.subtitle": {
        "en": "Projector + computer + webcam. No touchscreen.",
        "fr": "Projecteur + ordinateur + webcam. Sans écran tactile.",
        "ar": "بروجكتور + حاسوب + كاميرا ويب. بلا شاشة لمس.",
        "nl": "Beamer + computer + webcam. Zonder touchscreen.",
    },
    "camera.preview": {
        "en": "Camera preview (starting…)",
        "fr": "Aperçu caméra (démarrage…)",
        "ar": "معاينة الكاميرا (جارٍ التشغيل…)",
        "nl": "Cameravoorbeeld (bezig met starten…)",
    },

    # ---- status labels ----------------------------------------------------
    "status.mode": {"en": "Mode", "fr": "Mode", "ar": "الوضع", "nl": "Modus"},
    "status.presentation": {
        "en": "Presentation", "fr": "Présentation", "ar": "العرض",
        "nl": "Presentatie"},
    "status.pointer": {"en": "Pointer", "fr": "Pointeur", "ar": "المؤشر",
                       "nl": "Aanwijzer"},
    "status.command": {
        "en": "Last command", "fr": "Dernière commande", "ar": "آخر أمر",
        "nl": "Laatste opdracht"},
    "status.interaction": {
        "en": "Interaction", "fr": "Interaction", "ar": "التفاعل",
        "nl": "Interactie"},
    "status.gesture": {"en": "Gesture", "fr": "Geste", "ar": "الإيماءة",
                       "nl": "Gebaar"},
    "status.timer": {"en": "Timer", "fr": "Minuteur", "ar": "المؤقت",
                     "nl": "Timer"},
    "status.quiz": {"en": "Quiz", "fr": "QCM", "ar": "الاختبار", "nl": "Quiz"},
    "status.tool": {"en": "Tool", "fr": "Outil", "ar": "الأداة",
                    "nl": "Gereedschap"},
    "status.strokes": {"en": "Strokes", "fr": "Traits", "ar": "الشطب",
                       "nl": "Streken"},
    "status.safety": {"en": "Safety", "fr": "Sécurité", "ar": "الأمان",
                      "nl": "Veiligheid"},
    "status.fps": {"en": "FPS", "fr": "FPS", "ar": "إطار/ث", "nl": "FPS"},
    "status.lighting": {
        "en": "Lighting", "fr": "Luminosité", "ar": "الإضاءة",
        "nl": "Verlichting"},
    "status.noise": {
        "en": "Noise", "fr": "Bruit", "ar": "الضوضاء", "nl": "Geluid"},
    "status.hand": {
        "en": "Hand", "fr": "Main", "ar": "اليد", "nl": "Hand"},
    "env.dark": {"en": "dark", "fr": "sombre", "ar": "مظلم", "nl": "donker"},
    "env.low": {"en": "low", "fr": "faible", "ar": "خافت", "nl": "laag"},
    "env.good": {"en": "good", "fr": "bonne", "ar": "جيد", "nl": "goed"},
    "env.bright": {"en": "bright", "fr": "forte", "ar": "ساطع", "nl": "fel"},
    "env.ok": {"en": "quiet", "fr": "calme", "ar": "هادئ", "nl": "rustig"},
    "env.loud": {"en": "loud", "fr": "bruyant", "ar": "صاخب", "nl": "lawaaierig"},
    "hand.seen": {"en": "seen", "fr": "détectée", "ar": "مرئية", "nl": "gezien"},
    "hand.lost": {"en": "not seen", "fr": "non détectée", "ar": "غير مرئية",
                  "nl": "niet gezien"},

    # ---- buttons ----------------------------------------------------------
    "btn.demo_real": {"en": "Demo / Real", "fr": "Démo / Réel",
                      "ar": "عرض / حقيقي", "nl": "Demo / Echt"},
    "btn.overlay": {"en": "Overlay", "fr": "Superposition", "ar": "التراكب",
                    "nl": "Overlay"},
    "btn.calibration": {"en": "Calibration", "fr": "Calibrage",
                        "ar": "المعايرة", "nl": "Calibratie"},
    "btn.clear": {"en": "Clear", "fr": "Effacer", "ar": "مسح", "nl": "Wissen"},
    "btn.next_slide": {"en": "Next ▶", "fr": "Suivante ▶", "ar": "التالية ▶", "nl": "Volgende ▶"},
    "btn.prev_slide": {"en": "◀ Prev", "fr": "◀ Précédente", "ar": "◀ السابقة", "nl": "◀ Vorige"},
    "btn.window": {"en": "Window", "fr": "Fenêtre", "ar": "النافذة",
                   "nl": "Venster"},
    "btn.help": {"en": "Help", "fr": "Aide", "ar": "مساعدة", "nl": "Help"},

    # ---- tools ------------------------------------------------------------
    "tool.point": {"en": "Point", "fr": "Point", "ar": "نقطة", "nl": "Punt"},
    "tool.draw": {"en": "Draw", "fr": "Tracer", "ar": "رسم", "nl": "Tekenen"},
    "tool.highlight": {"en": "Highlight", "fr": "Surligner", "ar": "تظليل",
                       "nl": "Markeren"},
    "tool.erase": {"en": "Erase", "fr": "Effacer", "ar": "مسح",
                   "nl": "Wissen"},

    # ---- controls ---------------------------------------------------------
    "btn.export": {"en": "Export PDF/Image", "fr": "Exporter PDF/Image",
                   "ar": "تصدير PDF/صورة", "nl": "Exporteer PDF/Image"},
    "label.camera": {"en": "Webcam:", "fr": "Caméra :", "ar": "الكاميرا :",
                     "nl": "Webcam:"},
    "export.success": {"en": "Board exported to {path}", "fr": "Tableau exporté sous {path}",
                       "ar": "تم تصدير اللوحة إلى {path}", "nl": "Bord geëxporteerd naar {path}"},
    "label.sensitivity": {
        "en": "Pointer sensitivity:", "fr": "Sensibilité du pointeur :",
        "ar": "حساسية المؤشر:", "nl": "Gevoeligheid aanwijzer:"},
    "label.voice": {"en": "Voice:", "fr": "Voix :", "ar": "الصوت :",
                    "nl": "Stem:"},
    "label.performance": {
        "en": "Low-CPU mode:", "fr": "Mode faible CPU :",
        "ar": "وضع منخفض المعالج:", "nl": "Lage-CPU-modus:"},
    "label.external_app": {
        "en": "Whiteboard app:", "fr": "Appli tableau :",
        "ar": "تطبيق السبورة:", "nl": "Bordapp:"},
    "extapp.none": {"en": "none (keyboard only)", "fr": "aucune (clavier seul)",
                    "ar": "بلا (لوحة مفاتيح فقط)", "nl": "geen (alleen toetsenbord)"},
    "extapp.openboard": {"en": "OpenBoard", "fr": "OpenBoard", "ar": "أوبن بورد",
                         "nl": "OpenBoard"},
    "extapp.xournalpp": {"en": "Xournal++", "fr": "Xournal++", "ar": "زورنال بلس",
                         "nl": "Xournal++"},
    "sens.low": {"en": "low", "fr": "faible", "ar": "منخفض", "nl": "laag"},
    "sens.medium": {"en": "medium", "fr": "moyenne", "ar": "متوسط",
                    "nl": "gemiddeld"},
    "sens.high": {"en": "high", "fr": "élevée", "ar": "مرتفع", "nl": "hoog"},

    "hint.keyboard": {
        "en": ("Keyboard fallback: F5 start · ESC stop · →/← slides · B pause · "
               "Ctrl+/Ctrl- zoom · PgUp/PgDn scroll · Del clear"),
        "fr": ("Raccourcis clavier : F5 démarrer · ÉCHAP arrêter · →/← diapos · "
               "B pause · Ctrl+/Ctrl- zoom · PgPréc/PgSuiv défil. · Suppr effacer"),
        "ar": ("بدائل لوحة المفاتيح: F5 بدء · ESC إيقاف · →/← الشرائح · B إيقاف مؤقت · "
               "Ctrl+/Ctrl- تكبير · PgUp/PgDn تمرير · Del مسح"),
        "nl": ("Toetsenbord: F5 start · ESC stop · →/← dia's · B pauze · "
               "Ctrl+/Ctrl- zoom · PgUp/PgDn scrollen · Del wissen"),
    },

    # ---- confirmations ----------------------------------------------------
    "confirm.clear": {
        "en": "Clear all annotations?", "fr": "Effacer toutes les annotations ?",
        "ar": "مسح كل الملاحظات؟", "nl": "Alle aantekeningen wissen?"},
    "confirm.title": {"en": "EDU-AIR", "fr": "EDU-AIR", "ar": "إيدو-إير",
                      "nl": "EDU-AIR"},

    "calibration.title": {
        "en": "Quick calibration", "fr": "Calibrage rapide",
        "ar": "معايرة سريعة", "nl": "Snelle calibratie"},
    "calibration.body": {
        "en": "Quick calibration ran.\n\nHomography: {homography}\n"
              "Alignment error: {err:.3f}\nStages: {stages}",
        "fr": "Calibrage rapide effectué.\n\nHomographie : {homography}\n"
              "Erreur d'alignement : {err:.3f}\nÉtapes : {stages}",
        "ar": "تمت المعايرة السريعة.\n\nالإسقاط: {homography}\n"
              "خطأ المحاذاة: {err:.3f}\nالمراحل: {stages}",
        "nl": "Snelle calibratie uitgevoerd.\n\nHomografie: {homography}\n"
              "Uitlijnfout: {err:.3f}\nStadia: {stages}"},
    "calibration.ok": {"en": "OK", "fr": "OK", "ar": "موافق", "nl": "OK"},
    "calibration.fallback": {"en": "fallback", "fr": "secours",
                             "ar": "احتياطي", "nl": "reserve"},

    # ---- overlay HUD ------------------------------------------------------
    "hud.slide": {
        "en": "Slide {cur}/{total} [{state}]",
        "fr": "Diapo {cur}/{total} [{state}]",
        "ar": "الشريحة {cur}/{total} [{state}]",
        "nl": "Dia {cur}/{total} [{state}]"},
    "hud.cmd": {"en": "Cmd: {cmd}", "fr": "Cmd : {cmd}", "ar": "الأمر: {cmd}",
                "nl": "Cmd: {cmd}"},
    "hud.tool_clock": {
        "en": "Tool: {tool} · Clock: {secs}s",
        "fr": "Outil : {tool} · Chrono : {secs}s",
        "ar": "الأداة: {tool} · المؤقت: {secs}ث",
        "nl": "Tool: {tool} · Klok: {secs}s"},
    "hud.quiz": {"en": "Quiz: {state}", "fr": "QCM : {state}",
                 "ar": "الاختبار: {state}", "nl": "Quiz: {state}"},
    "quiz.on": {"en": "ON", "fr": "ACTIF", "ar": "نشط", "nl": "AAN"},
    "quiz.off": {"en": "off", "fr": "inactif", "ar": "متوقف", "nl": "uit"},
    "hud.demo": {
        "en": "DEMO MODE — no real control",
        "fr": "MODE DÉMO — aucun contrôle réel",
        "ar": "وضع العرض — لا تحكم حقيقي",
        "nl": "DEMO MODUS — geen echte controle"},

    # ---- quiz overlay -----------------------------------------------------
    "quiz.question": {"en": "QUESTION {n}", "fr": "QUESTION {n}",
                      "ar": "السؤال {n}", "nl": "VRAAG {n}"},
    "quiz.correct": {"en": "Correct: {x}", "fr": "Bonne réponse : {x}",
                     "ar": "الإجابة الصحيحة: {x}", "nl": "Juist: {x}"},

    # ---- value tokens -----------------------------------------------------
    "state.idle": {"en": "idle", "fr": "inactif", "ar": "خامل",
                   "nl": "inactief"},
    "state.active": {"en": "active", "fr": "actif", "ar": "نشط", "nl": "actief"},
    "state.paused": {"en": "paused", "fr": "en pause", "ar": "متوقف مؤقتا",
                     "nl": "gepauzeerd"},
    "mode.demo": {"en": "demo", "fr": "démo", "ar": "عرض", "nl": "demo"},
    "mode.real": {"en": "real", "fr": "réel", "ar": "حقيقي", "nl": "echt"},
    "ptr.visible": {"en": "visible", "fr": "visible", "ar": "مرئي",
                    "nl": "zichtbaar"},
    "ptr.hidden": {"en": "hidden", "fr": "caché", "ar": "مخفي", "nl": "verborgen"},
    "voice.unavailable": {
        "en": "voice unavailable", "fr": "voix indisponible",
        "ar": "الصوت غير متاح", "nl": "stem niet beschikbaar"},
    "voice.engine": {"en": "voice engine: {name}", "fr": "moteur vocal : {name}",
                     "ar": "محرك الصوت: {name}", "nl": "stemmotor: {name}"},
    "fps.line": {"en": "fps {fps:.1f} hands {hands}",
                 "fr": "fps {fps:.1f} mains {hands}",
                 "ar": "إطار/ث {fps:.1f} أيدي {hands}",
                 "nl": "fps {fps:.1f} handen {hands}"},
}


def t(key: str, lang: str | None = None, **fmt) -> str:
    """Translate a UI key into the current (or given) language."""
    lang = lang or current_language()
    entry = STRINGS.get(key, {})
    text = entry.get(lang) or entry.get("en") or key
    if fmt:
        try:
            text = text.format(**fmt)
        except (KeyError, ValueError, IndexError):
            text = entry.get("en") or key
    return text


def tv(key: str) -> str:
    """Translate a value token like 'state.active' into the UI language."""
    return t(key)


# ---------------------------------------------------------------------------
# Convenience: verbose language name / short tag shown in list boxes.
# ---------------------------------------------------------------------------
def language_name(lang: str | None = None) -> str:
    lang = lang or current_language()
    return LANG_NAMES.get(lang, lang)


def language_tag(lang: str | None = None) -> str:
    lang = lang or current_language()
    return {"en": "EN", "fr": "FR", "ar": "ع", "nl": "NL"}.get(lang, lang.upper())