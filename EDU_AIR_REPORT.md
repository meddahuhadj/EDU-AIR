# EDU-AIR — Contactless Interactive Classroom
## Implementation & Testing Report

Status: **complete** — 98 automated tests, all passing.

---

## 1. What was built

EDU-AIR transforms the **HADJ NO-TOUCH AI** base system into a contactless
classroom system that needs nothing but a **computer + webcam + projector**.
No touchscreen is required. The teacher stands in front of the class and uses
hand gestures and voice in **English, French or Arabic** to:

- start / navigate / stop a slide presentation (F5/←/→/B/Page keys);
- control an **interactive pointer** (smoothed, spike-protected, calibrated);
- **annotate** the projected image (draw / highlight / dots at distance);
- run a **voice quiz** (A/B/C/D answers, reveal, results);
- start/stop a **classroom timer**;
- calibrate the webcam→projector alignment in **5 steps**.

All logic is in a new package `edu_air/` that reuses the HADJ infrastructure
(hand tracking, gesture classifier, Win32 input, voice catalogue, safety
primitives) without any network dependency. A fully synthetic **demo mode**
(`--demo`) lets the whole flow be previewed with zero hardware.

### Deliverables created

| File | Purpose |
|---|---|
| `edu_air/__init__.py` | package metadata (v1.0.0) |
| `edu_air/config.py` | persisted settings (JSON in `%LOCALAPPDATA%\EDU-AIR`) |
| `edu_air/pointer.py` | interactive pointer (calibration + quality pipeline) |
| `edu_air/presentation.py` | presentation controller/driver abstraction |
| `edu_air/annotation.py` | air-annotation model (draw/highlight/erase) |
| `edu_air/quiz.py` | voice quiz engine |
| `edu_air/voice.py` | EN/FR/AR classroom voice-command catalogue |
| `edu_air/intent.py` | voice/gesture → classroom-action intent engine |
| `edu_air/safety.py` | deny-by-default safety gate |
| `edu_air/calibration.py` | 5-step projector calibration + homography |
| `edu_air/accessibility.py` | large targets, dwell, reduced motion, presets |
| `edu_air/demo.py` | synthetic hands + scripted teaching sequence |
| `edu_air/classroom.py` | central `ClassroomSession` state machine + backends |
| `edu_air/ui.py` | PySide6 control window + projection overlay + pipeline |
| `edu_air/logging_setup.py` | rotating file logging (no camera/audio content) |
| `edu_air_main.py` | entry point (real or `--demo`) |
| `tests_edu_air/` | 98 hardware-free tests (11 files) |
| `edu_air_requirements.txt` | pinned dependency list |
| `Lancer_EDU_AIR.bat` / `Lancer_EDU_AIR_Demo.bat` | one-click launchers |

---

## 2. Architecture

```
 webcam ---------> HandTracker (HADJ) ------> GestureEngine (HADJ)
                      |  landmarks                    |  GestureEvent
 mic ------------> SpeechManager (HADJ) -------> cvoice.parse() (edu_air)
                      |  recognised text             |  ClassroomVoiceResult
                                                      v
                                          ClassroomIntentEngine
                                          (voice + gesture -> action)
                                                      |
                                                      v
                                          ClassroomSafetyEngine
                                          (deny-by-default gate)
                                                      |
                                                      v
                                     ClassroomSession._apply(action)
                                      |          |         |
                           Presentation   Annotation   Quiz / Timer
                           Controller     Model       Engine
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

### 3.3 Air annotation  (`annotation.py`)
Normalized [0..1] coordinates that render identically on any projector
resolution. Tools: point (dot), draw (ink), highlight (wide translucent),
erase (radius-based stroke removal). Live stroke model with `dirty`
repainting; max stroke cap; undo.

### 3.4 Voice quiz  (`quiz.py`, `voice.py`)
State machine `idle → question → answered → results`. Teacher drives it by
voice: `start/end quiz`, `next/previous question`, `show answer`,
`answer A/B/C/D` (also **Ar**abic: `الاجابه ب` and **Fr**ench: `réponse b`).
Statistics (correct/wrong/skipped) + per-question elapsed time.

### 3.5 Voice commands, EN/FR/AR  (`voice.py`)
The HADJ phrase catalogue is extended at runtime with classroom phrases
(quiz, pointer, annotation, timer, pause). Robustness fixes over the base
parser were added in EDU-AIR:
- answer-letter capture is re-extracted by EDU-AIR itself (the base parser
  does not forward `(?P<letter>…)`);
- Arabic hamza-normalized patterns (`ابدا`…) so recognised text matches;
- Arabic letters `ا ب ج د` map to `a b c d`.

### 3.6 Intent engine + routing  (`intent.py`)
Canonical map of voice/gesture → classroom action + **domain routing**
(`route()`): while a quiz is running, presentation/annotation/timer actions
are swallowed, but quiz actions and safety toggles always pass.

### 3.7 Calibration  (`calibration.py`)
5 wizard stages (camera / projection area / corners / alignment / gesture
test), each with honest status (`done/skipped/failed/partial`). Builds a
webcam→projector **homography** (RANSAC) with an affine fallback. Skipped
corners are flagged on the report as *estimated*, never silently precise.

### 3.8 Accessibility  (`accessibility.py`)
Large targets, one-hand gestures, dwell click presets, reduced motion,
voice-first hinting; presets are applied to pointer/annotation settings.

### 3.9 Classroom session + safety  (`classroom.py`, `safety.py`)
`ClassroomSession` aggregates everything, converts every input into a
`ClassroomIntent`, and runs it only after the safety gate. It records every
interaction to an audit log and publishes a `ClassroomStatus` snapshot for
the overlay HUD.

### 3.10 UI  (`ui.py`)
- **ClassroomWindow** (control dock): status grid, tool palette, sensitivity,
  language selector, camera preview, keyboard fallback (F5/arrows/B/Delete
  /A-D work without gestures).
- **OverlayWindow**: transparent full-screen painter over the projector —
  strokes, pointer crosshair, quiz panel (question/options/score) and HUD.
- **ClassroomPipeline**: background loop (camera → tracker → gesture engine →
  session) with a synthetic-hand fallback in demo mode; emits preview frames
  and voice text via Qt signals.

### 3.11 Demo mode  (`demo.py`)
Synthetic `HandData` builds (`_fan_landmarks`), a wandering `moving_point`,
and a 3-language scripted teaching sequence that runs the full classroom
journey (start → next/prev slides → quiz → answers → reveal → end).

---

## 4. Testing

Command used (project root):

```
py -3.12 -m pytest tests_edu_air -q
```

Result: **98 passed** (2 benign deprecation warnings from the
`speech_recognition` dependency).

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

### Manual verification performed
- `edu_air_main.py --demo` launches, stays running, and exits cleanly on
  request (verified with a 6 s live run + forced termination).
- Python 3.12 import smoke-test of all edu_air modules passed.

---

## 5. Hardware & environment

| Item | Requirement | Cost hint |
|---|---|---|
| Computer | Windows 10/11, Python 3.10–3.12 | any office PC |
| Webcam | 640×480 or better, facing the teacher | standard built-in/webcam ≈ low cost |
| Projector | any resolution ≥ 800×600 | school projector |
| Microphone | optional; EN/FR/AR voice commands | built-in mic is enough |

No touchscreen, no special sensor, no network. All computation is local with
MediaPipe hand tracking + OpenCV.

---

## 6. Safety model summary

| Risk | Example | Behaviour |
|---|---|---|
| safe | next slide, zoom, timer, quiz start/next/answer | runs immediately |
| confirm | clear all annotations | requires confirmation (unless demo, or level=none) |
| critical | end the quiz session | always an explicit confirmation — never auto-approved |
| unknown | any action not in the catalogue | denied by default, audited as blocked |
| pause/stop | pause presentation, pointer off | safety toggles bypass confirmation so an incident can always be stopped reflexively |

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

- `ui.py::_run_calibration` is a **quick-autofill** wizard around the real
  calibration state machine; a fully interactive 5-step walkthrough can be
  wired to the live tracker with the same `ProjectorCalibration` object.
- Voice sends recognised text into the session from the speech thread; in a
  multi-classroom deployment the session would be wrapped with a queue so all
  inputs were serialised (safe already: Qt-queued signals, single session).
- Base-parser alternation length scoring is reused from HADJ; EDU-AIR works
  around its Arabic edge cases with locally registered, longer patterns.