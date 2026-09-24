/* ============================================================
   EDU-AIR SMART SURFACE — Main Application Logic
   ============================================================ */

(() => {
  "use strict";

  // --- Utility Functions ---
  const $ = (s, c) => (c || document).querySelector(s);
  const $$ = (s, c) => Array.prototype.slice.call((c || document).querySelectorAll(s));

  // --- Clock Updater ---
  function updateClock() {
    const el = $("#app-clock");
    if (!el) return;
    const now = new Date();
    const hrs = String(now.getHours()).padStart(2, "0");
    const mins = String(now.getMinutes()).padStart(2, "0");
    const secs = String(now.getSeconds()).padStart(2, "0");
    el.textContent = `${hrs}:${mins}:${secs}`;
  }
  setInterval(updateClock, 1000);
  updateClock();

  // --- Internationalization (i18n) Delegate ---
  if (window.EDU_AIR_I18N) {
    window.EDU_AIR_I18N.init();
  }

  // --- Status Pills Toggles ---
  $$(".status-pill").forEach((pill) => {
    pill.addEventListener("click", () => {
      pill.classList.toggle("active");
    });
  });

  // --- Light / Dark Theme Switcher ---
  const btnThemeToggle = $("#btn-toggle-theme");
  let savedTheme = (function() {
    try { return localStorage.getItem("edu_air_theme") || "dark"; }
    catch(e) { return "dark"; }
  })();

  function applyThemeMode(mode) {
    document.documentElement.setAttribute("data-theme", mode);
    if (btnThemeToggle) {
      btnThemeToggle.textContent = (mode === "light") ? "🌙" : "☀️";
      btnThemeToggle.title = (mode === "light") ? "Passer au thème Sombre" : "Passer au thème Clair";
    }
    try { localStorage.setItem("edu_air_theme", mode); } catch(e) {}
  }

  if (btnThemeToggle) {
    btnThemeToggle.addEventListener("click", () => {
      savedTheme = (savedTheme === "dark") ? "light" : "dark";
      applyThemeMode(savedTheme);
    });
  }
  applyThemeMode(savedTheme);

  // --- Sidebar & Module View Router ---
  const sidebarItems = $$(".sidebar-item");
  const moduleViews = $$(".module-view");

  sidebarItems.forEach((item) => {
    item.addEventListener("click", () => {
      const targetId = item.getAttribute("data-target-view");
      if (!targetId) return;

      sidebarItems.forEach((i) => i.classList.remove("active"));
      item.classList.add("active");

      moduleViews.forEach((view) => {
        if (view.id === targetId) {
          view.classList.add("active-view");
        } else {
          view.classList.remove("active-view");
        }
      });
    });
  });

  // ============================================================
  // MODULE 9: PRÉSENTATION AIR — SLIDE ENGINE
  // ============================================================

  let gslidesEmbedUrl = "https://docs.google.com/presentation/d/e/2PACX-1vR3S6zC0x-zN_X8z3/embed?start=false&loop=false&delayms=3000";

  function createGSlidesContent(embedUrl) {
    return `
      <div style="width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative;">
        <iframe src="${embedUrl}" frameborder="0" width="100%" height="100%" allowfullscreen="true" mozallowfullscreen="true" webkitallowfullscreen="true" style="border-radius: 12px; border: none; background: #fff; width: 100%; height: 100%;"></iframe>
      </div>
    `;
  }

  const decks = {
    pythagore: [
      {
        title: "Maths 4ème : Théorème de Pythagore",
        subtitle: "Introduction à la géométrie dans le triangle rectangle",
        content: `
          <div style="text-align: center;">
            <h1 style="font-size: 2.2rem; color: #00f2fe; margin-bottom: 1rem;">📐 Théorème de Pythagore</h1>
            <p style="font-size: 1.2rem; color: #e8effc;">Séquence Pédagogique — Cycle 4 (4ème / 3ème)</p>
            <div style="margin-top: 2rem; padding: 1.2rem; background: rgba(0,242,254,0.1); border-radius: 12px; border: 1px solid rgba(0,242,254,0.3); display: inline-block;">
              ✋ Utilisez vos gestes aériens ou les boutons ci-dessous pour contrôler le diaporama
            </div>
          </div>
        `
      },
      {
        title: "Slide 2 : Énoncé & Formule Fondamentale",
        subtitle: "Relation entre l'hypoténuse et les côtés de l'angle droit",
        content: `
          <div style="display: flex; gap: 2rem; align-items: center; justify-content: center; width: 100%;">
            <!-- Geometric Triangle SVG -->
            <svg width="280" height="220" viewBox="0 0 280 220" style="filter: drop-shadow(0 0 12px rgba(0,242,254,0.4));">
              <polygon points="40,180 240,180 40,40" fill="rgba(0,242,254,0.15)" stroke="#00f2fe" stroke-width="4" />
              <!-- Right angle symbol -->
              <polyline points="40,160 60,160 60,180" fill="none" stroke="#ffb84d" stroke-width="3" />
              <!-- Labels -->
              <text x="30" y="200" fill="#fff" font-weight="bold" font-size="18">A</text>
              <text x="245" y="200" fill="#fff" font-weight="bold" font-size="18">B</text>
              <text x="30" y="30" fill="#fff" font-weight="bold" font-size="18">C</text>
              <text x="140" y="205" fill="#3ddc97" font-weight="bold" font-size="16">a = 4 cm</text>
              <text x="10" y="110" fill="#3ddc97" font-weight="bold" font-size="16">b = 3 cm</text>
              <text x="150" y="100" fill="#00f2fe" font-weight="bold" font-size="18">c = 5 cm (Hypoténuse)</text>
            </svg>
            
            <div style="text-align: left; background: rgba(10,20,38,0.9); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(0,242,254,0.3);">
              <h3 style="color: #00f2fe; margin-bottom: 0.8rem;">Formule de Pythagore :</h3>
              <div style="font-size: 1.8rem; font-weight: 800; color: #ffb84d; font-family: monospace; margin-bottom: 1rem;">
                BC² = AB² + AC²
              </div>
              <p style="color: #e8effc; font-size: 1rem;">Calcul numérique :</p>
              <p style="color: #9fb0cf; font-family: monospace; font-size: 1.1rem;">c² = 4² + 3² = 16 + 9 = 25<br>c = √25 = <strong style="color:#00f2fe;">5 cm</strong></p>
            </div>
          </div>
        `
      },
      {
        title: "Slide 3 : Application Pratique en Classe",
        subtitle: "Calculer la hauteur d'une échelle posée contre un mur",
        content: `
          <div style="text-align: center; max-width: 600px;">
            <h3 style="color: #00f2fe; margin-bottom: 1rem;">Problème Échelle & Mur</h3>
            <p style="font-size: 1.1rem; color: #e8effc; line-height: 1.6;">
              Une échelle de <strong>5 mètres</strong> s'appuie contre un mur vertical. Son pied est situé à <strong>3 mètres</strong> du mur.
            </p>
            <div style="margin-top: 1.5rem; padding: 1.2rem; background: rgba(61,220,151,0.15); border: 1px solid #3ddc97; border-radius: 12px; font-size: 1.2rem; font-weight: bold; color: #3ddc97;">
              Hauteur atteinte sur le mur : h = √(5² - 3²) = 4 mètres
            </div>
          </div>
        `
      },
      {
        title: "Slide 4 : Quiz Instantané Éléves",
        subtitle: "Vérification rapide de la compréhension",
        content: `
          <div style="text-align: center; max-width: 600px;">
            <h3 style="color: #ffb84d; margin-bottom: 1rem;">Question flash :</h3>
            <p style="font-size: 1.2rem; color: #fff;">Si les deux côtés de l'angle droit mesurent 6 cm et 8 cm, quelle est la longueur de l'hypoténuse ?</p>
            <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 1.5rem;">
              <button class="btn-app btn-app-ghost" style="font-size: 1.1rem; padding: 0.8rem 1.5rem;">A) 9 cm</button>
              <button class="btn-app btn-app-primary" style="font-size: 1.1rem; padding: 0.8rem 1.5rem;">B) 10 cm ✓</button>
              <button class="btn-app btn-app-ghost" style="font-size: 1.1rem; padding: 0.8rem 1.5rem;">C) 14 cm</button>
            </div>
          </div>
        `
      },
      {
        title: "Slide 5 : Synthèse & Devoirs",
        subtitle: "Résumé du cours et exercices d'entraînement",
        content: `
          <div style="text-align: left; max-width: 550px;">
            <h3 style="color: #00f2fe; margin-bottom: 1rem;">À retenir pour le prochain cours :</h3>
            <ul style="line-height: 2; color: #e8effc; font-size: 1.05rem;">
              <li>✓ Le théorème s'applique <strong>uniquement</strong> dans un triangle rectangle.</li>
              <li>✓ L'hypoténuse est toujours le côté le plus long opposé à l'angle droit.</li>
              <li>✓ Exercices N° 12, 14 et 15 page 148 du manuel.</li>
            </ul>
          </div>
        `
      }
    ],
    heart: [
      {
        title: "SVT : Anatomie du Cœur",
        subtitle: "Système Cardiovasculaire — Collège",
        content: `<h1 style="color:#00f2fe;">❤️ Anatomie du Cœur Humain</h1><p>Ventricules, oreillettes et circulation sanguine.</p>`
      },
      {
        title: "Circulation Sanguine",
        subtitle: "Grande et Petite Circulation",
        content: `<h2 style="color:#ff5d5d;">🫀 Circulation de l'Oxygène</h2><p>Trajet du sang rouge (oxygéné) et du sang bleu (désoxygéné).</p>`
      }
    ],
    physics: [
      {
        title: "Physique : Circuit Électrique",
        subtitle: "Loi d'Ohm U = R x I",
        content: `<h1 style="color:#00f2fe;">⚡ Circuits Électriques & Tension</h1><p>Étude des composants en série et en dérivation.</p>`
      }
    ],
    history: [
      {
        title: "Histoire : La Révolution Française",
        subtitle: "Année 1789 — Prise de la Bastille",
        content: `<h1 style="color:#ffb84d;">🏛️ La Révolution Française de 1789</h1><p>De la réunion des États Généraux à la Déclaration des Droits de l'Homme.</p>`
      }
    ],
    gslides: [
      {
        title: "Google Slides en direct",
        content: createGSlidesContent(gslidesEmbedUrl)
      }
    ]
  };

  let currentDeckKey = "pythagore";
  let currentSlideIndex = 0;

  function renderCurrentSlide() {
    const deck = decks[currentDeckKey] || decks["pythagore"];
    if (currentSlideIndex >= deck.length) currentSlideIndex = deck.length - 1;
    if (currentSlideIndex < 0) currentSlideIndex = 0;

    const slide = deck[currentSlideIndex];
    const stage = $("#slide-content-render");
    const counter = $("#slide-counter-display");

    if (stage) {
      stage.innerHTML = slide.content;
    }
    if (counter) {
      counter.textContent = `${currentSlideIndex + 1} / ${deck.length}`;
    }
  }

  // Deck selector
  const deckSelect = $("#presentation-deck-select");
  if (deckSelect) {
    deckSelect.addEventListener("change", (e) => {
      currentDeckKey = e.target.value;
      currentSlideIndex = 0;
      renderCurrentSlide();
    });
  }

  // Prev / Next Slide Buttons
  const btnPrev = $("#btn-slide-prev");
  const btnNext = $("#btn-slide-next");

  if (btnPrev) {
    btnPrev.addEventListener("click", () => {
      currentSlideIndex--;
      renderCurrentSlide();
    });
  }
  if (btnNext) {
    btnNext.addEventListener("click", () => {
      currentSlideIndex++;
      renderCurrentSlide();
    });
  }

  // Keyboard navigation Left / Right Arrow
  window.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") {
      currentSlideIndex--;
      renderCurrentSlide();
    } else if (e.key === "ArrowRight") {
      currentSlideIndex++;
      renderCurrentSlide();
    }
  });

  renderCurrentSlide();

  // ============================================================
  // ANNOTATION CANVAS ON PRESENTATION
  // ============================================================

  const drawCanvas = $("#presentation-draw-canvas");
  if (drawCanvas) {
    const ctx = drawCanvas.getContext("2d");
    let isDrawing = false;
    let activeTool = "pen";
    let activeColor = "#00f2fe";
    let historyStack = [];

    // Tool chips
    $$(".tool-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        $$(".tool-chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        if (chip.id === "tool-pen") activeTool = "pen";
        if (chip.id === "tool-highlighter") activeTool = "highlighter";
        if (chip.id === "tool-eraser") activeTool = "eraser";
      });
    });

    // Color dots
    $$(".color-dot").forEach((dot) => {
      dot.addEventListener("click", () => {
        $$(".color-dot").forEach((d) => d.classList.remove("active"));
        dot.classList.add("active");
        activeColor = dot.getAttribute("data-color");
      });
    });

    const customColor = $("#custom-color-picker");
    if (customColor) {
      customColor.addEventListener("input", (e) => {
        activeColor = e.target.value;
      });
    }

    function saveState() {
      historyStack.push(ctx.getImageData(0, 0, drawCanvas.width, drawCanvas.height));
      if (historyStack.length > 20) historyStack.shift();
    }

    function getCanvasCoords(e) {
      const rect = drawCanvas.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      return {
        x: (clientX - rect.left) * (drawCanvas.width / rect.width),
        y: (clientY - rect.top) * (drawCanvas.height / rect.height)
      };
    }

    drawCanvas.addEventListener("mousedown", (e) => {
      saveState();
      isDrawing = true;
      const pos = getCanvasCoords(e);
      ctx.beginPath();
      ctx.moveTo(pos.x, pos.y);
    });

    drawCanvas.addEventListener("mousemove", (e) => {
      if (!isDrawing) return;
      const pos = getCanvasCoords(e);

      if (activeTool === "pen") {
        ctx.strokeStyle = activeColor;
        ctx.lineWidth = 4;
        ctx.lineCap = "round";
        ctx.globalAlpha = 1.0;
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
      } else if (activeTool === "highlighter") {
        ctx.strokeStyle = activeColor;
        ctx.lineWidth = 18;
        ctx.lineCap = "square";
        ctx.globalAlpha = 0.35;
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
      } else if (activeTool === "eraser") {
        ctx.clearRect(pos.x - 15, pos.y - 15, 30, 30);
      }
    });

    window.addEventListener("mouseup", () => {
      isDrawing = false;
    });

    // Undo & Clear
    const btnUndo = $("#btn-draw-undo");
    const btnClear = $("#btn-draw-clear");

    if (btnUndo) {
      btnUndo.addEventListener("click", () => {
        if (historyStack.length > 0) {
          const state = historyStack.pop();
          ctx.putImageData(state, 0, 0);
        } else {
          ctx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
        }
      });
    }

    if (btnClear) {
      btnClear.addEventListener("click", () => {
        saveState();
        ctx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
      });
    }
  }

  // ============================================================
  // SPOTLIGHT & LOUPE ZOOM OVERLAYS
  // ============================================================

  const canvasBox = $("#slide-canvas-container");
  const spotlightMask = $("#spotlight-mask-layer");
  const loupeLens = $("#loupe-lens-layer");
  const btnSpotlight = $("#btn-toggle-spotlight");
  const btnLoupe = $("#btn-toggle-loupe");

  let spotlightActive = false;
  let loupeActive = false;

  if (btnSpotlight) {
    btnSpotlight.addEventListener("click", () => {
      spotlightActive = !spotlightActive;
      btnSpotlight.classList.toggle("btn-app-primary", spotlightActive);
      btnSpotlight.classList.toggle("btn-app-ghost", !spotlightActive);
      if (spotlightMask) spotlightMask.classList.toggle("active", spotlightActive);
    });
  }

  if (btnLoupe) {
    btnLoupe.addEventListener("click", () => {
      loupeActive = !loupeActive;
      btnLoupe.classList.toggle("btn-app-primary", loupeActive);
      btnLoupe.classList.toggle("btn-app-ghost", !loupeActive);
      if (loupeLens) loupeLens.classList.toggle("active", loupeActive);
    });
  }

  if (canvasBox) {
    canvasBox.addEventListener("mousemove", (e) => {
      const rect = canvasBox.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      if (spotlightActive && spotlightMask) {
        spotlightMask.style.setProperty("--sp-x", `${(x / rect.width) * 100}%`);
        spotlightMask.style.setProperty("--sp-y", `${(y / rect.height) * 100}%`);
      }

      if (loupeActive && loupeLens) {
        loupeLens.style.left = `${x - 90}px`;
        loupeLens.style.top = `${y - 90}px`;
      }
    });
  }

  // ============================================================
  // MINUTEUR DE CLASSE TNI (TIMER)
  // ============================================================

  let timerSeconds = 180;
  let timerInterval = null;
  let timerRunning = false;

  const timerDigits = $("#class-timer-digits");
  const btnTimerStart = $("#btn-timer-start-pause");
  const btnTimerReset = $("#btn-timer-reset");

  function formatTime(s) {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }

  function updateTimerDisplay() {
    if (timerDigits) {
      timerDigits.textContent = formatTime(timerSeconds);
    }
  }

  $$(".timer-preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      $$(".timer-preset-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const val = parseInt(btn.getAttribute("data-preset"), 10);
      timerSeconds = val;
      if (timerRunning) clearInterval(timerInterval);
      timerRunning = false;
      if (btnTimerStart) btnTimerStart.textContent = "▶ DÉMARRER";
      updateTimerDisplay();
    });
  });

  if (btnTimerStart) {
    btnTimerStart.addEventListener("click", () => {
      if (!timerRunning) {
        timerRunning = true;
        btnTimerStart.textContent = "⏸ PAUSE";
        timerInterval = setInterval(() => {
          if (timerSeconds > 0) {
            timerSeconds--;
            updateTimerDisplay();
          } else {
            clearInterval(timerInterval);
            timerRunning = false;
            btnTimerStart.textContent = "▶ DÉMARRER";
            alert("⏰ MINUTEUR TERMINÉ ! Temps écoulé pour l'activité.");
          }
        }, 1000);
      } else {
        timerRunning = false;
        clearInterval(timerInterval);
        btnTimerStart.textContent = "▶ DÉMARRER";
      }
    });
  }

  if (btnTimerReset) {
    btnTimerReset.addEventListener("click", () => {
      if (timerRunning) clearInterval(timerInterval);
      timerRunning = false;
      if (btnTimerStart) btnTimerStart.textContent = "▶ DÉMARRER";
      timerSeconds = 180;
      updateTimerDisplay();
    });
  }

  updateTimerDisplay();

  // ============================================================
  // OTHER MODULE INTERACTIVITIES
  // ============================================================

  // --- Module 7: Labo Air Electric Circuit Simulator ---
  const sliderU = $("#slider-u");
  const sliderR = $("#slider-r");
  const valU = $("#val-u");
  const valR = $("#val-r");
  const valI = $("#val-i");
  const bulb = $("#bulb-glow");

  function updateCircuit() {
    if (!sliderU || !sliderR) return;
    const u = parseFloat(sliderU.value);
    const r = parseFloat(sliderR.value);
    const i = (u / r).toFixed(2);

    if (valU) valU.textContent = `${u}V`;
    if (valR) valR.textContent = `${r}Ω`;
    if (valI) valI.textContent = `${i} A`;

    if (bulb) {
      const brightness = Math.min(1.0, u / 18);
      bulb.style.opacity = brightness;
      bulb.style.boxShadow = `0 0 ${brightness * 40}px #ffea00`;
    }
  }

  if (sliderU) sliderU.addEventListener("input", updateCircuit);
  if (sliderR) sliderR.addEventListener("input", updateCircuit);

  // --- Module 8: Quiz Air Polling Simulator ---
  const btnQuizSim = $("#btn-quiz-simulate");
  if (btnQuizSim) {
    btnQuizSim.addEventListener("click", () => {
      alert("📊 Vote de la classe mis à jour : +1 réponse enregistrée pour Option A !");
    });
  }

  // --- Module 10: Prof IA Chatbot ---
  const chatInput = $("#ai-chat-input");
  const chatSend = $("#btn-ai-chat-send");
  const chatMessages = $("#ai-chat-messages");

  if (chatSend && chatInput && chatMessages) {
    chatSend.addEventListener("click", () => {
      const text = chatInput.value.trim();
      if (!text) return;

      // Add User Message
      const userMsg = document.createElement("div");
      userMsg.style.cssText = "background: rgba(148,180,255,0.1); border: 1px solid rgba(126,195,255,0.2); padding: 0.8rem; border-radius: 12px; max-width: 80%; align-self: flex-end;";
      userMsg.innerHTML = `<strong>Vous :</strong> ${text}`;
      chatMessages.appendChild(userMsg);
      chatInput.value = "";
      chatMessages.scrollTop = chatMessages.scrollHeight;

      // Simulate AI Answer
      setTimeout(() => {
        const aiMsg = document.createElement("div");
        aiMsg.style.cssText = "background: rgba(0,242,254,0.1); border: 1px solid rgba(0,242,254,0.3); padding: 0.8rem; border-radius: 12px; max-width: 80%; align-self: flex-start;";
        aiMsg.innerHTML = `<strong>🤖 Prof IA :</strong> Voici une suggestion de séquence pour votre question sur "${text}" :<br>1. Rappel de la formule.<br>2. Exercice guidé pas à pas.<br>3. Évaluation par quiz instantané.`;
        chatMessages.appendChild(aiMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }, 700);
    });
  }

  // --- Modals Toggle Logic ---
  $$("[data-close-modal]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-close-modal");
      const modal = $(`#${targetId}`);
      if (modal) modal.classList.remove("active");
    });
  });

  const btnImportPptx = $("#btn-modal-import-pptx");
  if (btnImportPptx) {
    btnImportPptx.addEventListener("click", () => {
      const m = $("#modal-import-pptx");
      if (m) m.classList.add("active");
    });
  }

  const btnGSlides = $("#btn-modal-gslides");
  if (btnGSlides) {
    btnGSlides.addEventListener("click", () => {
      const m = $("#modal-gslides");
      if (m) m.classList.add("active");
    });
  }

  const btnAddSlide = $("#btn-modal-add-slide");
  if (btnAddSlide) {
    btnAddSlide.addEventListener("click", () => {
      const m = $("#modal-add-slide");
      if (m) m.classList.add("active");
    });
  }

  // Helper to parse Google Slides URL
  function convertToGSlidesEmbedUrl(rawUrl) {
    if (!rawUrl || !rawUrl.trim()) {
      return "https://docs.google.com/presentation/d/e/2PACX-1vR3S6zC0x-zN_X8z3/embed?start=false&loop=false&delayms=3000";
    }
    let url = rawUrl.trim();
    const match = url.match(/\/d\/([a-zA-Z0-9_-]+)/);
    if (match && match[1]) {
      const id = match[1];
      return `https://docs.google.com/presentation/d/${id}/embed?start=false&loop=false&delayms=3000`;
    }
    return url;
  }

  const btnConfirmGSlides = $("#btn-confirm-gslides");
  if (btnConfirmGSlides) {
    btnConfirmGSlides.addEventListener("click", () => {
      const inputUrl = $("#input-gslides-url");
      const rawUrl = inputUrl ? inputUrl.value : "";
      gslidesEmbedUrl = convertToGSlidesEmbedUrl(rawUrl);

      decks.gslides = [
        {
          title: "Google Slides en direct",
          content: createGSlidesContent(gslidesEmbedUrl)
        }
      ];

      currentDeckKey = "gslides";
      currentSlideIndex = 0;

      if (deckSelect) {
        deckSelect.value = "gslides";
      }
      renderCurrentSlide();

      const m = $("#modal-gslides");
      if (m) m.classList.remove("active");
      alert("✅ Présentation Google Slides chargée avec succès !");
    });
  }

  const btnConfirmImport = $("#btn-confirm-import");
  if (btnConfirmImport) {
    btnConfirmImport.addEventListener("click", () => {
      const fileInput = $("#input-file-pptx");
      const fileName = (fileInput && fileInput.files && fileInput.files[0]) ? fileInput.files[0].name : "Présentation_Importée.pptx";

      decks.imported = [
        {
          title: `${fileName} — Page 1`,
          subtitle: "Document importé en classe",
          content: `
            <div style="text-align: center; max-width: 600px;">
              <h2 style="color: #00f2fe; margin-bottom: 1rem;">📁 ${fileName}</h2>
              <p style="font-size: 1.1rem; color: #e8effc;">Document PPTX / PDF importé et rendu dans EDU-AIR Smart Surface.</p>
              <div style="margin-top: 1.5rem; padding: 1.5rem; background: rgba(0,242,254,0.1); border-radius: 12px; border: 1px solid rgba(0,242,254,0.3);">
                ✍️ Vous pouvez maintenant annoter ce document avec le stylo aérien ou la souris.
              </div>
            </div>
          `
        },
        {
          title: `${fileName} — Page 2`,
          subtitle: "Définitions et exercices",
          content: `
            <div style="text-align: center; max-width: 600px;">
              <h3 style="color: #3ddc97; margin-bottom: 1rem;">Section 2 : Applications & Schémas</h3>
              <p style="color: #e8effc;">Analyse en direct avec la classe.</p>
            </div>
          `
        }
      ];

      if (deckSelect && !deckSelect.querySelector("option[value='imported']")) {
        const opt = document.createElement("option");
        opt.value = "imported";
        opt.textContent = `📁 ${fileName} (2 slides)`;
        deckSelect.appendChild(opt);
      }

      currentDeckKey = "imported";
      currentSlideIndex = 0;
      if (deckSelect) deckSelect.value = "imported";
      renderCurrentSlide();

      const m = $("#modal-import-pptx");
      if (m) m.classList.remove("active");
      alert(`✅ Fichier ${fileName} importé avec succès !`);
    });
  }

  const btnConfirmAddSlide = $("#btn-confirm-add-slide");
  if (btnConfirmAddSlide) {
    btnConfirmAddSlide.addEventListener("click", () => {
      const inputTitle = $("#input-new-slide-title");
      const titleText = (inputTitle && inputTitle.value.trim()) ? inputTitle.value.trim() : "Nouvelle Slide";

      const currentDeck = decks[currentDeckKey] || decks["pythagore"];
      const newSlideNum = currentDeck.length + 1;

      currentDeck.push({
        title: `Slide ${newSlideNum} : ${titleText}`,
        subtitle: "Slide ajoutée au cours",
        content: `
          <div style="text-align: center; max-width: 600px;">
            <h2 style="color: #00f2fe; margin-bottom: 1rem;">✨ ${titleText}</h2>
            <p style="font-size: 1.1rem; color: #e8effc;">Espace de cours vierge pour annotations et prise de notes.</p>
          </div>
        `
      });

      currentSlideIndex = currentDeck.length - 1;
      renderCurrentSlide();

      if (inputTitle) inputTitle.value = "";
      const m = $("#modal-add-slide");
      if (m) m.classList.remove("active");
      alert(`✅ Nouvelle slide "${titleText}" ajoutée au diaporama !`);
    });
  }

  // --- PiP WebCam Video Initialization ---
  const pipVideo = $("#pip-webcam-video");
  if (pipVideo && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then((stream) => {
        pipVideo.srcObject = stream;
      })
      .catch((err) => {
        console.log("Webcam notice:", err.message);
      });
  }

  // ============================================================
  // MODULE 4: DESSIN AIR CANVAS ENGINE & GABARITS
  // ============================================================

  const drawCanvas = $("#air-draw-canvas");
  if (drawCanvas) {
    const ctx = drawCanvas.getContext("2d");
    let isDrawing = false;
    let currentColor = "#00f2fe";
    let currentLineWidth = 4;
    let isEraser = false;

    // Color selector setup for Air Draw
    const drawView = $("#view-draw");
    if (drawView) {
      const colorDots = drawView.querySelectorAll(".color-dot");
      colorDots.forEach((dot) => {
        dot.addEventListener("click", () => {
          colorDots.forEach((d) => d.classList.remove("active"));
          dot.classList.add("active");
          currentColor = dot.getAttribute("data-color") || "#00f2fe";
          isEraser = false;
          if ($("#draw-tool-pen")) $("#draw-tool-pen").classList.add("active");
          if ($("#draw-tool-eraser")) $("#draw-tool-eraser").classList.remove("active");
        });
      });
    }

    // Canvas drawing handlers
    function startDraw(e) {
      isDrawing = true;
      const rect = drawCanvas.getBoundingClientRect();
      const x = (e.clientX || (e.touches && e.touches[0].clientX)) - rect.left;
      const y = (e.clientY || (e.touches && e.touches[0].clientY)) - rect.top;
      ctx.beginPath();
      ctx.moveTo(x, y);
    }

    function moveDraw(e) {
      if (!isDrawing) return;
      const rect = drawCanvas.getBoundingClientRect();
      const x = (e.clientX || (e.touches && e.touches[0].clientX)) - rect.left;
      const y = (e.clientY || (e.touches && e.touches[0].clientY)) - rect.top;
      
      ctx.lineWidth = isEraser ? 24 : currentLineWidth;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.strokeStyle = isEraser ? "#060912" : currentColor;
      ctx.lineTo(x, y);
      ctx.stroke();
    }

    function stopDraw() {
      isDrawing = false;
    }

    drawCanvas.addEventListener("mousedown", startDraw);
    drawCanvas.addEventListener("mousemove", moveDraw);
    drawCanvas.addEventListener("mouseup", stopDraw);
    drawCanvas.addEventListener("mouseleave", stopDraw);

    drawCanvas.addEventListener("touchstart", (e) => { e.preventDefault(); startDraw(e); }, { passive: false });
    drawCanvas.addEventListener("touchmove", (e) => { e.preventDefault(); moveDraw(e); }, { passive: false });
    drawCanvas.addEventListener("touchend", stopDraw);

    // Tools & Colors
    const btnPen = $("#draw-tool-pen");
    const btnEraser = $("#draw-tool-eraser");
    if (btnPen && btnEraser) {
      btnPen.addEventListener("click", () => {
        isEraser = false;
        btnPen.classList.add("active");
        btnEraser.classList.remove("active");
      });
      btnEraser.addEventListener("click", () => {
        isEraser = true;
        btnEraser.classList.add("active");
        btnPen.classList.remove("active");
      });
    }

    const btnClear = $("#btn-airdraw-clear");
    if (btnClear) {
      btnClear.addEventListener("click", () => {
        ctx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
        const box = $("#ocr-result-box");
        if (box) box.style.display = "none";
      });
    }

    // Stamps: Timeline (Frise)
    const btnFrise = $("#btn-stamp-frise");
    if (btnFrise) {
      btnFrise.addEventListener("click", () => {
        ctx.strokeStyle = "#00f2fe";
        ctx.lineWidth = 3;
        ctx.beginPath();
        // Axis line
        ctx.moveTo(80, 210);
        ctx.lineTo(950, 210);
        // Arrow head
        ctx.lineTo(930, 195);
        ctx.moveTo(950, 210);
        ctx.lineTo(930, 225);
        // Ticks & Dates
        const ticks = [150, 350, 550, 750];
        const labels = ["1789", "1848", "1914", "1945"];
        ticks.forEach((tx, idx) => {
          ctx.moveTo(tx, 195);
          ctx.lineTo(tx, 225);
          ctx.font = "bold 14px Segoe UI, sans-serif";
          ctx.fillStyle = "#ffb84d";
          ctx.fillText(labels[idx], tx - 15, 250);
        });
        ctx.stroke();
        alert("📐 Gabarit Frise Chronologique vectorisé sur le tableau !");
      });
    }

    // Stamps: Table Grid
    const btnTable = $("#btn-stamp-table");
    if (btnTable) {
      btnTable.addEventListener("click", () => {
        ctx.strokeStyle = "#3ddc97";
        ctx.lineWidth = 2;
        ctx.strokeRect(100, 60, 800, 280);
        // Horizontal divider
        ctx.beginPath();
        ctx.moveTo(100, 120);
        ctx.lineTo(900, 120);
        // Vertical divider
        ctx.moveTo(500, 60);
        ctx.lineTo(500, 340);
        ctx.stroke();

        ctx.font = "bold 16px Segoe UI, sans-serif";
        ctx.fillStyle = "#3ddc97";
        ctx.fillText("Colonne A (Variable 1)", 140, 95);
        ctx.fillText("Colonne B (Variable 2)", 540, 95);
        alert("📊 Gabarit Tableau à double entrée inséré !");
      });
    }

    // OCR / Math Recognition Simulator
    const btnOcr = $("#btn-ocr-convert");
    if (btnOcr) {
      btnOcr.addEventListener("click", () => {
        const box = $("#ocr-result-box");
        const txt = $("#ocr-text-render");
        if (box && txt) {
          const samples = [
            "BC² = AB² + AC²  ➔  LaTeX: \\sqrt{AB^2 + AC^2}",
            "f(x) = \\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}",
            "E = mc²  ➔  Énergie & Masse Relativiste",
            "CO₂ + H₂O ➔ H₂CO₃  (Acide Carbonique)"
          ];
          const chosen = samples[Math.floor(Math.random() * samples.length)];
          txt.textContent = chosen;
          box.style.display = "block";
          alert("🔤 Tracé manuscrit analysé et converti en texte LaTeX !");
        }
      });
    }
  }

  // ============================================================
  // MODULE ENRICHMENTS: TNI / TBI CLASSROOM INTERACTORS
  // ============================================================

  // 1. Role Switcher
  const roleSelect = $("#user-role-select");
  if (roleSelect) {
    roleSelect.addEventListener("change", (e) => {
      const role = e.target.value;
      const roleLabels = {
        teacher: "Enseignant (Contrôle total & Calibrations)",
        student: "Élève (Interactions guidées)",
        tech: "Technicien / Admin (Maintenance parc TNI)"
      };
      alert(`👤 Profil basculé vers : ${roleLabels[role] || role}`);
    });
  }

  // 2. Export TNI Modal
  const btnExportTni = $("#btn-modal-export-tni");
  if (btnExportTni) {
    btnExportTni.addEventListener("click", () => {
      const m = $("#modal-export-tni");
      if (m) m.classList.add("active");
    });
  }

  // Export Buttons Simulators
  ["btn-export-notebook", "btn-export-flipchart", "btn-export-iwb", "btn-export-scorm"].forEach((id) => {
    const btn = $(`#${id}`);
    if (btn) {
      btn.addEventListener("click", () => {
        const fmt = id.replace("btn-export-", "").toUpperCase();
        alert(`📥 Génération du fichier export TNI .${fmt.toLowerCase()} en cours...\nTéléchargement prêt pour archivage établissement & ENT !`);
        const m = $("#modal-export-tni");
        if (m) m.classList.remove("active");
      });
    }
  });

  // 3. Quiz QR Modal
  const btnQuizQr = $("#btn-quiz-qr");
  if (btnQuizQr) {
    btnQuizQr.addEventListener("click", () => {
      const m = $("#modal-quiz-qr");
      if (m) m.classList.add("active");
    });
  }

  // 4. Smart Surface Specialty Backgrounds
  const wbBgSelect = $("#wb-bg-select");
  const wbCanvas = $("#whiteboard-full-canvas");
  if (wbBgSelect && wbCanvas) {
    wbBgSelect.addEventListener("change", (e) => {
      const bg = e.target.value;
      wbCanvas.style.backgroundColor = "#08101e";
      
      if (bg === "grid") {
        wbCanvas.style.backgroundImage = "linear-gradient(rgba(0, 242, 254, 0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 242, 254, 0.15) 1px, transparent 1px)";
        wbCanvas.style.backgroundSize = "30px 30px";
      } else if (bg === "music") {
        wbCanvas.style.backgroundImage = "linear-gradient(rgba(255, 255, 255, 0.25) 2px, transparent 2px)";
        wbCanvas.style.backgroundSize = "100% 16px";
      } else if (bg === "timeline") {
        wbCanvas.style.backgroundImage = "linear-gradient(0deg, transparent 48%, rgba(255, 184, 77, 0.6) 50%, transparent 52%), linear-gradient(90deg, rgba(255, 184, 77, 0.4) 2px, transparent 2px)";
        wbCanvas.style.backgroundSize = "100% 100%, 80px 100%";
      } else if (bg === "map") {
        wbCanvas.style.backgroundImage = "radial-gradient(circle, rgba(61, 220, 151, 0.15) 2px, transparent 2px)";
        wbCanvas.style.backgroundSize = "40px 40px";
      } else {
        wbCanvas.style.backgroundImage = "none";
      }
    });
  }

  // 5. Virtual Laser Mode Toggle
  const btnLaserMode = $("#btn-pointer-laser-mode");
  let isLaserActive = false;
  if (btnLaserMode) {
    btnLaserMode.addEventListener("click", () => {
      isLaserActive = !isLaserActive;
      btnLaserMode.classList.toggle("btn-app-primary", isLaserActive);
      btnLaserMode.classList.toggle("btn-app-ghost", !isLaserActive);
      document.body.classList.toggle("laser-pointer-active", isLaserActive);
      alert(isLaserActive ? "🔦 Pointeur Laser Virtuel ACTIF (désignation sans écriture)" : "✋ Mode Pointeur standard réactivé");
    });
  }

  // 6. 3D Cutaway Mode & Snapshot
  const btn3dCoupe = $("#btn-3d-coupe");
  const view3d = $("#view-air-3d");
  if (btn3dCoupe && view3d) {
    btn3dCoupe.addEventListener("click", () => {
      view3d.classList.toggle("cut-view-active");
      const isCut = view3d.classList.contains("cut-view-active");
      btn3dCoupe.style.background = isCut ? "rgba(255, 93, 93, 0.3)" : "";
      alert(isCut ? "✂️ Mode Coupe Transversale Activé" : "◠ Vue 3D Intégrale Réactivée");
    });
  }

  const btn3dSnapshot = $("#btn-3d-snapshot");
  if (btn3dSnapshot) {
    btn3dSnapshot.addEventListener("click", () => {
      alert("📸 Capture annotée 3D exportée vers le compte-rendu de séance (PDF) !");
    });
  }

  // 7. STEM Lab Selector & Error Calculator
  const labSelect = $("#lab-sim-select");
  const labExpSlider = $("#slider-lab-exp");
  const labExpVal = $("#val-lab-exp");
  const labErrorVal = $("#val-lab-error");

  function updateLabCalc() {
    if (!labExpSlider || !labExpVal || !labErrorVal) return;
    const exp = parseFloat(labExpSlider.value);
    const theo = 6.0; // Theoretical reference
    const diffPct = Math.abs((exp - theo) / theo * 100).toFixed(1);

    labExpVal.textContent = `${exp.toFixed(1)} V`;
    labErrorVal.textContent = `${diffPct}%`;
    if (parseFloat(diffPct) < 5.0) {
      labErrorVal.style.color = "#3ddc97";
    } else {
      labErrorVal.style.color = "#ff5d5d";
    }
  }

  if (labExpSlider) {
    labExpSlider.addEventListener("input", updateLabCalc);
  }

  if (labSelect) {
    labSelect.addEventListener("change", (e) => {
      alert(`🧪 Simulation baseline chargée : ${e.target.options[e.target.selectedIndex].text}`);
    });
  }

  // 8. AI Teacher 3-Tier Differentiated Exercises
  const btnAiDiff = $("#btn-ai-diff-ex");
  if (btnAiDiff && chatMessages) {
    btnAiDiff.addEventListener("click", () => {
      const diffMsg = document.createElement("div");
      diffMsg.style.cssText = "background: rgba(139,123,255,0.15); border: 1px solid rgba(139,123,255,0.4); padding: 1rem; border-radius: 12px; margin-top: 0.5rem;";
      diffMsg.innerHTML = `
        <h4 style="color: #8b7bff; margin-bottom: 0.5rem;">✦ Exercices Différenciés (3 Niveaux de Difficulté)</h4>
        <div style="font-size: 0.9rem; line-height: 1.6;">
          <p style="color: #3ddc97;">🟢 <strong>Niveau 1 (Socle) :</strong> Calculer l'hypoténuse quand a=3 et b=4.</p>
          <p style="color: #ffb84d;">🟡 <strong>Niveau 2 (Intermédiaire) :</strong> Retrouver la hauteur d'un triangle connaissant l'hypoténuse 13 cm et le côté 5 cm.</p>
          <p style="color: #ff5d5d;">🔴 <strong>Niveau 3 (Approfondissement) :</strong> Démontrer la réciproque du théorème dans une charpente de toit.</p>
        </div>
      `;
      chatMessages.appendChild(diffMsg);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    });
  }

  // 9. TNI Timer Ambient Glow Toggle
  const classTimer = $("#class-timer");
  const slideContainer = $("#slide-canvas-container");
  if (classTimer && slideContainer) {
    let timerRunning = false;
    classTimer.addEventListener("click", () => {
      timerRunning = !timerRunning;
      slideContainer.classList.toggle("timer-active-glow", timerRunning);
    });
  }

  console.log("EDU-AIR Smart Surface App Initialized.");
})();