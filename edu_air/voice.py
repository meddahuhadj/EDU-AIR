"""Classroom voice commands (English / French / Arabic).

Extends the HADJ voice-command catalogue with classroom-specific phrases and
maps them to classroom intents. Parsing is fully local (the recognised text
is matched against the phrase catalogue; no audio or text ever leaves the
machine for this step).

Supported classroom voice control:
  "Next slide" / "Slide suivante" / "الشريحة التالية"
  "Previous slide"
  "Start" / "Start presentation"
  "Pause" (black screen)
  "Start quiz", "Next question", "Answer A/B/C/D", "Show answer", "End quiz"
  "Open the next exercise"
  "Zoom in / zoom out", "Scroll up / down"
  "Draw", "Highlight", "Erase", "Clear annotations"
  "Show pointer / Hide pointer"
  "Start timer"
  Board: "next page", "new page", "grid / ruled lines / blank page", "undo"
  Lesson sequencer: "next step" / "previous step"

Every phrase resolves to a canonical classroom intent. The classroom intent
engine then maps it to an approved, registered classroom action (see
``edu_air.safety``) — never to arbitrary computer commands.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from hadj_no_touch.voice import voice_commands as vc

# --- classroom intent names (canonical, engine-agnostic) -------------------
START_QUIZ = "START_QUIZ"
STOP_QUIZ = "STOP_QUIZ"
RESTART_QUIZ = "RESTART_QUIZ"
NEXT_QUESTION = "NEXT_QUESTION"
PREV_QUESTION = "PREV_QUESTION"
ANSWER_LETTER = "ANSWER_LETTER"
REVEAL_ANSWER = "REVEAL_ANSWER"
POINTER_ON = "POINTER_ON"
POINTER_OFF = "POINTER_OFF"
TOGGLE_WALL_MODE = "TOGGLE_WALL_MODE"
ANNOTATE = "ANNOTATE"            # params: tool in draw|highlight|erase
DRAW = "DRAW"
HIGHLIGHT = "HIGHLIGHT"
ERASE_ANNOTATION = "ERASE_ANNOTATION"
CLEAR_ANNOTATIONS = "CLEAR_ANNOTATIONS"
PAUSE_PRESENTATION = "PAUSE_PRESENTATION"
RESUME_PRESENTATION = "RESUME_PRESENTATION"
NEXT_EXERCISE = "NEXT_EXERCISE"
START_TIMER = "START_TIMER"
STOP_TIMER = "STOP_TIMER"
PARTICIPATION_MARK = "PARTICIPATION_MARK"
LESSON_NEXT = "LESSON_NEXT"
LESSON_PREV = "LESSON_PREV"

# --- interactive whiteboard (TNI) -------------------------------------------
BOARD_NEXT_PAGE = "BOARD_NEXT_PAGE"
BOARD_PREV_PAGE = "BOARD_PREV_PAGE"
BOARD_ADD_PAGE = "BOARD_ADD_PAGE"
BOARD_CLEAR_PAGE = "BOARD_CLEAR_PAGE"
BOARD_DELETE_PAGE = "BOARD_DELETE_PAGE"
BOARD_BACKGROUND = "BOARD_BACKGROUND"          # raw text scanned for the skin
BOARD_UNDO = "BOARD_UNDO"

# Intent constants already defined by the HADJ voice catalogue that the
# classroom reuses directly.
from hadj_no_touch.voice.voice_commands import (  # noqa: F401
    NEXT_SLIDE, PREV_SLIDE, START_PRESENTATION, END_PRESENTATION,
    ZOOM_IN, ZOOM_OUT, SCROLL_UP, SCROLL_DOWN,
)

# Convert a spoken letter to an answer index 0..3.
LETTER_TO_INDEX = {"a": 0, "b": 1, "c": 2, "d": 3}
AR_LETTER_TO_LATIN = {"ا": "a", "ب": "b", "ج": "c", "د": "d"}


@dataclass
class ClassroomVoiceResult:
    intent: str = vc.NONE_INTENT
    params: dict = field(default_factory=dict)
    confidence: float = 0.0
    language: str = "en"
    raw_text: str = ""


def _ar_normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    out = []
    for c in text:
        if unicodedata.combining(c):
            continue
        if c in "أإآ":
            c = "ا"
        elif c == "ة":
            c = "ه"
        elif c == "ى":
            c = "ي"
        elif c == "ـ":
            continue
        out.append(c)
    return "".join(out).lower()


# ---------------------------------------------------------------------------
# Classroom phrase catalogue (appended to the HADJ catalogue at runtime).
# Each entry: {intent, langs, patterns, param, map} where ``map`` applies a
# lambda to the captured param value.
# ---------------------------------------------------------------------------
CLASSROOM_COMMANDS: list[dict] = [
    # --- quiz ---------------------------------------------------------------
    {"intent": START_QUIZ, "langs": ["en"],
     "patterns": [r"\bstart\s+(?:a\s+|the\s+|this\s+)?quiz\b",
                  r"\bbegin\s+(?:a\s+|the\s+|this\s+)?quiz\b"]},
    {"intent": START_QUIZ, "langs": ["fr"],
     "patterns": [r"\b(?:d[ée]marrer|commencer|lancer)\s+(?:un\s+|le\s+)?quiz\b"]},
    {"intent": START_QUIZ, "langs": ["ar"],
     "patterns": [r"ابدا\s+الاختبار|بدء\s+الاختبار|شغل\s+الاختبار"]},

    {"intent": STOP_QUIZ, "langs": ["en"],
     "patterns": [r"\b(?:end|stop|quit|exit)\s+(?:the\s+|this\s+)?quiz\b"]},
    {"intent": STOP_QUIZ, "langs": ["fr"],
     "patterns": [r"\b(?:terminer|arr[eê]ter|finir)\s+(?:le\s+)?quiz\b"]},
    {"intent": STOP_QUIZ, "langs": ["ar"],
     "patterns": [r"انهي\s+الاختبار|اوقف\s+الاختبار|انتهاء\s+الاختبار"]},

    {"intent": RESTART_QUIZ, "langs": ["en"],
     "patterns": [r"\brestart\s+(?:the\s+|this\s+)?quiz\b"]},
    {"intent": RESTART_QUIZ, "langs": ["fr"],
     "patterns": [r"\bre(?:commencer|jouer)\s+(?:le\s+)?quiz\b"]},
    {"intent": RESTART_QUIZ, "langs": ["ar"],
     "patterns": [r"اعاده\s+الاختبار|اعد\s+الاختبار"]},

    {"intent": NEXT_QUESTION, "langs": ["en"],
     "patterns": [r"\bnext\s+(?:question|exercise)\b", r"\bfollowing\s+question\b"]},
    {"intent": NEXT_QUESTION, "langs": ["fr"],
     "patterns": [r"\b(?:question|exercice)\s+suivant(e)?\b"]},
    {"intent": NEXT_QUESTION, "langs": ["ar"],
     "patterns": [r"السؤال\s+التالي|السوال\s+التالي"]},

    {"intent": PREV_QUESTION, "langs": ["en"],
     "patterns": [r"\bprevious\s+question\b", r"\bprev\s+question\b",
                  r"\bback\s+to\s+(?:the\s+)?previous\s+question\b"]},
    {"intent": PREV_QUESTION, "langs": ["fr"],
     "patterns": [r"\bquestion\s+pr[ée]c[ée]dente\b"]},
    {"intent": PREV_QUESTION, "langs": ["ar"],
     "patterns": [r"السؤال\s+السابق"]},

    {"intent": REVEAL_ANSWER, "langs": ["en"],
     "patterns": [r"\bshow\s+(?:me\s+)?(?:the\s+)?answer\b",
                  r"\breveal\s+(?:the\s+)?answer\b"]},
    {"intent": REVEAL_ANSWER, "langs": ["fr"],
     "patterns": [r"\baffiche\s+(?:la\s+)?r[ée]ponse\b",
                  r"\br[ée]v[èe]le\s+(?:la\s+)?r[ée]ponse\b"]},
    {"intent": REVEAL_ANSWER, "langs": ["ar"],
     "patterns": [r"اظهر\s+الاجابه|اظهر\s+الجواب|اكشف\s+الاجابه"]},

    # answer letter: "answer A", "I choose B", "option C", "B please"
    {"intent": ANSWER_LETTER, "langs": ["en"],
     "patterns": [r"\banswer\s+(?:is\s+|it's\s+)?(?P<letter>[abcd])\b",
                  r"\b(?:i\s+)?(?:pick|choose)\s+(?:option\s+)?(?P<letter>[abcd])\b",
                  r"\boption\s+(?P<letter>[abcd])\b",
                  r"\b(?P<letter>[abcd])\s+please\b"]},
    {"intent": ANSWER_LETTER, "langs": ["fr"],
     "patterns": [r"\br[ée]ponse\s+(?P<letter>[abcd])\b",
                  r"\bchoisis\s+(?:la\s+)?lettre\s+(?P<letter>[abcd])\b",
                  r"\boption\s+(?P<letter>[abcd])\b",
                  r"\b(?P<letter>[abcd])\s+s'il\s+vous\s+pla[iî]t\b"]},
    {"intent": ANSWER_LETTER, "langs": ["ar"],
     "patterns": [r"(?:الاجابه|الجواب)\s+(?P<letter>[ابجداabcd])",
                  r"اختر\s+(?P<letter>[ابجداabcd])"]},

    # --- presentation extras ------------------------------------------------
    {"intent": START_PRESENTATION, "langs": ["ar"],
     "patterns": [r"ابدا\s+العرض\s+التقديمي"]},
    {"intent": PREV_SLIDE, "langs": ["ar"],
     "patterns": [r"الشريحه\s+السابقه|ارجع\s+(?:الى\s+)?الشريحه\s+السابقه|عرض\s+الشريحه\s+السابقه"]},
    {"intent": PAUSE_PRESENTATION, "langs": ["en"],
     "patterns": [r"\bpause\s+(?:the\s+)?presentation\b",
                  r"\bblack\s+(?:screen|out)\b", r"\bblank\s+screen\b"]},
    {"intent": PAUSE_PRESENTATION, "langs": ["fr"],
     "patterns": [r"\bpause\s+(?:la\s+)?pr[ée]sentation\b",
                  r"\b[ée]cran\s+noir\b"]},
    {"intent": PAUSE_PRESENTATION, "langs": ["ar"],
     "patterns": [r"ايقاف\s+مؤقت\s+للعرض|شاشه\s+سوداء|تجميد\s+العرض"]},

    {"intent": RESUME_PRESENTATION, "langs": ["en"],
     "patterns": [r"\b(?:resume|continue|unpause)\s+(?:the\s+)?presentation\b",
                  r"\b(?:resume|continue|unpause)\b"]},
    {"intent": RESUME_PRESENTATION, "langs": ["fr"],
     "patterns": [r"\b(?:reprendre|continuer|unpause)\s+(?:la\s+)?pr[ée]sentation\b",
                  r"\b(?:reprendre|continuer|unpause)\b",
                  r"\breprendre\s+(?:le\s+)?cours\b"]},
    {"intent": RESUME_PRESENTATION, "langs": ["ar"],
     "patterns": [r"استئناف\s+العرض|متابعة\s+العرض|واصل"]},

    {"intent": NEXT_EXERCISE, "langs": ["en"],
     "patterns": [r"\bnext\s+exercise\b", r"\bopen\s+(?:the\s+)?next\s+exercise\b"]},
    {"intent": NEXT_EXERCISE, "langs": ["fr"],
     "patterns": [r"\bexercice\s+suivant\b", r"\bouvre\s+l'exercice\s+suivant\b"]},
    {"intent": NEXT_EXERCISE, "langs": ["ar"],
     "patterns": [r"التمرين\s+التالي|التمارين\s+التاليه|افتح\s+التمرين\s+التالي"]},

    # --- interactive pointer --------------------------------------------------
    {"intent": POINTER_ON, "langs": ["en"],
     "patterns": [r"\b(?:show|enable|turn\s+on|activate)\s+(?:the\s+)?(?:pointer|laser)\b",
                  r"\bpointer\s+on\b"]},
    {"intent": POINTER_ON, "langs": ["fr"],
     "patterns": [r"\baffiche\s+le\s+pointeur\b", r"\bpointeur\s+en\s+marche\b"]},
    {"intent": POINTER_ON, "langs": ["ar"],
     "patterns": [r"اظهر\s+المؤشر|فعل\s+المؤشر"]},

    {"intent": POINTER_OFF, "langs": ["en"],
     "patterns": [r"\b(?:hide|disable|turn\s+off|deactivate)\s+(?:the\s+)?(?:pointer|laser)\b",
                  r"\bpointer\s+off\b"]},
    {"intent": POINTER_OFF, "langs": ["fr"],
     "patterns": [r"\bcache\s+le\s+pointeur\b", r"\bpointeur\s+arr[êe]t[ée]\b"]},
    {"intent": POINTER_OFF, "langs": ["ar"],
     "patterns": [r"اخفاء\s+المؤشر|ايقاف\s+المؤشر"]},

    # --- wall / touch mode -----------------------------------------------------
    {"intent": TOGGLE_WALL_MODE, "langs": ["en"],
     "patterns": [r"\b(?:wall|touch|smartboard)\s+mode\b",
                  r"\bswitch\s+to\s+(?:the\s+)?(?:wall|touch)\s+mode\b"]},
    {"intent": TOGGLE_WALL_MODE, "langs": ["fr"],
     "patterns": [r"\bmode\s+mural\b", r"\bmode\s+tableau\b",
                  r"\bpasse(?:r)?\s+(?:en|au)\s+mode\s+mural\b"]},
    {"intent": TOGGLE_WALL_MODE, "langs": ["ar"],
     "patterns": [r"وضع\s+الجدار|وضع\s+اللمس"]},

    # --- annotation tools -----------------------------------------------------
    {"intent": DRAW, "langs": ["en", "fr"],
     "patterns": [r"\bdraw(?:ing)?\s+mode\b", r"\bdessin\s+mode\b", r"\bdessiner\b"]},
    {"intent": DRAW, "langs": ["ar"], "patterns": [r"وضع\s+الرسم|رسم"]},

    {"intent": HIGHLIGHT, "langs": ["en"],
     "patterns": [r"\bhighligh(t|ting)\s+mode\b"]},
    {"intent": HIGHLIGHT, "langs": ["fr"],
     "patterns": [r"\bsurlign(er|age)\b"]},
    {"intent": HIGHLIGHT, "langs": ["ar"],
     "patterns": [r"تظليل|تمييز"]},

    {"intent": ERASE_ANNOTATION, "langs": ["en"],
     "patterns": [r"\beras(e|ing)\s+mode\b", r"\buse\s+the\s+eraser\b"]},
    {"intent": ERASE_ANNOTATION, "langs": ["fr"],
     "patterns": [r"\b(?:mode\s+)?effacement\b", r"\bgom(me|mer)\b"]},
    {"intent": ERASE_ANNOTATION, "langs": ["ar"],
     "patterns": [r"وضع\s+المسح|امسح"]},

    {"intent": CLEAR_ANNOTATIONS, "langs": ["en"],
     "patterns": [r"\bclear\s+(?:the\s+)?(?:annotation|annotations|board|notes|drawings)\b",
                  r"\bwipe\s+(?:the\s+)?board\b"]},
    {"intent": CLEAR_ANNOTATIONS, "langs": ["fr"],
     "patterns": [r"\befface(r)?\s+tout\b", r"\bvider\s+le\s+tableau\b"]},
    {"intent": CLEAR_ANNOTATIONS, "langs": ["ar"],
     "patterns": [r"امسح\s+السبورخ|امسح\s+السبوره|مسح\s+الكل"]},

    # --- interactive board (TNI) ----------------------------------------------
    {"intent": BOARD_NEXT_PAGE, "langs": ["en"],
     "patterns": [r"\b(?:next|following)\s+(?:board\s+)?page\b",
                  r"\bnext\s+(?:tni\s+)?whiteboard\b", r"\bfollowing\s+sheet\b"]},
    {"intent": BOARD_NEXT_PAGE, "langs": ["fr"],
     "patterns": [r"\bpage\s+suivante\b", r"\b(?:tableau|panneau)\s+suivant\b"]},
    {"intent": BOARD_NEXT_PAGE, "langs": ["ar"],
     "patterns": [r"الصفحة\s+التالية|الصفحات\s+التاليه|التالي\s+في\s+السبوره"]},
    {"intent": BOARD_NEXT_PAGE, "langs": ["nl"],
     "patterns": [r"\bvolgende\s+pagina\b", r"\bvolgende\s+blad\b"]},

    {"intent": BOARD_PREV_PAGE, "langs": ["en"],
     "patterns": [r"\bprevious\s+(?:board\s+)?page\b",
                  r"\bprevious\s+(?:tni\s+)?whiteboard\b", r"\bprevious\s+sheet\b"]},
    {"intent": BOARD_PREV_PAGE, "langs": ["fr"],
     "patterns": [r"\bpage\s+pr[ée]c[ée]dente\b"]},
    {"intent": BOARD_PREV_PAGE, "langs": ["ar"],
     "patterns": [r"الصفحة\s+السابقة|السابق\s+في\s+السبوره"]},
    {"intent": BOARD_PREV_PAGE, "langs": ["nl"],
     "patterns": [r"\bvorige\s+pagina\b", r"\bvorige\s+blad\b"]},

    {"intent": BOARD_ADD_PAGE, "langs": ["en"],
     "patterns": [r"\b(?:new|another)\s+(?:board\s+)?page\b",
                  r"\badd\s+(?:a\s+|an\s+)?page\b", r"\bfresh\s+page\b"]},
    {"intent": BOARD_ADD_PAGE, "langs": ["fr"],
     "patterns": [r"\bnouvelle\s+page\b", r"\bnouvelle\s+feuille\b",
                  r"\bajouter\s+(?:une\s+)?page\b"]},
    {"intent": BOARD_ADD_PAGE, "langs": ["ar"],
     "patterns": [r"صفحة\s+جديدة|ورقة\s+جديدة"]},
    {"intent": BOARD_ADD_PAGE, "langs": ["nl"],
     "patterns": [r"\bnieuwe\s+pagina\b", r"\bnieuw\s+blad\b"]},

    {"intent": BOARD_CLEAR_PAGE, "langs": ["en"],
     "patterns": [r"\bclear\s+(?:this|the)\s+page\b", r"\berase\s+(?:this|the)\s+page\b"]},
    {"intent": BOARD_CLEAR_PAGE, "langs": ["fr"],
     "patterns": [r"\befface(r)?\s+cette\s+page\b", r"\bvider\s+cette\s+page\b"]},
    {"intent": BOARD_CLEAR_PAGE, "langs": ["ar"],
     "patterns": [r"امسح\s+هذه\s+الصفحة|مسح\s+هذه\s+الصفحة"]},
    {"intent": BOARD_CLEAR_PAGE, "langs": ["nl"],
     "patterns": [r"\bwis\s+(?:deze|de)\s+pagina\b"]},

    {"intent": BOARD_DELETE_PAGE, "langs": ["en"],
     "patterns": [r"\bdelete\s+(?:this|the)\s+page\b", r"\bremove\s+(?:this|the)\s+page\b"]},
    {"intent": BOARD_DELETE_PAGE, "langs": ["fr"],
     "patterns": [r"\bsupprime\s+(?:cette|la)\s+page\b", r"\berase\s+(?:cette|la)\s+page\b"]},
    {"intent": BOARD_DELETE_PAGE, "langs": ["ar"],
     "patterns": [r"احذف\s+هذه\s+الصفحة|حذف\s+الصفحة"]},
    {"intent": BOARD_DELETE_PAGE, "langs": ["nl"],
     "patterns": [r"\bverwijder\s+(?:deze|de)\s+pagina\b"]},

    {"intent": BOARD_BACKGROUND, "langs": ["en"],
     "patterns": [r"\bgrid\s+(?:background\s+)?(?:on\s+)?(?:plea?se\s+page)?\b",
                  r"\bruled\s+(?:lines|paper)\b",
                  r"\b(?:empty|blank)\s+(?:page|whiteboard|board)\b"]},
    {"intent": BOARD_BACKGROUND, "langs": ["fr"],
     "patterns": [r"\bquadrill(?:age|é|e)\b", r"\blignes\s+r[ée]gl[ée]es\b",
                  r"\bpage\s+(?:blanche|vide)\b", r"\bfond\s+quadrill[ée]\b"]},
    {"intent": BOARD_BACKGROUND, "langs": ["ar"],
     "patterns": [r"شبك|جدول|مسطره|سطر\s+مستقيم|صفحة\s+فارغه|خلفيه\s+شبكيه"]},
    {"intent": BOARD_BACKGROUND, "langs": ["nl"],
     "patterns": [r"\bruit\s+(?:blokjes|grid)\b", r"\blijnen\s+(?:papier)?\b",
                  r"\blege\s+pagina\b"]},

    {"intent": BOARD_UNDO, "langs": ["en"],
     "patterns": [r"\bundo\b",
                  r"\bundo\s+(?:the\s+(?:last\s+)?)?(?:stroke|drawing|annotation)\b"]},
    {"intent": BOARD_UNDO, "langs": ["fr"],
     "patterns": [r"\ban[nu]ul(?:e|er)\s+(?:le\s+)?dernier\s+tra(?:it|ç|ce)\b",
                  r"\bannuler\s+le\s+dessin\b"]},
    {"intent": BOARD_UNDO, "langs": ["ar"],
     "patterns": [r"تراجع|ارجع\s+خطوه\s+واحده|الغاء\s+اخر\s+رسمه"]},
    {"intent": BOARD_UNDO, "langs": ["nl"],
     "patterns": [r"\bongedaan\s+maken\b", r"\bundo\b"]},

    # --- classroom timer ------------------------------------------------------
    {"intent": START_TIMER, "langs": ["en"],
     "patterns": [r"\b(?:start|begin|launch)\s+(?:a\s+|the\s+|this\s+)?(?:class|lesson)?\s*timer\b",
                  r"\btime\s+(?:me|us)\b"]},
    {"intent": START_TIMER, "langs": ["fr"],
     "patterns": [r"\b(?:d[ée]marre|lance)\s+le\s+chrono\b",
                  r"\bchronom[èe]tre\b"]},
    {"intent": START_TIMER, "langs": ["ar"],
     "patterns": [r"شغل\s+المؤقت|ابدأ\s+المؤقت|ابدأ\s+العد\s+التنازلي"]},

    {"intent": STOP_TIMER, "langs": ["en"],
     "patterns": [r"\b(?:stop|end|reset)\s+(?:the\s+)?timer\b"]},
    {"intent": STOP_TIMER, "langs": ["fr"],
     "patterns": [r"\barr[eê]te\s+le\s+chrono\b"]},
    {"intent": STOP_TIMER, "langs": ["ar"],
     "patterns": [r"اوقف\s+المؤقت"]},

    # --- participation tally --------------------------------------------------
    {"intent": PARTICIPATION_MARK, "langs": ["en"],
     "patterns": [r"\bparticipation\b",
                  r"\b(?:mark|log|count)\s+(?:a\s+)?participation\b",
                  r"\bgood\s+participation\b"]},
    {"intent": PARTICIPATION_MARK, "langs": ["fr"],
     "patterns": [r"\bparticipation\b",
                  r"\b(?:note|marque)\s+(?:une\s+)?participation\b"]},
    {"intent": PARTICIPATION_MARK, "langs": ["ar"],
     "patterns": [r"سجل\s+مشاركه|مشاركه\s+جيده"]},

    # --- lesson sequencer -------------------------------------------------------
    {"intent": LESSON_NEXT, "langs": ["en"],
     "patterns": [r"\bnext\s+step\b"]},
    {"intent": LESSON_PREV, "langs": ["en"],
     "patterns": [r"\b(?:previous|prior)\s+step\b"]},
    {"intent": LESSON_NEXT, "langs": ["fr"],
     "patterns": [r"\b[ée]tape\s+suivante\b"]},
    {"intent": LESSON_PREV, "langs": ["fr"],
     "patterns": [r"\b[ée]tape\s+pr[ée]c[ée]dente\b"]},
    {"intent": LESSON_NEXT, "langs": ["ar"],
     "patterns": [r"الخطوه\s+التاليه"]},
    {"intent": LESSON_PREV, "langs": ["ar"],
     "patterns": [r"الخطوه\s+السابقه"]},

    # --- Dutch --------------------------------------------------------------
    {"intent": START_QUIZ, "langs": ["nl"],
     "patterns": [r"\bstart\s+(?:de\s+|een\s+|dit\s+)?quiz\b",
                  r"\bbegin\s+(?:de\s+|een\s+)?quiz\b"]},
    {"intent": STOP_QUIZ, "langs": ["nl"],
     "patterns": [r"\b(?:stop|beeindig|be[ée]indig|sluit)\s+(?:de\s+)?quiz\b"]},
    {"intent": RESTART_QUIZ, "langs": ["nl"],
     "patterns": [r"\bherstart\s+(?:de\s+)quiz\b"]},
    {"intent": NEXT_QUESTION, "langs": ["nl"],
     "patterns": [r"\bvolgende\s+(?:vraag|oefening)\b"]},
    {"intent": PREV_QUESTION, "langs": ["nl"],
     "patterns": [r"\bvorige\s+vraag\b"]},
    {"intent": REVEAL_ANSWER, "langs": ["nl"],
     "patterns": [r"\b(?:toon|laat)\s+(?:het\s+)?antwoord\b",
                  r"\bantwoord\s+zien\b"]},
    {"intent": ANSWER_LETTER, "langs": ["nl"],
     "patterns": [r"\bantwoord\s+(?P<letter>[abcd])\b",
                  r"\bantwoord\s+is\s+(?P<letter>[abcd])\b",
                  r"\bik\s+kiess?\s+optie\s+(?P<letter>[abcd])\b",
                  r"\boptie\s+(?P<letter>[abcd])\b"]},
    {"intent": START_PRESENTATION, "langs": ["nl"],
     "patterns": [r"\bstart\s+presentatie\b", r"\bbegin\s+(?:de\s+)?presentatie\b"]},
    {"intent": PREV_SLIDE, "langs": ["nl"],
     "patterns": [r"\bvorige\s+(?:dia|slide)\b", r"\bga\s+terug\b"]},
    {"intent": NEXT_SLIDE, "langs": ["nl"],
     "patterns": [r"\bvolgende\s+(?:dia|slide)\b", r"\bvolgende\s+dia\b"]},
    {"intent": PAUSE_PRESENTATION, "langs": ["nl"],
     "patterns": [r"\bpauzeer\s+(?:de\s+)?presentatie\b", r"\bpauze\b"]},
    {"intent": NEXT_EXERCISE, "langs": ["nl"],
     "patterns": [r"\bvolgende\s+oefening\b"]},
    {"intent": POINTER_ON, "langs": ["nl"],
     "patterns": [r"\b(?:toon|activeer|zet\s+aan)\s+(?:de\s+)?pointer\b",
                  r"\bpointer\s+aan\b"]},
    {"intent": POINTER_OFF, "langs": ["nl"],
     "patterns": [r"\b(?:verberg|zet\s+uit)\s+(?:de\s+)?pointer\b",
                  r"\bpointer\s+uit\b"]},
    {"intent": TOGGLE_WALL_MODE, "langs": ["nl"],
     "patterns": [r"\bwand\s*modus\b", r"\baanraak\s*modus\b"]},
    {"intent": DRAW, "langs": ["nl"],
     "patterns": [r"\b(?:teken|tekening)\s+modus\b"]},
    {"intent": HIGHLIGHT, "langs": ["nl"],
     "patterns": [r"\bmarkeer\s+modus\b", r"\bmarkeren\b"]},
    {"intent": ERASE_ANNOTATION, "langs": ["nl"],
     "patterns": [r"\bgum\s+modus\b", r"\buitgummen\b"]},
    {"intent": CLEAR_ANNOTATIONS, "langs": ["nl"],
     "patterns": [r"\bwis\s+(?:het\s+)?(?:bord|scherm)\b",
                  r"\bmaak\s+het\s+bord\s+schoon\b"]},
    {"intent": START_TIMER, "langs": ["nl"],
     "patterns": [r"\bstart\s+(?:de\s+)?timer\b",
                  r"\bstart\s+(?:de\s+)?klok\b"]},
    {"intent": STOP_TIMER, "langs": ["nl"],
     "patterns": [r"\bstop\s+(?:de\s+)?timer\b", r"\bstop\s+(?:de\s+)?klok\b"]},
    {"intent": PARTICIPATION_MARK, "langs": ["nl"],
     "patterns": [r"\bparticipatie\b", r"\bnoteer\s+(?:een\s+)?participatie\b"]},
    {"intent": LESSON_NEXT, "langs": ["nl"],
     "patterns": [r"\bvolgende\s+stap\b"]},
    {"intent": LESSON_PREV, "langs": ["nl"],
     "patterns": [r"\bvorige\s+stap\b"]},
]


_registered = False


def register_classroom_commands() -> bool:
    """Register the classroom phrases into the shared HADJ voice catalogue.

    Idempotent: repeated registration never duplicates an intent+pattern pair.
    Returns True when the catalogue was actually extended on this call.
    """
    global _registered
    if _registered:
        return False
    # De-duplicate against existing entries (same intent + pattern).
    existing = {(c["intent"], tuple(c.get("patterns", [])))
                for c in vc.COMMANDS}
    added = 0
    for cmd in CLASSROOM_COMMANDS:
        key = (cmd["intent"], tuple(cmd.get("patterns", [])))
        if key not in existing:
            vc.COMMANDS.append(cmd)
            existing.add(key)
            added += 1
    _registered = True
    return added > 0


def _extract_letter(text: str, language: str = "en") -> str:
    """Recover the answer letter from the raw spoken text.

    The shared HADJ parser does not forward ``(?P<letter>...)`` captures, so
    the classroom layer re-scans its own catalogue to fill the parameter.
    """
    import re as _re
    lang = language.split("-")[0].lower() if "-" in language else language.lower()
    lang = {"en": "en", "fr": "fr", "ar": "ar", "nl": "nl"}.get(lang, "en")
    prepared = _ar_normalize(text.strip()) if lang == "ar" else text.strip().lower()
    for cmd in CLASSROOM_COMMANDS:
        if cmd["intent"] != ANSWER_LETTER or lang not in cmd["langs"]:
            continue
        for pattern in cmd["patterns"]:
            m = _re.search(pattern, prepared)
            if m:
                return m.group("letter")
    return ""


def parse(text: str, language: str = "en") -> ClassroomVoiceResult:
    """Parse classroom voice text into a canonical classroom intent.

    Combines the HADJ catalogue (slide/zoom/scroll/start/stop …) with the
    classroom catalogue (quiz, pointer, annotation, timer …).
    """
    register_classroom_commands()
    result = vc.parse(text, language)
    res = ClassroomVoiceResult(
        intent=result.intent,
        params=dict(result.params),
        confidence=result.confidence,
        language=result.language,
        raw_text=text,
    )
    # Answer-letter parameter: keep the letter lower-cased.
    if res.intent == ANSWER_LETTER:
        letter = str(res.params.get("letter", "")).lower()
        if not letter:
            letter = _extract_letter(text, res.language).lower()
        letter = AR_LETTER_TO_LATIN.get(letter, letter)
        res.params["letter"] = letter
        res.params["answer_index"] = LETTER_TO_INDEX.get(letter, -1)
    return res


class NoiseProbe:
    """Optional ambient-noise meter feeding the classroom traffic light.

    Uses ``sounddevice`` when available (the same backend as the voice
    recogniser); reports a coarse ``"ok"`` / ``"loud"`` verdict so the
    teacher gets an honest hint when recognition may struggle. Every failure
    path degrades to ``"unknown"`` — never crashes the pipeline.
    """

    RMS_LOUD = 0.02          # rough float32 RMS threshold for "loud"
    DEFAULT_SAMPLE_RATE = 44100

    def read(self, duration: float = 0.5) -> str:
        try:
            import numpy as np
            import sounddevice as sd
            samples = int(self.DEFAULT_SAMPLE_RATE * max(0.05, duration))
            rec = sd.rec(samples, samplerate=self.DEFAULT_SAMPLE_RATE,
                         channels=1, dtype="float32", blocking=True)
            rms = float(np.sqrt(float(np.mean(np.asarray(rec, dtype="float64") ** 2))))
            if not np.isfinite(rms) or rms < 1e-6:
                return "unknown"
            return "loud" if rms >= self.RMS_LOUD else "ok"
        except Exception:
            return "unknown"