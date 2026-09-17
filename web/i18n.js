/* ============================================================
   HADJ NO-TOUCH AI — i18n.js
   Full interface translation layer: English, Français, العربية,
   Nederlands. Runtime language switching, RTL support for Arabic,
   persisted choice, plain-text + innerHTML + aria-label targets.
   ============================================================ */

window.hadjI18n = (() => {
  "use strict";

  const VERSION = "1.3.0";
  const STORE_KEY = "hadj.notouch.lang";
  const SUPPORTED = ["en", "fr", "ar", "nl"];

  const NAMES = {
    en: "English",
    fr: "Français",
    ar: "العربية",
    nl: "Nederlands",
  };

  const DIR = { en: "ltr", fr: "ltr", nl: "ltr", ar: "rtl" };

  let current = "en";

  const STR = {
    /* ================= ENGLISH ================= */
    en: {
      "meta.title": "HADJ NO-TOUCH AI — Control the computer without touching it",
      "meta.desc":
        "Control the computer without touching it — hand gestures, voice and gaze for Windows. Privacy-first, camera frames stay local. Available in English, Français, العربية and Nederlands.",
      "skip": "Skip to content",
      "nav.aria": "Primary navigation",
      "nav.homeAria": "HADJ NO-TOUCH AI — home",
      "nav.how": "How it works",
      "nav.gestures": "Gestures",
      "nav.voice": "Voice",
      "nav.modes": "Modes",
      "nav.privacy": "Privacy",
      "nav.download": "Download",
      "nav.install": "Install",
      "nav.run": "Run on Windows",
      "lang.label": "Language — English",
      "hero.eyebrow": "Contactless computer control · Camera-local",
      "hero.title": 'Control the computer <span class="grad-text">without touching it.</span>',
      "hero.sub":
        "HADJ NO-TOUCH AI turns your webcam into a virtual interaction plane. Hand gestures, voice and gaze drive Windows — hands-free, private, and yours. No sensors, no touching — camera frames stay on your machine.",
      "hero.download": "Download for Windows",
      "hero.demo": "Try the demo",
      "hero.noteTitle": "Windows 10 / 11 (x64)",
      "hero.noteBody":
        "Packaged as a native desktop app, downloaded as a ZIP from GitHub Releases. Needs only a webcam + microphone — MediaPipe and the intent engine run locally, on this machine.",
      "hero.noteMeta":
        'After install there is no telemetry and no account, and the app downloads nothing at runtime. Note: voice recognition uses Google\'s cloud API by default — pick Vosk or SAPI for fully local recognition. Verify the binary with <code>SHA-256&nbsp;CAF27A9BE6B7CABE747A2FF817D9B5CA83142F6472F7C15D56EB20D29D98F188</code>.',
      "hero.chip1": '<span class="chip-dot" aria-hidden="true"></span>EN / FR / AR / NL voice',
      "hero.chip2": '<span class="chip-dot" aria-hidden="true"></span>Webcam only',
      "hero.chip3": '<span class="chip-dot" aria-hidden="true"></span>Camera stays local',
      "hero.chip4": '<span class="chip-dot" aria-hidden="true"></span>Privacy-first',
      "hero.demoAria":
        "Live demo of the virtual interaction plane — your mouse stands in for the air-pointer",
      "hero.live": "LIVE",
      "hero.trackTop": "HADJ-OS // TRACKING",
      "hero.grid": "GRID 20PX",
      "hero.target": "TARGET 01 · CLICK ZONE",
      "hero.pinchBtn": "PINCH TO CLICK",
      "demo.ready": "ready",
      "demo.clicked": "click ✓",
      "demo.hud.mode": "MODE",
      "demo.hud.gesture": "GESTURE",
      "demo.hud.x": "X",
      "demo.hud.y": "Y",
      "demo.hud.conf": "CONF",
      "demo.hud.clicks": "CLICKS",
      "demo.hint":
        'mouse = air pointer · <strong>hold left</strong> = pinch→click · <kbd>space</kbd> = palm mode · wheel = scroll',
      "demo.touchHint": "tap a control = pinch-click · drag = move the pointer",
      "demo.palmOn":
        'Palm mode ON — wheel scrolls <strong>big steps</strong>. <kbd>space</kbd> to exit.',
      "demo.noscript":
        "The live demo needs JavaScript. The Windows app itself works entirely on your machine, no browser required.",
      "demo.confirm": "PINCH CONFIRMED",
      "demo.confirmSub": "• click →",
      "hero.scroll": "SCROLL",
      "stats.profiles": "auto profiles",
      "stats.languages": "languages",
      "stats.webcam": "webcam",
      "stats.touch": "touch",
      "how.eyebrow": "01 / Pipeline",
      "how.title": "From webcam to Windows<br>control in one line of motion.",
      "how.lede":
        "Four local stages. Camera frames never leave your machine — every frame is handled on-device by bundled models and the runtime you already have.",
      "how.s1tag": "MediaPipe input layer",
      "how.s1title": "Webcam + Mic",
      "how.s1text":
        "Your camera streams frames locally into the tracking layer; the microphone feeds the voice engine (Google by default, or Vosk/SAPI for on-device recognition). Resolution and rate adapt to the machine so tracking stays smooth.",
      "how.s2tag": "MediaPipe landmarks",
      "how.s2title": "Track",
      "how.s2text":
        "Hands, face and pose landmarks are extracted at ~30 fps — 21 points per hand — with per-camera calibration for lighting and distance.",
      "how.s3tag": "Intent engine",
      "how.s3title": "Understand",
      "how.s3text":
        "Gesture + voice phrases are mapped onto a small set of intents with confidence scoring and debounce, so false triggers stay rare.",
      "how.s4tag": "Windows control layer",
      "how.s4title": "Act",
      "how.s4text":
        "Intent becomes a native action — mouse, keyboard, media keys, window and virtual-desktop control — through the OS API.",
      "gestures.eyebrow": "02 / Gesture library",
      "gestures.title": "Nine gestures. That's the whole vocabulary.",
      "gestures.lede":
        "Small, deliberate moves — each one filtered, debounced and confidence-scored before it reaches the Windows control layer.",
      "g1.title": "Move",
      "g1.trigger": "Index finger up",
      "g1.note": "Precision pointer — filtered and smoothed. Sub-pixel feel on a 1080p screen.",
      "g2.title": "Click",
      "g2.trigger": "Pinch · index + thumb",
      "g2.note":
        "Tap for a click. Hold to keep the button pressed — the origin of pinch-to-hold interactions.",
      "g3.title": "Double-click",
      "g3.trigger": "Double pinch",
      "g3.note": "Two quick taps, like the habit you already have. Opens files and apps.",
      "g4.title": "Drag",
      "g4.trigger": "Pinch + hold + move",
      "g4.note": "Grab windows, files and slider handles. Release the pinch to drop.",
      "g5.title": "Right-click",
      "g5.trigger": "Thumb + middle",
      "g5.note":
        "Context menu on demand — for power users who refuse to live without it.",
      "g6.title": "Scroll",
      "g6.trigger": "Open palm, vertical",
      "g6.note":
        "Palm up, glide the hand — the plane maps hand height to scroll velocity.",
      "g7.title": "Swipe",
      "g7.trigger": "Swipe, left / right",
      "g7.note": "Next and previous — slides, pages, browser tabs. Velocity-aware.",
      "g8.title": "Pause",
      "g8.trigger": "Palm held flat",
      "g8.note": "Hold the palm open for one beat — control halts until you lower it.",
      "g9.title": "Lock",
      "g9.trigger": "Fist",
      "g9.note": "Instant lock screen. The gesture everyone knows by instinct.",
      "voice.eyebrow": "03 / Voice layer",
      "voice.title": "Say it. Or just point.",
      "voice.lede":
        "A local intent engine maps recognized phrases onto the same intents as gestures. Recognition itself runs on Google's cloud by default, or fully local with Vosk/SAPI. Example commands, four languages, one vocabulary.",
      "voice.tableAria": "Voice commands by language",
      "voice.colTask": "Task",
      "voice.colEn": "English",
      "voice.colFr": "Français",
      "voice.colAr": "العربية",
      "voice.colNl": "Nederlands",
      "voice.r1.task": "Open an app",
      "voice.r1.en": "“open chrome”",
      "voice.r1.fr": "“ouvre chrome”",
      "voice.r1.ar": "“افتح كروم”",
      "voice.r1.nl": "“open chrome”",
      "voice.r2.task": "Write a note",
      "voice.r2.en": "“type: call back at…”",
      "voice.r2.fr": "“note : rappeler…”",
      "voice.r2.ar": "“اكتب ملاحظة”",
      "voice.r2.nl": "“type: bel terug om…”",
      "voice.r3.task": "Next slide",
      "voice.r3.en": "“next slide”",
      "voice.r3.fr": "“diapositive suivante”",
      "voice.r3.ar": "“الشريحة التالية”",
      "voice.r3.nl": "“volgende dia”",
      "voice.r4.task": "Scroll down",
      "voice.r4.en": "“scroll down”",
      "voice.r4.fr": "“descends la page”",
      "voice.r4.ar": "“مرّر للأسفل”",
      "voice.r4.nl": "“scroll naar beneden”",
      "voice.r5.task": "Pause media",
      "voice.r5.en": "“pause the music”",
      "voice.r5.fr": "“mets en pause”",
      "voice.r5.ar": "“أوقف الموسيقى”",
      "voice.r5.nl": "“zet de muziek stil”",
      "voice.r6.task": "Freeze everything",
      "voice.r6.en": "“freeze”",
      "voice.r6.fr": "“bloque tout”",
      "voice.r6.ar": "“تجمّد”",
      "voice.r6.nl": "“bevries alles”",
      "voice.callTitle": "Voice-first “hands busy” mode",
      "voice.callText":
        "When your hands are full — gloves, tools, a plate — voice alone can drive the machine. The same intent engine, zero gestures required.",
      "voice.callBeta": "FR / AR / NL at beta level",
      "modes.eyebrow": "04 / Modes & profiles",
      "modes.title": "Tuned for how you actually work.",
      "modes.lede":
        "Thirteen auto profiles switch gesture sensitivity, dead zones and voice behaviour per environment — most never need touching.",
      "modes.m1.title": "Hands Busy",
      "modes.m1.text":
        "Voice-first. Gloves, food, tools. Gestures limited to a reserved safe set.",
      "modes.m1.p1": "Voice leads",
      "modes.m1.p2": "Amber-tier gestures only",
      "modes.m2.title": "Industrial",
      "modes.m2.text":
        "HMI panels & line work. Big dead zones, slow deliberate moves, high debounce.",
      "modes.m2.p1": "Extended dead zones",
      "modes.m2.p2": "Slow-mode tracking",
      "modes.m3.title": "Medical",
      "modes.m3.text":
        "Sterile-room browsing and paperwork. Time-limit triggers, hands stay clean.",
      "modes.m3.disc":
        "Not a clinical device — no diagnosis, no treatment, no monitoring of patients.",
      "modes.m4.title": "Presentation",
      "modes.m4.text":
        "Slide decks, laser-pointer lane, precision click zones far from the screen edges.",
      "modes.m4.p1": "Laser lane active",
      "modes.m4.p2": "Click zones tuned",
      "modes.m5.title": "Media",
      "modes.m5.text":
        "Fullscreen video with timeline scrub, volume by palm height, swipe for tracks.",
      "modes.m5.p1": "Scrub gestures",
      "modes.m5.p2": "Palm = volume",
      "modes.m6.title": "Accessibility",
      "modes.m6.text":
        "Large hit zones, dwell-to-click, switch-friendly. Fewer, kinder gestures.",
      "modes.m6.p1": "Dwell-to-click",
      "modes.m6.p2": "Big targets",
      "modes.m7.title": "Browser / PDF",
      "modes.m7.text":
        "Scroll + zoom profiles mapped to palm distance, tab swipes, page-turn pinches.",
      "modes.m7.p1": "Zoom by distance",
      "modes.m7.p2": "Tab swipe",
      "modes.m8.title": "CAD · Kiosk · Custom",
      "modes.m8.text":
        "CAD orbit and precision pick, locked kiosk floors, and fully remappable custom profiles. Five more profiles ship out of the box — all thirteen auto-detect context when enabled.",
      "modes.m8.p1": "13",
      "modes.m8.p2": "4",
      "modes.m8.p3": "1",
      "modes.m8.mem": "MEM",
      "modes.m8.profiles": "PROFILES",
      "modes.m8.voice": "VOICE",
      "modes.m8.cam": "CAM",
      "try.eyebrow": "05 / Live plane",
      "try.title": "Try it — right here.",
      "try.lede":
        'The mouse is your air-pointer. Push left and hold to pinch-click, wheel over the document to scroll, hit <kbd>space</kbd> for palm mode (wheel scrolls big steps). Works on touch: tap to click, drag to move.',
      "try.mediaOutput": "OUTPUT",
      "try.mediaAria": "Demo media player — controls respond to pinch clicks",
      "try.prevAria": "Previous track",
      "try.nextAria": "Next track",
      "try.playAria": "Play or pause",
      "try.playPause": "Play or pause",
      "try.docLabel": "DOC",
      "try.docTitle": "quickstart.txt — scrollable",
      "try.docAria":
        "Scrollable quick-start document. Wheel scrolls; palm mode scrolls in large steps.",
      "try.quickTitle": "QUICKSTART — CONTACTLESS SETUP",
      "try.step1":
        "<strong>Install</strong> the Windows app. MediaPipe runtime and language packs bundle in.",
      "try.step2":
        "<strong>Calibrate.</strong> Sit at your desk, raise one hand. The plane locks your arm’s reachable box and maps it to the full screen.",
      "try.step3":
        "<strong>Point.</strong> Index finger raised = move. Notice the plane tracks from the shoulder, not the palm — small wrist work, big screen travel.",
      "try.step4":
        "<strong>Pinch to click.</strong> Index + thumb closing. Hold to grab, release to drop.",
      "try.step5":
        "<strong>Scroll.</strong> Open palm, glide vertically. Wheel-speed follows hand height.",
      "try.step6":
        "<strong>Voice.</strong> Say “open chrome”. Recognition stays on-device when you pick the Vosk or SAPI engine (the default Google engine needs internet); the intent engine then maps the phrase locally, so accents are fine.",
      "try.step7":
        "<strong>Emergency stop.</strong> Press <kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>H</kbd> any time — everything freezes. Press it again to resume.",
      "try.afterLine":
        "That’s the whole system. Every action above is the same intent pipeline the demo plane shows: gesture or voice → intent engine → Windows control layer.",
      "try.figCap1":
        'Wheel over this panel to scroll it. <strong>Space</strong> then wheel = big palm-mode steps.',
      "try.mediaStart": "Pinch-click the play button. It’s a real button — keyboard works too.",
      "privacy.eyebrow": "06 / Privacy",
      "privacy.title": "Never leaves this machine.",
      "privacy.lede":
        "Video frames and intent logs stay on-device. Audio does too on the Vosk/SAPI engines; the default Google engine sends your phrase to Google for recognition. There is no account, no sync, no analytics beacon to phone home to.",
      "privacy.p1t": "Local processing",
      "privacy.p1":
        "MediaPipe models and the intent engine run on this computer. Camera frames are handled and discarded in memory and never leave your machine. Mic audio is the one exception: the default voice engine (Google Web Speech) sends your spoken phrase to Google's servers; the Vosk and SAPI engines keep recognition fully on-device.",
      "privacy.p2t": "Camera toggle",
      "privacy.p2":
        "A single switch in the tray menu kills the camera instantly. A global hotkey does the same without touching the tray.",
      "privacy.p3t": "Privacy mode",
      "privacy.p3":
        "Optional live-preview blur or blank. You and nearby people can see tracking is active without anyone seeing faces on screen.",
      "privacy.p4t": "Wipe data",
      "privacy.p4":
        "One click clears query logs, settings and calibration. Everything HADJ has learned about you fits in a few files and forgets in a tap.",
      "privacy.foot":
        "Optional — 100% local video processing: no sensors, no telemetry, no account. (Voice recognition: local on Vosk/SAPI, cloud by default on Google.)",
      "safety.eyebrow": "07 / Safety",
      "safety.title": "A kill switch that is always on tap.",
      "safety.lede":
        "Contactless control is powerful; it's also engineered to stay out of your way. These are not optional extras.",
      "safety.stop": "EMERGENCY STOP",
      "safety.stopKeys": "CTRL + ALT + H",
      "safety.stopCaption":
        "Press <strong>CTRL + ALT + H</strong> (or the on-screen button). Every gesture and voice control freezes immediately — press the same key again to resume. Nothing moves in between.",
      "safety.s1t": "Jump rejection",
      "safety.s1":
        "Sudden, unnaturally fast motion is discarded, not acted on. Debounce and dead-man logic treat a flinch as noise, never as a command.",
      "safety.s2t": "Dead zones",
      "safety.s2":
        "Define an edge buffer where gestures are ignored entirely — so resting your hand near the screen never triggers anything. Calibrated per desk.",
      "safety.s3t": "Confirm destructive actions",
      "safety.s3":
        "Drag-to-delete, shutdown, format — anything destructive asks once before it happens. A confirmation is a second, deliberate pinch.",
      "faq.eyebrow": "08 / FAQ",
      "faq.title": "Straight answers.",
      "faq.q1.sum": "Is my webcam footage sent anywhere?",
      "faq.q1.body":
        "No — camera frames stay in memory on your machine and are used only to derive landmarks. There is no upload path for video, no server, no account. The one exception is mic audio: the default voice engine (Google Web Speech) sends your phrase to Google for recognition; the Vosk and SAPI engines keep it on-device. The PWA page you're on right now also runs fully offline after first load; the camera is never touched by the page.",
      "faq.q2.sum": "Which Windows versions are supported?",
      "faq.q2.body":
        "Windows 10 and Windows 11, 64-bit, with a standard UVC webcam. Microphone for the voice layer is optional. A dedicated GPU is not required — MediaPipe runs on CPU and modest integrated graphics.",
      "faq.q3.sum": "Does it work fully offline?",
      "faq.q3.body":
        "Almost — with one nuance. Tracking, gestures, the intent engine and gaze all run fully offline with the bundled MediaPipe models. Voice recognition is fully offline when you select the Vosk or SAPI engine; the default Google engine needs an internet connection. This page is a PWA — after the first visit it can be installed and run from the local service-worker cache with no connection at all.",
      "faq.q4.sum": "How accurate are the gestures really?",
      "faq.q4.body":
        "Each intent passes a confidence gate (typically 0.85–0.97, shown live in the demo) and a debounce window before it reaches the Windows control layer. Calibration tunes the reference box for your arm length and camera angle, which is where most “wobbly” systems fail.",
      "faq.q5.sum": "What about gaze and custom gestures?",
      "faq.q5.body":
        "Gaze tracking and user-recorded custom gestures are marked experimental — they ship behind a flag and are off by default. They're excluded from the guaranteed gesture set until they meet the same confidence bar as the nine core gestures.",
      "faq.q6.sum": "Can I use it alongside mouse and keyboard?",
      "faq.q6.body":
        "Yes. Control is hybrid and switchable — tray toggle, hotkey, or automatic pause when your hands are at the keys. Most people use the mouse for fine work and gestures for everything else.",
      "download.eyebrow": "09 / Download",
      "download.title": "Get HADJ NO-TOUCH AI.",
      "download.lede":
        "Free, open-source, and runs on your machine. No account required. (Voice recognition is cloud by default — local on the Vosk/SAPI engines.)",
      "download.beta": "v2.0-beta",
      "download.latest": "Latest",
      "download.btn": "Download for Windows",
      "download.meta": "Windows 10 / 11 (x64) · ~205 MB ZIP · No installer needed",
      "download.reqTitle": "System Requirements",
      "req.os": "OS",
      "req.cam": "Camera",
      "req.mic": "Mic",
      "req.gpu": "GPU",
      "req.ram": "RAM",
      "req.disk": "Disk",
      "req.osVal": "Windows 10 / 11, 64-bit",
      "req.camVal": "Standard UVC webcam",
      "req.micVal": "Optional (for voice commands)",
      "req.gpuVal": "Not required — runs on CPU",
      "req.ramVal": "4 GB recommended",
      "req.diskVal": "~500 MB free space",
      "download.instTitle": "Installation",
      "download.inst1": "Download the ZIP file above.",
      "download.inst2": "Extract to any folder (e.g. <code>C:\\HADJ</code>).",
      "download.inst3": "Double-click <code>HADJ-NO-TOUCH-AI.exe</code>.",
      "download.inst4": "Allow camera/mic access when prompted.",
      "download.inst5": "Follow the on-screen calibration wizard.",
      "download.instNote":
        "No installer, no admin rights needed. The app is portable — run from any folder.",
      "download.verifyTitle": "Verify the Download",
      "download.verifyText": "SHA-256 checksum for integrity verification:",
      "download.verifyHow":
        "A <code>.sha256</code> sidecar file with the same digest is published alongside the ZIP. Verify with PowerShell:<br><code>Get-FileHash .\\HADJ-NO-TOUCH-AI-Windows.zip -Algorithm SHA256</code>",
      "download.insideTitle": "What's Inside",
      "download.inside1": "main application",
      "download.inside2": "launcher script",
      "download.inside3": "MediaPipe models (Vosk voice pack optional)",
      "download.inside4": "13 auto-detect profiles",
      "download.inside5": "EN / FR / AR / NL voice commands",
      "download.footRow": "Also available on",
      "download.footGit": "GitHub",
      "download.footNote":
        "Open source · No telemetry · No account · Camera frames stay local",
      "footer.quick": "Quick links",
      "footer.safety": "Safety",
      "footer.faq": "FAQ",
      "footer.line": "No touch is the point.",
      "footer.bottom": "HADJ NO-TOUCH AI · contactless computer control for Windows",
      "footer.beta": "v2.0-beta",
      "footer.exp": "gaze & custom gestures experimental",
      "footer.pwa": "PWA · offline ready",
      "demo.trackNow": "Now playing a local file — no stream, all on your machine.",
      "demo.playing": "Playing — pinch-click again or press the button to pause.",
      "demo.paused": "Paused. Pinch-click play when you're ready.",
    },

    /* ================= FRANÇAIS ================= */
    fr: {
      "meta.title": "HADJ NO-TOUCH AI — Contrôlez l'ordinateur sans le toucher",
      "meta.desc":
        "Contrôlez l'ordinateur sans le toucher — gestes de la main, voix et regard pour Windows. Confidentialité d'abord, les images de la caméra restent locales. Disponible en anglais, français, arabe et néerlandais.",
      "skip": "Aller au contenu",
      "nav.aria": "Navigation principale",
      "nav.homeAria": "HADJ NO-TOUCH AI — accueil",
      "nav.how": "Fonctionnement",
      "nav.gestures": "Gestes",
      "nav.voice": "Voix",
      "nav.modes": "Modes",
      "nav.privacy": "Confidentialité",
      "nav.download": "Télécharger",
      "nav.install": "Installer",
      "nav.run": "Lancer sur Windows",
      "lang.label": "Langue — Français",
      "hero.eyebrow": "Contrôle sans contact · Caméra locale",
      "hero.title": 'Contrôlez l’ordinateur <span class="grad-text">sans le toucher.</span>',
      "hero.sub":
        "HADJ NO-TOUCH AI transforme votre webcam en plan d'interaction virtuel. Gestes de la main, voix et regard pilotent Windows — sans les mains, privé et à vous. Ni capteurs, ni contact — les images restent sur votre machine.",
      "hero.download": "Télécharger pour Windows",
      "hero.demo": "Essayer la démo",
      "hero.noteTitle": "Windows 10 / 11 (x64)",
      "hero.noteBody":
        "Livré en application de bureau native, téléchargé en ZIP depuis GitHub Releases. Il ne faut qu'une webcam + un micro — MediaPipe et le moteur d'intention tournent localement, sur cette machine.",
      "hero.noteMeta":
        'Après l’installation, pas de télémétrie ni de compte, et l’application ne télécharge rien au démarrage. Remarque : la reconnaissance vocale utilise l’API cloud de Google par défaut — choisissez Vosk ou SAPI pour une reconnaissance 100 % locale. Vérifiez le binaire avec <code>SHA-256&nbsp;CAF27A9BE6B7CABE747A2FF817D9B5CA83142F6472F7C15D56EB20D29D98F188</code>.',
      "hero.chip1": '<span class="chip-dot" aria-hidden="true"></span>Voix EN / FR / AR / NL',
      "hero.chip2": '<span class="chip-dot" aria-hidden="true"></span>Webcam uniquement',
      "hero.chip3": '<span class="chip-dot" aria-hidden="true"></span>La caméra reste locale',
      "hero.chip4": '<span class="chip-dot" aria-hidden="true"></span>Confidentialité d’abord',
      "hero.demoAria":
        "Démo en direct du plan d'interaction virtuel — la souris représente le pointeur aérien",
      "hero.live": "DIRECT",
      "hero.trackTop": "HADJ-OS // SUIVI",
      "hero.grid": "GRILLE 20PX",
      "hero.target": "CIBLE 01 · ZONE DE CLIC",
      "hero.pinchBtn": "PINCEZ POUR CLIQUER",
      "demo.ready": "prêt",
      "demo.clicked": "clic ✓",
      "demo.hud.mode": "MODE",
      "demo.hud.gesture": "GESTE",
      "demo.hud.x": "X",
      "demo.hud.y": "Y",
      "demo.hud.conf": "CONF",
      "demo.hud.clicks": "CLICS",
      "demo.hint":
        'souris = pointeur aérien · <strong>maintenez gauche</strong> = pincer→cliquer · <kbd>espace</kbd> = mode paume · molette = défilement',
      "demo.touchHint": "toucher une commande = pincer-cliquer · glisser = déplacer le pointeur",
      "demo.palmOn":
        'Mode paume ACTIVÉ — la molette défile par <strong>grands pas</strong>. <kbd>espace</kbd> pour quitter.',
      "demo.noscript":
        "La démo en direct nécessite JavaScript. L'application Windows, elle, fonctionne entièrement sur votre machine, sans navigateur.",
      "demo.confirm": "PINCEMENT CONFIRMÉ",
      "demo.confirmSub": "• clic →",
      "hero.scroll": "DÉFILER",
      "stats.profiles": "profils auto",
      "stats.languages": "langues",
      "stats.webcam": "webcam",
      "stats.touch": "contact",
      "how.eyebrow": "01 / Pipeline",
      "how.title": "De la webcam à Windows,<br>le contrôle en une ligne de mouvement.",
      "how.lede":
        "Quatre étapes locales. Les images de la caméra ne quittent jamais votre machine — chaque image est traitée sur l'appareil par les modèles embarqués et l'environnement d'exécution déjà présent.",
      "how.s1tag": "Couche d'entrée MediaPipe",
      "how.s1title": "Webcam + Micro",
      "how.s1text":
        "Votre caméra diffuse les images localement dans la couche de suivi ; le micro alimente le moteur vocal (Google par défaut, ou Vosk/SAPI pour une reconnaissance sur appareil). La résolution et la cadence s'adaptent à la machine pour un suivi fluide.",
      "how.s2tag": "Repères MediaPipe",
      "how.s2title": "Suivre",
      "how.s2text":
        "Les repères mains, visage et posture sont extraits à ~30 images/s — 21 points par main — avec étalonnage par caméra pour la luminosité et la distance.",
      "how.s3tag": "Moteur d'intention",
      "how.s3title": "Comprendre",
      "how.s3text":
        "Les gestes et phrases vocales sont mappés sur un petit ensemble d'intentions avec score de confiance et anti-rebond : les déclenchements accidentels restent rares.",
      "how.s4tag": "Couche de contrôle Windows",
      "how.s4title": "Agir",
      "how.s4text":
        "L'intention devient une action native — souris, clavier, touches média, contrôle des fenêtres et des bureaux virtuels — via l'API du système.",
      "gestures.eyebrow": "02 / Bibliothèque de gestes",
      "gestures.title": "Neuf gestes. Tout le vocabulaire.",
      "gestures.lede":
        "Des mouvements délibérés et précis — chacun filtré, anti-rebond et noté sur la confiance avant d'atteindre la couche de contrôle Windows.",
      "g1.title": "Déplacer",
      "g1.trigger": "Index levé",
      "g1.note": "Pointeur de précision — filtré et lissé. Sensation subpixel sur un écran 1080p.",
      "g2.title": "Cliquer",
      "g2.trigger": "Pince · index + pouce",
      "g2.note":
        "Toucher pour cliquer. Maintenez pour garder le bouton enfoncé — l'origine des interactions pincer-maintenir.",
      "g3.title": "Double-clic",
      "g3.trigger": "Double pincement",
      "g3.note": "Deux petits clics, comme l'habitude que vous avez déjà. Ouvre fichiers et applications.",
      "g4.title": "Glisser",
      "g4.trigger": "Pincer + maintenir + déplacer",
      "g4.note": "Saisissez fenêtres, fichiers et curseurs. Relâchez le pincement pour déposer.",
      "g5.title": "Clic droit",
      "g5.trigger": "Pouce + majeur",
      "g5.note": "Le menu contextuel à la demande — pour ceux qui ne peuvent pas s'en passer.",
      "g6.title": "Faire défiler",
      "g6.trigger": "Paume ouverte, vertical",
      "g6.note":
        "Paume levée, glissez la main — le plan relie la hauteur de la main à la vitesse de défilement.",
      "g7.title": "Balayer",
      "g7.trigger": "Balayage, gauche / droite",
      "g7.note": "Suivant et précédent — diapos, pages, onglets. Sensible à la vitesse.",
      "g8.title": "Pause",
      "g8.trigger": "Paume à plat",
      "g8.note": "Gardez la paume ouverte un instant — le contrôle s'arrête jusqu'à ce que vous la baissiez.",
      "g9.title": "Verrouiller",
      "g9.trigger": "Poing",
      "g9.note": "Verrouillage instantané. Le geste que tout le monde connaît d'instinct.",
      "voice.eyebrow": "03 / Couche vocale",
      "voice.title": "Dites-le. Ou montrez du doigt.",
      "voice.lede":
        "Un moteur d'intention local mappe les phrases reconnues sur les mêmes intentions que les gestes. La reconnaissance s'appuie sur le cloud Google par défaut, ou 100 % locale avec Vosk/SAPI. Exemples de commandes, quatre langues, un vocabulaire.",
      "voice.tableAria": "Commandes vocales par langue",
      "voice.colTask": "Tâche",
      "voice.colEn": "English",
      "voice.colFr": "Français",
      "voice.colAr": "العربية",
      "voice.colNl": "Nederlands",
      "voice.r1.task": "Ouvrir une application",
      "voice.r1.en": "“open chrome”",
      "voice.r1.fr": "“ouvre chrome”",
      "voice.r1.ar": "“افتح كروم”",
      "voice.r1.nl": "“open chrome”",
      "voice.r2.task": "Écrire une note",
      "voice.r2.en": "“type: call back at…”",
      "voice.r2.fr": "“note : rappeler…”",
      "voice.r2.ar": "“اكتب ملاحظة”",
      "voice.r2.nl": "“type: bel terug om…”",
      "voice.r3.task": "Diapositive suivante",
      "voice.r3.en": "“next slide”",
      "voice.r3.fr": "“diapositive suivante”",
      "voice.r3.ar": "“الشريحة التالية”",
      "voice.r3.nl": "“volgende dia”",
      "voice.r4.task": "Faire défiler vers le bas",
      "voice.r4.en": "“scroll down”",
      "voice.r4.fr": "“descends la page”",
      "voice.r4.ar": "“مرّر للأسفل”",
      "voice.r4.nl": "“scroll naar beneden”",
      "voice.r5.task": "Mettre en pause",
      "voice.r5.en": "“pause the music”",
      "voice.r5.fr": "“mets en pause”",
      "voice.r5.ar": "“أوقف الموسيقى”",
      "voice.r5.nl": "“zet de muziek stil”",
      "voice.r6.task": "Tout figer",
      "voice.r6.en": "“freeze”",
      "voice.r6.fr": "“bloque tout”",
      "voice.r6.ar": "“تجمّد”",
      "voice.r6.nl": "“bevries alles”",
      "voice.callTitle": "Mode « mains occupées » à la voix",
      "voice.callText":
        "Quand vos mains sont prises — gants, outils, un plateau — la voix seule pilote la machine. Le même moteur d'intention, zéro geste requis.",
      "voice.callBeta": "FR / AR / NL au niveau bêta",
      "modes.eyebrow": "04 / Modes & profils",
      "modes.title": "Réglé pour votre façon de travailler.",
      "modes.lede":
        "Treize profils automatiques adaptent la sensibilité des gestes, les zones mortes et le comportement vocal par environnement — la plupart ne demandent aucun réglage.",
      "modes.m1.title": "Mains occupées",
      "modes.m1.text":
        "La voix d'abord. Gants, repas, outils. Gestes limités à un ensemble sûr réservé.",
      "modes.m1.p1": "La voix mène",
      "modes.m1.p2": "Gestes de niveau ambre uniquement",
      "modes.m2.title": "Industriel",
      "modes.m2.text":
        "Panneaux IHM & travail à la chaîne. Grandes zones mortes, gestes lents et volontaires, anti-rebond élevé.",
      "modes.m2.p1": "Zones mortes étendues",
      "modes.m2.p2": "Suivi en mode lent",
      "modes.m3.title": "Médical",
      "modes.m3.text":
        "Navigation en salle stérile et paperasse. Déclencheurs à durée limitée, mains propres.",
      "modes.m3.disc":
        "Pas un dispositif clinique — ni diagnostic, ni traitement, ni surveillance des patients.",
      "modes.m4.title": "Présentation",
      "modes.m4.text":
        "Diaporamas, couloir du pointeur laser, zones de clic précises loin des bords de l'écran.",
      "modes.m4.p1": "Couloir laser actif",
      "modes.m4.p2": "Zones de clic affinées",
      "modes.m5.title": "Médias",
      "modes.m5.text":
        "Vidéo plein écran avec balayage de la timeline, volume selon la hauteur de la paume, balayage pour les pistes.",
      "modes.m5.p1": "Gestes de balayage",
      "modes.m5.p2": "Paume = volume",
      "modes.m6.title": "Accessibilité",
      "modes.m6.text":
        "Grandes zones tactiles, cliquer-en-s’arrêtant, compatible contacteurs. Moins de gestes, plus doux.",
      "modes.m6.p1": "Clique au repos",
      "modes.m6.p2": "Grandes cibles",
      "modes.m7.title": "Navigateur / PDF",
      "modes.m7.text":
        "Profils de défilement + zoom reliés à la distance de la paume, balayage d'onglets, pincements pour tourner la page.",
      "modes.m7.p1": "Zoom par distance",
      "modes.m7.p2": "Balayage d'onglets",
      "modes.m8.title": "CAO · Kiosque · Personnalisé",
      "modes.m8.text":
        "Orbite CAO et sélection de précision, kiosques verrouillés et profils personnalisés entièrement remappables. Cinq profils supplémentaires sont fournis — les treize détectent le contexte automatiquement quand ils sont activés.",
      "modes.m8.p1": "13",
      "modes.m8.p2": "4",
      "modes.m8.p3": "1",
      "modes.m8.mem": "MÉM",
      "modes.m8.profiles": "PROFILS",
      "modes.m8.voice": "VOIX",
      "modes.m8.cam": "CAM",
      "try.eyebrow": "05 / Plan en direct",
      "try.title": "Essayez — ici même.",
      "try.lede":
        'La souris est votre pointeur aérien. Appuyez et maintenez à gauche pour pincer-cliquer, la molette sur le document pour défiler, <kbd>espace</kbd> pour le mode paume (la molette défait par grands pas). Fonctionne au toucher : toucher pour cliquer, glisser pour bouger.',
      "try.mediaOutput": "SORTIE",
      "try.mediaAria": "Lecteur média de démo — les commandes répondent aux clics par pincement",
      "try.prevAria": "Piste précédente",
      "try.nextAria": "Piste suivante",
      "try.playAria": "Lire ou mettre en pause",
      "try.playPause": "Lire ou mettre en pause",
      "try.docLabel": "DOC",
      "try.docTitle": "quickstart.txt — défilable",
      "try.docAria":
        "Document de démarrage rapide défilable. La molette défait ; le mode paume défait par grands pas.",
      "try.quickTitle": "DÉMARRAGE RAPIDE — CONFIGURATION SANS CONTACT",
      "try.step1":
        "<strong>Installez</strong> l'application Windows. L'environnement MediaPipe et les packs de langue sont inclus.",
      "try.step2":
        "<strong>Étalonnez.</strong> Asseyez-vous à votre bureau, levez une main. Le plan verrouille le volume accessible de votre bras et le mappe sur tout l'écran.",
      "try.step3":
        "<strong>Visez.</strong> Index levé = bouger. Notez que le plan suit l'épaule, pas la paume — petit travail du poignet, grande course à l'écran.",
      "try.step4":
        "<strong>Pincez pour cliquer.</strong> Index + pouce qui se rapprochent. Maintenez pour saisir, relâchez pour déposer.",
      "try.step5":
        "<strong>Défilez.</strong> Paume ouverte, glissez verticalement. La vitesse suit la hauteur de la main.",
      "try.step6":
        "<strong>La voix.</strong> Dites « ouvre chrome ». La reconnaissance reste sur l'appareil avec Vosk ou SAPI (le moteur Google par défaut a besoin d'Internet) ; le moteur d'intention mappe ensuite la phrase localement, les accents passent.",
      "try.step7":
        "<strong>Arrêt d'urgence.</strong> Appuyez sur <kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>H</kbd> à tout moment — tout se fige. Appuyez à nouveau pour reprendre.",
      "try.afterLine":
        "C'est tout le système. Chaque action ci-dessus suit le même pipeline d'intention que le plan de démo : geste ou voix → moteur d'intention → couche de contrôle Windows.",
      "try.figCap1":
        'Faites défiler ce panneau avec la molette. <strong>Espace</strong> puis molette = grands pas en mode paume.',
      "try.mediaStart": "Pincez-cliquez sur le bouton de lecture. C'est un vrai bouton — le clavier marche aussi.",
      "privacy.eyebrow": "06 / Confidentialité",
      "privacy.title": "Ne quitte jamais cette machine.",
      "privacy.lede":
        "Les images vidéo et les journaux d'intention restent sur l'appareil. L'audio aussi sur les moteurs Vosk/SAPI ; par défaut le moteur Google envoie votre phrase à Google pour reconnaissance. Pas de compte, pas de synchronisation, aucune balise analytique.",
      "privacy.p1t": "Traitement local",
      "privacy.p1":
        "Les modèles MediaPipe et le moteur d'intention tournent sur cet ordinateur. Les images de la caméra sont traitées et jetées en mémoire, elles ne quittent jamais la machine. L'audio du micro est l'unique exception : par défaut, le moteur vocal (Google Web Speech) envoie la phrase prononcée aux serveurs de Google ; les moteurs Vosk et SAPI gardent la reconnaissance entièrement sur l'appareil.",
      "privacy.p2t": "Couper la caméra",
      "privacy.p2":
        "Un simple interrupteur du menu de la barre d'état coupe la caméra instantanément. Un raccourci global fait de même sans toucher au menu.",
      "privacy.p3t": "Mode confidentialité",
      "privacy.p3":
        "Brouillage ou écran noir de l'aperçu, en option. Vous et les personnes autour voyez que le suivi est actif, sans que personne ne voie de visages à l'écran.",
      "privacy.p4t": "Effacer les données",
      "privacy.p4":
        "Un clic efface les journaux de requêtes, les réglages et l'étalonnage. Tout ce que HADJ a appris sur vous tient dans quelques fichiers et s'oublie d'un geste.",
      "privacy.foot":
        "Optionnel — traitement vidéo 100 % local : aucun capteur, aucune télémétrie, aucun compte. (Reconnaissance vocale : locale sur Vosk/SAPI, cloud par défaut sur Google.)",
      "safety.eyebrow": "07 / Sécurité",
      "safety.title": "Un interrupteur d'arrêt toujours à portée.",
      "safety.lede":
        "Le contrôle sans contact est puissant ; il est aussi conçu pour ne pas vous gêner. Ce ne sont pas des options superflues.",
      "safety.stop": "ARRÊT D'URGENCE",
      "safety.stopKeys": "CTRL + ALT + H",
      "safety.stopCaption":
        "Appuyez sur <strong>CTRL + ALT + H</strong> (ou le bouton à l'écran). Tous les gestes et commandes vocales se figent immédiatement — appuyez à nouveau pour reprendre. Rien ne bouge entre-temps.",
      "safety.s1t": "Rejet des à-coups",
      "safety.s1":
        "Un mouvement soudain et anormalement rapide est écarté, jamais exécuté. L'anti-rebond et la logique homme-mort traitent un sursaut comme du bruit, jamais comme une commande.",
      "safety.s2t": "Zones mortes",
      "safety.s2":
        "Définissez une bordure où les gestes sont purement ignorés — ainsi, reposer la main près de l'écran ne déclenche rien. Étalonné par bureau.",
      "safety.s3t": "Confirmer les actions destructrices",
      "safety.s3":
        "Suppression par glisser, extinction, formatage — toute action destructrice demande confirmation avant d'agir. C'est un second pincement, délibéré.",
      "faq.eyebrow": "08 / FAQ",
      "faq.title": "Des réponses claires.",
      "faq.q1.sum": "Mes images de webcam sont-elles envoyées quelque part ?",
      "faq.q1.body":
        "Non — les images restent en mémoire sur votre machine et ne servent qu'à dériver des repères. Aucun chemin d'envoi pour la vidéo, aucun serveur, aucun compte. La seule exception est l'audio du micro : le moteur vocal par défaut (Google Web Speech) envoie votre phrase à Google pour reconnaissance ; Vosk et SAPI la gardent sur l'appareil. Cette page PWA fonctionne aussi entièrement hors ligne après le premier chargement ; la caméra n'est jamais touchée par la page.",
      "faq.q2.sum": "Quelles versions de Windows sont prises en charge ?",
      "faq.q2.body":
        "Windows 10 et Windows 11, 64 bits, avec une webcam UVC standard. Le micro pour la couche vocale est optionnel. Aucune carte graphique dédiée requise — MediaPipe tourne sur CPU et sur les graphiques intégrés modestes.",
      "faq.q3.sum": "Fonctionne-t-il entièrement hors ligne ?",
      "faq.q3.body":
        "Presque — avec une nuance. Suivi, gestes, moteur d'intention et regard tournent entièrement hors ligne avec les modèles MediaPipe inclus. La reconnaissance vocale est hors ligne avec Vosk ou SAPI ; le moteur Google par défaut a besoin d'une connexion. Cette page est une PWA — après la première visite, elle s'installe et tourne depuis le cache du service worker, sans connexion du tout.",
      "faq.q4.sum": "Quelle est la précision réelle des gestes ?",
      "faq.q4.body":
        "Chaque intention passe un seuil de confiance (typiquement 0.85–0.97, affiché en direct dans la démo) et une fenêtre anti-rebond avant d'atteindre la couche de contrôle Windows. L'étalonnage règle la boîte de référence sur la longueur de votre bras et l'angle de la caméra — là où la plupart des systèmes « instables » échouent.",
      "faq.q5.sum": "Et le regard et les gestes personnalisés ?",
      "faq.q5.body":
        "Le suivi du regard et les gestes personnalisés enregistrés sont marqués expérimentaux — ils sortent derrière un drapeau et sont désactivés par défaut. Ils sont exclus de l'ensemble garanti tant qu'ils n'atteignent pas le même niveau de confiance que les neuf gestes principaux.",
      "faq.q6.sum": "Peut-on l'utiliser avec souris et clavier ?",
      "faq.q6.body":
        "Oui. Le contrôle est hybride et interchangeable — interrupteur de la barre d'état, raccourci, ou pause automatique quand vos mains sont au clavier. La plupart des gens utilisent la souris pour le travail fin et les gestes pour tout le reste.",
      "download.eyebrow": "09 / Téléchargement",
      "download.title": "Obtenez HADJ NO-TOUCH AI.",
      "download.lede":
        "Gratuit, open-source, tourne sur votre machine. Aucun compte requis. (Reconnaissance vocale : cloud par défaut — locale sur les moteurs Vosk/SAPI.)",
      "download.beta": "v2.0-bêta",
      "download.latest": "Dernière",
      "download.btn": "Télécharger pour Windows",
      "download.meta": "Windows 10 / 11 (x64) · ZIP ~205 Mo · Pas d'installeur",
      "download.reqTitle": "Configuration requise",
      "req.os": "Système",
      "req.cam": "Caméra",
      "req.mic": "Micro",
      "req.gpu": "GPU",
      "req.ram": "RAM",
      "req.disk": "Disque",
      "req.osVal": "Windows 10 / 11, 64 bits",
      "req.camVal": "Webcam UVC standard",
      "req.micVal": "Optionnel (pour les commandes vocales)",
      "req.gpuVal": "Non requis — tourne sur CPU",
      "req.ramVal": "4 Go conseillés",
      "req.diskVal": "~500 Mo d'espace libre",
      "download.instTitle": "Installation",
      "download.inst1": "Téléchargez le fichier ZIP ci-dessus.",
      "download.inst2": "Extrayez dans n'importe quel dossier (ex. <code>C:\\HADJ</code>).",
      "download.inst3": "Double-cliquez sur <code>HADJ-NO-TOUCH-AI.exe</code>.",
      "download.inst4": "Autorisez l'accès caméra/micro quand demandé.",
      "download.inst5": "Suivez l'assistant d'étalonnage à l'écran.",
      "download.instNote":
        "Pas d'installeur, pas de droits administrateur. L'application est portable — lancez-la depuis n'importe quel dossier.",
      "download.verifyTitle": "Vérifier le téléchargement",
      "download.verifyText": "Somme de contrôle SHA-256 pour vérifier l'intégrité :",
      "download.verifyHow":
        "Un fichier <code>.sha256</code> avec la même empreinte est publié à côté du ZIP. Vérifiez avec PowerShell :<br><code>Get-FileHash .\\HADJ-NO-TOUCH-AI-Windows.zip -Algorithm SHA256</code>",
      "download.insideTitle": "Contenu",
      "download.inside1": "application principale",
      "download.inside2": "script de lancement",
      "download.inside3": "Modèles MediaPipe (pack vocal Vosk en option)",
      "download.inside4": "13 profils à détection automatique",
      "download.inside5": "Commandes vocales EN / FR / AR / NL",
      "download.footRow": "Aussi disponible sur",
      "download.footGit": "GitHub",
      "download.footNote":
        "Open source · Aucune télémétrie · Aucun compte · Les images restent locales",
      "footer.quick": "Liens rapides",
      "footer.safety": "Sécurité",
      "footer.faq": "FAQ",
      "footer.line": "Sans contact, c'est le principe.",
      "footer.bottom": "HADJ NO-TOUCH AI · contrôle sans contact de Windows",
      "footer.beta": "v2.0-bêta",
      "footer.exp": "regard & gestes personnalisés expérimentaux",
      "footer.pwa": "PWA · prête hors ligne",
      "demo.trackNow": "Lecture d'un fichier local — aucun flux, tout sur votre machine.",
      "demo.playing": "Lecture — re-pincez-cliquez ou appuyez sur le bouton pour mettre en pause.",
      "demo.paused": "En pause. Pincez-cliquez sur lecture quand vous êtes prêt.",
    },

    /* ================= العربية ================= */
    ar: {
      "meta.title": "HADJ NO-TOUCH AI — تحكّم في الحاسوب دون لمسه",
      "meta.desc":
        "تحكّم في الحاسوب دون لمسه — بالإيماءات والصوت والنظرة لنظام Windows. الخصوصية أولاً، تبقى لقطات الكاميرا على جهازك. متاح بالإنجليزية والفرنسية والعربية والهولندية.",
      "skip": "تخطَّ إلى المحتوى",
      "nav.aria": "التنقل الرئيسي",
      "nav.homeAria": "HADJ NO-TOUCH AI — الرئيسية",
      "nav.how": "كيف يعمل",
      "nav.gestures": "الإيماءات",
      "nav.voice": "الصوت",
      "nav.modes": "الأوضاع",
      "nav.privacy": "الخصوصية",
      "nav.download": "التنزيل",
      "nav.install": "تثبيت",
      "nav.run": "تشغيل على Windows",
      "lang.label": "اللغة — العربية",
      "hero.eyebrow": "تحكّم دون لمس · الكاميرا محلية",
      "hero.title": 'تحكّم في الحاسوب <span class="grad-text">دون أن تلمسه.</span>',
      "hero.sub":
        "يحوّل HADJ NO-TOUCH AI كاميرا الويب إلى مستوى تفاعل افتراضي. إيماءات اليد والصوت والنظرة تقود Windows — دون استخدام اليدين، وبخصوصية تامة، وبياناتك ملكك. لا حساسات، لا لمس — لقطات الكاميرا تبقى على جهازك.",
      "hero.download": "نزّل لـ Windows",
      "hero.demo": "جرّب العرض التجريبي",
      "hero.noteTitle": "Windows 10 / 11 (x64)",
      "hero.noteBody":
        "يُوزَّع كتطبيق سطح مكتب أصلي، تُنزّله بصيغة ZIP من إصدارات GitHub. لا يتطلب سوى كاميرا ويب + ميكروفون — تعمل MediaPipe ومحرك النوايا محلياً على هذا الجهاز.",
      "hero.noteMeta":
        'بعد التثبيت لا توجد أيّة مقاييس أو حسابات، والتطبيق لا يُنزّل شيئاً عند التشغيل. ملاحظة: يستخدم التعرف على الصوت واجهة Google السحابية افتراضياً — اختر Vosk أو SAPI للحصول على تعرّف محلي بالكامل. تحقّق من الملف بفحص <code>SHA-256&nbsp;CAF27A9BE6B7CABE747A2FF817D9B5CA83142F6472F7C15D56EB20D29D98F188</code>.',
      "hero.chip1": '<span class="chip-dot" aria-hidden="true"></span>صوت EN / FR / AR / NL',
      "hero.chip2": '<span class="chip-dot" aria-hidden="true"></span>كاميرا ويب فقط',
      "hero.chip3": '<span class="chip-dot" aria-hidden="true"></span>الكاميرا تبقى محلية',
      "hero.chip4": '<span class="chip-dot" aria-hidden="true"></span>الخصوصية أولاً',
      "hero.demoAria": "عرض مباشر لمستوى التفاعل الافتراضي — الفأرة تمثّل المؤشر الهوائي",
      "hero.live": "مباشر",
      "hero.trackTop": "HADJ-OS // التتبّع",
      "hero.grid": "شبكة 20 بكسل",
      "hero.target": "الهدف 01 · منطقة النقر",
      "hero.pinchBtn": "اقرص للنقر",
      "demo.ready": "جاهز",
      "demo.clicked": "نقرة ✓",
      "demo.hud.mode": "الوضع",
      "demo.hud.gesture": "الإيماءة",
      "demo.hud.x": "X",
      "demo.hud.y": "Y",
      "demo.hud.conf": "الثقة",
      "demo.hud.clicks": "النقرات",
      "demo.hint":
        'الفأرة = مؤشر هوائي · <strong>أبقِ الزر الأيسر</strong> = قرص→نقرة · <kbd>مسافة</kbd> = وضع راحة اليد · العجلة = تمرير',
      "demo.touchHint": "المس زراً = قرص والضغط · اسحب = تحريك المؤشر",
      "demo.palmOn":
        'وضع راحة اليد مُفعّل — العجلة تتمرر <strong>قفزات كبيرة</strong>. <kbd>مسافة</kbd> للخروج.',
      "demo.noscript":
        "العرض المباشر يتطلب JavaScript. تطبيق Windows نفسه يعمل بالكامل على جهازك، دون متصفح.",
      "demo.confirm": "تمّ تأكيد القرص",
      "demo.confirmSub": "• نقرة ←",
      "hero.scroll": "مرّر",
      "stats.profiles": "ملفاً تلقائياً",
      "stats.languages": "لغات",
      "stats.webcam": "كاميرا ويب",
      "stats.touch": "لمس",
      "how.eyebrow": "01 / خط المعالجة",
      "how.title": "من كاميرا الويب إلى Windows<br>التحكم بخطوة حركة واحدة.",
      "how.lede":
        "أربع مراحل محلية. لا تغادر لقطات الكاميرا جهازك أبداً — تُعالَج كل لقطة على الجهاز بالنماذج المدمجة وبيئة التشغيل الموجودة لديك.",
      "how.s1tag": "طبقة إدخال MediaPipe",
      "how.s1title": "كاميرا ويب + ميكروفون",
      "how.s1text":
        "تبثّ كاميرتك اللقطات محلياً إلى طبقة التتبّع؛ ويغذّي الميكروفون محرك الصوت (Google افتراضياً، أو Vosk/SAPI لتعرّف على الجهاز). تتكيّف الدقة والمعدل مع الجهاز ليظلّ التتبّع سلساً.",
      "how.s2tag": "معالم MediaPipe",
      "how.s2title": "تتبّع",
      "how.s2text":
        "تُستخرَج معالم اليدين والوجه ووضعية الجسم بمعدل ~30 لقطة/ثانية — 21 نقطة لكل يد — مع معايرة لكل كاميرا حسب الإضاءة والمسافة.",
      "how.s3tag": "محرك النوايا",
      "how.s3title": "افهم",
      "how.s3text":
        "تُرسم الإيماءات والعبارات الصوتية على مجموعة صغيرة من النوايا مع تسجيل الثقة ومنع الارتداد، فتقلّ التنبيهات الخاطئة.",
      "how.s4tag": "طبقة تحكم Windows",
      "how.s4title": "نفّذ",
      "how.s4text":
        "تتحول النية إلى إجراء أصلي — فأرة، لوحة مفاتيح، مفاتيح الوسائط، نوافذ وسطح مكتب افتراضي — عبر واجهة نظام التشغيل.",
      "gestures.eyebrow": "02 / مكتبة الإيماءات",
      "gestures.title": "تسع إيماءات. هذا هو كل القاموس.",
      "gestures.lede":
        "حركات صغيرة مدروسة — كلٌّ منها يُرقّى ويُفلتر ويُسجَّل وفق الثقة قبل وصوله إلى طبقة تحكم Windows.",
      "g1.title": "حرّك",
      "g1.trigger": "السبابة مرفوعة",
      "g1.note": "مؤشر دقيق — مُرقّى ومُلمّل. إحساس دون البكسل على شاشة 1080p.",
      "g2.title": "انقر",
      "g2.trigger": "قرص · سبابة + إبهام",
      "g2.note":
        "لُمسة للنقر. أبقِ للإبقاء على الزر مضغوطاً — أصل تفاعلات القرص والإبقاء.",
      "g3.title": "نقرة مزدوجة",
      "g3.trigger": "قرص مزدوج",
      "g3.note": "لمستان سريعتان، كعادتك تماماً. تفتح الملفات والتطبيقات.",
      "g4.title": "اسحب",
      "g4.trigger": "قرص + إبقاء + تحريك",
      "g4.note": "أمسك النوافذ والملفات والمقابض. أفلِت القرص للإسقاط.",
      "g5.title": "نقرة يمين",
      "g5.trigger": "إبهام + وسطى",
      "g5.note": "قائمة السياق عند الطلب — لمن لا يقبلون الاستغناء عنها.",
      "g6.title": "مرّر",
      "g6.trigger": "راحة مفتوحة، عمودي",
      "g6.note":
        "ارفع راحة اليد وانزلق باليد — يربط المستوى ارتفاع اليد بسرعة التمرير.",
      "g7.title": "اسحب للأمام/للخلف",
      "g7.trigger": "تمرير، يمين / يسار",
      "g7.note": "التالي والسابق — شرائح، صفحات، تبويبات. يراعي السرعة.",
      "g8.title": "إيقاف",
      "g8.trigger": "راحة اليد مسطّحة",
      "g8.note": "أبقِ راحة اليد مفتوحة لحظة — يتوقف التحكم حتى تُخفضها.",
      "g9.title": "قفل",
      "g9.trigger": "قبضة اليد",
      "g9.note": "قفل شاشة فوري. الإيماءة التي يعرفها الجميع غريزياً.",
      "voice.eyebrow": "03 / طبقة الصوت",
      "voice.title": "قُلها. أو أشر بيدك.",
      "voice.lede":
        "محرك نوايا محلي يربط العبارات المعترف بها بنفس نوايا الإيماءات. التعرف نفسه يعمل عبر سحابة Google افتراضياً، أو محلياً بالكامل مع Vosk/SAPI. أمثلة أوامر، أربع لغات، مفردات واحدة.",
      "voice.tableAria": "الأوامر الصوتية حسب اللغة",
      "voice.colTask": "المهمة",
      "voice.colEn": "English",
      "voice.colFr": "Français",
      "voice.colAr": "العربية",
      "voice.colNl": "Nederlands",
      "voice.r1.task": "افتح تطبيقاً",
      "voice.r1.en": "“open chrome”",
      "voice.r1.fr": "“ouvre chrome”",
      "voice.r1.ar": "“افتح كروم”",
      "voice.r1.nl": "“open chrome”",
      "voice.r2.task": "اكتب ملاحظة",
      "voice.r2.en": "“type: call back at…”",
      "voice.r2.fr": "“note : rappeler…”",
      "voice.r2.ar": "“اكتب ملاحظة”",
      "voice.r2.nl": "“type: bel terug om…”",
      "voice.r3.task": "الشريحة التالية",
      "voice.r3.en": "“next slide”",
      "voice.r3.fr": "“diapositive suivante”",
      "voice.r3.ar": "“الشريحة التالية”",
      "voice.r3.nl": "“volgende dia”",
      "voice.r4.task": "مرّر للأسفل",
      "voice.r4.en": "“scroll down”",
      "voice.r4.fr": "“descends la page”",
      "voice.r4.ar": "“مرّر للأسفل”",
      "voice.r4.nl": "“scroll naar beneden”",
      "voice.r5.task": "أوقف الوسائط",
      "voice.r5.en": "“pause the music”",
      "voice.r5.fr": "“mets en pause”",
      "voice.r5.ar": "“أوقف الموسيقى”",
      "voice.r5.nl": "“zet de muziek stil”",
      "voice.r6.task": "جمّد كل شيء",
      "voice.r6.en": "“freeze”",
      "voice.r6.fr": "“bloque tout”",
      "voice.r6.ar": "“تجمّد”",
      "voice.r6.nl": "“bevries alles”",
      "voice.callTitle": "وضع « الأيدي مشغولة » بالصوت أولاً",
      "voice.callText":
        "عندما تكون يداك مشغولتين — قفازات، أدوات، صينية طعام — يقود الصوت وحده الجهاز. نفس محرك النوايا، صفر إيماءات.",
      "voice.callBeta": "FR / AR / NL بمستوى تجريبي",
      "modes.eyebrow": "04 / الأوضاع والملفات",
      "modes.title": "مضبوط على طريقة عملك الحقيقية.",
      "modes.lede":
        "ثلاثة عشر ملفاً تلقائياً تَضبط حساسية الإيماءات والمناطق الميتة وسلوك الصوت حسب البيئة — معظمها لا يحتاج أيّ تدخّل.",
      "modes.m1.title": "أيدٍ مشغولة",
      "modes.m1.text":
        "الصوت أولاً. قفازات، طعام، أدوات. الإيماءات مقتصرة على مجموعة آمنة محجوزة.",
      "modes.m1.p1": "الصوت يقود",
      "modes.m1.p2": "إيماءات المستوى الكهربرتقالي فقط",
      "modes.m2.title": "صناعي",
      "modes.m2.text":
        "لوحات HMI وأعمال خط الإنتاج. مناطق ميتة كبيرة، حركات بطيئة متعمدة، منع ارتداد عالٍ.",
      "modes.m2.p1": "مناطق ميتة ممتدة",
      "modes.m2.p2": "تتبّع بالوضع البطيء",
      "modes.m3.title": "طبّي",
      "modes.m3.text":
        "تصفّح في الغرفة المعقّمة وأعمال ورقية. مؤقّتات محدودة، أيدٍ نظيفة.",
      "modes.m3.disc":
        "ليس جهازاً إكلينيكياً — لا تشخيص، لا علاج، لا مراقبة للمرضى.",
      "modes.m4.title": "عرض تقديمي",
      "modes.m4.text":
        "شرائح، ممر مؤشر الليزر، مناطق نقر دقيقة بعيداً عن حواف الشاشة.",
      "modes.m4.p1": "ممر الليزر نشط",
      "modes.m4.p2": "مناطق نقر مضبوطة",
      "modes.m5.title": "وسائط",
      "modes.m5.text":
        "فيديو بملء الشاشة مع تمرير الخط الزمني، مستوى الصوت حسب ارتفاع راحة اليد، تمرير للانتقال بين المسارات.",
      "modes.m5.p1": "إيماءات تمرير",
      "modes.m5.p2": "راحة اليد = مستوى الصوت",
      "modes.m6.title": "إتاحة الوصول",
      "modes.m6.text":
        "مناطق تفاعل كبيرة، انقر بالتوقّف، متوافق مع المفاتيح. إيماءات أقل وألطف.",
      "modes.m6.p1": "انقر بالتوقّف",
      "modes.m6.p2": "أهداف كبيرة",
      "modes.m7.title": "متصفح / PDF",
      "modes.m7.text":
        "ملفات تمرير + تكبير مرتبطة بمسافة راحة اليد، تمرير التبويبات، قرصات لقلب الصفحات.",
      "modes.m7.p1": "تكبير بالمسافة",
      "modes.m7.p2": "تمرير التبويبات",
      "modes.m8.title": "CAD · كشك · مخصص",
      "modes.m8.text":
        "دوران CAD واختيار دقيق، كشكات مقفلة، وملفات مخصصة قابلة لإعادة التعيين بالكامل. خمسة ملفات إضافية تأتي جاهزة — تكتشف الثلاثة عشر السياق تلقائياً عند تفعيلها.",
      "modes.m8.p1": "13",
      "modes.m8.p2": "4",
      "modes.m8.p3": "1",
      "modes.m8.mem": "الذاكرة",
      "modes.m8.profiles": "ملفات",
      "modes.m8.voice": "الصوت",
      "modes.m8.cam": "كاميرا",
      "try.eyebrow": "05 / مستوى مباشر",
      "try.title": "جرّبه — هنا على الفور.",
      "try.lede":
        'الفأرة هي مؤشرك الهوائي. اضغط مع الإبقاء يساراً لقرص والنقر، العجلة فوق المستند للتمرير، <kbd>مسافة</kbd> لوضع راحة اليد (العجلة تتمرر بقفزات كبيرة). يعمل باللمس: لمسة للنقر، سحب للتحريك.',
      "try.mediaOutput": "المخرج",
      "try.mediaAria": "مشغّل وسائط تجريبي — الأزرار تستجيب لنقرات القرص",
      "try.prevAria": "المسار السابق",
      "try.nextAria": "المسار التالي",
      "try.playAria": "تشغيل أو إيقاف",
      "try.playPause": "تشغيل أو إيقاف",
      "try.docLabel": "مستند",
      "try.docTitle": "quickstart.txt — قابل للتمرير",
      "try.docAria": "مستند بداية سريعة قابل للتمرير. العجلة تتمرر؛ وضع راحة اليد بقفزات كبيرة.",
      "try.quickTitle": "بداية سريعة — إعداد دون لمس",
      "try.step1":
        "<strong>ثبّت</strong> تطبيق Windows. بيئة MediaPipe وحزم اللغات مدمجة.",
      "try.step2":
        "<strong>عايِر.</strong> اجلس على مكتبك وارفع يداً واحدة. يثبّت المستوى مربّع مدى ذراعك ويرسمه على كامل الشاشة.",
      "try.step3":
        "<strong>أشر.</strong> السبابة مرفوعة = حركة. لاحظ أن المستوى يتبع الكتف لا راحة اليد — حركة رسغ صغيرة، تنقّل كبير بالشاشة.",
      "try.step4":
        "<strong>اقرص للنقر.</strong> سبابة + إبهام يُقتربان. أبقِ للإمساك، أفلِت للإسقاط.",
      "try.step5":
        "<strong>مرّر.</strong> راحة مفتوحة، انزلق عمودياً. تتبع السرعة ارتفاع اليد.",
      "try.step6":
        "<strong>الصوت.</strong> قل « افتح كروم ». يبقى التعرف على الجهاز عند اختيار Vosk أو SAPI (محرك Google الافتراضي يحتاج إنترنت)؛ ثم يربط محرك النوايا العبارة محلياً، فلا مشكلة مع اللهجات.",
      "try.step7":
        "<strong>إيقاف طارئ.</strong> اضغط <kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>H</kbd> في أي وقت — يتجمد كل شيء. اضغط مجدداً للاستئناف.",
      "try.afterLine":
        "هذا هو النظام كله. كل إجراء أعلاه هو نفس خط النوايا الذي يظهره المستوى التجريبي: إيماءة أو صوت → محرك النوايا → طبقة تحكم Windows.",
      "try.figCap1":
        'مرّر العجلة فوق هذا اللوح للتمرير. <strong>مسافة</strong> ثم عجلة = قفزات كبيرة بوضع راحة اليد.',
      "try.mediaStart": "اقرص وانقر زر التشغيل. إنه زر حقيقي — تعمل لوحة المفاتيح أيضاً.",
      "privacy.eyebrow": "06 / الخصوصية",
      "privacy.title": "لا يغادر هذا الجهاز أبداً.",
      "privacy.lede":
        "لقطات الفيديو وسجلات النوايا تبقى على الجهاز. الصوت كذلك على محركات Vosk/SAPI؛ محرك Google الافتراضي يرسل عبارتك إلى Google للتعرف. لا حسابات، لا مزامنة، ولا إشارات تحليلات.",
      "privacy.p1t": "معالجة محلية",
      "privacy.p1":
        "نماذج MediaPipe ومحرك النوايا تعمل على هذا الحاسوب. تُعالَج لقطات الكاميرا في الذاكرة وتُتجاهل، لا تغادر جهازك أبداً. صوت الميكروفون هو الاستثناء الوحيد: محرك الصوت الافتراضي (Google Web Speech) يرسل العبارة المنطوقة إلى خوادم Google؛ محركا Vosk وSAPI يبقيان التعرف محلياً بالكامل.",
      "privacy.p2t": "إيقاف الكاميرا",
      "privacy.p2":
        "مفتاح واحد في قائمة علبة النظام يقطع الكاميرا فوراً. اختصار عام يفعل نفس الشيء دون لمس العلبة.",
      "privacy.p3t": "وضع الخصوصية",
      "privacy.p3":
        "تشويش أو تعتيم اختياري للمعاينة المباشرة. ترى أنت ومن حولك أن التتبع نشط دون أن يرى أحد الوجوه على الشاشة.",
      "privacy.p4t": "مسح البيانات",
      "privacy.p4":
        "نقرة واحدة تمسح سجلات الاستعلامات والإعدادات والمعايرة. كل ما تعلّمه HADJ عنك يتسع في ملفات قليلة ويُنسى بلمسة.",
      "privacy.foot":
        "اختياري — معالجة فيديو محلية 100%: لا حساسات، لا مقاييس، لا حسابات. (التعرف على الصوت: محلي على Vosk/SAPI، سحابي افتراضياً على Google.)",
      "safety.eyebrow": "07 / الأمان",
      "safety.title": "مفتاح إيقاف في متناول اليد دائماً.",
      "safety.lede":
        "التحكم دون لمس قوي؛ وهو مصمم أيضاً ليبقى بعيداً عن طريقك. هذه ليست إضافات اختيارية.",
      "safety.stop": "إيقاف طارئ",
      "safety.stopKeys": "CTRL + ALT + H",
      "safety.stopCaption":
        "اضغط <strong>CTRL + ALT + H</strong> (أو الزر على الشاشة). تتجمد كل الإيماءات والأوامر الصوتية فوراً — اضغط نفس المفتاح للاستئناف. لا يتحرك شيء بينهما.",
      "safety.s1t": "رفض القفزات",
      "safety.s1":
        "تُتجاهل الحركة المفاجئة السريعة جداً ولا تُنفَّذ. تعالج منطق منع الارتداد و« اليد الميتة » الارتجافة كضجيج، لا كأمر.",
      "safety.s2t": "مناطق ميتة",
      "safety.s2":
        "حدّد نطاق حافة تُتجاهل فيه الإيماءات تماماً — فلا يحفّز وضع اليد قرب الشاشة شيئاً. معايَر لكل مكتب.",
      "safety.s3t": "تأكيد الإجراءات الخطرة",
      "safety.s3":
        "حذف بالسحب، إيقاف التشغيل، تهيئة — أي إجراء خطر يطلب التأكيد قبل التنفيذ. التأكيد هو قرصة ثانية متعمدة.",
      "faq.eyebrow": "08 / الأسئلة الشائعة",
      "faq.title": "إجابات صريحة.",
      "faq.q1.sum": "هل تُرسَل لقطات كاميرا الويب إلى أي مكان؟",
      "faq.q1.body":
        "لا — لقطات الكاميرا تبقى في ذاكرة جهازك وتُستخدم فقط لاستخراج المعالم. لا مسار رفع للفيديو، لا خادم، لا حسابات. الاستثناء الوحيد هو صوت الميكروفون: محرك الصوت الافتراضي (Google Web Speech) يرسل عبارتك إلى Google للتعرف؛ محركا Vosk وSAPI يبقيانها على الجهاز. هذه الصفحة PWA تعمل أيضاً بالكامل دون اتصال بعد أول تحميل؛ الصفحة لا تلمس الكاميرا أبداً.",
      "faq.q2.sum": "ما إصدارات Windows المدعومة؟",
      "faq.q2.body":
        "Windows 10 و Windows 11، بنية 64 بت، مع كاميرا ويب UVC قياسية. الميكروفون لطبقة الصوت اختياري. لا حاجة لبطاقة رسوميات منفصلة — تعمل MediaPipe على المعالج والرسوميات المدمجة الأساسية.",
      "faq.q3.sum": "هل يعمل دون اتصال بالكامل؟",
      "faq.q3.body":
        "تقريباً — مع فارق واحد. التتبّع والإيماءات ومحرك النوايا والنظر تعمل كلها دون اتصال مع نماذج MediaPipe المدمجة. التعرف على الصوت دون اتصال عند اختيار Vosk أو SAPI؛ محرك Google الافتراضي يحتاج اتصالاً بالإنترنت. هذه الصفحة PWA — بعد الزيارة الأولى يمكن تثبيتها وتشغيلها من ذاكرة خادم الخدمة دون أي اتصال.",
      "faq.q4.sum": "ما دقة الإيماءات فعلياً؟",
      "faq.q4.body":
        "كل نية تعبر بوابة ثقة (عادة 0.85–0.97، تظهر مباشرة في العرض) ونافذة منع ارتداد قبل الوصول إلى طبقة تحكم Windows. تضبط المعايرة صندوق المرجع حسب طول ذراعك وزاوية الكاميرا — حيث يفشل معظم الأنظمة « المهتزة ».",
      "faq.q5.sum": "ماذا عن النظرة والإيماءات المخصصة؟",
      "faq.q5.body":
        "تتبّع النظرة والإيماءات المخصصة المسجلة تأتي موسومة بأنها تجريبية — خلف راية وهي معطلة افتراضياً. مستبعدة من مجموعة الإيماءات المضمونة حتى تبلغ مستوى الثقة نفسه للإيماءات التسع الأساسية.",
      "faq.q6.sum": "هل يمكن استخدامه مع الفأرة ولوحة المفاتيح؟",
      "faq.q6.body":
        "نعم. التحكم هجين وقابل للتبديل — مفتاح في علبة النظام، اختصار، أو إيقاف تلقائي عندما تكون يداك على المفاتيح. يستخدم معظم الناس الفأرة للعمل الدقيق والإيماءات لكل شيء آخر.",
      "download.eyebrow": "09 / التنزيل",
      "download.title": "احصل على HADJ NO-TOUCH AI.",
      "download.lede":
        "مجاني، مفتوح المصدر، ويعمل على جهازك. لا حاجة لحساب. (التعرف على الصوت سحابي افتراضياً — محلي على محركي Vosk/SAPI.)",
      "download.beta": "v2.0 تجريبي",
      "download.latest": "الأحدث",
      "download.btn": "نزّل لـ Windows",
      "download.meta": "Windows 10 / 11 (x64) · ZIP ~205 م.ب · لا حاجة لمثبّت",
      "download.reqTitle": "المتطلبات النظامية",
      "req.os": "النظام",
      "req.cam": "الكاميرا",
      "req.mic": "الميكروفون",
      "req.gpu": "GPU",
      "req.ram": "الذاكرة",
      "req.disk": "القرص",
      "req.osVal": "Windows 10 / 11، بنية 64 بت",
      "req.camVal": "كاميرا ويب UVC قياسية",
      "req.micVal": "اختياري (لأوامر الصوت)",
      "req.gpuVal": "غير مطلوب — يعمل على CPU",
      "req.ramVal": "يُنصح بـ 4 ج.ب",
      "req.diskVal": "مساحة خالية ~500 م.ب",
      "download.instTitle": "التثبيت",
      "download.inst1": "نزّل ملف ZIP أعلاه.",
      "download.inst2": "فك الضغط في أي مجلد (مثل <code>C:\\HADJ</code>).",
      "download.inst3": "انقر نقراً مزدوجاً على <code>HADJ-NO-TOUCH-AI.exe</code>.",
      "download.inst4": "اسمح بالوصول إلى الكاميرا/الميكروفون عند الطلب.",
      "download.inst5": "اتبع معالج المعايرة الذي يظهر على الشاشة.",
      "download.instNote":
        "لا مثبّت، لا صلاحيات مدير. التطبيق محمول — شغّله من أي مجلد.",
      "download.verifyTitle": "تحقق من التنزيل",
      "download.verifyText": "مجموع تحقق SHA-256 للتحقق من السلامة:",
      "download.verifyHow":
        "يُنشر ملف <code>.sha256</code> جانبي بنفس البصمة بجانب ZIP. تحقق عبر PowerShell:<br><code>Get-FileHash .\\HADJ-NO-TOUCH-AI-Windows.zip -Algorithm SHA256</code>",
      "download.insideTitle": "ماذا يوجد بالداخل",
      "download.inside1": "التطبيق الرئيسي",
      "download.inside2": "سكريبت التشغيل",
      "download.inside3": "نماذج MediaPipe (حزمة صوت Vosk اختيارية)",
      "download.inside4": "13 ملفاً بكشف تلقائي",
      "download.inside5": "أوامر صوتية EN / FR / AR / NL",
      "download.footRow": "متاح أيضاً على",
      "download.footGit": "GitHub",
      "download.footNote": "مفتوح المصدر · لا مقاييس · لا حسابات · لقطات الكاميرا محلية",
      "footer.quick": "روابط سريعة",
      "footer.safety": "الأمان",
      "footer.faq": "الأسئلة الشائعة",
      "footer.line": "لا لمس هو الفكرة.",
      "footer.bottom": "HADJ NO-TOUCH AI · تحكم دون لمس في Windows",
      "footer.beta": "v2.0 تجريبي",
      "footer.exp": "النظرة والإيماءات المخصصة تجريبية",
      "footer.pwa": "PWA · جاهز دون اتصال",
      "demo.trackNow": "تشغيل ملف محلي — لا بث، كل شيء على جهازك.",
      "demo.playing": "تشغيل — اقرص وانقر مجدداً أو اضغط الزر للإيقاف.",
      "demo.paused": "متوقف. اقرص وانقر على التشغيل عندما تكون جاهزاً.",
    },

    /* ================= NEDERLANDS ================= */
    nl: {
      "meta.title": "HADJ NO-TOUCH AI — Bedien de computer zonder hem aan te raken",
      "meta.desc":
        "Bedien de computer zonder hem aan te raken — handgebaren, stem en blik voor Windows. Privacy eerst, camerabeelden blijven lokaal. Beschikbaar in Engels, Frans, Arabisch en Nederlands.",
      "skip": "Ga naar de inhoud",
      "nav.aria": "Hoofdnavigatie",
      "nav.homeAria": "HADJ NO-TOUCH AI — home",
      "nav.how": "Hoe het werkt",
      "nav.gestures": "Gebaren",
      "nav.voice": "Stem",
      "nav.modes": "Modi",
      "nav.privacy": "Privacy",
      "nav.download": "Downloaden",
      "nav.install": "Installeren",
      "nav.run": "Draaien op Windows",
      "lang.label": "Taal — Nederlands",
      "hero.eyebrow": "Contactloze bediening · Camera lokaal",
      "hero.title": 'Bedien de computer <span class="grad-text">zonder hem aan te raken.</span>',
      "hero.sub":
        "HADJ NO-TOUCH AI maakt van je webcam een virtueel interactievlak. Handgebaren, stem en blik besturen Windows — handsfree, privé en van jou. Geen sensoren, geen aanraking — camerabeelden blijven op je machine.",
      "hero.download": "Downloaden voor Windows",
      "hero.demo": "Probeer de demo",
      "hero.noteTitle": "Windows 10 / 11 (x64)",
      "hero.noteBody":
        "Wordt geleverd als native desktop-app, gedownload als ZIP via GitHub Releases. Alleen een webcam + microfoon nodig — MediaPipe en de intentiemotor draaien lokaal, op deze machine.",
      "hero.noteMeta":
        'Na installatie geen telemetrie en geen account, en de app downloadt niets tijdens gebruik. Opmerking: spraakherkenning gebruikt standaard de cloud-API van Google — kies Vosk of SAPI voor volledig lokale herkenning. Controleer het bestand met <code>SHA-256&nbsp;CAF27A9BE6B7CABE747A2FF817D9B5CA83142F6472F7C15D56EB20D29D98F188</code>.',
      "hero.chip1": '<span class="chip-dot" aria-hidden="true"></span>Stem EN / FR / AR / NL',
      "hero.chip2": '<span class="chip-dot" aria-hidden="true"></span>Alleen webcam',
      "hero.chip3": '<span class="chip-dot" aria-hidden="true"></span>Camera blijft lokaal',
      "hero.chip4": '<span class="chip-dot" aria-hidden="true"></span>Privacy eerst',
      "hero.demoAria":
        "Live demo van het virtuele interactievlak — je muis staat voor de lucht-aanwijzer",
      "hero.live": "LIVE",
      "hero.trackTop": "HADJ-OS // TRACKING",
      "hero.grid": "GRID 20PX",
      "hero.target": "DOEL 01 · KLIKZONE",
      "hero.pinchBtn": "KNIP OM TE KLIKKEN",
      "demo.ready": "klaar",
      "demo.clicked": "klik ✓",
      "demo.hud.mode": "MODUS",
      "demo.hud.gesture": "GEBAAR",
      "demo.hud.x": "X",
      "demo.hud.y": "Y",
      "demo.hud.conf": "VERT",
      "demo.hud.clicks": "KLIKKEN",
      "demo.hint":
        'muis = lucht-aanwijzer · <strong>links ingedrukt houden</strong> = knijpen→klik · <kbd>spatie</kbd> = palmmodus · wiel = scrollen',
      "demo.touchHint": "tik op een knop = knijp-klik · sleep = aanwijzer verplaatsen",
      "demo.palmOn":
        'Palmmodus AAN — het wiel scrolt met <strong>grote stappen</strong>. <kbd>spatie</kbd> om te stoppen.',
      "demo.noscript":
        "De live demo heeft JavaScript nodig. De Windows-app zelf werkt volledig op je machine, geen browser vereist.",
      "demo.confirm": "KNIP BEVESTIGD",
      "demo.confirmSub": "• klik →",
      "hero.scroll": "SCROLL",
      "stats.profiles": "auto profielen",
      "stats.languages": "talen",
      "stats.webcam": "webcam",
      "stats.touch": "aanraking",
      "how.eyebrow": "01 / Pijplijn",
      "how.title": "Van webcam naar Windows<br>besturing in één bewegingslijn.",
      "how.lede":
        "Vier lokale fasen. Camerabeelden verlaten je machine nooit — elk beeld wordt on-device verwerkt door gebundelde modellen en de runtime die je al hebt.",
      "how.s1tag": "MediaPipe invoerlaag",
      "how.s1title": "Webcam + Microfoon",
      "how.s1text":
        "Je camera streamt beelden lokaal naar de trackinglaag; de microfoon voedt de spraakmotor (standaard Google, of Vosk/SAPI voor on-device herkenning). Resolutie en snelheid passen zich aan de machine aan, zodat tracking soepel blijft.",
      "how.s2tag": "MediaPipe landmarks",
      "how.s2title": "Volgen",
      "how.s2text":
        "Hand-, gezichts- en houding-kenmerken worden geëxtraheerd op ~30 beelden/s — 21 punten per hand — met per-camera kalibratie voor licht en afstand.",
      "how.s3tag": "Intentiemotor",
      "how.s3title": "Begrijpen",
      "how.s3text":
        "Gebaar- en spraakzinnen worden gekoppeld aan een kleine set intenties met betrouwbaarheidsscore en debounce, zodat valse triggers zeldzaam blijven.",
      "how.s4tag": "Windows besturingslaag",
      "how.s4title": "Handelen",
      "how.s4text":
        "De intentie wordt een native actie — muis, toetsenbord, mediasleutels, venster- en virtueel bureaublad-besturing — via de OS-API.",
      "gestures.eyebrow": "02 / Gebaarbibliotheek",
      "gestures.title": "Negen gebaren. Dat is het hele vocabulaire.",
      "gestures.lede":
        "Kleine, bewuste bewegingen — elk gefilterd, gedebounced en op betrouwbaarheid gescoord voordat het de Windows besturingslaag bereikt.",
      "g1.title": "Bewegen",
      "g1.trigger": "Wijsvinger omhoog",
      "g1.note": "Precisie-aanwijzer — gefilterd en gladgestreken. Subpixel-gevoel op een 1080p-scherm.",
      "g2.title": "Klikken",
      "g2.trigger": "Knijpen · wijsvinger + duim",
      "g2.note":
        "Tik voor een klik. Houd vast om de knop ingedrukt te houden — de oorsprong van knijp-en-houd-interacties.",
      "g3.title": "Dubbelklikken",
      "g3.trigger": "Dubbel knijpen",
      "g3.note": "Twee snelle tikken, net als de gewoonte die je al hebt. Opent bestanden en apps.",
      "g4.title": "Slepen",
      "g4.trigger": "Knijp + houd + beweeg",
      "g4.note": "Grijp vensters, bestanden en schuifgrepen. Laat het knijpen los om neer te zetten.",
      "g5.title": "Rechtsklikken",
      "g5.trigger": "Duim + middelvinger",
      "g5.note": "Contextmenu op afroep — voor powerusers die er niet zonder kunnen.",
      "g6.title": "Scrollen",
      "g6.trigger": "Open palm, verticaal",
      "g6.note":
        "Palm omhoog, glijd met de hand — het vlak koppelt handhoogte aan scrollsnelheid.",
      "g7.title": "Vegen",
      "g7.trigger": "Veeg, links / rechts",
      "g7.note": "Volgende en vorige — dia's, pagina's, browsertabbladen. Snelheidsbewust.",
      "g8.title": "Pauze",
      "g8.trigger": "Palm plat gehouden",
      "g8.note": "Houd de palm een tel open — de besturing pauzeert tot je hem laat zakken.",
      "g9.title": "Vergrendelen",
      "g9.trigger": "Vuist",
      "g9.note": "Direct slotscreen. Het gebaar dat iedereen instinctief kent.",
      "voice.eyebrow": "03 / Stemlag",
      "voice.title": "Zeg het. Of wijs gewoon.",
      "voice.lede":
        "Een lokale intentiemotor koppelt herkende zinnen aan dezelfde intenties als gebaren. De herkenning zelf draait standaard op de cloud van Google, of volledig lokaal met Vosk/SAPI. Voorbeeldcommando's, vier talen, één vocabulaire.",
      "voice.tableAria": "Stemcommando's per taal",
      "voice.colTask": "Taak",
      "voice.colEn": "English",
      "voice.colFr": "Français",
      "voice.colAr": "العربية",
      "voice.colNl": "Nederlands",
      "voice.r1.task": "Een app openen",
      "voice.r1.en": "“open chrome”",
      "voice.r1.fr": "“ouvre chrome”",
      "voice.r1.ar": "“افتح كروم”",
      "voice.r1.nl": "“open chrome”",
      "voice.r2.task": "Een notitie schrijven",
      "voice.r2.en": "“type: call back at…”",
      "voice.r2.fr": "“note : rappeler…”",
      "voice.r2.ar": "“اكتب ملاحظة”",
      "voice.r2.nl": "“type: bel terug om…”",
      "voice.r3.task": "Volgende dia",
      "voice.r3.en": "“next slide”",
      "voice.r3.fr": "“diapositive suivante”",
      "voice.r3.ar": "“الشريحة التالية”",
      "voice.r3.nl": "“volgende dia”",
      "voice.r4.task": "Naar beneden scrollen",
      "voice.r4.en": "“scroll down”",
      "voice.r4.fr": "“descends la page”",
      "voice.r4.ar": "“مرّر للأسفل”",
      "voice.r4.nl": "“scroll naar beneden”",
      "voice.r5.task": "Media pauzeren",
      "voice.r5.en": "“pause the music”",
      "voice.r5.fr": "“mets en pause”",
      "voice.r5.ar": "“أوقف الموسيقى”",
      "voice.r5.nl": "“zet de muziek stil”",
      "voice.r6.task": "Alles bevriezen",
      "voice.r6.en": "“freeze”",
      "voice.r6.fr": "“bloque tout”",
      "voice.r6.ar": "“تجمّد”",
      "voice.r6.nl": "“bevries alles”",
      "voice.callTitle": "Stem-forward “handen vol” modus",
      "voice.callText":
        "Wanneer je handen vol zijn — handschoenen, gereedschap, een dienblad — kan de stem alleen de machine besturen. Dezelfde intentiemotor, nul gebaren nodig.",
      "voice.callBeta": "FR / AR / NL op bètaniveau",
      "modes.eyebrow": "04 / Modi & profielen",
      "modes.title": "Afgestemd op hoe je echt werkt.",
      "modes.lede":
        "Dertien automatische profielen passen gebaargevoeligheid, dode zones en stemgedrag per omgeving aan — de meeste hoef je nooit aan te raken.",
      "modes.m1.title": "Handen vol",
      "modes.m1.text":
        "Stem eerst. Handschoenen, eten, gereedschap. Gebaren beperkt tot een gereserveerde veilige set.",
      "modes.m1.p1": "Stem leidt",
      "modes.m1.p2": "Alleen amber-gebaren",
      "modes.m2.title": "Industrieel",
      "modes.m2.text":
        "HMI-panelen & lijnwerk. Grote dode zones, langzame bewuste bewegingen, hoge debounce.",
      "modes.m2.p1": "Uitgebreide dode zones",
      "modes.m2.p2": "Tracking in langzame modus",
      "modes.m3.title": "Medisch",
      "modes.m3.text":
        "Bladeren in steriele ruimtes en administratie. Tijdlimiet-triggers, handen blijven schoon.",
      "modes.m3.disc":
        "Geen klinisch apparaat — geen diagnose, geen behandeling, geen monitoring van patiënten.",
      "modes.m4.title": "Presentatie",
      "modes.m4.text":
        "Slide-decks, laserpointer-baan, precisie-klikzones ver van de schermranden.",
      "modes.m4.p1": "Laserbaan actief",
      "modes.m4.p2": "Klikzones afgesteld",
      "modes.m5.title": "Media",
      "modes.m5.text":
        "Fullscreen video met tijdlijn scrubbing, volume via palmhoogte, veeg voor nummers.",
      "modes.m5.p1": "Scrubgebaren",
      "modes.m5.p2": "Palm = volume",
      "modes.m6.title": "Toegankelijkheid",
      "modes.m6.text":
        "Grote hitzones, dwell-to-click, schakelaarvriendelijk. Minder, vriendelijkere gebaren.",
      "modes.m6.p1": "Dwell-to-click",
      "modes.m6.p2": "Grote doelen",
      "modes.m7.title": "Browser / PDF",
      "modes.m7.text":
        "Scroll + zoom profielen gekoppeld aan palmafstand, tabvegen, omslag-knijpen.",
      "modes.m7.p1": "Zoom op afstand",
      "modes.m7.p2": "Tabveeg",
      "modes.m8.title": "CAD · Kiosk · Aangepast",
      "modes.m8.text":
        "CAD-orbit en precisie-selectie, vergrendelde kioskvloeren en volledig hertoewijsbare aangepaste profielen. Nog vijf profielen zitten er standaard in — alle dertien detecteren automatisch de context wanneer ingeschakeld.",
      "modes.m8.p1": "13",
      "modes.m8.p2": "4",
      "modes.m8.p3": "1",
      "modes.m8.mem": "GEHEUG",
      "modes.m8.profiles": "PROFIELEN",
      "modes.m8.voice": "STEM",
      "modes.m8.cam": "CAM",
      "try.eyebrow": "05 / Live vlak",
      "try.title": "Probeer het — hier.",
      "try.lede":
        'De muis is je lucht-aanwijzer. Houd links ingedrukt om te knijp-klikken, wiel over het document om te scrollen, <kbd>spatie</kbd> voor palmmodus (wiel scrolt met grote stappen). Werkt op aanraking: tik om te klikken, sleep om te bewegen.',
      "try.mediaOutput": "UITGANG",
      "try.mediaAria": "Demo mediaspeler — knoppen reageren op knijp-klikken",
      "try.prevAria": "Vorige nummer",
      "try.nextAria": "Volgende nummer",
      "try.playAria": "Afspelen of pauzeren",
      "try.playPause": "Afspelen of pauzeren",
      "try.docLabel": "DOC",
      "try.docTitle": "quickstart.txt — scrollbaar",
      "try.docAria":
        "Scrollbaar quick-start document. Wiel scrolt; palmmodus scrolt met grote stappen.",
      "try.quickTitle": "SNELSTART — CONTACTLOZE INSTALLATIE",
      "try.step1":
        "<strong>Installeer</strong> de Windows-app. MediaPipe-runtime en taalpakketten zitten erin.",
      "try.step2":
        "<strong>Kalibreer.</strong> Ga aan je bureau zitten en steek één hand op. Het vlak vergrendelt het bereikbare blok van je arm en koppelt het aan het hele scherm.",
      "try.step3":
        "<strong>Wijs.</strong> Wijsvinger omhoog = bewegen. Merk op dat het vlak vanaf de schouder volgt, niet de palm — klein polswerk, grote schermreizen.",
      "try.step4":
        "<strong>Knijp om te klikken.</strong> Wijsvinger + duim sluiten. Houd vast om te pakken, laat los om neer te zetten.",
      "try.step5":
        "<strong>Scroll.</strong> Open palm, glijd verticaal. Wietsnelheid volgt handhoogte.",
      "try.step6":
        "<strong>Stem.</strong> Zeg “open chrome”. Herkenning blijft on-device met Vosk of SAPI (de standaard Google-motor heeft internet nodig); daarna koppelt de intentiemotor de zin lokaal, accenten zijn geen probleem.",
      "try.step7":
        "<strong>Noodstop.</strong> Druk op <kbd>CTRL</kbd>+<kbd>ALT</kbd>+<kbd>H</kbd> wanneer je maar wilt — alles bevriest. Druk nogmaals om verder te gaan.",
      "try.afterLine":
        "Dat is het hele systeem. Elke actie hierboven doorloopt dezelfde intentiepijplijn als het demovlak toont: gebaar of stem → intentiemotor → Windows besturingslaag.",
      "try.figCap1":
        'Scroll over dit paneel met het wiel. <strong>Spatie</strong> en dan wiel = grote palmmodus-stappen.',
      "try.mediaStart": "Knijp-klik op de afspeelknop. Het is een echte knop — toetsenbord werkt ook.",
      "privacy.eyebrow": "06 / Privacy",
      "privacy.title": "Verlaat deze machine nooit.",
      "privacy.lede":
        "Videobeelden en intentielogs blijven on-device. Audio ook op de Vosk/SAPI-motoren; de standaard Google-motor stuurt je zin naar Google voor herkenning. Geen account, geen sync, geen analytics-baken.",
      "privacy.p1t": "Lokale verwerking",
      "privacy.p1":
        "MediaPipe-modellen en de intentiemotor draaien op deze computer. Camerabeelden worden in het geheugen verwerkt en weggegooid, en verlaten je machine nooit. Microfoonaudio is de enige uitzondering: de standaard spraakmotor (Google Web Speech) stuurt je gesproken zin naar de servers van Google; Vosk en SAPI houden de herkenning volledig on-device.",
      "privacy.p2t": "Camera schakelaar",
      "privacy.p2":
        "Een enkele schakelaar in het sys-tray-menu schakelt de camera direct uit. Een globale sneltoets doet hetzelfde zonder het menu aan te raken.",
      "privacy.p3t": "Privacymodus",
      "privacy.p3":
        "Optionele vervaging of leeg scherm voor de live preview. Jij en mensen om je heen zien dat tracking actief is zonder dat iemand gezichten op het scherm ziet.",
      "privacy.p4t": "Gegevens wissen",
      "privacy.p4":
        "Eén klik wist querylogs, instellingen en kalibratie. Alles wat HADJ over jou heeft geleerd past in een paar bestanden en vergeet in een tik.",
      "privacy.foot":
        "Optioneel — 100% lokale videoverwerking: geen sensoren, geen telemetrie, geen account. (Spraakherkenning: lokaal op Vosk/SAPI, standaard cloud op Google.)",
      "safety.eyebrow": "07 / Veiligheid",
      "safety.title": "Een kill-switch die altijd binnen handbereik is.",
      "safety.lede":
        "Contactloze besturing is krachtig; het is ook ontworpen om uit de weg te blijven. Dit zijn geen optionele extra's.",
      "safety.stop": "NOODSTOP",
      "safety.stopKeys": "CTRL + ALT + H",
      "safety.stopCaption":
        "Druk op <strong>CTRL + ALT + H</strong> (of de on-screen knop). Elk gebaar en elke spraakbesturing bevriest onmiddellijk — druk nogmaals op dezelfde toets om verder te gaan. Niets beweegt daartussen.",
      "safety.s1t": "Sprongafwijzing",
      "safety.s1":
        "Plotselinge, onnatuurlijk snelle beweging wordt weggegooid, niet uitgevoerd. Debounce en dead-man logica behandelen een schrikbeweging als ruis, nooit als commando.",
      "safety.s2t": "Dode zones",
      "safety.s2":
        "Definieer een randbuffer waar gebaren volledig worden genegeerd — zodat het laten rusten van je hand bij het scherm nooit iets activeert. Gekalibreerd per bureau.",
      "safety.s3t": "Bevestig destructieve acties",
      "safety.s3":
        "Sleep-om-te-verwijderen, uitschakelen, formatteren — elke destructieve actie vraagt eenmaal voordat het gebeurt. Een bevestiging is een tweede, bewuste knijp.",
      "faq.eyebrow": "08 / FAQ",
      "faq.title": "Rechte antwoorden.",
      "faq.q1.sum": "Wordt mijn webcambeeld ergens naartoe gestuurd?",
      "faq.q1.body":
        "Nee — camerabeelden blijven in het geheugen van je machine en worden alleen gebruikt om landmarks af te leiden. Er is geen uploadpad voor video, geen server, geen account. De enige uitzondering is microfoonaudio: de standaard spraakmotor (Google Web Speech) stuurt je zin naar Google voor herkenning; Vosk en SAPI houden het on-device. Deze PWA-pagina draait ook volledig offline na de eerste lading; de pagina raakt de camera nooit aan.",
      "faq.q2.sum": "Welke Windows-versies worden ondersteund?",
      "faq.q2.body":
        "Windows 10 en Windows 11, 64-bit, met een standaard UVC-webcam. Microfoon voor de stemlaag is optioneel. Een dedicated GPU is niet nodig — MediaPipe draait op CPU en bescheiden geïntegreerde graphics.",
      "faq.q3.sum": "Werkt het volledig offline?",
      "faq.q3.body":
        "Bijna — met één nuance. Tracking, gebaren, de intentiemotor en blik draaien volledig offline met de gebundelde MediaPipe-modellen. Spraakherkenning is volledig offline met Vosk of SAPI; de standaard Google-motor heeft internet nodig. Deze pagina is een PWA — na het eerste bezoek kan hij worden geïnstalleerd en draaien vanuit de service-worker cache zonder enige verbinding.",
      "faq.q4.sum": "Hoe nauwkeurig zijn de gebaren echt?",
      "faq.q4.body":
        "Elke intentie passeert een betrouwbaarheidsdrempel (meestal 0.85–0.97, live getoond in de demo) en een debounce-venster voordat hij de Windows besturingslaag bereikt. Kalibratie stemt het referentieblok af op je armlengte en camerahoek — waar de meeste “wiebelige” systemen falen.",
      "faq.q5.sum": "Hoe zit het met blik en eigen gebaren?",
      "faq.q5.body":
        "Bliktracking en door de gebruiker opgenomen gebaren zijn gemarkeerd als experimenteel — ze zitten achter een vlag en staan standaard uit. Ze vallen buiten de gegarandeerde gebaarset tot ze dezelfde betrouwbaarheidslat halen als de negen kerngebaren.",
      "faq.q6.sum": "Kan ik het naast muis en toetsenbord gebruiken?",
      "faq.q6.body":
        "Ja. Besturing is hybride en schakelbaar — tray-schakelaar, sneltoets, of automatische pauze wanneer je handen op de toetsen zijn. De meeste mensen gebruiken de muis voor fijn werk en gebaren voor al het overige.",
      "download.eyebrow": "09 / Download",
      "download.title": "Krijg HADJ NO-TOUCH AI.",
      "download.lede":
        "Gratis, open-source en draait op je machine. Geen account nodig. (Spraakherkenning is standaard cloud — lokaal op Vosk/SAPI.)",
      "download.beta": "v2.0-bèta",
      "download.latest": "Nieuwste",
      "download.btn": "Downloaden voor Windows",
      "download.meta": "Windows 10 / 11 (x64) · ~205 MB ZIP · Geen installateur nodig",
      "download.reqTitle": "Systeemvereisten",
      "req.os": "Besturingssysteem",
      "req.cam": "Camera",
      "req.mic": "Microfoon",
      "req.gpu": "GPU",
      "req.ram": "RAM",
      "req.disk": "Schijf",
      "req.osVal": "Windows 10 / 11, 64-bit",
      "req.camVal": "Standaard UVC-webcam",
      "req.micVal": "Optioneel (voor stemcommando's)",
      "req.gpuVal": "Niet nodig — draait op CPU",
      "req.ramVal": "4 GB aanbevolen",
      "req.diskVal": "~500 MB vrije ruimte",
      "download.instTitle": "Installatie",
      "download.inst1": "Download het ZIP-bestand hierboven.",
      "download.inst2": "Pak uit naar een willekeurige map (bijv. <code>C:\\HADJ</code>).",
      "download.inst3": "Dubbelklik op <code>HADJ-NO-TOUCH-AI.exe</code>.",
      "download.inst4": "Sta toegang tot camera/microfoon toe wanneer gevraagd.",
      "download.inst5": "Volg de installatiewizard voor kalibratie op het scherm.",
      "download.instNote":
        "Geen installateur, geen beheerdersrechten nodig. De app is draagbaar — te starten vanuit elke map.",
      "download.verifyTitle": "Controleer de download",
      "download.verifyText": "SHA-256-checksum om de integriteit te controleren:",
      "download.verifyHow":
        "Een <code>.sha256</code>-bijbestand met dezelfde vingerafdruk wordt naast de ZIP gepubliceerd. Controleer met PowerShell:<br><code>Get-FileHash .\\HADJ-NO-TOUCH-AI-Windows.zip -Algorithm SHA256</code>",
      "download.insideTitle": "Wat zit erin",
      "download.inside1": "hoofdapplicatie",
      "download.inside2": "starterscript",
      "download.inside3": "MediaPipe-modellen (Vosk spraakpakket optioneel)",
      "download.inside4": "13 auto-detect profielen",
      "download.inside5": "Stemcommando's EN / FR / AR / NL",
      "download.footRow": "Ook verkrijgbaar op",
      "download.footGit": "GitHub",
      "download.footNote": "Open source · Geen telemetrie · Geen account · Camerabeelden blijven lokaal",
      "footer.quick": "Snelle links",
      "footer.safety": "Veiligheid",
      "footer.faq": "FAQ",
      "footer.line": "Geen aanraking is het punt.",
      "footer.bottom": "HADJ NO-TOUCH AI · contactloze besturing voor Windows",
      "footer.beta": "v2.0-bèta",
      "footer.exp": "blik & eigen gebaren experimenteel",
      "footer.pwa": "PWA · offline gereed",
      "demo.trackNow": "Nu wordt een lokaal bestand afgespeeld — geen stream, alles op je machine.",
      "demo.playing": "Speelt af — knijp-klik opnieuw of druk op de knop om te pauzeren.",
      "demo.paused": "Gepauzeerd. Knijp-klik op afspelen wanneer je klaar bent.",
    },
  };

  /* ---------- Lookup ---------- */

  const lookup = (lang, key) => {
    const dict = STR[lang] || STR.en;
    switch (typeof dict[key]) {
      case "string":
        return dict[key];
      case "undefined":
        break;
      default:
        return String(dict[key]);
    }
    const en = STR.en[key];
    if (typeof en === "string") return en;
    return key;
  };

  /* ---------- Public API ---------- */

  const t = (key, lang) => lookup(lang || current, key);

  const supported = (code) => SUPPORTED.indexOf(code) !== -1;

  const detect = () => {
    try {
      const saved = window.localStorage.getItem(STORE_KEY);
      if (saved && supported(saved)) return saved;
    } catch (_) {}
    const nav = (navigator.language || "en").toLowerCase().slice(0, 2);
    return supported(nav) ? nav : "en";
  };

  const apply = () => {
    const doc = document;
    doc.documentElement.lang = current;
    doc.documentElement.dir = DIR[current] || "ltr";

    doc.querySelectorAll("[data-i18n]").forEach((el) => {
      el.textContent = t(el.getAttribute("data-i18n"));
    });
    doc.querySelectorAll("[data-i18n-html]").forEach((el) => {
      el.innerHTML = t(el.getAttribute("data-i18n-html"));
    });
    doc.querySelectorAll("[data-i18n-aria]").forEach((el) => {
      el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria")));
    });

    const title = t("meta.title");
    if (doc.title !== title) doc.title = title;
    const meta = doc.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute("content", t("meta.desc"));

    window.dispatchEvent(new CustomEvent("hadjlangchange", { detail: { lang: current } }));
  };

  const setLang = (lang) => {
    if (!supported(lang)) return;
    current = lang;
    try {
      window.localStorage.setItem(STORE_KEY, lang);
    } catch (_) {}
    apply();
  };

  const init = () => {
    current = detect();
    apply();
    return current;
  };

  const isRTL = () => (DIR[current] || "ltr") === "rtl";

  return {
    VERSION,
    SUPPORTED,
    NAMES,
    dir: DIR,
    current: () => current,
    t,
    init,
    apply,
    setLang,
    isRTL,
    RTL: isRTL,
  };
})();