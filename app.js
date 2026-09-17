/* EDU-AIR — PWA interactivity: i18n wiring + classroom demo */
(function () {
  "use strict";

  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

  const i18n = window.eduI18n;
  const t = (k) => (i18n ? i18n.t(k) : k);

  const canvas = $("#stage");
  const ctx = canvas.getContext("2d");
  const CW = canvas.width, CH = canvas.height;

  /* ---------------- demo state ---------------- */
  const SLIDES = 3;
  const QUIZ_Q = 3;
  const QUIZ_ANSWER = [1, 2, 1]; // correct option per question

  let slide = 0;
  let zoom = 1;
  let paused = false;
  let tool = "point";
  let strokes = [];
  let pointer = { x: -50, y: -50, inStage: false, down: false };
  let dragStroke = null;
  let clearArmed = false;

  let timerRunning = false;
  let timerSecs = 0;
  let timerIv = null;

  let quizOn = false;
  let quizIdx = 0;
  let quizScore = 0;
  let quizAnswered = -1; // -1 none, 0..3 chosen option
  let quizRevealed = false;

  let paint = "cyan";
  let focusMode = false;
  let motionOk = true;
  let pulses = [];
  let pulseTimer = null;

  /* ---------------- dom refs ---------------- */
  const H = {
    slide: $("#hud-slide"),
    tool: $("#hud-tool"),
    clock: $("#hud-clock"),
    quiz: $("#hud-quiz"),
    hint: $("#demo-hint"),
    timer: $("#timer-btn"),
    quizBtn: $("#quiz-btn"),
  };
  const quizPanel = () => $("#quiz-panel");
  const shell = $("#stage-shell");
  const demoCard = $("#demo-card");
  const focusBtn = $("#focus-btn");
  const focusLbl = $("#focus-lbl");
  const focusExit = $("#focus-exit");
  const motionBtn = $("#motion-btn");
  const motionLbl = $("#motion-lbl");

  /* ---------------- helpers ---------------- */
  function pos(e) {
    const r = canvas.getBoundingClientRect();
    return {
      x: (clamp(e.clientX - r.left, 0, r.width) / r.width) * CW,
      y: (clamp(e.clientY - r.top, 0, r.height) / r.height) * CH,
    };
  }

  function fmtClock(s) {
    const m = Math.floor(s / 60), ss = s % 60;
    return String(m).padStart(2, "0") + ":" + String(ss).padStart(2, "0");
  }

  function roundedRectPath(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function drawScene() {
    ctx.clearRect(0, 0, CW, CH);
    drawSlide();
    drawStrokes();
    if (!paused) drawPointer();
    drawPulses();
  }

  function drawPulses() {
    if (!pulses.length) return;
    const now = performance.now();
    const alive = [];
    for (const p of pulses) {
      const k = (now - p.start) / 650;
      if (k >= 1) continue;
      alive.push(p);
      const e = 1 - Math.pow(1 - k, 3);
      ctx.globalAlpha = 1 - k;
      ctx.strokeStyle = p.color;
      ctx.lineWidth = Math.max(1, 4 * (1 - k));
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r0 + (p.maxR - p.r0) * e, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
    pulses = alive;
  }

  function addPulse(x, y, color, big) {
    if (!motionOk) return;
    pulses.push({ x, y, color, r0: big ? 18 : 8, maxR: big ? 60 : 26, start: performance.now() });
    if (pulses.length > 8) pulses.shift();
    if (pulseTimer) clearTimeout(pulseTimer);
    pulseTimer = setTimeout(() => {
      pulseTimer = null;
      if (pulses.length) { pulses = []; drawScene(); }
    }, 700);
  }

  function drawSlide() {
    const g = ctx.createLinearGradient(0, 0, 0, CH);
    g.addColorStop(0, "#0D1915");
    g.addColorStop(1, "#0A120F");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, CW, CH);

    ctx.strokeStyle = "rgba(169,245,216,.05)";
    ctx.lineWidth = 1;
    for (let x = 0; x <= CW; x += 48) { ctx.beginPath(); ctx.moveTo(x + .5, 0); ctx.lineTo(x + .5, CH); ctx.stroke(); }
    for (let y = 0; y <= CH; y += 48) { ctx.beginPath(); ctx.moveTo(0, y + .5); ctx.lineTo(CW, y + .5); ctx.stroke(); }

    const zx = CW * 0.5, zy = CH * 0.5;
    const sw = CW * 0.82 * zoom, sh = CH * 0.78 * zoom;
    const sx = zx - sw / 2, sy = zy - sh / 2;

    ctx.fillStyle = "rgba(0,0,0,.4)";
    roundedRectPath(sx + 8, sy + 12, sw, sh, 14); ctx.fill();

    const sheet = ctx.createLinearGradient(sx, sy, sx, sy + sh);
    sheet.addColorStop(0, "#F6FAF7");
    sheet.addColorStop(1, "#E9F0EB");
    ctx.fillStyle = sheet;
    roundedRectPath(sx, sy, sw, sh, 14); ctx.fill();
    ctx.strokeStyle = "rgba(20,40,34,.25)";
    ctx.lineWidth = 1;
    roundedRectPath(sx, sy, sw, sh, 14); ctx.stroke();

    const mx = sx + sw * 0.08;
    const cw = sw * 0.84;

    ctx.fillStyle = "#1B3A31";
    roundedRectPath(mx, sy + sh * 0.09, cw, sh * 0.09, 7); ctx.fill();
    ctx.fillStyle = "#0E1B19";
    ctx.font = "700 " + Math.max(14, sh * 0.05) + "px system-ui, sans-serif";
    ctx.textBaseline = "middle";
    ctx.fillText("EDU-AIR · " + (slide + 1) + "/" + SLIDES, mx + 14, sy + sh * 0.135);

    const bl = [
      { w: 0.95, h: 0.055, y: 0.24 },
      { w: 0.78, h: 0.055, y: 0.34 },
      { w: 0.86, h: 0.055, y: 0.44 },
      { w: 0.62, h: 0.055, y: 0.54 },
    ];
    ctx.fillStyle = "rgba(27,58,49,.16)";
    for (const b of bl) {
      roundedRectPath(mx, sy + sh * b.y, cw * b.w, sh * b.h, 6); ctx.fill();
    }

    const dx = sx + sw * 0.62, dy = sy + sh * 0.68;
    const dsz = Math.min(sw * 0.26, sh * 0.18);
    ctx.strokeStyle = "#2AA48A";
    ctx.lineWidth = 2.5;
    if (slide === 0) {
      ctx.beginPath(); ctx.moveTo(dx - dsz / 2, dy + dsz / 2); ctx.lineTo(dx, dy - dsz / 2); ctx.lineTo(dx + dsz / 2, dy + dsz / 2); ctx.closePath(); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(dx - dsz / 3, dy + dsz / 2); ctx.lineTo(dx - dsz / 3, dy + dsz * .1); ctx.stroke();
    } else if (slide === 1) {
      ctx.beginPath(); ctx.arc(dx, dy, dsz / 3, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(dx - dsz / 3, dy - dsz / 3); ctx.lineTo(dx + dsz / 3, dy + dsz / 3); ctx.stroke();
    } else {
      for (let i = -1; i <= 1; i++) {
        ctx.beginPath(); ctx.moveTo(dx + i * dsz / 4, dy + dsz / 3); ctx.lineTo(dx + i * dsz / 4, dy - dsz / 3); ctx.stroke();
      }
      ctx.beginPath(); ctx.moveTo(dx - dsz / 2, dy + dsz / 2); ctx.lineTo(dx + dsz / 2, dy + dsz / 2); ctx.stroke();
    }

    ctx.fillStyle = "#FFD166";
    ctx.beginPath(); ctx.arc(sx + sw - 34 * zoom, sy + sh * 0.09, 15 * zoom, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#0E1B19";
    ctx.font = "800 " + Math.max(13, 14 * zoom) + "px Consolas, monospace";
    ctx.textAlign = "center";
    ctx.fillText(String(slide + 1), sx + sw - 34 * zoom, sy + sh * 0.09 + 1);
    ctx.textAlign = "left";
  }

  function drawStrokes() {
    for (const s of strokes) {
      if (s.tool === "highlight") {
        ctx.globalAlpha = 0.5;
        ctx.strokeStyle = s.color;
        ctx.lineWidth = 26;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.beginPath();
        s.pts.forEach((p, i) => (i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)));
        ctx.stroke();
        ctx.globalAlpha = 1;
      } else {
        ctx.strokeStyle = s.color;
        ctx.lineWidth = s.width;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.beginPath();
        s.pts.forEach((p, i) => (i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)));
        ctx.stroke();
      }
    }
  }

  function drawPointer() {
    if (!pointer.inStage) return;
    const r = pointer.down ? 15 : 10;
    ctx.strokeStyle = pointer.down ? "#FFD166" : "#A9F5D8";
    ctx.lineWidth = pointer.down ? 2.5 : 2;
    ctx.beginPath();
    ctx.arc(pointer.x, pointer.y, r, 0, Math.PI * 2);
    ctx.stroke();
    if (pointer.down) {
      ctx.fillStyle = "rgba(255,209,102,.15)";
      ctx.beginPath();
      ctx.arc(pointer.x, pointer.y, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#FFE39A";
      ctx.beginPath(); ctx.arc(pointer.x - r * .55, pointer.y, 2.5, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(pointer.x + r * .55, pointer.y, 2.5, 0, Math.PI * 2); ctx.fill();
    } else {
      ctx.fillStyle = "#A9F5D8";
      ctx.beginPath(); ctx.arc(pointer.x, pointer.y, 2.2, 0, Math.PI * 2); ctx.fill();
    }
  }

  /* ---------------- stroke tools ---------------- */
  const PALETTE = { cyan: "#4DC8FF", amber: "#FFD166", blue: "#5B8CFF", magenta: "#FF5DA2", white: "#FFFFFF" };

  function addPoint(p) {
    if (tool === "erase") {
      strokes = strokes.filter((s) => !s.pts.some((q) => Math.hypot(q.x - p.x, q.y - p.y) < 26));
      return;
    }
    if (!dragStroke) {
      dragStroke = { tool, color: PALETTE[paint], width: tool === "draw" ? 4 : 8, pts: [p] };
      strokes.push(dragStroke);
    } else {
      const last = dragStroke.pts[dragStroke.pts.length - 1];
      if (Math.hypot(p.x - last.x, p.y - last.y) > 2.5) dragStroke.pts.push(p);
    }
  }

  function clearBoard() {
    strokes = [];
    dragStroke = null;
    clearArmed = false;
    updateToolbar();
  }

  /* ---------------- toolbar / hud ---------------- */
  function updateToolbar() {
    $$(".toolbar [data-tool]").forEach((b) => b.classList.toggle("active", b.dataset.tool === tool));
    const clear = $('[data-tool="clear"]');
    clear.classList.toggle("arming", clearArmed);
    clear.textContent = clearArmed ? "?" : t("demo.toolClear");
  }

  function setTool(next) {
    tool = next;
    if (next !== "clear") clearArmed = false;
    updateToolbar();
    renderHud();
    setHint();
  }

  function setHint() {
    H.hint.textContent = pointer.inStage && pointer.down ? t("demo.hintPress") : t("demo.hintMove");
  }

  function renderHud() {
    H.slide.textContent = (slide + 1) + "/" + SLIDES;
    H.tool.textContent = t("demo.tool" + tool[0].toUpperCase() + tool.slice(1));
    H.clock.textContent = fmtClock(timerSecs);
    H.quiz.textContent = quizOn ? t("demo.quizOn") : t("demo.quizOff");
    H.timer.textContent = timerRunning ? t("demo.timerStop") : t("demo.timerStart");
    H.quizBtn.textContent = quizOn ? t("demo.quizStop") : t("demo.quizStart");
  }

  function updateSlide(d) {
    slide = clamp(slide + d, 0, SLIDES - 1);
    clearBoard();
    renderHud();
    drawScene();
  }

  function updateZoom(d) {
    zoom = clamp(zoom + d, 0.5, 2);
    drawScene();
  }

  function togglePause() {
    paused = !paused;
    shell.classList.toggle("paused", paused);
    pauseOverlay.classList.toggle("hidden", !paused);
    canvas.style.cursor = paused ? "default" : "none";
    if (paused) canvas.blur();
    drawScene();
  }

  function toggleTimer() {
    timerRunning = !timerRunning;
    if (timerRunning) {
      timerSecs = 0;
      H.clock.textContent = fmtClock(timerSecs);
      timerIv = setInterval(() => {
        timerSecs++;
        H.clock.textContent = fmtClock(timerSecs);
      }, 1000);
    } else if (timerIv) {
      clearInterval(timerIv);
      timerIv = null;
    }
    renderHud();
  }

  /* ---------------- quiz ---------------- */
  function renderQuizDoor() {
    const panel = quizPanel();
    if (!quizOn) { panel.classList.add("hidden"); return; }
    panel.classList.remove("hidden");

    const q = quizIdx;
    $("#quiz-q").textContent = t("demo.q" + (q + 1) + "u");
    ["a", "b", "c", "d"].forEach((o, i) => {
      const el = $("#quiz-o" + o);
      el.querySelector(".qopletter").textContent = t("demo.opt" + o.toUpperCase());
      el.querySelector(".qoptext").textContent = t("demo.q" + (q + 1) + o);
      el.classList.remove("pick", "correct", "wrong");
      if (quizAnswered === i) el.classList.add("pick", i === QUIZ_ANSWER[q] ? "correct" : "wrong");
      if (quizRevealed && i === QUIZ_ANSWER[q]) el.classList.add("correct");
    });

    const fb = $("#quiz-fb");
    if (quizAnswered >= 0) {
      fb.textContent = quizAnswered === QUIZ_ANSWER[q]
        ? t("demo.correct")
        : t("demo.wrong") + " " + String.fromCharCode(65 + QUIZ_ANSWER[q]) + ".";
      fb.classList.add("show");
    } else if (quizRevealed) {
      fb.textContent = t("demo.correct");
      fb.classList.add("show");
    } else {
      fb.textContent = "";
      fb.classList.remove("show");
    }
    $("#quiz-score").textContent = t("demo.score") + ": " + quizScore + "/" + QUIZ_Q;
    $("#quiz-reveal").textContent = t("demo.reveal");
    $("#quiz-next").textContent = t("demo.nextQ");
  }

  function quizAnswer(i) {
    if (!quizOn || quizAnswered >= 0 || quizRevealed) return;
    quizAnswered = i;
    if (i === QUIZ_ANSWER[quizIdx]) quizScore++;
    addPulse(CW * 0.5, CH * 0.5, i === QUIZ_ANSWER[quizIdx] ? "#34D399" : "#F87171", true);
    renderQuizDoor();
    drawScene();
  }

  function quizReveal() {
    if (!quizOn) return;
    if (quizAnswered < 0) quizRevealed = true;
    renderQuizDoor();
    drawScene();
  }

  function quizNext() {
    if (!quizOn) return;
    quizAnswered = -1;
    quizRevealed = false;
    quizIdx = (quizIdx + 1) % QUIZ_Q;
    addPulse(CW * 0.5, CH * 0.5, "#FFD166", true);
    renderQuizDoor();
    drawScene();
  }

  function toggleQuiz() {
    quizOn = !quizOn;
    if (quizOn) {
      quizAnswered = -1;
      quizRevealed = false;
      quizScore = 0;
      if (quizIdx >= QUIZ_Q) quizIdx = 0;
    }
    addPulse(CW * 0.5, CH * 0.5, "#FFD166", true);
    renderHud();
    renderQuizDoor();
    drawScene();
  }

  /* ---------------- demo panel markup ---------------- */
  const quizPanelDiv = document.createElement("div");
  quizPanelDiv.id = "quiz-panel";
  quizPanelDiv.className = "quiz-panel hidden";
  quizPanelDiv.setAttribute("role", "dialog");
  quizPanelDiv.setAttribute("aria-label", "Quiz");
  quizPanelDiv.innerHTML =
    '<span class="quiz-q" id="quiz-q"></span>' +
    '<div class="quiz-opts">' +
      '<button type="button" class="qop" id="quiz-oa" data-opt="0"><span class="qopletter">A</span><span class="qoptext"></span></button>' +
      '<button type="button" class="qop" id="quiz-ob" data-opt="1"><span class="qopletter">B</span><span class="qoptext"></span></button>' +
      '<button type="button" class="qop" id="quiz-oc" data-opt="2"><span class="qopletter">C</span><span class="qoptext"></span></button>' +
      '<button type="button" class="qop" id="quiz-od" data-opt="3"><span class="qopletter">D</span><span class="qoptext"></span></button>' +
    "</div>" +
    '<p class="quiz-fb" id="quiz-fb"></p>' +
    '<div class="quiz-bar">' +
      '<span class="quiz-score" id="quiz-score"></span>' +
      '<div class="quiz-actions">' +
        '<button type="button" class="tool" id="quiz-reveal"></button>' +
        '<button type="button" class="tool" id="quiz-next"></button>' +
      "</div>" +
    "</div>";
  shell.appendChild(quizPanelDiv);

  const pauseOverlay = document.createElement("div");
  pauseOverlay.id = "pause-overlay";
  pauseOverlay.className = "paused-overlay hidden";
  pauseOverlay.textContent = "PAUSED";
  shell.appendChild(pauseOverlay);

  $$(".qop", quizPanelDiv).forEach((b) => b.addEventListener("click", () => quizAnswer(+b.dataset.opt)));
  $("#quiz-reveal").addEventListener("click", quizReveal);
  $("#quiz-next").addEventListener("click", quizNext);

  /* ---------------- pointer interaction ---------------- */
  canvas.addEventListener("pointermove", (e) => {
    const p = pos(e);
    pointer.x = p.x; pointer.y = p.y;
    pointer.inStage = true;
    drawScene();
  });
  canvas.addEventListener("pointerenter", () => {
    pointer.inStage = true;
    setHint();
    drawScene();
  });
  canvas.addEventListener("pointerleave", () => {
    pointer.inStage = false;
    pointer.down = false;
    dragStroke = null;
    setHint();
    drawScene();
  });
  canvas.addEventListener("pointerdown", (e) => {
    if (paused || e.button !== 0) return;
    const p = pos(e);
    pointer.down = true;
    pointer.x = p.x; pointer.y = p.y;
    setHint();
    addPoint(p);
    addPulse(p.x, p.y, tool === "point" ? "#FFD166" : tool === "erase" ? "#94A3B8" : PALETTE[paint], false);
    drawScene();
  });
  window.addEventListener("pointermove", (e) => {
    if (!pointer.down) return;
    const p = pos(e);
    pointer.x = clamp(p.x, 0, CW);
    pointer.y = clamp(p.y, 0, CH);
    addPoint(p);
    drawScene();
  });
  window.addEventListener("pointerup", (e) => {
    if (!pointer.down) return;
    const p = pos(e);
    pointer.down = false;
    if (dragStroke) {
      const moved = dragStroke.pts.length;
      if (moved <= 1 && tool !== "erase") {
        strokes.push({ tool: "point", color: PALETTE[paint], width: 8, pts: [p, { x: p.x + 0.01, y: p.y + 0.01 }] });
      }
      dragStroke = null;
      addPulse(p.x, p.y, tool === "erase" ? "#94A3B8" : PALETTE[paint], false);
    }
    setHint();
    drawScene();
  });

  /* ---------------- keyboard fallback ---------------- */
  window.addEventListener("keydown", (e) => {
    const el = e.target;
    if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.tagName === "SELECT")) return;
    if (e.code === "F5") { e.preventDefault(); slide = 0; clearBoard(); renderHud(); drawScene(); }
    else if (e.code === "Escape") { e.preventDefault(); if (focusMode) { toggleFocus(); } else { slide = 0; clearBoard(); renderHud(); drawScene(); } }
    else if (e.key === "f" || e.key === "F") { toggleFocus(); }
    else if (e.key === "ArrowRight") { updateSlide(1); }
    else if (e.key === "ArrowLeft") { updateSlide(-1); }
    else if (e.key === "b" || e.key === "B") { togglePause(); }
    else if (e.ctrlKey && (e.key === "+" || e.key === "-" || e.key === "=" || e.key === "_")) { e.preventDefault(); updateZoom(e.key === "=" || e.key === "+" ? 0.25 : -0.25); }
    else if (e.key === "Delete" || e.key === "Backspace") { clearBoard(); drawScene(); }
  });

  /* ---------------- toolbar events ---------------- */
  $$(".toolbar [data-tool]").forEach((b) => {
    b.addEventListener("click", () => {
      if (b.dataset.tool !== "clear") { setTool(b.dataset.tool); drawScene(); return; }
      if (strokes.length === 0) { clearArmed = false; updateToolbar(); return; }
      if (clearArmed) { clearBoard(); drawScene(); return; }
      clearArmed = true;
      updateToolbar();
      window.setTimeout(() => { clearArmed = false; updateToolbar(); }, 2400);
      return;
    });
  });
  $("#slide-prev").addEventListener("click", () => updateSlide(-1));
  $("#slide-next").addEventListener("click", () => updateSlide(1));
  $("#zoom-in").addEventListener("click", () => updateZoom(0.25));
  $("#zoom-out").addEventListener("click", () => updateZoom(-0.25));
  $("#timer-btn").addEventListener("click", toggleTimer);
  $("#quiz-btn").addEventListener("click", toggleQuiz);

  /* ---------------- palette swatches ---------------- */
  $$(".swatch").forEach((b) => {
    b.addEventListener("click", () => {
      paint = b.dataset.paint;
      $$(".swatch").forEach((o) => o.classList.toggle("active", o === b));
    });
  });

  /* ---------------- presentation: focus + motion ---------------- */
  function syncFocusUI() {
    focusLbl.textContent = t(focusMode ? "demo.focusExit" : "demo.focus");
    focusBtn.setAttribute("aria-pressed", String(focusMode));
    focusBtn.classList.toggle("active", focusMode);
  }

  function toggleFocus() {
    focusMode = !focusMode;
    demoCard.classList.toggle("focus", focusMode);
    syncFocusUI();
    drawScene();
  }

  focusBtn.addEventListener("click", toggleFocus);
  focusExit.addEventListener("click", toggleFocus);

  const matchReduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");

  function motionPref() {
    try { return localStorage.getItem("edu.air.motion"); } catch (e) { return null; }
  }

  function applyMotion() {
    const saved = motionPref();
    motionOk = saved ? saved === "on" : !(matchReduce && matchReduce.matches);
    document.documentElement.dataset.motion = motionOk ? "on" : "off";
    motionLbl.textContent = t(motionOk ? "demo.motionOn" : "demo.motionOff");
    motionBtn.setAttribute("aria-pressed", String(motionOk));
    motionBtn.classList.toggle("active", motionOk);
    if (!motionOk) pulses = [];
    drawScene();
  }

  motionBtn.addEventListener("click", () => {
    const want = !motionOk;
    try { localStorage.setItem("edu.air.motion", want ? "on" : "off"); } catch (e) {}
    applyMotion();
  });

  if (matchReduce) {
    matchReduce.addEventListener("change", () => applyMotion());
  }

  /* ---------------- language switcher ---------------- */
  const select = $("#lang-select");
  const currentTag = $("#lang-current");
  const TAGS = { en: "EN", fr: "FR", ar: "AR", nl: "NL" };

  function syncLang() {
    const l = i18n.current();
    select.value = l;
    currentTag.textContent = TAGS[l] || "EN";
  }

  select.addEventListener("change", () => {
    i18n.setLang(select.value);
    i18n.apply();
  });

  const reRenderDynamic = () => {
    updateToolbar();
    renderHud();
    renderQuizDoor();
    syncLang();
    applyMotion();
    syncFocusUI();
    drawScene();
  };

  window.addEventListener("edulangchange", reRenderDynamic);

  /* ---------------- install prompt ---------------- */
  let deferredInstall = null;
  const installBtn = $("#install-btn");
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredInstall = e;
    installBtn.style.display = "inline";
  });
  installBtn.addEventListener("click", async () => {
    if (!deferredInstall) { installBtn.style.textDecoration = "line-through"; return; }
    deferredInstall.prompt();
    await deferredInstall.userChoice;
    deferredInstall = null;
    installBtn.style.display = "none";
  });
  window.addEventListener("appinstalled", () => {
    deferredInstall = null;
    installBtn.style.display = "none";
  });

  /* ---------------- service worker ---------------- */
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("sw.js").catch(() => {});
    });
  }

  /* ---------------- init ---------------- */
  function boot() {
    i18n.init();
    syncLang();
    renderHud();
    updateToolbar();
    renderQuizDoor();
    applyMotion();
    syncFocusUI();
    drawScene();
    H.hint.textContent = t("demo.hintMove");
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();