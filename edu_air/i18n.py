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
    "status.board": {"en": "Board", "fr": "Tableau", "ar": "السبورة",
                     "nl": "Bord"},
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
    "btn.wall_mode": {"en": "Wall mode", "fr": "Mode mural",
                      "ar": "وضع الجدار", "nl": "Wandmodus"},
    "btn.rehearsal": {"en": "Rehearsal mode", "fr": "Mode maquette",
                      "ar": "وضع التدريب", "nl": "Repetitiemodus"},
    "rehearsal.window_title": {
        "en": "EDU-AIR — Rehearsal preview (no projector needed)",
        "fr": "EDU-AIR — Aperçu maquette (sans vidéoprojecteur)",
        "ar": "EDU-AIR — معاينة التدريب (بدون جهاز عرض)",
        "nl": "EDU-AIR — Repetitievoorbeeld (geen beamer nodig)"},
    "hud.wall_mode": {"en": "WALL MODE — touch to write", "fr": "MODE MURAL — touchez pour écrire",
                      "ar": "وضع الجدار — المس للكتابة", "nl": "WANDMODUS — raak aan om te schrijven"},
    "hud.calibration_drift": {
        "en": "Calibration looks off — recalibrate",
        "fr": "Calibrage désaligné — recalibrer",
        "ar": "المعايرة غير دقيقة — أعد المعايرة",
        "nl": "Kalibratie klopt niet — herkalibreer"},
    "btn.clear": {"en": "Clear", "fr": "Effacer", "ar": "مسح", "nl": "Wissen"},
    "btn.next_slide": {"en": "Next ▶", "fr": "Suivante ▶", "ar": "التالية ▶", "nl": "Volgende ▶"},
    "btn.prev_slide": {"en": "◀ Prev", "fr": "◀ Précédente", "ar": "◀ السابقة", "nl": "◀ Vorige"},
    "btn.window": {"en": "Window", "fr": "Fenêtre", "ar": "النافذة",
                   "nl": "Venster"},
    "btn.help": {"en": "Help", "fr": "Aide", "ar": "مساعدة", "nl": "Help"},

    # ---- interactive board (TNI) -------------------------------------------
    "btn.board_title": {"en": "Board", "fr": "Tableau", "ar": "السبورة",
                        "nl": "Bord"},
    "btn.board_prev": {"en": "◀ Page", "fr": "◀ Page", "ar": "◀ صفحة",
                       "nl": "◀ Pagina"},
    "btn.board_next": {"en": "Page ▶", "fr": "Page ▶", "ar": "صفحة ▶",
                       "nl": "Pagina ▶"},
    "btn.board_add": {"en": "+ Page", "fr": "+ Page", "ar": "+ صفحة",
                      "nl": "+ Pagina"},
    "btn.board_del": {"en": "Delete", "fr": "Supprimer", "ar": "حذف",
                      "nl": "Verwijderen"},
    "btn.board_undo": {"en": "Undo", "fr": "Annuler", "ar": "تراجع",
                       "nl": "Ongedaan"},
    "label.board_bg": {"en": "Background:", "fr": "Fond :", "ar": "الخلفية :",
                       "nl": "Achtergrond:"},
    "label.board_persist": {
        "en": "Save notebook on exit", "fr": "Sauvegarder le carnet à la fermeture",
        "ar": "حفظ الدفتر عند الإغلاق", "nl": "Notitieboek opslaan bij afsluiten"},
    "confirm.del_page": {
        "en": "Delete this board page? This removes its notes.",
        "fr": "Supprimer cette page du tableau ? Ses annotations seront perdues.",
        "ar": "حذف هذه الصفحة من السبورة؟ سيتم فقدان ملاحظاتها.",
        "nl": "Deze bordpagina verwijderen? De aantekeningen gaan verloren."},

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
    "btn.export_pdf": {"en": "Board → PDF", "fr": "Tableau → PDF",
                       "ar": "السبورة → PDF", "nl": "Bord → PDF"},
    "btn.export_quiz": {"en": "Export quiz results", "fr": "Exporter résultats quiz",
                        "ar": "تصدير نتائج الاختبار", "nl": "Exporteer quizresultaten"},
    "label.camera": {"en": "Webcam:", "fr": "Caméra :", "ar": "الكاميرا :",
                     "nl": "Webcam:"},
    "export.success": {"en": "Board exported to {path}", "fr": "Tableau exporté sous {path}",
                       "ar": "تم تصدير اللوحة إلى {path}", "nl": "Bord geëxporteerd naar {path}"},
    "export.pdf_success": {
        "en": "Board ({page} pages) exported to {path}",
        "fr": "Tableau ({page} pages) exporté sous {path}",
        "ar": "تم تصدير اللوحة ({page} صفحات) إلى {path}",
        "nl": "Bord ({page} pagina's) geëxporteerd naar {path}"},
    "confirm.last_page": {
        "en": "This is the last page — add a new page before deleting.",
        "fr": "C'est la dernière page — ajoutez une page avant de supprimer.",
        "ar": "هذه آخر صفحة — أضف صفحة جديدة قبل الحذف.",
        "nl": "Dit is de laatste pagina — voeg eerst een nieuwe pagina toe."},
    "export.quiz_empty": {
        "en": "No quiz answers to export yet — start a quiz and answer at least one question.",
        "fr": "Aucune réponse de quiz à exporter — démarrez un quiz et répondez à au moins une question.",
        "ar": "لا توجد إجابات اختبار للتصدير بعد — ابدأ اختبارًا وأجب عن سؤال واحد على الأقل.",
        "nl": "Nog geen quizantwoorden om te exporteren — start een quiz en beantwoord minstens één vraag."},
    "export.quiz_success": {
        "en": "Quiz results exported to {path}", "fr": "Résultats du quiz exportés sous {path}",
        "ar": "تم تصدير نتائج الاختبار إلى {path}", "nl": "Quizresultaten geëxporteerd naar {path}"},
    "btn.participation": {"en": "Participation +1", "fr": "Participation +1",
                          "ar": "مشاركة +1", "nl": "Participatie +1"},
    "btn.export_participation": {
        "en": "Export participation", "fr": "Exporter participations",
        "ar": "تصدير المشاركات", "nl": "Exporteer participaties"},
    "participation.marked": {
        "en": "Participation logged (total: {n})", "fr": "Participation enregistrée (total : {n})",
        "ar": "تم تسجيل المشاركة (المجموع: {n})", "nl": "Participatie genoteerd (totaal: {n})"},
    "export.participation_empty": {
        "en": "No participations to export yet — mark at least one first.",
        "fr": "Aucune participation à exporter — enregistrez-en au moins une d'abord.",
        "ar": "لا توجد مشاركات للتصدير بعد — سجل واحدة على الأقل أولاً.",
        "nl": "Nog geen participaties om te exporteren — noteer er eerst minstens één."},
    "export.participation_success": {
        "en": "Participation tally exported to {path}",
        "fr": "Relevé des participations exporté sous {path}",
        "ar": "تم تصدير سجل المشاركات إلى {path}",
        "nl": "Participatielijst geëxporteerd naar {path}"},
    "btn.lesson_load": {"en": "Load lesson…", "fr": "Charger le cours…",
                        "ar": "تحميل الدرس…", "nl": "Les laden…"},
    "btn.lesson_prev": {"en": "◀ Step", "fr": "◀ Étape", "ar": "◀ خطوة",
                        "nl": "◀ Stap"},
    "btn.lesson_next": {"en": "Step ▶", "fr": "Étape ▶", "ar": "خطوة ▶",
                        "nl": "Stap ▶"},
    "label.lesson_none": {"en": "No lesson loaded", "fr": "Aucun cours chargé",
                          "ar": "لم يتم تحميل درس", "nl": "Geen les geladen"},
    "label.offline_voice": {
        "en": "Offline voice (Vosk)", "fr": "Voix hors-ligne (Vosk)",
        "ar": "التعرف الصوتي دون اتصال (Vosk)", "nl": "Offline spraak (Vosk)"},
    "label.offline_voice_tip": {
        "en": "Requires the vosk package and a model in models/vosk-<lang>/ "
              "next to the app. Falls back to disabled (never silently "
              "online) if no local model is found.",
        "fr": "Nécessite le paquet vosk et un modèle dans models/vosk-<lang>/ "
              "à côté de l'application. Désactivée (jamais de bascule "
              "silencieuse en ligne) si aucun modèle local n'est trouvé.",
        "ar": "يتطلب حزمة vosk ونموذجًا في models/vosk-<lang>/ بجانب "
              "التطبيق. يتم التعطيل (بدون رجوع صامت للإنترنت) إذا لم يتم "
              "العثور على نموذج محلي.",
        "nl": "Vereist het vosk-pakket en een model in models/vosk-<lang>/ "
              "naast de app. Wordt uitgeschakeld (nooit stil online) als "
              "geen lokaal model wordt gevonden."},
    "lesson.load_failed": {
        "en": "Could not read that lesson file (missing or invalid JSON).",
        "fr": "Impossible de lire ce fichier de cours (manquant ou JSON invalide).",
        "ar": "تعذر قراءة ملف الدرس (مفقود أو JSON غير صالح).",
        "nl": "Kon dat lesbestand niet lezen (ontbreekt of ongeldige JSON)."},
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

    # ---- wall/touch mode ---------------------------------------------------
    "label.touch_backend": {
        "en": "Touch backend:", "fr": "Détection tactile :",
        "ar": "خلفية اللمس:", "nl": "Aanraakmethode:"},
    "label.touch_sensitivity": {
        "en": "Contact sensitivity:", "fr": "Sensibilité du contact :",
        "ar": "حساسية اللمس:", "nl": "Aanraakgevoeligheid:"},
    "label.palm_rejection": {
        "en": "Palm rejection:", "fr": "Rejet de la paume :",
        "ar": "رفض راحة اليد:", "nl": "Handpalmweigering:"},
    "label.touch_debug": {
        "en": "Touch debug overlay:", "fr": "Overlay debug tactile :",
        "ar": "تراكب تصحيح اللمس:", "nl": "Aanraak-debugoverlay:"},
    "backend.shadow_gap": {
        "en": "Shadow gap (webcam only)", "fr": "Écart d'ombre (webcam seule)",
        "ar": "فجوة الظل (كاميرا فقط)", "nl": "Schaduwkloof (alleen webcam)"},
    "backend.ir_pen": {
        "en": "IR pen (experimental)", "fr": "Stylet IR (expérimental)",
        "ar": "قلم أشعة تحت الحمراء (تجريبي)", "nl": "IR-pen (experimenteel)"},
    "backend.color_marker": {
        "en": "Color marker (experimental)", "fr": "Marqueur coloré (expérimental)",
        "ar": "قلم ملون (تجريبي)", "nl": "Kleurmarker (experimenteel)"},

    "hint.keyboard": {
        "en": ("Keyboard fallback: F5 start · ESC stop · →/← slides · B pause · "
               "Ctrl+/Ctrl- zoom · PgUp/PgDn scroll · Del clear · W wall mode · "
               "P participation"),
        "fr": ("Raccourcis clavier : F5 démarrer · ÉCHAP arrêter · →/← diapos · "
               "B pause · Ctrl+/Ctrl- zoom · PgPréc/PgSuiv défil. · Suppr effacer · "
               "W mode mural · P participation"),
        "ar": ("بدائل لوحة المفاتيح: F5 بدء · ESC إيقاف · →/← الشرائح · B إيقاف مؤقت · "
               "Ctrl+/Ctrl- تكبير · PgUp/PgDn تمرير · Del مسح · W وضع الجدار · "
               "P مشاركة"),
        "nl": ("Toetsenbord: F5 start · ESC stop · →/← dia's · B pauze · "
               "Ctrl+/Ctrl- zoom · PgUp/PgDn scrollen · Del wissen · W wandmodus · "
               "P participatie"),
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

    "calibration.touch_plane_prompt": {
        "en": ("Also calibrate the touch plane for wall mode?\n\n"
               "You will touch each of the 4 board corners for about 2 "
               "seconds. Skip this and wall mode falls back to default "
               "contact thresholds."),
        "fr": ("Calibrer aussi le plan tactile pour le mode mural ?\n\n"
               "Vous allez toucher chacun des 4 coins du tableau pendant "
               "environ 2 secondes. Si vous passez cette étape, le mode "
               "mural utilisera les seuils de contact par défaut."),
        "ar": ("هل تريد أيضًا معايرة مستوى اللمس لوضع الجدار؟\n\n"
               "ستلمس كل ركن من أركان اللوحة الأربعة لمدة ثانيتين تقريبًا. "
               "إذا تخطيت هذه الخطوة سيستخدم وضع الجدار عتبات التلامس "
               "الافتراضية."),
        "nl": ("Ook het aanraakvlak voor de wandmodus kalibreren?\n\n"
               "U raakt elk van de 4 bordhoeken ongeveer 2 seconden aan. "
               "Slaat u dit over, dan gebruikt de wandmodus de "
               "standaard contactdrempels.")},
    "calibration.touch_plane_step": {
        "en": "Touch and hold the {corner} corner of the board now, then click OK.",
        "fr": "Touchez et maintenez le coin {corner} du tableau maintenant, puis cliquez sur OK.",
        "ar": "المس واستمر في لمس الزاوية {corner} من اللوحة الآن، ثم انقر موافق.",
        "nl": "Raak nu de {corner} hoek van het bord aan en houd vast, klik dan op OK."},
    "calibration.corner_tl": {"en": "top-left", "fr": "supérieur gauche",
                              "ar": "العلوية اليسرى", "nl": "linksboven"},
    "calibration.corner_tr": {"en": "top-right", "fr": "supérieur droit",
                              "ar": "العلوية اليمنى", "nl": "rechtsboven"},
    "calibration.corner_br": {"en": "bottom-right", "fr": "inférieur droit",
                              "ar": "السفلية اليمنى", "nl": "rechtsonder"},
    "calibration.corner_bl": {"en": "bottom-left", "fr": "inférieur gauche",
                              "ar": "السفلية اليسرى", "nl": "linksonder"},
    "calibration.touch_plane_done": {
        "en": "Touch plane calibrated from {n} samples across {corners} corners.",
        "fr": "Plan tactile calibré à partir de {n} échantillons sur {corners} coins.",
        "ar": "تمت معايرة مستوى اللمس من {n} عينة عبر {corners} زوايا.",
        "nl": "Aanraakvlak gekalibreerd uit {n} samples over {corners} hoeken."},

    "calibration.corner_point_step": {
        "en": ("Point at the {corner} corner of the wall with your index finger "
               "(no contact needed), hold steady, then click OK."),
        "fr": ("Pointez le coin {corner} du mur avec votre index (pas besoin de "
               "toucher), maintenez, puis cliquez sur OK."),
        "ar": ("أشر إلى الزاوية {corner} من الحائط بإصبعك السبابة (دون الحاجة "
               "للمس)، حافظ على ثباته، ثم انقر موافق."),
        "nl": ("Wijs met uw wijsvinger naar de {corner} hoek van de muur (geen "
               "aanraking nodig), houd stil, klik dan op OK.")},
    "calibration.corners_done": {
        "en": "{n}/4 corners measured live from the tracker.",
        "fr": "{n}/4 coins mesurés en direct par le suivi de main.",
        "ar": "تم قياس {n}/4 من الزوايا مباشرة عبر تتبع اليد.",
        "nl": "{n}/4 hoeken live gemeten door de tracker."},
    "calibration.corners_incomplete": {
        "en": ("Only {n}/4 corners were measured (hand not seen in time) — "
               "falling back to an estimated mapping."),
        "fr": ("Seulement {n}/4 coins mesurés (main non détectée à temps) — "
               "repli sur une projection estimée."),
        "ar": ("تم قياس {n}/4 زوايا فقط (لم يتم رصد اليد في الوقت المناسب) — "
               "الرجوع إلى إسقاط تقديري."),
        "nl": ("Slechts {n}/4 hoeken gemeten (hand niet op tijd gezien) — "
               "terugvallen op een geschatte projectie.")},
    "calibration.alignment_step": {
        "en": ("Point at the highlighted target on the wall with your index "
               "finger, hold steady, then click OK. (target {n} of {total})"),
        "fr": ("Pointez la cible affichée sur le mur avec votre index, "
               "maintenez, puis cliquez sur OK. (cible {n} sur {total})"),
        "ar": ("أشر إلى الهدف المميز على الحائط بإصبعك السبابة، حافظ على "
               "ثباته، ثم انقر موافق. (الهدف {n} من {total})"),
        "nl": ("Wijs naar het gemarkeerde doel op de muur met uw wijsvinger, "
               "houd stil, klik dan op OK. (doel {n} van {total})")},
    "calibration.alignment_result": {
        "en": "Alignment measured from {n} live targets — mean error {err:.3f}.",
        "fr": "Alignement mesuré sur {n} cibles réelles — erreur moyenne {err:.3f}.",
        "ar": "تم قياس المحاذاة من {n} أهداف حقيقية — متوسط الخطأ {err:.3f}.",
        "nl": "Uitlijning gemeten op {n} live doelen — gemiddelde fout {err:.3f}."},
    "btn.log_class": {"en": "Log this class", "fr": "Journaliser le cours",
                      "ar": "تسجيل هذا الدرس", "nl": "Les loggen"},
    "btn.export_journal": {"en": "Export journal (PDF)",
                           "fr": "Exporter le journal (PDF)",
                           "ar": "تصدير السجل (PDF)",
                           "nl": "Exporteer logboek (PDF)"},
    "journal.title": {"en": "Class journal", "fr": "Journal de classe",
                      "ar": "سجل الفصل", "nl": "Lesboek"},
    "journal.notes_prompt": {
        "en": "Notes for this class (optional):",
        "fr": "Notes pour ce cours (optionnel) :",
        "ar": "ملاحظات لهذا الدرس (اختياري):",
        "nl": "Notities voor deze les (optioneel):"},
    "journal.logged": {
        "en": "Class logged for {date} (entry {n}).",
        "fr": "Cours journalisé pour le {date} (entrée {n}).",
        "ar": "تم تسجيل الدرس بتاريخ {date} (إدخال {n}).",
        "nl": "Les gelogd voor {date} (item {n})."},
    "journal.pdf_title": {"en": "EDU-AIR — Class journal",
                          "fr": "EDU-AIR — Journal de classe",
                          "ar": "EDU-AIR — سجل الفصل",
                          "nl": "EDU-AIR — Lesboek"},
    "journal.col_date": {"en": "Date", "fr": "Date", "ar": "التاريخ", "nl": "Datum"},
    "journal.col_time": {"en": "Time", "fr": "Heure", "ar": "الوقت", "nl": "Tijd"},
    "journal.col_pages": {"en": "Pages", "fr": "Pages", "ar": "الصفحات", "nl": "Pagina's"},
    "journal.col_notes": {"en": "Notes", "fr": "Notes", "ar": "ملاحظات", "nl": "Notities"},
    "journal.mail_subject": {
        "en": "EDU-AIR class journal", "fr": "Journal de classe EDU-AIR",
        "ar": "سجل الفصل EDU-AIR", "nl": "EDU-AIR lesboek"},
    "journal.mail_body": {
        "en": "The class journal PDF is attached below (drag it in from "
              "the file browser that just opened).",
        "fr": "Le PDF du journal de classe est à joindre ci-dessous "
              "(glissez-le depuis l'explorateur de fichiers qui vient de "
              "s'ouvrir).",
        "ar": "ملف PDF لسجل الفصل يُرفق أدناه (اسحبه من متصفح الملفات "
              "الذي فُتح للتو).",
        "nl": "De PDF van het lesboek moet hieronder worden bijgevoegd "
              "(sleep het vanuit de zojuist geopende bestandsverkenner)."},
    "export.journal_empty": {
        "en": "No classes logged yet — click \"Log this class\" first.",
        "fr": "Aucun cours journalisé — cliquez d'abord sur « Journaliser le cours ».",
        "ar": "لم يتم تسجيل أي درس بعد — انقر أولاً على «تسجيل هذا الدرس».",
        "nl": "Nog geen lessen gelogd — klik eerst op \"Les loggen\"."},
    "export.journal_success": {
        "en": "Journal exported to {path} — mail compose window opened, "
              "attach the PDF from the file browser that just opened.",
        "fr": "Journal exporté sous {path} — fenêtre de composition mail "
              "ouverte, joignez le PDF depuis l'explorateur de fichiers "
              "qui vient de s'ouvrir.",
        "ar": "تم تصدير السجل إلى {path} — تم فتح نافذة إنشاء البريد، "
              "أرفق ملف PDF من متصفح الملفات الذي فُتح للتو.",
        "nl": "Logboek geëxporteerd naar {path} — mailvenster geopend, "
              "voeg de PDF toe vanuit de zojuist geopende "
              "bestandsverkenner."},
    "label.shape_correction": {
        "en": "Shape correction", "fr": "Correction de formes",
        "ar": "تصحيح الأشكال", "nl": "Vormcorrectie"},
    "btn.quick_calibration": {
        "en": "Quick calibration (3 pts)", "fr": "Calibration rapide (3 pts)",
        "ar": "معايرة سريعة (3 نقاط)", "nl": "Snelle kalibratie (3 pt)"},
    "calibration.quick_point_step": {
        "en": ("Point at the highlighted target on the wall with your index "
               "finger, hold steady, then click OK. (point {n} of {total})"),
        "fr": ("Pointez la cible affichée sur le mur avec votre index, "
               "maintenez, puis cliquez sur OK. (point {n} sur {total})"),
        "ar": ("أشر إلى الهدف المميز على الحائط بإصبعك السبابة، حافظ على "
               "ثباته، ثم انقر موافق. (النقطة {n} من {total})"),
        "nl": ("Wijs naar het gemarkeerde doel op de muur met uw wijsvinger, "
               "houd stil, klik dan op OK. (punt {n} van {total})")},
    "calibration.quick_done": {
        "en": "Quick calibration updated from {n}/3 points.",
        "fr": "Calibration rapide mise à jour à partir de {n}/3 points.",
        "ar": "تم تحديث المعايرة السريعة من {n}/3 نقاط.",
        "nl": "Snelle kalibratie bijgewerkt met {n}/3 punten."},
    "calibration.quick_incomplete": {
        "en": ("Only {n}/3 points were measured (hand not seen in time) — "
               "pointer calibration left unchanged."),
        "fr": ("Seulement {n}/3 points mesurés (main non détectée à temps) — "
               "calibration du pointeur inchangée."),
        "ar": ("تم قياس {n}/3 نقاط فقط (لم يتم رصد اليد في الوقت المناسب) — "
               "معايرة المؤشر لم تتغير."),
        "nl": ("Slechts {n}/3 punten gemeten (hand niet op tijd gezien) — "
               "kalibratie van de aanwijzer ongewijzigd.")},
    "calibration.quick_no_camera": {
        "en": "Quick calibration needs a live camera tracker (unavailable "
              "in demo mode or before the camera starts).",
        "fr": "La calibration rapide nécessite un suivi caméra en direct "
              "(indisponible en mode démo ou avant le démarrage caméra).",
        "ar": "تتطلب المعايرة السريعة تتبعًا مباشرًا بالكاميرا (غير متوفر في "
              "وضع العرض التجريبي أو قبل تشغيل الكاميرا).",
        "nl": "Snelle kalibratie vereist een live camera-tracker (niet "
              "beschikbaar in demomodus of voordat de camera start)."},

    # ---- overlay HUD ------------------------------------------------------
    "hud.slide": {
        "en": "Slide {cur}/{total} [{state}]",
        "fr": "Diapo {cur}/{total} [{state}]",
        "ar": "الشريحة {cur}/{total} [{state}]",
        "nl": "Dia {cur}/{total} [{state}]"},
    "hud.board_page": {
        "en": "Board page {cur}/{total} ({bg})",
        "fr": "Page tableau {cur}/{total} ({bg})",
        "ar": "صفحة اللوحة {cur}/{total} ({bg})",
        "nl": "Bord pagina {cur}/{total} ({bg})"},
    "bg.blank": {"en": "Blank", "fr": "Vide", "ar": "فارغ", "nl": "Leeg"},
    "bg.grid": {"en": "Grid", "fr": "Quadrillage", "ar": "شبكة", "nl": "Rooster"},
    "bg.lines": {"en": "Ruled lines", "fr": "Lignes", "ar": "أسطر", "nl": "Lijnen"},
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