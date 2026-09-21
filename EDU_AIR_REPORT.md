# EDU-AIR — Contactless Interactive Classroom
## Implementation & Testing Report

Status: **complete, actively evolving** — 307 automated tests in
`tests_edu_air` (up from 98 at v1.0.0), all passing, plus the 197 tests of
the shared `hadj_no_touch` base the app is built on.

---

## 1. What was built

EDU-AIR transforms the **HADJ NO-TOUCH AI** base system into a classroom
system that needs nothing but a **computer + webcam + projector** — no
touchscreen hardware required, though the projected surface *can* now be
made touch-reactive in software (§3.12). The teacher stands in front of the
class and uses hand gestures and voice in **English, French, Arabic or
Dutch** to:

- start / navigate / stop a slide presentation (F5/←/→/B/Page keys);
- control an **interactive pointer** (smoothed, spike-protected, calibrated);
- **annotate** the projected image (draw / highlight / dots at distance) on
  a full **multi-page interactive whiteboard** (TNI), with export;
- switch to **wall/touch mode**: the projected surface itself becomes the
  input device, via webcam-based finger/shadow/IR-pen/marker detection —
  no dedicated touch-sensitive board hardware;
- run a **voice quiz** (A/B/C/D answers, reveal, results, CSV export) and
  tally **student participation** (CSV export);
- follow a prepared **lesson plan** ("next step" walks through slides,
  quizzes, timed group work and whiteboard pages in sequence);
- rehearse a class alone in **rehearsal mode** before presenting live;
- start/stop a **classroom timer**;
- calibrate the webcam→projector alignment via a **live, interactive**
  corner + alignment wizard;
- optionally run voice recognition **fully offline** (Vosk), never silently
  falling back to the online engine once offline is requested.

All logic is in a new package `edu_air/` that reuses the HADJ infrastructure
(hand tracking, gesture classifier, Win32 input, voice catalogue, safety
primitives) without any required network dependency (voice defaults to the
online Google engine, but never *has* to leave the machine — see §3.16). A
fully synthetic **demo mode** (`--demo`) lets the whole flow be previewed
with zero hardware.

### Deliverables created

| File | Purpose |
|---|---|
| `edu_air/__init__.py` | package metadata |
| `edu_air/config.py` | persisted settings (JSON in `%LOCALAPPDATA%\EDU-AIR`) |
| `edu_air/pointer.py` | interactive pointer (calibration + quality pipeline) |
| `edu_air/presentation.py` | presentation controller/driver abstraction |
| `edu_air/annotation.py` | air-annotation ink model (draw/highlight/erase) |
| `edu_air/board.py` | multi-page interactive whiteboard (TNI) around the ink model |
| `edu_air/touch/` | wall/touch mode: `SurfaceTouchDetector` + 3 interchangeable backends (shadow-gap, IR pen, colour marker), palm rejection, contact state machine, per-zone calibration, drift monitor |
| `edu_air/quiz.py` | voice quiz engine + CSV results export |
| `edu_air/participation.py` | manual participation tally + CSV export |
| `edu_air/lesson.py` | lesson-plan sequencer (slide/quiz/timer/board steps) |
| `edu_air/voice.py` | EN/FR/AR/NL classroom voice-command catalogue |
| `edu_air/intent.py` | voice/gesture → classroom-action intent engine |
| `edu_air/safety.py` | deny-by-default safety gate |
| `edu_air/calibration.py` | interactive projector calibration + homography |
| `edu_air/accessibility.py` | large targets, dwell, reduced motion, presets |
| `edu_air/demo.py` | synthetic hands + scripted teaching sequence |
| `edu_air/classroom.py` | central `ClassroomSession` state machine (re-exports `backends`/`classroom_status`, see below) |
| `edu_air/backends.py` | `ClassroomBackend`/`RealBackend`/`DemoBackend`/`RecordingBackend` (split out of `classroom.py`) |
| `edu_air/classroom_status.py` | `ClassroomStatus` HUD/dock snapshot dataclass (split out of `classroom.py`) |
| `edu_air/ui.py` | PySide6 control dock (`ClassroomWindow`) |
| `edu_air/overlay.py` | transparent full-screen projector overlay (`OverlayWindow`, split out of `ui.py`) |
| `edu_air/pipeline.py` | camera/gesture/voice/touch background loop (`ClassroomPipeline`, `LowFpsWatchdog`, split out of `ui.py`) |
| `edu_air/logging_setup.py` | rotating file logging (no camera/audio content) |
| `edu_air_main.py` | entry point (real or `--demo`) |
| `lessons/example_lesson.json` | bundled example plan, opened by default by "Load lesson…" |
| `tests_edu_air/` | 307 hardware-free tests (~30 files) |
| `requirements.txt` | dependency list (Vosk offline voice is optional, commented) |
| `build_edu_air.py` | PyInstaller build script |
| `Lancer_EDU_AIR.bat` / `Lancer_EDU_AIR_Demo_TNI.bat` | one-click launchers |

---

## 2. Architecture

```
 webcam ---------> HandTracker (HADJ) ------> GestureEngine (HADJ)
                      |  landmarks                    |  GestureEvent
                      |                                |
                      +--> SurfaceTouchDetector (edu_air.touch, wall mode)
                      |        |  TouchEvent (DOWN/MOVE/UP)
 mic ------------> SpeechManager (HADJ, Google or offline Vosk) -> cvoice.parse()
                      |  recognised text                          |  ClassroomVoiceResult
                                                                   v
                                          ClassroomIntentEngine
                                          (voice + gesture + touch -> action)
                                                      |
                                                      v
                                          ClassroomSafetyEngine
                                          (deny-by-default gate)
                                                      |
                                                      v
                                     ClassroomSession._apply(action)
                              |         |         |         |         |
                      Presentation  Board    Quiz /     Lesson   Participation
                      Controller   (TNI ink) Timer      Plan     Tracker
                              |         |
                       Backend (Real=Win32 / Demo / Recording)
```

Key design decisions:

- **Model/logic separated from Qt.** Pointer, presentation, annotation, quiz,
  calibration, voice, intent and safety are pure Python with no GUI — fully
  unit-testable.
- **OS seam via drivers/backends.** `PresentationDriver`, `ClassroomBackend`
  (`RealBackend`, `DemoBackend`, `RecordingBackend`) keep the OS calls out of
  logic; demo mode never touches the keyboard/mouse.
- **Safety by default.** Every intent must be registered in the classroom
  action catalogue (`edu_air.safety`). Unknown/LLM/typo actions are refused.
  `ANNOTATION_CLEAR` requires confirmation; `QUIZ_STOP` is *critical* and is
  never auto-approved. Demo mode auto-approves to stay fluid.
- **Demo = same session, synthetic input.** `DemoSession` feeds the real
  `ClassroomSession` with synthetic hands and a localized script, so the demo
  exercises the identical state machine as real use.

---

## 3. Feature details

### 3.1 Interactive pointer  (`pointer.py`)
Pipeline: raw fingertip → clamp → calibration homography → **spike rejection**
(single-frame jumps over `max_jump_ratio` × diagonal are ignored) → **dead
zone** (sub-threshold tremor held) → sensitivity gain → **EMA smoothing with
jitter damping** → screen pixels. Three sensitivity presets (low/medium/high).
Metrics (tremor, spikes, latency) are reported to the HUD.

### 3.2 Presentation controller  (`presentation.py`)
State machine `IDLE ↔ ACTIVE ↔ PAUSED`, keymap for PowerPoint/Impress/PDF
(F5, ESC, Right/Left, B, Ctrl+Plus/Minus, PgUp/PgDn). All commands produce a
`CommandRecord` for the audit trail. `go_to()` scrolls relatively (PowerPoint
cannot jump directly).

### 3.3 Air annotation + interactive whiteboard (TNI)  (`annotation.py`, `board.py`)
Normalized [0..1] coordinates that render identically on any projector
resolution. Tools: point (dot), draw (ink), highlight (wide translucent),
erase (radius-based stroke removal). Live stroke model with `dirty`
repainting; max stroke cap; undo. `WhiteboardModel` (`board.py`) lifts this
single ink model into a full multi-page notebook: unlimited pages (each
with its own ink + background skin — blank/grid/ruled lines), page
navigation/add/delete, per-page undo, JSON notebook save/load (auto-restore
on startup when enabled) and whole-board PDF/image export.
`ClassroomSession.annotation` stays a thin property over the *current*
page's model, so every gesture/touch drawing path keeps working unchanged.

### 3.4 Voice quiz  (`quiz.py`, `voice.py`)
State machine `idle → question → answered → results`. Teacher drives it by
voice: `start/end quiz`, `next/previous question`, `show answer`,
`answer A/B/C/D` (also **Ar**abic: `الاجابه ب` and **Fr**ench: `réponse b`).
Statistics (correct/wrong/skipped) + per-question elapsed time.

### 3.5 Voice commands, EN/FR/AR/NL  (`voice.py`)
The HADJ phrase catalogue is extended at runtime with classroom phrases
(quiz, pointer, annotation, timer, pause, wall-mode toggle, board
navigation, participation marking, "next/previous step" for the lesson
sequencer). Robustness fixes over the base parser were added in EDU-AIR:
- answer-letter capture is re-extracted by EDU-AIR itself (the base parser
  does not forward `(?P<letter>…)`);
- Arabic hamza-normalized patterns (`ابدا`…) so recognised text matches;
- Arabic letters `ا ب ج د` map to `a b c d`;
- Dutch (`nl`) added as a fourth full language across every classroom
  phrase category, not just a subset.

### 3.6 Intent engine + routing  (`intent.py`)
Canonical map of voice/gesture → classroom action + **domain routing**
(`route()`): while a quiz is running, presentation/annotation/timer actions
are swallowed, but quiz actions and safety toggles always pass.

### 3.7 Calibration  (`calibration.py`)
6 wizard stages (camera / projection area / corners / touch plane /
alignment / gesture test), each with honest status
(`done/skipped/failed/partial`). Builds a webcam→projector **homography**
(RANSAC) with an affine fallback. Skipped corners are flagged on the report
as *estimated*, never silently precise. Corners and live alignment now run
as a genuine **interactive wizard** (`ui.py::_calibrate_corners_live` /
`_calibrate_alignment_live`) that captures real fingertip samples from the
live camera feed and projects a moving target on the overlay — not just an
autofill shortcut; the touch-plane stage (§3.12) is skipped automatically
if wall mode is never engaged, so it never breaks a contactless-only setup.
A `HomographyDriftMonitor` watches mapped touch positions for
out-of-bounds drift during a session and surfaces a "recalibration
suggested" flag on the HUD instead of silently mis-tracking.

### 3.8 Accessibility  (`accessibility.py`)
Large targets, one-hand gestures, dwell click presets, reduced motion,
voice-first hinting; presets are applied to pointer/annotation settings.

### 3.9 Classroom session + safety  (`classroom.py`, `safety.py`)
`ClassroomSession` aggregates everything, converts every input into a
`ClassroomIntent`, and runs it only after the safety gate. It records every
interaction to an audit log and publishes a `ClassroomStatus` snapshot for
the overlay HUD.

### 3.10 UI  (`ui.py`, `overlay.py`, `pipeline.py`)
Originally one 2117-line `ui.py`; split this session into three modules
(re-exported from `ui.py` for compatibility, so no call site broke):
- **ClassroomWindow** (`ui.py`, control dock): status grid, tool palette,
  sensitivity, language selector, camera preview, keyboard fallback
  (F5/arrows/B/Delete/A-D work without gestures), wall-mode/touch settings,
  lesson sequencer controls, participation/quiz export buttons, rehearsal
  toggle, offline-voice checkbox.
- **OverlayWindow** (`overlay.py`): transparent full-screen painter over the
  projector — strokes, pointer crosshair, quiz panel (question/options/
  score), calibration target and HUD (incl. the wall-mode badge).
- **ClassroomPipeline** (`pipeline.py`): background loop (camera → tracker →
  gesture engine → touch detector → session) with a synthetic-hand fallback
  in demo mode and an isolated camera reader thread (a stuck driver can no
  longer freeze the whole app); emits preview frames and voice text via Qt
  signals; includes `LowFpsWatchdog`, which auto-switches the classroom to
  its low-CPU preset after a sustained FPS drop instead of staying stuck
  degraded.

### 3.11 Demo mode  (`demo.py`)
Synthetic `HandData` builds (`_fan_landmarks`), a wandering `moving_point`,
and a scripted teaching sequence (EN/FR/AR/NL) that runs the full classroom
journey (start → next/prev slides → quiz → answers → reveal → end).

### 3.12 Wall/touch mode  (`edu_air/touch/`)
Turns the projected surface itself into a touch input, without dedicated
touch-sensitive hardware:
- **`SurfaceTouchDetector`** (`touch/detector.py`) orchestrates one of three
  interchangeable backends (`touch/backends/`):
  - **`ShadowGapFingerBackend`** (default) — measures the pixel gap between
    a fingertip and its own projector-cast shadow as a contact proxy, with
    adaptive contrast-vs-local-background thresholds (no hard-coded
    brightness constants) and a consecutive-dark-run check that rejects a
    body/arm shadow being mistaken for a finger's;
  - **`IRPenBackend`** — an infrared pen/LED, detected the same
    adaptive-contrast way rather than a fixed global threshold;
  - **`ColorMarkerBackend`** — an HSV-tracked coloured marker + shadow-gap.
- **`PalmRejectionFilter`** picks one real fingertip candidate out of all
  tracked hands, honouring the "require pose" setting end-to-end.
- **`ContactStateMachine`** applies hysteresis (`down_threshold <
  up_threshold` + debounce frames) so DOWN/MOVE/UP never flickers.
- **`plane_calibration.py`** learns a per-zone (3×3 grid) baseline from
  the touch-plane calibration stage instead of one global constant.
- **`HomographyDriftMonitor`** (§3.7) watches for a calibration that no
  longer fits the room.
- Wired into `ClassroomSession.handle_touch_event` (`classroom.py`):
  contact itself *is* the click in wall mode (mirrors the contactless
  pinch-click path one-for-one), gated by `interaction_mode == MODE_WALL`
  and toggled via voice/gesture/keyboard (`W`) — `TOGGLE_WALL_MODE` is a
  safety toggle, so switching never waits on a confirmation dialog while a
  teacher's hand is on the wall.

### 3.13 Participation tracking  (`participation.py`)
A manual per-mark tally (`ParticipationTracker`) the teacher triggers by
voice/gesture/button each time a student participates — a single
teacher-facing webcam has no way to see which student raised a hand, so
this is the teacher marking the moment themselves. Same CSV export shape
as the quiz results (`quiz.py`'s `QuizAnswerRecord`/`to_csv_rows`).

### 3.14 Lesson sequencer  (`lesson.py`)
`LessonPlan`/`LessonStep`: an ordered course outline (slide/quiz/timer/
board steps) a teacher prepares ahead of class as JSON
(`lessons/example_lesson.json` ships as a working example, opened by
default by "Load lesson…") and steps through live with one "next step"
command. Each step is a named shortcut through the *same* safety-gated
actions a teacher would trigger by hand (`next_slide`, `quiz.start`,
`board.next_page`, or a timer that auto-stops after its planned duration) —
never a new capability, and it deliberately does **not** auto-stop an
active quiz when moving to the next step (ending a quiz is a CRITICAL,
always-confirmed action; a lesson step must never silently bypass that).

### 3.15 Rehearsal mode
A `set_rehearsal_mode` toggle on `OverlayWindow` lets a teacher preview the
whole flow — pointer, annotations, quiz panel, wall-mode badge — on their
own screen before presenting to a class, without needing a second
projector.

### 3.16 Offline voice (Vosk)  (`hadj_no_touch/voice/speech_recognition.py`)
`VoskSpeechEngine` runs recognition fully locally (audio never leaves the
machine); `SpeechManager` never silently falls back to the online Google
engine once offline was explicitly requested — it disables voice instead
and surfaces that honestly. No model ships by default (40 MB–1+ GB per
language); `resolve_vosk_model_path()` auto-detects a `models/vosk-<lang>/`
folder dropped next to the app (source tree or built `.exe`, no rebuild
needed) and a dock checkbox ("Offline voice (Vosk)") opts in once one is
present.

---

## 4. Testing

Command used (project root):

```
py -3.12 -m pytest tests_edu_air -q
```

Result: **307 passed** (2 benign deprecation warnings from the
`speech_recognition` dependency; run repeatedly for stability against a
known unrelated flake — an intermittent native `sounddevice`/PortAudio
crash on test collection that self-resolves on retry and reproduces even
on an unmodified checkout).

The original 98-test suite (v1.0.0, table below) is unchanged; ~209 tests
were added across ~19 new files for wall/touch mode, the interactive
whiteboard (TNI), participation, the lesson sequencer, rehearsal mode, the
low-FPS watchdog, quiz/participation CSV export, and the `ui.py`/
`classroom.py` split — summarized after the original table rather than
enumerated test-by-test.

| Test file | # tests | What it covers |
|---|---|---|
| `test_pointer.py` | 10 | first sample, mirror, dead zone, spike rejection, sensitivity presets, invalid preset fallback, EMA convergence, disabled pointer, calibration hook, reset |
| `test_presentation.py` | 9 | idle-ignored, start F5, clamping, stop ESC, pause toggle, Ctrl+zoom, page scroll, go-to relative, history/callback |
| `test_annotation.py` | 8 | stroke lifecycle, highlight flag, dot, erase radius, clear/undo, max-strokes trim, geometry→pixels, noop in point mode |
| `test_quiz.py` | 11 | start, correct/wrong/ignore-repeat stats, inactive-safe, navigation/reveal, results transition, stop, restart, tick, labels |
| `test_voice.py` | 11 | idempotent registration, empty-safe, EN/FR/AR quiz, answer-letter params (EN/FR/AR), pointer/annotation, timer/pause, unknown→none |
| `test_intent.py` | 9 | voice mapping, quiz mapping, presentation mapping, unmapped→none, gesture mapping, REST→none, routing (safety-toggle pass, quiz-gating, quiz pass, pointer/annotation) |
| `test_safety.py` | 9 | deny-by-default, safe allowed, clear→confirm, quiz-stop always critical, "all" level, allow-list restriction, audit, registry, on_audit callback |
| `test_calibration.py` | 7 | homography round-trip, <4 pts, linear fallback, stage order, full wizard, estimated corners, partial gesture test, camera-fail/reset |
| `test_classroom.py` | 15 | 3-language demo e2e, real-mode keys, unknown-voice ignore, swipe/circle gestures, quiz critical/pending/approve/deny, annotation draw, clear confirm (real) vs auto (demo), timer tick, status snapshot, control lock, voice answer, recorded clicks |
| `test_demo.py` | 5 | synthetic hand index tip, pinch thumb-index, moving point bounds, script start marker, demo session feeds classroom |
| `test_ui_smoke.py` | 1 | GUI boots in demo mode and exits cleanly (Windows only) |

### Tests added since v1.0.0 (by area)

| Area | Test files | Covers |
|---|---|---|
| Wall/touch mode | `test_touch_state_machine.py`, `test_touch_detector.py`, `test_touch_palm_rejection.py`, `test_touch_shadow_search.py`, `test_touch_backends_integration.py`, `test_touch_calibration_stage.py`, `test_touch_plane_calibration.py`, `test_touch_drift_monitor.py`, `test_touch_performance.py`, `test_touch_settings.py`, `test_classroom_touch.py` | hysteresis, palm rejection (`require_pose`), shadow search + body-shadow rejection, per-backend detection (shadow-gap/IR pen/colour marker), zone calibration, drift monitoring, per-frame performance ceiling, settings round-trip, end-to-end `handle_touch_event` |
| Interactive whiteboard (TNI) | `test_board.py` | pages, navigation, per-page undo, backgrounds, notebook save/load (incl. malformed-file robustness), voice/safety integration |
| Lesson sequencer | `test_lesson.py`, `test_classroom_lesson.py` | pure `LessonPlan` state machine, JSON load robustness, bundled example file, end-to-end step execution (slide/quiz/timer/board), voice phrases |
| Participation | `test_participation.py`, `test_classroom_participation.py` | tally + CSV export, safety-gated end-to-end, voice phrase |
| Offline voice | `test_voice_offline.py` | `resolve_vosk_model_path()` resolution order, settings persistence (incl. old-config-file backward compatibility) |
| Other UX | `test_low_fps_watchdog.py`, `test_quiz_export.py`, `test_calibration_median.py` | auto low-CPU downgrade, quiz CSV export, calibration median helper |
| Live GUI (`test_ui_smoke.py`, extended) | — | wall-mode toggle, fingertip capture + overlay calibration target, rehearsal mode, lesson sequencer — all driven against a *real* running `ClassroomPipeline`/Qt event loop, not mocks |

### Manual verification performed
- `edu_air_main.py --demo` launched via a real background process,
  windows enumerated by handle, dock screenshotted (`PrintWindow`) and
  driven via Windows UI Automation (button clicks, checkbox state) —
  repeated after the `ui.py`/`classroom.py` split and after adding the
  lesson sequencer and offline-voice checkbox, each time confirming no
  crash and the expected on-screen state.
- Python 3.12 import smoke-test of all edu_air modules passed.

---

## 5. Hardware & environment

| Item | Requirement | Cost hint |
|---|---|---|
| Computer | Windows 10/11, Python 3.10–3.12 | any office PC |
| Webcam | 640×480 or better, facing the teacher | standard built-in/webcam ≈ low cost |
| Projector | any resolution ≥ 800×600 | school projector |
| Microphone | optional; EN/FR/AR/NL voice commands | built-in mic is enough |

No touchscreen, no special sensor required. All computation is local with
MediaPipe hand tracking + OpenCV; voice defaults to the online Google
engine but can run fully offline via Vosk once a model is added (§3.16) —
network access is a convenience, never a hard requirement.

---

## 6. Safety model summary

| Risk | Example | Behaviour |
|---|---|---|
| safe | next slide, zoom, timer, quiz start/next/answer, board page nav, participation mark, lesson step | runs immediately |
| confirm | clear all annotations, clear/delete a board page | requires confirmation (unless demo, or level=none) |
| critical | end the quiz session | always an explicit confirmation — never auto-approved, and a lesson step advancing away from a quiz step deliberately does not bypass this (§3.14) |
| unknown | any action not in the catalogue | denied by default, audited as blocked |
| pause/stop | pause presentation, pointer off, wall-mode toggle, participation mark | safety toggles bypass confirmation so an incident can always be stopped reflexively, or a reflexive command always lands |

Every executed/blocked/pending action is written to the rotation log and the
in-memory audit trail.

---

## 7. How to run

```bat
:: real mode (webcam + mic + real computer control)
Lancer_EDU_AIR.bat

:: demo mode (synthetic hands/voice, nothing touches the OS)
Lancer_EDU_AIR_Demo.bat
:: or
py -3.12 edu_air_main.py --demo
```

Tests:

```bat
py -3.12 -m pytest tests_edu_air -q
```

---

## 8. Known limitations (honest scope)

- Corners and live alignment now run as a genuine interactive wizard
  (§3.7); the remaining wizard stages (camera/projection-area/gesture-test)
  are still lighter-weight checks rather than a full guided walkthrough.
- Wall/touch mode tracks **one contact at a time** (palm rejection selects
  a single candidate) — no simultaneous multi-touch like some dedicated
  interactive-whiteboard hardware. It is also sensitive to ambient
  lighting and camera/projector positioning; the drift monitor (§3.7)
  flags when a recalibration looks warranted rather than silently
  mis-tracking, but it cannot substitute for a stable setup.
- Offline voice (Vosk, §3.16) has no small, general-purpose Arabic model
  at the same ~40 MB tier as EN/FR/NL — the closest options are a
  Tunisian-dialect model (~165 MB, may not match the mostly Modern
  Standard Arabic classroom commands well) or an MSA model starting
  around ~330 MB. No model is bundled; this is a deliberate deployment
  decision left to whoever packages the app, not a code gap.
- Voice sends recognised text into the session from the speech thread; in a
  multi-classroom deployment the session would be wrapped with a queue so all
  inputs were serialised (safe already: Qt-queued signals for GUI-bound
  paths, plain-callable connections execute on the emitting thread and rely
  on the same GIL-based informal thread-safety as the rest of the pipeline —
  acceptable for a single-teacher, single-session desktop app, not for
  concurrent sessions).
- Base-parser alternation length scoring is reused from HADJ; EDU-AIR works
  around its Arabic edge cases with locally registered, longer patterns.
- `QuestionBank.load()` (JSON quiz banks) has no call site in the current
  UI (quiz questions are the built-in set) and, unlike `board.py`/
  `lesson.py`, does not yet guard a malformed field the way §3.3/3.14's
  loaders do — low priority while it stays unreachable from the app, but
  worth the same fix before any UI wires it up.