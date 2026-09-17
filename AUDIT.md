# HADJ NO-TOUCH AI â€” Full Audit (Step 0)

Audit date: 2026-09-16. Base: `HADJ NO-TOUCH AI v3.0` (HEAD 40eb0f5 + uncommitted v3.0 work).
Verified on this machine: Python 3.12.10, PySide6 + MediaPipe + OpenCV + numpy installed.
Test suite: `py -3.12 -m pytest tests` â†’ **196 passed, 4 warnings** (~17.6 s).
This exactly matches the `CHECKLISTS.md` release target, confirming checked-in claims are real.

## 1. Verdict

The build is genuinely working, well-architected and honest in most places:

- REAL vs DEMO badge, AUDIO ONLINE / AUDIO LOCAL badge, deny-by-default Safety Engine,
  honest `SKIPPED` results from the Test Lab, no fabricated metrics â€” all real and tested.
- The "AI" is **rule-based / heuristic**, not generative. This must stay labelled honestly.
- Detection â†’ Intent â†’ Authorization â†’ Execution layers are kept separate in the code.

Critical gap (breaking the honesty/safety doctrine):

- The Gesture Trainer auto-fires a saved custom gesture on any similar motion at
  confidence >= 0.55 in the live loop (`core/app.py:331-336`) with no test-then-assign
  step and no confirmation â€” including `launch_app`, `type_text`, `open_document`.
  This is the single most important safety gap.

## 2. Feature matrix â€” Feature | Status | Reliability | Priority

Status legend: Real / Experimental / Simulation / Unavailable / Missing / Broken.
Reliability: High (tested) / Medium / Low, based on code review + test suite.

### Perception

| Feature | Status | Reliability | Priority |
|---|---|---|---|
| Camera manager (DirectShow/MSMF, uniform-frame rejection, retry, cached probe) | Real | High (tested) | P1 |
| Hand tracking (MediaPipe, up to 2 hands, handedness selection) | Real | High | P1 |
| Face tracking / head direction (FaceMesh) | Real | Medium (light-dependent) | P2 |
| Gaze estimation (iris) | Experimental, optional, off by default | Low | P4 |
| Environment quality (lighting/contrast estimate) | Real | Medium | P3 |
| Interaction plane + homography calibration (5 stages) | Real â€” estimated mapping, not touch | Medium | P1 |

### Interaction

| Feature | Status | Reliability | Priority |
|---|---|---|---|
| Air mouse (dead zones, smoothing, mirroring, left-handed) | Real | High | P1 |
| Gesture classifier (9 poses, confidence >= 0.55) | Real | High (tested) | P1 |
| Gesture engine (temporal FSM, debounce, cooldown, jump rejection, drag, scroll) | Real | High (tested) | P1 |
| Click precision metrics (clean <= 12% drift) | Real, measured | High | P1 |
| Pinch click/drag, double/right click, scroll, swipe | Real | High (tested) | P1 |
| Fist lock, palm pause | Real | Medium | P2 |
| Virtual keyboard (air keyboard) | Real (button/settings only) | Medium | P4 |
| Laser pointer mode | Real | High | P2 |

### AI / Intent

| Feature | Status | Reliability | Priority |
|---|---|---|---|
| Intent engine (gesture â†’ context â†’ action) | Real | High (tested) | P1 |
| Context engine (foreground window â†’ 7 categories) | Real | High | P1 |
| Multimodal fusion (gaze-gate, copilot hint) | Real; gaze inputs experimental | Medium | P3 |
| AI Action Planner (preview â†’ confirm â†’ run) | Real â€” heuristic rules, not generative AI | Medium | P2 |
| AI Copilot suggestions | Real heuristic hints | Medium | P3 |

### Voice

| Feature | Status | Reliability | Priority |
|---|---|---|---|
| EN/FR/AR command parsing (40+ intents) | Real | High (tested) | P1 |
| Google engine (online, default) | Real | High when online | P1 |
| Vosk (offline) | Available but not shipped (dep commented) | Medium | P1 |
| SAPI (offline) | Unavailable â€” honestly disabled, no silent fallback | â€” | P3 |
| Dictation | Real | Medium | P3 |
| Custom voice commands | Real | High | P2 |

### Automation

| Feature | Status | Reliability | Priority |
|---|---|---|---|
| Macros (voice/gesture/button triggers, multi-step, persisted) | Real | High (tested) | P2 |
| Custom gestures (teach-my-gesture, 24x42 templates) | Real â€” AUTO-FIRES live at >=0.55, no test step | Medium | P1 |
| Custom commands registry | Real | High | P2 |
| History + analytics | Real | High | P2 |
| Head actions (turn/direction â†’ context actions) | Real | Medium | P3 |

### Windows control

| Feature | Status | Reliability | Priority |
|---|---|---|---|
| Mouse (SendInput) | Real | High (tested) | P1 |
| Keyboard (VK map + Unicode typing) | Real | High (tested) | P1 |
| Media keys + pycaw (optional) | Real | Medium | P2 |
| Window/app control (launch, close, minimize, switch) | Real | Medium | P2 |
| Screenshot (Pillow) | Real | High | P3 |

### Safety / Privacy

| Feature | Status | Reliability | Priority |
|---|---|---|---|
| Safety Engine (RISK levels, registry, deny-by-default) | Real | High (tested) | P0 |
| Confirmation prompts (safe/confirm/critical) | Real | High (tested) | P0 |
| Emergency stop â€” keyboard + voice + UI button | Real (all 3 paths) | High | P0 |
| Demo mode (simulates, loud, exempt safety toggles) | Real | High (tested) | P0 |
| Privacy mode (blur, halts processing) + camera/mic toggles | Real | High | P0 |
| AUDIO ONLINE / AUDIO LOCAL honest badge | Real | High | P0 |
| Voice engine choices (Google/Vosk/SAPI) + honest AUDIO ONLINE/LOCAL disclosure; Vosk/SAPI never send audio | Real | High | P2 |
| Offline-first voice policy (`offline_first`, default off): prefers local Vosk; if no Vosk model when on, voice is DISABLED with explicit disclosure, never a silent Google fallback (config.py + speech_recognition.py offline_first seam) | Real | High | P1 |
| Static landing publish — alternate hosts: `netlify.toml` + `web/_headers` publish only the `web/` PWA landing (same unit `vercel.json`/`vercel.json` publishes). The AI is a local desktop app and is NEVER deployed to any host | Real, disk-verified (tests/test_netlify_deploy.py, 196 green) | High | P1 |
| Clear-all-data / activity log | Real | High | P3 |

### UI / Web / Build

| Feature | Status | Reliability | Priority |
|---|---|---|---|
| Dashboard (badges, metrics, controls) | Real | High | P1 |
| Calibration wizard | Real â€” "Skip" button does NOT skip (broken) | Medium | P2 |
| Gesture trainer | Real â€” test-then-assign gate added (P1a): recorded samples are replayed through the same resample+distance machinery and must pass a reproducibility dry-run (`core/app.py:1206` â†’ `ui/gesture_trainer.py:172`) before an action is bound; nothing persists on failure | Medium | P1 |
| Macro Studio / Planner preview / Test Lab / Settings / Help | Real | High | P2 |
| Debug panel | Real â€” minor bugs (gaze double-assign, unbounded buffer) | Medium | P4 |
| Tray icon | Real | High | P2 |
| PWA landing + demo (mouse-simulated air pointer, fake player) | Real but Simulation, no backend | n/a | P4 |
| PyInstaller build | Real | Medium â€” SHIPS `web/.env.local` OIDC token | P1 |
| Config (JSON) + SQLite (WAL) persistence | Real | High | P1 |
| Tests (196 passed / 4 warnings) | Real | High | P0 |

### Missing / deferred (labelled honestly)

| Feature | Status | Priority |
|---|---|---|
| Offline-first default (Vosk bundled side by side) | Missing (Google online is default) | P1 |
| Wake word / phrase confirmation for critical voice cmds | Missing | P1 |
| Metric DB / automatic baseline recording | Missing | P3 |
| Local AI agent (v3), SDK/API, enterprise | Missing â€” v3 roadmap | â€” |
| Generative ("LLM") features | Missing by design (heuristic only) | â€” |

## 3. Top issues

1. **Gesture Trainer auto-fires saved gestures live** with no test-then-assign step and
   no confirmation (`core/app.py:331-336`) â€” violates Authorization-before-execution
   for custom actions.
2. **`build_app.py` bundles `web/.env.local` (live Vercel OIDC token) + `.vercel/`
   into the shipped EXE** â€” secret leak. Remove from bundle.
3. Calibration wizard **"Skip (estimate)" behaves identically to "Confirm"** â€” it does
   not skip.
4. `logging_setup.py` **silently swallows** file-handler failures.
5. Debug panel: gaze row double-assign, unbounded CSV buffer.
6. Offline story incomplete â€” SAPI honestly unavailable, Vosk not bundled.

## 4. Other findings (minor)

- `calibration_wizard.py`: `start_calibration()` not guarded against a missing camera;
  imports `cv2` and `numpy` awkwardly; `anchors_norm[:1]` draws only one anchor.
- `gesture_trainer.py`: records block the UI thread (~1.2 s per sample); names default
  to "custom"; empty action saves as "(unassigned)" but says "assigned to dashboard";
  gesture names containing " â†’ " are mis-parsed on delete.
- `panels.py` Settings Center: applies `head` values via `self.core.head` attributes that
  may desync from `self.head`; SAPI correctly listed as unavailable.
- `main_window.py` / `dashboard.py`: mostly clean; tray + dialogs wired correctly.
- `build_app.py`: no icon, no version metadata; warns success from folder existence.
- `web/`: honest PWA demo; `.env.local` token leak (see issue 2).

## 5. Test suite

13 files, 196 test functions. Verified green on this machine. Coverage sweet spots:
safety, demo mode, history, performance, macros, planner, custom commands, head tracking,
custom gestures matching, camera probing, calibration, interaction plane, keyboard VK map,
voice parsing, privacy/sensitivity honesty seams.
