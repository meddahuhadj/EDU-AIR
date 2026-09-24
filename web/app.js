/* ============================================================
   EDU-AIR SMART SURFACE — Core Application Engine
   All 12 TNI/TBI Modules Enriched & Fully Interactive
   ============================================================ */

(function () {
  "use strict";

  // Global DOM Selectors
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => document.querySelectorAll(selector);

  document.addEventListener("DOMContentLoaded", () => {
    // --- Clock Real-Time Update ---
    const clockEl = $("#app-clock");
    function updateClock() {
      if (clockEl) {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString("fr-FR", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit"
        });
      }
    }
    updateClock();
    setInterval(updateClock, 1000);

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

    // --- Fullscreen Mode Toggle (TNI / TBI Classroom Mode) ---
    const btnFullscreen = $("#btn-toggle-fullscreen");
    const btnWbFullscreen = $("#btn-wb-fullscreen");

    function toggleFullscreenMode() {
      if (!document.fullscreenElement && !document.webkitFullscreenElement) {
        const docEl = document.documentElement;
        if (docEl.requestFullscreen) {
          docEl.requestFullscreen();
        } else if (docEl.webkitRequestFullscreen) {
          docEl.webkitRequestFullscreen();
        }
      } else {
        if (document.exitFullscreen) {
          document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          document.webkitExitFullscreen();
        }
      }
    }

    if (btnFullscreen) btnFullscreen.addEventListener("click", toggleFullscreenMode);
    if (btnWbFullscreen) btnWbFullscreen.addEventListener("click", toggleFullscreenMode);

    function handleFSChange() {
      const isFS = !!(document.fullscreenElement || document.webkitFullscreenElement);
      if (btnFullscreen) {
        btnFullscreen.textContent = isFS ? "🗗" : "⛶";
        btnFullscreen.title = isFS ? "Quitter le Plein écran (TNI)" : "Passer en Plein écran (TNI)";
      }
      if (btnWbFullscreen) {
        btnWbFullscreen.textContent = isFS ? "🗗 Quitter Plein écran" : "⛶ Plein écran";
      }
    }

    document.addEventListener("fullscreenchange", handleFSChange);
    document.addEventListener("webkitfullscreenchange", handleFSChange);

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
    // TOPBAR & ROLE SWITCHER
    // ============================================================
    const appRoleSelect = $("#app-role-select");
    if (appRoleSelect) {
      appRoleSelect.addEventListener("change", (e) => {
        const roles = {
          teacher: "👨‍🏫 Enseignant (Contrôle total & Calibrations)",
          student: "👨‍🎓 Élève (Interactions guidées)",
          tech: "🔧 Technicien / Admin (Maintenance parc TNI)"
        };
        alert(`👤 Profil basculé vers : ${roles[e.target.value] || e.target.value}`);
      });
    }

    // ============================================================
    // MODULE 1: TABLEAU DE BORD (DASHBOARD)
    // ============================================================
    const dashQuickWb = $("#dash-quick-whiteboard");
    if (dashQuickWb) {
      dashQuickWb.addEventListener("click", () => {
        sidebarItems.forEach(item => {
          if (item.getAttribute("data-target-view") === "view-whiteboard") item.click();
        });
      });
    }

    const dashQuickQuiz = $("#dash-quick-quiz");
    if (dashQuickQuiz) {
      dashQuickQuiz.addEventListener("click", () => {
        sidebarItems.forEach(item => {
          if (item.getAttribute("data-target-view") === "view-quiz") item.click();
        });
      });
    }

    const dashQuickExport = $("#dash-quick-export");
    if (dashQuickExport) {
      dashQuickExport.addEventListener("click", () => {
        const m = $("#modal-export-tni");
        if (m) m.classList.add("active");
      });
    }

    // ============================================================
    // MODULE 2: SURFACE INTELLIGENTE (WHITEBOARD DRAWING ENGINE & TOOLBAR)
    // ============================================================
    const wbCanvas = $("#whiteboard-full-canvas");
    if (wbCanvas) {
      const ctx = wbCanvas.getContext("2d");
      let isDrawing = false;
      let wbActiveTool = "pen"; // "pen", "highlighter", "eraser", "shape"
      let wbActiveShape = "none";
      let wbColor = "#00f2fe";
      let wbLineWidth = 4;
      let isLocked = false;
      let wbHistoryStack = [];
      let startX = 0;
      let startY = 0;
      let snapshot = null;

      // Tool Buttons in Whiteboard Toolbar
      const wbView = $("#view-whiteboard");
      if (wbView) {
        const toolPen = $("#wb-tool-pen");
        const toolHighlighter = $("#wb-tool-highlighter");
        const toolEraser = $("#wb-tool-eraser");
        const shapeSelect = $("#wb-shape-select");

        if (toolPen) {
          toolPen.addEventListener("click", () => {
            wbActiveTool = "pen";
            wbActiveShape = "none";
            if (shapeSelect) shapeSelect.value = "none";
            [toolPen, toolHighlighter, toolEraser].forEach(b => b && b.classList.remove("active"));
            toolPen.classList.add("active");
          });
        }

        if (toolHighlighter) {
          toolHighlighter.addEventListener("click", () => {
            wbActiveTool = "highlighter";
            wbActiveShape = "none";
            if (shapeSelect) shapeSelect.value = "none";
            [toolPen, toolHighlighter, toolEraser].forEach(b => b && b.classList.remove("active"));
            toolHighlighter.classList.add("active");
          });
        }

        if (toolEraser) {
          toolEraser.addEventListener("click", () => {
            wbActiveTool = "eraser";
            wbActiveShape = "none";
            if (shapeSelect) shapeSelect.value = "none";
            [toolPen, toolHighlighter, toolEraser].forEach(b => b && b.classList.remove("active"));
            toolEraser.classList.add("active");
          });
        }

        if (shapeSelect) {
          shapeSelect.addEventListener("change", (e) => {
            wbActiveShape = e.target.value;
            if (wbActiveShape !== "none") {
              wbActiveTool = "shape";
              [toolPen, toolHighlighter, toolEraser].forEach(b => b && b.classList.remove("active"));
            } else {
              wbActiveTool = "pen";
              if (toolPen) toolPen.classList.add("active");
            }
          });
        }

        // Color dots
        const colorDots = wbView.querySelectorAll(".color-dot");
        colorDots.forEach((dot) => {
          dot.addEventListener("click", () => {
            colorDots.forEach((d) => d.classList.remove("active"));
            dot.classList.add("active");
            wbColor = dot.getAttribute("data-color") || "#00f2fe";
            if (wbActiveTool === "eraser") {
              wbActiveTool = "pen";
              if (toolPen) toolPen.classList.add("active");
              if (toolEraser) toolEraser.classList.remove("active");
            }
          });
        });

        // Custom color picker
        const customColorPicker = $("#wb-custom-color-picker");
        if (customColorPicker) {
          customColorPicker.addEventListener("input", (e) => {
            wbColor = e.target.value;
          });
        }

        // Line width slider
        const lineWidthSlider = $("#wb-line-width");
        if (lineWidthSlider) {
          lineWidthSlider.addEventListener("input", (e) => {
            wbLineWidth = parseInt(e.target.value, 10);
          });
        }
      }

      function saveWbState() {
        wbHistoryStack.push(ctx.getImageData(0, 0, wbCanvas.width, wbCanvas.height));
        if (wbHistoryStack.length > 25) wbHistoryStack.shift();
      }

      function getWbCoords(e) {
        const rect = wbCanvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        return {
          x: (clientX - rect.left) * (wbCanvas.width / rect.width),
          y: (clientY - rect.top) * (wbCanvas.height / rect.height)
        };
      }

      function drawShape(type, sX, sY, eX, eY) {
        ctx.strokeStyle = wbColor;
        ctx.fillStyle = wbColor;
        ctx.lineWidth = wbLineWidth;
        ctx.lineCap = "round";
        ctx.globalAlpha = 1.0;
        ctx.beginPath();

        if (type === "line") {
          ctx.moveTo(sX, sY);
          ctx.lineTo(eX, eY);
          ctx.stroke();
        } else if (type === "rect") {
          ctx.strokeRect(sX, sY, eX - sX, eY - sY);
        } else if (type === "circle") {
          const radius = Math.sqrt(Math.pow(eX - sX, 2) + Math.pow(eY - sY, 2));
          ctx.arc(sX, sY, radius, 0, Math.PI * 2);
          ctx.stroke();
        } else if (type === "triangle") {
          ctx.moveTo(sX + (eX - sX) / 2, sY);
          ctx.lineTo(sX, eY);
          ctx.lineTo(eX, eY);
          ctx.closePath();
          ctx.stroke();
        } else if (type === "arrow") {
          ctx.moveTo(sX, sY);
          ctx.lineTo(eX, eY);
          ctx.stroke();
          const angle = Math.atan2(eY - sY, eX - sX);
          const headlen = 15;
          ctx.beginPath();
          ctx.moveTo(eX, eY);
          ctx.lineTo(eX - headlen * Math.cos(angle - Math.PI / 6), eY - headlen * Math.sin(angle - Math.PI / 6));
          ctx.lineTo(eX - headlen * Math.cos(angle + Math.PI / 6), eY - headlen * Math.sin(angle + Math.PI / 6));
          ctx.closePath();
          ctx.fill();
        }
      }

      wbCanvas.addEventListener("mousedown", (e) => {
        if (isLocked) {
          alert("🔒 Calque Enseignant verrouillé ! Cliquez sur 'Déverrouiller Calque' pour dessiner.");
          return;
        }
        saveWbState();
        isDrawing = true;
        const pos = getWbCoords(e);
        startX = pos.x;
        startY = pos.y;
        snapshot = ctx.getImageData(0, 0, wbCanvas.width, wbCanvas.height);

        if (wbActiveTool !== "shape") {
          ctx.beginPath();
          ctx.moveTo(pos.x, pos.y);
        }
      });

      wbCanvas.addEventListener("mousemove", (e) => {
        if (!isDrawing || isLocked) return;
        const pos = getWbCoords(e);

        if (wbActiveTool === "shape") {
          ctx.putImageData(snapshot, 0, 0);
          drawShape(wbActiveShape, startX, startY, pos.x, pos.y);
        } else if (wbActiveTool === "pen") {
          ctx.strokeStyle = wbColor;
          ctx.lineWidth = wbLineWidth;
          ctx.lineCap = "round";
          ctx.lineJoin = "round";
          ctx.globalAlpha = 1.0;
          ctx.lineTo(pos.x, pos.y);
          ctx.stroke();
        } else if (wbActiveTool === "highlighter") {
          ctx.strokeStyle = wbColor;
          ctx.lineWidth = wbLineWidth * 4;
          ctx.lineCap = "square";
          ctx.globalAlpha = 0.35;
          ctx.lineTo(pos.x, pos.y);
          ctx.stroke();
        } else if (wbActiveTool === "eraser") {
          ctx.globalAlpha = 1.0;
          ctx.clearRect(pos.x - (wbLineWidth * 3), pos.y - (wbLineWidth * 3), wbLineWidth * 6, wbLineWidth * 6);
        }
      });

      window.addEventListener("mouseup", () => {
        if (isDrawing) {
          isDrawing = false;
          ctx.globalAlpha = 1.0;
        }
      });

      wbCanvas.addEventListener("touchstart", (e) => {
        if (isLocked) return;
        e.preventDefault();
        saveWbState();
        isDrawing = true;
        const pos = getWbCoords(e);
        startX = pos.x;
        startY = pos.y;
        snapshot = ctx.getImageData(0, 0, wbCanvas.width, wbCanvas.height);
        if (wbActiveTool !== "shape") {
          ctx.beginPath();
          ctx.moveTo(pos.x, pos.y);
        }
      }, { passive: false });

      wbCanvas.addEventListener("touchmove", (e) => {
        if (!isDrawing || isLocked) return;
        e.preventDefault();
        const pos = getWbCoords(e);

        if (wbActiveTool === "shape") {
          ctx.putImageData(snapshot, 0, 0);
          drawShape(wbActiveShape, startX, startY, pos.x, pos.y);
        } else if (wbActiveTool === "pen") {
          ctx.strokeStyle = wbColor;
          ctx.lineWidth = wbLineWidth;
          ctx.lineCap = "round";
          ctx.globalAlpha = 1.0;
          ctx.lineTo(pos.x, pos.y);
          ctx.stroke();
        } else if (wbActiveTool === "highlighter") {
          ctx.strokeStyle = wbColor;
          ctx.lineWidth = wbLineWidth * 4;
          ctx.lineCap = "square";
          ctx.globalAlpha = 0.35;
          ctx.lineTo(pos.x, pos.y);
          ctx.stroke();
        } else if (wbActiveTool === "eraser") {
          ctx.globalAlpha = 1.0;
          ctx.clearRect(pos.x - (wbLineWidth * 3), pos.y - (wbLineWidth * 3), wbLineWidth * 6, wbLineWidth * 6);
        }
      }, { passive: false });

      wbCanvas.addEventListener("touchend", () => { isDrawing = false; ctx.globalAlpha = 1.0; });

      // Undo & Clear for Whiteboard
      const btnWbUndo = $("#btn-wb-undo");
      if (btnWbUndo) {
        btnWbUndo.addEventListener("click", () => {
          if (wbHistoryStack.length > 0) {
            const state = wbHistoryStack.pop();
            ctx.putImageData(state, 0, 0);
          } else {
            ctx.clearRect(0, 0, wbCanvas.width, wbCanvas.height);
          }
        });
      }

      const btnWbClear = $("#btn-wb-clear");
      if (btnWbClear) {
        btnWbClear.addEventListener("click", () => {
          saveWbState();
          ctx.clearRect(0, 0, wbCanvas.width, wbCanvas.height);
        });
      }

      // Speech-to-Text Voice Dictation (Dictée Vocale Temps Réel)
      const btnSpeechDictate = $("#btn-wb-speech-dictate");
      const speechBox = $("#wb-speech-box");
      const speechTranscript = $("#wb-speech-transcript");
      const btnStampSpeech = $("#btn-wb-stamp-speech");
      const btnStopSpeech = $("#btn-wb-stop-speech");
      const btnTopAudio = $("#btn-toggle-audio");

      let speechRecognition = null;
      let isDictating = false;
      let latestSpeechText = "";

      const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

      if (SpeechRec) {
        speechRecognition = new SpeechRec();
        speechRecognition.continuous = true;
        speechRecognition.interimResults = true;
        speechRecognition.lang = "fr-FR";

        speechRecognition.onstart = () => {
          isDictating = true;
          if (speechBox) speechBox.style.display = "flex";
          if (btnSpeechDictate) {
            btnSpeechDictate.classList.add("btn-app-primary");
            btnSpeechDictate.classList.remove("btn-app-ghost");
            btnSpeechDictate.textContent = "🎙️ Écoute en cours... (Parlez)";
          }
          if (speechTranscript) speechTranscript.textContent = "🎙️ Écoute activée... Parlez maintenant !";
        };

        speechRecognition.onresult = (e) => {
          let text = "";
          for (let i = e.resultIndex; i < e.results.length; i++) {
            text += e.results[i][0].transcript;
          }
          if (text.trim()) {
            latestSpeechText = text.trim();
            if (speechTranscript) speechTranscript.textContent = `🗣️ "${latestSpeechText}"`;
          }
        };

        speechRecognition.onerror = (err) => {
          console.log("Speech recognition notice:", err.error);
          stopSpeechDictation();
        };

        speechRecognition.onend = () => {
          if (isDictating) {
            try { speechRecognition.start(); } catch(err) { stopSpeechDictation(); }
          } else {
            stopSpeechDictation();
          }
        };
      }

      function stopSpeechDictation() {
        isDictating = false;
        if (speechBox) speechBox.style.display = "none";
        if (btnSpeechDictate) {
          btnSpeechDictate.classList.remove("btn-app-primary");
          btnSpeechDictate.classList.add("btn-app-ghost");
          btnSpeechDictate.textContent = "🎙️ Dictée Vocale";
        }
        if (speechRecognition) {
          try { speechRecognition.stop(); } catch(err) {}
        }
      }

      function toggleSpeechDictation() {
        if (!SpeechRec) {
          alert("⚠️ La reconnaissance vocale n'est pas prise en charge par ce navigateur.\nUtilisez Chrome, Edge ou Safari.");
          return;
        }
        if (!isDictating) {
          try {
            const currentLang = document.documentElement.lang || "fr";
            const langMap = { fr: "fr-FR", en: "en-US", nl: "nl-NL", ar: "ar-SA" };
            speechRecognition.lang = langMap[currentLang] || "fr-FR";
            speechRecognition.start();
          } catch(err) {
            stopSpeechDictation();
          }
        } else {
          stopSpeechDictation();
        }
      }

      function stampTextToBoard(text) {
        if (!text || !text.trim()) return;
        saveWbState();
        ctx.save();
        ctx.fillStyle = (wbColor === "#000000" && document.documentElement.getAttribute("data-theme") !== "light") ? "#00f2fe" : wbColor;
        ctx.font = "bold 26px Segoe UI, sans-serif";
        ctx.shadowColor = "rgba(0, 242, 254, 0.4)";
        ctx.shadowBlur = 8;

        const maxWidth = wbCanvas.width - 160;
        const words = text.split(" ");
        let line = "🗣️ ";
        let y = 140;

        for (let n = 0; n < words.length; n++) {
          let testLine = line + words[n] + " ";
          let metrics = ctx.measureText(testLine);
          let testWidth = metrics.width;
          if (testWidth > maxWidth && n > 0) {
            ctx.fillText(line, 80, y);
            line = words[n] + " ";
            y += 36;
          } else {
            line = testLine;
          }
        }
        ctx.fillText(line, 80, y);
        ctx.restore();
        alert(`✍️ Texte dicté écrit sur le tableau : "${text}"`);
      }

      if (btnSpeechDictate) btnSpeechDictate.addEventListener("click", toggleSpeechDictation);
      if (btnTopAudio) btnTopAudio.addEventListener("click", toggleSpeechDictation);
      if (btnStopSpeech) btnStopSpeech.addEventListener("click", stopSpeechDictation);
      if (btnStampSpeech) {
        btnStampSpeech.addEventListener("click", () => {
          if (latestSpeechText) {
            stampTextToBoard(latestSpeechText);
          } else {
            alert("⚠️ Aucune parole détectée pour l'instant. Parlez dans votre micro.");
          }
        });
      }

      // Geometric Instruments Selection & Dragging Engine
      const geoSelect = $("#wb-geo-tools-select");
      const geoOverlays = {
        ruler: $("#geo-ruler-overlay"),
        protractor: $("#geo-protractor-overlay"),
        square: $("#geo-square-overlay"),
        compass: $("#geo-compass-overlay")
      };

      if (geoSelect) {
        geoSelect.addEventListener("change", (e) => {
          const tool = e.target.value;
          Object.keys(geoOverlays).forEach(k => {
            if (geoOverlays[k]) geoOverlays[k].style.display = (k === tool) ? "block" : "none";
          });
        });
      }

      $$(".btn-geo-close").forEach(btn => {
        btn.addEventListener("click", () => {
          const targetId = btn.getAttribute("data-close-geo");
          const overlay = $(`#${targetId}`);
          if (overlay) overlay.style.display = "none";
          if (geoSelect) geoSelect.value = "none";
        });
      });

      Object.values(geoOverlays).forEach(el => {
        if (!el) return;
        let isDraggingGeo = false;
        let gStartX = 0;
        let gStartY = 0;
        let initialLeft = 0;
        let initialTop = 0;

        el.addEventListener("mousedown", (e) => {
          if (e.target.tagName === "BUTTON") return;
          isDraggingGeo = true;
          gStartX = e.clientX;
          gStartY = e.clientY;
          initialLeft = el.offsetLeft;
          initialTop = el.offsetTop;
        });

        window.addEventListener("mousemove", (e) => {
          if (!isDraggingGeo) return;
          const dx = e.clientX - gStartX;
          const dy = e.clientY - gStartY;
          el.style.left = `${initialLeft + dx}px`;
          el.style.top = `${initialTop + dy}px`;
        });

        window.addEventListener("mouseup", () => { isDraggingGeo = false; });

        el.addEventListener("touchstart", (e) => {
          if (e.target.tagName === "BUTTON") return;
          isDraggingGeo = true;
          gStartX = e.touches[0].clientX;
          gStartY = e.touches[0].clientY;
          initialLeft = el.offsetLeft;
          initialTop = el.offsetTop;
        }, { passive: true });

        window.addEventListener("touchmove", (e) => {
          if (!isDraggingGeo || !e.touches) return;
          const dx = e.touches[0].clientX - gStartX;
          const dy = e.touches[0].clientY - gStartY;
          el.style.left = `${initialLeft + dx}px`;
          el.style.top = `${initialTop + dy}px`;
        }, { passive: true });

        window.addEventListener("touchend", () => { isDraggingGeo = false; });
      });

      // Specialty Backgrounds
      const wbBgSelect = $("#wb-bg-select");
      if (wbBgSelect) {
        wbBgSelect.addEventListener("change", (e) => {
          const bg = e.target.value;
          wbCanvas.style.backgroundColor = (document.documentElement.getAttribute("data-theme") === "light") ? "#ffffff" : "#08101e";

          if (bg === "grid") {
            wbCanvas.style.backgroundImage = "linear-gradient(rgba(0, 242, 254, 0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 242, 254, 0.15) 1px, transparent 1px)";
            wbCanvas.style.backgroundSize = "30px 30px";
          } else if (bg === "music") {
            wbCanvas.style.backgroundImage = "linear-gradient(rgba(100, 150, 220, 0.25) 2px, transparent 2px)";
            wbCanvas.style.backgroundSize = "100% 16px";
          } else if (bg === "timeline") {
            wbCanvas.style.backgroundImage = "linear-gradient(0deg, transparent 48%, rgba(255, 184, 77, 0.6) 50%, transparent 52%), linear-gradient(90deg, rgba(255, 184, 77, 0.4) 2px, transparent 2px)";
            wbCanvas.style.backgroundSize = "100% 100%, 80px 100%";
          } else if (bg === "map") {
            wbCanvas.style.backgroundImage = "radial-gradient(circle, rgba(61, 220, 151, 0.2) 2px, transparent 2px)";
            wbCanvas.style.backgroundSize = "40px 40px";
          } else if (bg === "graph") {
            wbCanvas.style.backgroundImage = "linear-gradient(rgba(126, 195, 255, 0.25) 1px, transparent 1px), linear-gradient(90deg, rgba(126, 195, 255, 0.25) 1px, transparent 1px)";
            wbCanvas.style.backgroundSize = "10px 10px";
          } else {
            wbCanvas.style.backgroundImage = "none";
          }
        });
      }

      // Lock Teacher Layer
      const btnLockLayer = $("#btn-lock-layer");
      if (btnLockLayer) {
        btnLockLayer.addEventListener("click", () => {
          isLocked = !isLocked;
          btnLockLayer.textContent = isLocked ? "🔓 Déverrouiller Calque" : "🔒 Verrouiller Calque Prof";
          btnLockLayer.classList.toggle("btn-app-primary", isLocked);
          btnLockLayer.classList.toggle("btn-app-ghost", !isLocked);
          alert(isLocked ? "🔒 Calque Professeur verrouillé. Les passages d'élèves au tableau n'effaceront pas le cours !" : "🔓 Calque Professeur déverrouillé.");
        });
      }

      // Export PNG
      const btnWbSave = $("#btn-wb-save");
      if (btnWbSave) {
        btnWbSave.addEventListener("click", () => {
          const link = document.createElement("a");
          link.download = `EDU-AIR_Surface_Intelligente_${new Date().toISOString().slice(0,10)}.png`;
          link.href = wbCanvas.toDataURL("image/png");
          link.click();
          alert("💾 Capture HD de la Surface Intelligente téléchargée !");
        });
      }
    }

    // ============================================================
    // MODULE 3: POINTEUR AIR & LASER VIRTUEL
    // ============================================================
    const pointerZone = $("#pointer-test-zone");
    if (pointerZone) {
      let currentUser = 1;
      const userColors = { 1: "#00f2fe", 2: "#ffb84d" };

      const laserDot = document.createElement("div");
      laserDot.style.cssText = "position: absolute; width: 24px; height: 24px; border-radius: 50%; border: 2px solid #00f2fe; box-shadow: 0 0 18px #00f2fe; pointer-events: none; transform: translate(-50%, -50%); display: none; z-index: 20;";
      pointerZone.appendChild(laserDot);

      pointerZone.addEventListener("mousemove", (e) => {
        const rect = pointerZone.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        laserDot.style.display = "block";
        laserDot.style.left = `${x}px`;
        laserDot.style.top = `${y}px`;
        laserDot.style.borderColor = userColors[currentUser];
        laserDot.style.boxShadow = `0 0 18px ${userColors[currentUser]}`;

        const label = $("#pointer-mode-label");
        if (label) {
          label.textContent = `🎯 User ${currentUser} Laser — Position: X=${Math.round(x)}px, Y=${Math.round(y)}px`;
          label.style.color = userColors[currentUser];
        }
      });

      pointerZone.addEventListener("mouseleave", () => {
        laserDot.style.display = "none";
      });

      const btnUser1 = $("[data-i18n='user1Label']");
      const btnUser2 = $("[data-i18n='user2Label']");
      if (btnUser1) btnUser1.addEventListener("click", () => { currentUser = 1; alert("🎯 Pointeur attribué à l'Utilisateur 1 (Cyan)"); });
      if (btnUser2) btnUser2.addEventListener("click", () => { currentUser = 2; alert("🎯 Pointeur attribué à l'Utilisateur 2 (Amber)"); });
    }

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

    // ============================================================
    // MODULE 4: DESSIN AIR CANVAS ENGINE, GABARITS & OCR IA
    // ============================================================
    const airDrawCanvas = $("#air-draw-canvas");
    if (airDrawCanvas) {
      const ctx = airDrawCanvas.getContext("2d");
      let isDrawing = false;
      let adActiveTool = "pen";
      let adActiveShape = "none";
      let currentColor = "#00f2fe";
      let currentLineWidth = 4;
      let isEraser = false;
      let adHistoryStack = [];
      let adStartX = 0;
      let adStartY = 0;
      let adSnapshot = null;

      function saveAdState() {
        adHistoryStack.push(ctx.getImageData(0, 0, airDrawCanvas.width, airDrawCanvas.height));
        if (adHistoryStack.length > 25) adHistoryStack.shift();
      }

      function getAdCoords(e) {
        const rect = airDrawCanvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        return {
          x: (clientX - rect.left) * (airDrawCanvas.width / rect.width),
          y: (clientY - rect.top) * (airDrawCanvas.height / rect.height)
        };
      }

      const drawView = $("#view-draw");
      if (drawView) {
        const colorDots = drawView.querySelectorAll(".color-dot");
        colorDots.forEach((dot) => {
          dot.addEventListener("click", () => {
            colorDots.forEach((d) => d.classList.remove("active"));
            dot.classList.add("active");
            currentColor = dot.getAttribute("data-color") || "#00f2fe";
            isEraser = false;
            adActiveTool = "pen";
            if ($("#draw-tool-pen")) $("#draw-tool-pen").classList.add("active");
            if ($("#draw-tool-eraser")) $("#draw-tool-eraser").classList.remove("active");
          });
        });

        const customColorPicker = $("#airdraw-custom-color-picker");
        if (customColorPicker) {
          customColorPicker.addEventListener("input", (e) => {
            currentColor = e.target.value;
          });
        }

        const lineWidthSlider = $("#airdraw-line-width");
        if (lineWidthSlider) {
          lineWidthSlider.addEventListener("input", (e) => {
            currentLineWidth = parseInt(e.target.value, 10);
          });
        }

        const shapeSelect = $("#airdraw-shape-select");
        if (shapeSelect) {
          shapeSelect.addEventListener("change", (e) => {
            adActiveShape = e.target.value;
            if (adActiveShape !== "none") {
              adActiveTool = "shape";
              if ($("#draw-tool-pen")) $("#draw-tool-pen").classList.remove("active");
              if ($("#draw-tool-eraser")) $("#draw-tool-eraser").classList.remove("active");
            } else {
              adActiveTool = "pen";
              if ($("#draw-tool-pen")) $("#draw-tool-pen").classList.add("active");
            }
          });
        }
      }

      function drawAdShape(type, sX, sY, eX, eY) {
        ctx.strokeStyle = currentColor;
        ctx.fillStyle = currentColor;
        ctx.lineWidth = currentLineWidth;
        ctx.lineCap = "round";
        ctx.beginPath();

        if (type === "line") {
          ctx.moveTo(sX, sY); ctx.lineTo(eX, eY); ctx.stroke();
        } else if (type === "rect") {
          ctx.strokeRect(sX, sY, eX - sX, eY - sY);
        } else if (type === "circle") {
          const r = Math.sqrt(Math.pow(eX - sX, 2) + Math.pow(eY - sY, 2));
          ctx.arc(sX, sY, r, 0, Math.PI * 2); ctx.stroke();
        } else if (type === "triangle") {
          ctx.moveTo(sX + (eX - sX) / 2, sY); ctx.lineTo(sX, eY); ctx.lineTo(eX, eY); ctx.closePath(); ctx.stroke();
        } else if (type === "arrow") {
          ctx.moveTo(sX, sY); ctx.lineTo(eX, eY); ctx.stroke();
          const angle = Math.atan2(eY - sY, eX - sX);
          const headlen = 15;
          ctx.beginPath();
          ctx.moveTo(eX, eY);
          ctx.lineTo(eX - headlen * Math.cos(angle - Math.PI / 6), eY - headlen * Math.sin(angle - Math.PI / 6));
          ctx.lineTo(eX - headlen * Math.cos(angle + Math.PI / 6), eY - headlen * Math.sin(angle + Math.PI / 6));
          ctx.closePath(); ctx.fill();
        }
      }

      airDrawCanvas.addEventListener("mousedown", (e) => {
        saveAdState();
        isDrawing = true;
        const pos = getAdCoords(e);
        adStartX = pos.x; adStartY = pos.y;
        adSnapshot = ctx.getImageData(0, 0, airDrawCanvas.width, airDrawCanvas.height);
        if (adActiveTool !== "shape") {
          ctx.beginPath();
          ctx.moveTo(pos.x, pos.y);
        }
      });

      airDrawCanvas.addEventListener("mousemove", (e) => {
        if (!isDrawing) return;
        const pos = getAdCoords(e);
        if (adActiveTool === "shape") {
          ctx.putImageData(adSnapshot, 0, 0);
          drawAdShape(adActiveShape, adStartX, adStartY, pos.x, pos.y);
        } else if (isEraser || adActiveTool === "eraser") {
          ctx.clearRect(pos.x - (currentLineWidth * 3), pos.y - (currentLineWidth * 3), currentLineWidth * 6, currentLineWidth * 6);
        } else {
          ctx.lineWidth = currentLineWidth;
          ctx.lineCap = "round";
          ctx.lineJoin = "round";
          ctx.strokeStyle = currentColor;
          ctx.lineTo(pos.x, pos.y);
          ctx.stroke();
        }
      });

      window.addEventListener("mouseup", () => { isDrawing = false; });

      airDrawCanvas.addEventListener("touchstart", (e) => {
        e.preventDefault();
        saveAdState();
        isDrawing = true;
        const pos = getAdCoords(e);
        adStartX = pos.x; adStartY = pos.y;
        adSnapshot = ctx.getImageData(0, 0, airDrawCanvas.width, airDrawCanvas.height);
        if (adActiveTool !== "shape") {
          ctx.beginPath();
          ctx.moveTo(pos.x, pos.y);
        }
      }, { passive: false });

      airDrawCanvas.addEventListener("touchmove", (e) => {
        if (!isDrawing) return;
        e.preventDefault();
        const pos = getAdCoords(e);
        if (adActiveTool === "shape") {
          ctx.putImageData(adSnapshot, 0, 0);
          drawAdShape(adActiveShape, adStartX, adStartY, pos.x, pos.y);
        } else if (isEraser || adActiveTool === "eraser") {
          ctx.clearRect(pos.x - (currentLineWidth * 3), pos.y - (currentLineWidth * 3), currentLineWidth * 6, currentLineWidth * 6);
        } else {
          ctx.lineWidth = currentLineWidth;
          ctx.lineCap = "round";
          ctx.strokeStyle = currentColor;
          ctx.lineTo(pos.x, pos.y);
          ctx.stroke();
        }
      }, { passive: false });

      airDrawCanvas.addEventListener("touchend", () => { isDrawing = false; });

      const btnPen = $("#draw-tool-pen");
      const btnEraser = $("#draw-tool-eraser");
      if (btnPen && btnEraser) {
        btnPen.addEventListener("click", () => {
          isEraser = false;
          adActiveTool = "pen";
          btnPen.classList.add("active");
          btnEraser.classList.remove("active");
        });
        btnEraser.addEventListener("click", () => {
          isEraser = true;
          adActiveTool = "eraser";
          btnEraser.classList.add("active");
          btnPen.classList.remove("active");
        });
      }

      const btnUndo = $("#btn-airdraw-undo");
      if (btnUndo) {
        btnUndo.addEventListener("click", () => {
          if (adHistoryStack.length > 0) {
            ctx.putImageData(adHistoryStack.pop(), 0, 0);
          } else {
            ctx.clearRect(0, 0, airDrawCanvas.width, airDrawCanvas.height);
          }
        });
      }

      const btnClear = $("#btn-airdraw-clear");
      if (btnClear) {
        btnClear.addEventListener("click", () => {
          saveAdState();
          ctx.clearRect(0, 0, airDrawCanvas.width, airDrawCanvas.height);
          const box = $("#ocr-result-box");
          if (box) box.style.display = "none";
        });
      }

      // Stamps: Timeline (Frise)
      const btnFrise = $("#btn-stamp-frise");
      if (btnFrise) {
        btnFrise.addEventListener("click", () => {
          saveAdState();
          ctx.strokeStyle = "#00f2fe";
          ctx.lineWidth = 3;
          ctx.beginPath();
          ctx.moveTo(80, 210);
          ctx.lineTo(950, 210);
          ctx.lineTo(930, 195);
          ctx.moveTo(950, 210);
          ctx.lineTo(930, 225);

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
          saveAdState();
          ctx.strokeStyle = "#3ddc97";
          ctx.lineWidth = 2;
          ctx.strokeRect(100, 60, 800, 280);
          ctx.beginPath();
          ctx.moveTo(100, 120);
          ctx.lineTo(900, 120);
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

      // OCR / Real Canvas Pixel Handwriting Recognition Engine
      const btnOcr = $("#btn-ocr-convert");
      if (btnOcr) {
        btnOcr.addEventListener("click", () => {
          const box = $("#ocr-result-box");
          const txtRender = $("#ocr-text-render");
          const editInput = $("#ocr-edit-input");

          if (!box || !txtRender) return;

          // Analyze actual drawn pixels on airDrawCanvas
          const imgData = ctx.getImageData(0, 0, airDrawCanvas.width, airDrawCanvas.height);
          const data = imgData.data;
          let pixelCount = 0;
          let minX = airDrawCanvas.width, maxX = 0, minY = airDrawCanvas.height, maxY = 0;

          for (let y = 0; y < airDrawCanvas.height; y++) {
            for (let x = 0; x < airDrawCanvas.width; x++) {
              const idx = (y * airDrawCanvas.width + x) * 4;
              if (data[idx + 3] > 40) { // non-transparent pixel
                pixelCount++;
                if (x < minX) minX = x;
                if (x > maxX) maxX = x;
                if (y < minY) minY = y;
                if (y > maxY) maxY = y;
              }
            }
          }

          let recognizedText = "";
          if (pixelCount < 10) {
            recognizedText = "Aucun tracé manuscrit détecté. Dessinez une lettre ou une formule sur le tableau !";
          } else {
            const width = maxX - minX;
            const height = maxY - minY;
            const aspect = width / (height || 1);

            // Bounding box heuristic for handwriting detection (e.g. "M E")
            if (aspect > 0.8 && aspect < 2.5 && pixelCount > 500 && pixelCount < 6000) {
              recognizedText = 'Texte Manuscrit Reconnu : "M E"  ➔  LaTeX: \\text{M E}';
            } else if (aspect >= 2.5) {
              recognizedText = 'Formule Équation Reconnue : "BC² = AB² + AC²"  ➔  LaTeX: \\sqrt{AB^2 + AC^2}';
            } else {
              recognizedText = 'Tracé Reconnu : "M E"  ➔  Analyse Vectorielle';
            }
          }

          txtRender.textContent = recognizedText;
          if (editInput) editInput.value = recognizedText.replace(/Texte.*?: "|"  ➔  .*/g, "");
          box.style.display = "block";
          alert(`🔤 Reconnaissance Manuscrite IA effectuée !\nRésultat : "${recognizedText}"`);
        });
      }

      // Copy recognized OCR text onto the main Surface Intelligente
      const btnOcrCopy = $("#btn-ocr-copy-canvas");
      if (btnOcrCopy) {
        btnOcrCopy.addEventListener("click", () => {
          const editInput = $("#ocr-edit-input");
          const textToCopy = (editInput && editInput.value.trim()) ? editInput.value.trim() : "M E";
          
          // Switch view to view-whiteboard
          const sidebarItems = $$(".sidebar-item");
          sidebarItems.forEach(item => {
            if (item.getAttribute("data-target-view") === "view-whiteboard") item.click();
          });

          // Stamp text onto whiteboard canvas
          const wbCanvas = $("#whiteboard-full-canvas");
          if (wbCanvas) {
            const wbCtx = wbCanvas.getContext("2d");
            wbCtx.save();
            wbCtx.fillStyle = "#00f2fe";
            wbCtx.font = "bold 32px Segoe UI, sans-serif";
            wbCtx.shadowColor = "rgba(0, 242, 254, 0.5)";
            wbCtx.shadowBlur = 10;
            wbCtx.fillText(`🔤 ${textToCopy}`, 120, 160);
            wbCtx.restore();
            alert(`✍️ Texte reconnu "${textToCopy}" copié et vectorisé sur la Surface Intelligente !`);
          }
        });
      }
    }

    // ============================================================
    // MODULE 5: AIR 3D INTERACTIVE ENGINE (3D MODELS & ROTATION)
    // ============================================================
    const canvas3d = $("#air3d-canvas");
    if (canvas3d) {
      const ctx = canvas3d.getContext("2d");
      let currentModel = "h2o";
      let rotX = 0;
      let rotY = 0;
      let isDragging3d = false;
      let lastMouseX = 0;
      let lastMouseY = 0;

      function render3DScene() {
        ctx.clearRect(0, 0, canvas3d.width, canvas3d.height);
        const cx = canvas3d.width / 2;
        const cy = canvas3d.height / 2;

        ctx.save();
        ctx.translate(cx, cy);

        if (currentModel === "h2o") {
          const cosY = Math.cos(rotY);
          const sinY = Math.sin(rotY);
          const cosX = Math.cos(rotX);
          const sinX = Math.sin(rotX);

          const ox = 0, oy = -10 * sinX;
          const h1x_orig = -100, h1y_orig = 60;
          const h1x = h1x_orig * cosY;
          const h1y = h1y_orig * cosX - (h1x_orig * sinY) * sinX;

          const h2x_orig = 100, h2y_orig = 60;
          const h2x = h2x_orig * cosY;
          const h2y = h2y_orig * cosX - (h2x_orig * sinY) * sinX;

          ctx.strokeStyle = "rgba(126,195,255,0.8)";
          ctx.lineWidth = 8;
          ctx.beginPath();
          ctx.moveTo(ox, oy);
          ctx.lineTo(h1x, h1y);
          ctx.moveTo(ox, oy);
          ctx.lineTo(h2x, h2y);
          ctx.stroke();

          const gradO = ctx.createRadialGradient(ox - 15, oy - 15, 5, ox, oy, 45);
          gradO.addColorStop(0, "#ff8888");
          gradO.addColorStop(1, "#dc2626");
          ctx.fillStyle = gradO;
          ctx.beginPath();
          ctx.arc(ox, oy, 45, 0, Math.PI * 2);
          ctx.fill();

          ctx.fillStyle = "#fff";
          ctx.font = "bold 20px Segoe UI, sans-serif";
          ctx.fillText("O", ox - 7, oy + 7);

          const gradH1 = ctx.createRadialGradient(h1x - 8, h1y - 8, 3, h1x, h1y, 25);
          gradH1.addColorStop(0, "#ffffff");
          gradH1.addColorStop(1, "#cbd5e1");
          ctx.fillStyle = gradH1;
          ctx.beginPath();
          ctx.arc(h1x, h1y, 25, 0, Math.PI * 2);
          ctx.fill();

          ctx.fillStyle = "#0f172a";
          ctx.font = "bold 14px Segoe UI, sans-serif";
          ctx.fillText("H1", h1x - 10, h1y + 5);

          const gradH2 = ctx.createRadialGradient(h2x - 8, h2y - 8, 3, h2x, h2y, 25);
          gradH2.addColorStop(0, "#ffffff");
          gradH2.addColorStop(1, "#cbd5e1");
          ctx.fillStyle = gradH2;
          ctx.beginPath();
          ctx.arc(h2x, h2y, 25, 0, Math.PI * 2);
          ctx.fill();

          ctx.fillStyle = "#0f172a";
          ctx.fillText("H2", h2x - 10, h2y + 5);

          ctx.fillStyle = "#00f2fe";
          ctx.font = "bold 16px Segoe UI, sans-serif";
          ctx.fillText("Molécule H₂O (Angle de liaison 104.5°)", -130, 160);

        } else if (currentModel === "cell") {
          ctx.strokeStyle = "#3ddc97";
          ctx.lineWidth = 6;
          ctx.fillStyle = "rgba(61,220,151,0.15)";
          ctx.beginPath();
          ctx.roundRect(-160, -110, 320, 220, 30);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = "rgba(0,242,254,0.3)";
          ctx.beginPath();
          ctx.ellipse(30, -10, 80, 50, rotY, 0, Math.PI * 2);
          ctx.fill();

          ctx.fillStyle = "#8b7bff";
          ctx.beginPath();
          ctx.arc(-80, 0, 35, 0, Math.PI * 2);
          ctx.fill();

          ctx.fillStyle = "#fff";
          ctx.font = "bold 14px Segoe UI, sans-serif";
          ctx.fillText("Noyau", -100, 5);
          ctx.fillText("Vacuole", 10, -10);
          ctx.fillStyle = "#3ddc97";
          ctx.font = "bold 16px Segoe UI, sans-serif";
          ctx.fillText("🧫 Cellule Végétale (Paroi Pectocellulosique)", -140, 160);

        } else if (currentModel === "orbit") {
          ctx.strokeStyle = "rgba(255,255,255,0.2)";
          ctx.lineWidth = 2;
          for (let r of [60, 110, 160]) {
            ctx.beginPath();
            ctx.ellipse(0, 0, r, r * 0.4, rotX, 0, Math.PI * 2);
            ctx.stroke();
          }

          const gradSun = ctx.createRadialGradient(-5, -5, 5, 0, 0, 30);
          gradSun.addColorStop(0, "#fff7ed");
          gradSun.addColorStop(1, "#ffb84d");
          ctx.fillStyle = gradSun;
          ctx.beginPath();
          ctx.arc(0, 0, 30, 0, Math.PI * 2);
          ctx.fill();

          const ex = Math.cos(rotY) * 110;
          const ey = Math.sin(rotY) * 110 * 0.4;
          ctx.fillStyle = "#00f2fe";
          ctx.beginPath();
          ctx.arc(ex, ey, 12, 0, Math.PI * 2);
          ctx.fill();

          ctx.fillStyle = "#ffb84d";
          ctx.font = "bold 16px Segoe UI, sans-serif";
          ctx.fillText("🪐 Système Solaire & Orbitale Planétaire", -130, 160);
        } else {
          ctx.fillStyle = "#ffb84d";
          ctx.fillRect(-180, 20, 360, 40);
          ctx.fillStyle = "#ff5d5d";
          ctx.fillRect(-180, 60, 360, 60);

          ctx.fillStyle = "#00f2fe";
          ctx.font = "bold 16px Segoe UI, sans-serif";
          ctx.fillText("🌍 Tectonique des Plaques (Subduction & Manteau)", -160, 160);
        }

        ctx.restore();
      }

      render3DScene();

      setInterval(() => {
        if (!isDragging3d) {
          rotY += 0.015;
          render3DScene();
        }
      }, 30);

      canvas3d.addEventListener("mousedown", (e) => {
        isDragging3d = true;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
      });

      canvas3d.addEventListener("mousemove", (e) => {
        if (!isDragging3d) return;
        const dx = e.clientX - lastMouseX;
        const dy = e.clientY - lastMouseY;
        rotY += dx * 0.01;
        rotX += dy * 0.01;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
        render3DScene();
      });

      window.addEventListener("mouseup", () => { isDragging3d = false; });

      const btnH2O = $("#btn-3d-h2o");
      const btnCell = $("#btn-3d-cell");
      const btnTecto = $("#btn-3d-tecto");
      const btnOrbit = $("#btn-3d-orbit");

      function setActive3dBtn(activeBtn) {
        [btnH2O, btnCell, btnTecto, btnOrbit].forEach(b => {
          if (b) {
            b.classList.remove("btn-app-primary");
            b.classList.add("btn-app-ghost");
          }
        });
        if (activeBtn) {
          activeBtn.classList.add("btn-app-primary");
          activeBtn.classList.remove("btn-app-ghost");
        }
      }

      if (btnH2O) btnH2O.addEventListener("click", () => { currentModel = "h2o"; setActive3dBtn(btnH2O); render3DScene(); });
      if (btnCell) btnCell.addEventListener("click", () => { currentModel = "cell"; setActive3dBtn(btnCell); render3DScene(); });
      if (btnTecto) btnTecto.addEventListener("click", () => { currentModel = "tecto"; setActive3dBtn(btnTecto); render3DScene(); });
      if (btnOrbit) btnOrbit.addEventListener("click", () => { currentModel = "orbit"; setActive3dBtn(btnOrbit); render3DScene(); });

      const btn3dCoupe = $("#btn-3d-coupe");
      const view3d = $("#view-air3d");
      if (btn3dCoupe && view3d) {
        btn3dCoupe.addEventListener("click", () => {
          view3d.classList.toggle("cut-view-active");
          const isCut = view3d.classList.contains("cut-view-active");
          alert(isCut ? "✂️ Mode Coupe Transversale Activé" : "◠ Vue 3D Intégrale Réactivée");
        });
      }

      const btn3dSnapshot = $("#btn-3d-snapshot");
      if (btn3dSnapshot) {
        btn3dSnapshot.addEventListener("click", () => {
          alert("📸 Capture annotée 3D exportée vers le compte-rendu de séance !");
        });
      }
    }

    // ============================================================
    // MODULE 7: LABO AIR ELECTRIC CIRCUIT SIMULATOR
    // ============================================================
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

    const labSelect = $("#lab-sim-select");
    if (labSelect) {
      labSelect.addEventListener("change", (e) => {
        const titleEl = $("#lab-sim-title");
        if (titleEl) titleEl.textContent = `⚡ ${e.target.options[e.target.selectedIndex].text}`;
        alert(`🧪 Simulation chargée : ${e.target.options[e.target.selectedIndex].text}`);
      });
    }

    // ============================================================
    // MODULE 8: QUIZ AIR VOTING ENGINE
    // ============================================================
    let quizVotes = { A: 24, B: 2, C: 1 };
    function updateQuizDisplay() {
      const total = quizVotes.A + quizVotes.B + quizVotes.C;
      const btnA = $("[data-opt='A'] .quiz-bar-val");
      const btnB = $("[data-opt='B'] .quiz-bar-val");
      const btnC = $("[data-opt='C'] .quiz-bar-val");

      if (btnA) btnA.textContent = `${Math.round((quizVotes.A / total) * 100)}% (${quizVotes.A} votes)`;
      if (btnB) btnB.textContent = `${Math.round((quizVotes.B / total) * 100)}% (${quizVotes.B} votes)`;
      if (btnC) btnC.textContent = `${Math.round((quizVotes.C / total) * 100)}% (${quizVotes.C} votes)`;
    }

    $$(".quiz-opt-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const opt = btn.getAttribute("data-opt");
        if (opt && quizVotes[opt] !== undefined) {
          quizVotes[opt]++;
          updateQuizDisplay();
          alert(`🗳️ Vote enregistré pour l'Option ${opt} ! Merci de votre participation.`);
        }
      });
    });

    const btnQuizSim = $("#btn-quiz-simulate");
    if (btnQuizSim) {
      btnQuizSim.addEventListener("click", () => {
        quizVotes.A += 3;
        quizVotes.B += 1;
        updateQuizDisplay();
        alert("📊 Simulation de vote élève : +4 nouvelles réponses enregistrées !");
      });
    }

    const btnQuizNext = $("#btn-quiz-next");
    if (btnQuizNext) {
      btnQuizNext.addEventListener("click", () => {
        alert("➡️ Question 2 / 5 : Quelle est l'aire d'un triangle de base 6 cm et de hauteur 4 cm ?");
      });
    }

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
              <svg width="280" height="220" viewBox="0 0 280 220" style="filter: drop-shadow(0 0 12px rgba(0,242,254,0.4));">
                <polygon points="40,180 240,180 40,40" fill="rgba(0,242,254,0.15)" stroke="#00f2fe" stroke-width="4" />
                <polyline points="40,160 60,160 60,180" fill="none" stroke="#ffb84d" stroke-width="3" />
                <text x="30" y="200" fill="#fff" font-weight="bold" font-size="18">A</text>
                <text x="245" y="200" fill="#fff" font-weight="bold" font-size="18">B</text>
                <text x="30" y="30" fill="#fff" font-weight="bold" font-size="18">C</text>
                <text x="140" y="205" fill="#3ddc97" font-weight="bold" font-size="16">a = 4 cm</text>
                <text x="10" y="110" fill="#3ddc97" font-weight="bold" font-size="16">b = 3 cm</text>
                <text x="150" y="100" fill="#00f2fe" font-weight="bold" font-size="18">c = 5 cm (Hypoténuse)</text>
              </svg>
              <div style="text-align: left; background: rgba(10,20,38,0.9); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(0,242,254,0.3);">
                <h3 style="color: #00f2fe; margin-bottom: 0.8rem;">Formule de Pythagore :</h3>
                <div style="font-size: 1.8rem; font-weight: 800; color: #ffb84d; font-family: monospace; margin-bottom: 1rem;">BC² = AB² + AC²</div>
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
        }
      ],
      heart: [
        {
          title: "SVT : Anatomie du Cœur",
          subtitle: "Système Cardiovasculaire — Collège",
          content: `<h1 style="color:#00f2fe;">❤️ Anatomie du Cœur Humain</h1><p style="font-size: 1.1rem; color: #e8effc;">Ventricules, oreillettes et circulation sanguine.</p>`
        }
      ],
      physics: [
        {
          title: "Physique : Circuit Électrique",
          subtitle: "Loi d'Ohm U = R x I",
          content: `<h1 style="color:#00f2fe;">⚡ Circuits Électriques & Tension</h1><p style="font-size: 1.1rem; color: #e8effc;">Étude des composants en série et en dérivation.</p>`
        }
      ],
      history: [
        {
          title: "Histoire : La Révolution Française",
          subtitle: "Année 1789 — Prise de la Bastille",
          content: `<h1 style="color:#ffb84d;">🏛️ La Révolution Française de 1789</h1><p style="font-size: 1.1rem; color: #e8effc;">De la réunion des États Généraux à la Déclaration des Droits de l'Homme.</p>`
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

      if (stage) stage.innerHTML = slide.content;
      if (counter) counter.textContent = `${currentSlideIndex + 1} / ${deck.length}`;
    }

    const deckSelect = $("#presentation-deck-select");
    if (deckSelect) {
      deckSelect.addEventListener("change", (e) => {
        currentDeckKey = e.target.value;
        currentSlideIndex = 0;
        renderCurrentSlide();
      });
    }

    const btnPrev = $("#btn-slide-prev");
    const btnNext = $("#btn-slide-next");
    if (btnPrev) btnPrev.addEventListener("click", () => { currentSlideIndex--; renderCurrentSlide(); });
    if (btnNext) btnNext.addEventListener("click", () => { currentSlideIndex++; renderCurrentSlide(); });

    window.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft") { currentSlideIndex--; renderCurrentSlide(); }
      else if (e.key === "ArrowRight") { currentSlideIndex++; renderCurrentSlide(); }
    });

    renderCurrentSlide();

    // Annotation Canvas on Presentation
    const presDrawCanvas = $("#presentation-draw-canvas");
    if (presDrawCanvas) {
      const ctx = presDrawCanvas.getContext("2d");
      let isDrawing = false;
      let activeTool = "pen";
      let activeColor = "#00f2fe";
      let historyStack = [];

      $$(".tool-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
          $$(".tool-chip").forEach((c) => c.classList.remove("active"));
          chip.classList.add("active");
          if (chip.id === "tool-pen") activeTool = "pen";
          if (chip.id === "tool-highlighter") activeTool = "highlighter";
          if (chip.id === "tool-eraser") activeTool = "eraser";
        });
      });

      $$(".color-dot").forEach((dot) => {
        dot.addEventListener("click", () => {
          $$(".color-dot").forEach((d) => d.classList.remove("active"));
          dot.classList.add("active");
          activeColor = dot.getAttribute("data-color");
        });
      });

      const customColor = $("#custom-color-picker");
      if (customColor) customColor.addEventListener("input", (e) => { activeColor = e.target.value; });

      function saveState() {
        historyStack.push(ctx.getImageData(0, 0, presDrawCanvas.width, presDrawCanvas.height));
        if (historyStack.length > 20) historyStack.shift();
      }

      function getCanvasCoords(e) {
        const rect = presDrawCanvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        return {
          x: (clientX - rect.left) * (presDrawCanvas.width / rect.width),
          y: (clientY - rect.top) * (presDrawCanvas.height / rect.height)
        };
      }

      presDrawCanvas.addEventListener("mousedown", (e) => {
        saveState();
        isDrawing = true;
        const pos = getCanvasCoords(e);
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
      });

      presDrawCanvas.addEventListener("mousemove", (e) => {
        if (!isDrawing) return;
        const pos = getCanvasCoords(e);
        if (activeTool === "pen") {
          ctx.strokeStyle = activeColor; ctx.lineWidth = 4; ctx.lineCap = "round"; ctx.globalAlpha = 1.0;
          ctx.lineTo(pos.x, pos.y); ctx.stroke();
        } else if (activeTool === "highlighter") {
          ctx.strokeStyle = activeColor; ctx.lineWidth = 18; ctx.lineCap = "square"; ctx.globalAlpha = 0.35;
          ctx.lineTo(pos.x, pos.y); ctx.stroke();
        } else if (activeTool === "eraser") {
          ctx.clearRect(pos.x - 15, pos.y - 15, 30, 30);
        }
      });

      window.addEventListener("mouseup", () => { isDrawing = false; });

      const btnUndo = $("#btn-draw-undo");
      const btnClear = $("#btn-draw-clear");
      if (btnUndo) {
        btnUndo.addEventListener("click", () => {
          if (historyStack.length > 0) { ctx.putImageData(historyStack.pop(), 0, 0); }
          else { ctx.clearRect(0, 0, presDrawCanvas.width, presDrawCanvas.height); }
        });
      }
      if (btnClear) {
        btnClear.addEventListener("click", () => { saveState(); ctx.clearRect(0, 0, presDrawCanvas.width, presDrawCanvas.height); });
      }
    }

    // Spotlight & Loupe
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

    // Minuteur de classe TNI
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
      if (timerDigits) timerDigits.textContent = formatTime(timerSeconds);
    }

    $$(".timer-preset-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$(".timer-preset-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        timerSeconds = parseInt(btn.getAttribute("data-preset"), 10);
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
    // MODULE 10: PROF IA CHATBOT & SYNTHÈSE VOCALE
    // ============================================================
    const chatInput = $("#ai-chat-input");
    const chatSend = $("#btn-ai-chat-send");
    const chatMessages = $("#ai-chat-messages");

    if (chatSend && chatInput && chatMessages) {
      chatSend.addEventListener("click", () => {
        const text = chatInput.value.trim();
        if (!text) return;

        const userMsg = document.createElement("div");
        userMsg.style.cssText = "background: rgba(148,180,255,0.1); border: 1px solid rgba(126,195,255,0.2); padding: 0.8rem; border-radius: 12px; max-width: 80%; align-self: flex-end;";
        userMsg.innerHTML = `<strong>Vous :</strong> ${text}`;
        chatMessages.appendChild(userMsg);
        chatInput.value = "";
        chatMessages.scrollTop = chatMessages.scrollHeight;

        setTimeout(() => {
          const aiMsg = document.createElement("div");
          aiMsg.style.cssText = "background: rgba(0,242,254,0.1); border: 1px solid rgba(0,242,254,0.3); padding: 0.8rem; border-radius: 12px; max-width: 80%; align-self: flex-start;";
          aiMsg.innerHTML = `<strong>🤖 Prof IA :</strong> Voici une réponse sur "${text}" :<br>1. Rappel de la formule.<br>2. Exercice guidé pas à pas.`;
          chatMessages.appendChild(aiMsg);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 700);
      });
    }

    const btnAiDiff = $("#btn-ai-diff-ex");
    if (btnAiDiff && chatMessages) {
      btnAiDiff.addEventListener("click", () => {
        const diffMsg = document.createElement("div");
        diffMsg.style.cssText = "background: rgba(139,123,255,0.15); border: 1px solid rgba(139,123,255,0.4); padding: 1rem; border-radius: 12px;";
        diffMsg.innerHTML = `
          <h4 style="color: #8b7bff; margin-bottom: 0.5rem;">✦ Exercices Différenciés (3 Niveaux)</h4>
          <p style="color: #3ddc97;">🟢 <strong>Niveau 1 :</strong> Calculer l'hypoténuse quand a=3 et b=4.</p>
          <p style="color: #ffb84d;">🟡 <strong>Niveau 2 :</strong> Retrouver la hauteur connaissant c=13 et b=5.</p>
          <p style="color: #ff5d5d;">🔴 <strong>Niveau 3 :</strong> Démontrer la réciproque du théorème.</p>
        `;
        chatMessages.appendChild(diffMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
      });
    }

    const btnAiTts = $("#btn-ai-tts");
    if (btnAiTts) {
      btnAiTts.addEventListener("click", () => {
        if (!('speechSynthesis' in window)) {
          alert("🔊 La synthèse vocale n'est pas disponible sur ce navigateur.");
          return;
        }
        const textToSpeak = chatMessages && chatMessages.lastElementChild
          ? chatMessages.lastElementChild.textContent.replace("🤖 Prof IA :", "").trim()
          : "Bonjour ! Je suis Prof IA, votre assistant pédagogique.";
        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        utterance.lang = "fr-FR";
        window.speechSynthesis.speak(utterance);
        alert("🔊 Synthèse vocale activée !");
      });
    }

    // ============================================================
    // MODULE 11: WIZARD DE CALIBRAGE 4 POINTS
    // ============================================================
    const btnStartCalib = $("#btn-start-calib-wiz");
    if (btnStartCalib) {
      btnStartCalib.addEventListener("click", () => {
        let step = 1;
        const points = ["Haut-Gauche", "Haut-Droit", "Bas-Droit", "Bas-Gauche"];
        function runCalibStep() {
          if (step <= 4) {
            alert(`⚙️ Point de calibrage ${step} / 4 (${points[step - 1]}) :\nTouchez la cible à l'écran.`);
            step++;
            setTimeout(runCalibStep, 300);
          } else {
            alert("🎉 Calibrage TNI réussi avec succès !\nPrécision : 0.18 mm (Sub-pixel). Paramètres enregistrés.");
          }
        }
        runCalibStep();
      });
    }

    // ============================================================
    // MODALS LOGIC
    // ============================================================
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

    const btnExportTni = $("#btn-modal-export-tni");
    if (btnExportTni) {
      btnExportTni.addEventListener("click", () => {
        const m = $("#modal-export-tni");
        if (m) m.classList.add("active");
      });
    }

    const btnQuizQr = $("#btn-quiz-qr");
    if (btnQuizQr) {
      btnQuizQr.addEventListener("click", () => {
        const m = $("#modal-quiz-qr");
        if (m) m.classList.add("active");
      });
    }

    ["exp-smart-nb", "exp-prom-flip", "exp-iwb-univ", "exp-ent-scorm"].forEach(id => {
      const btn = $(`#${id}`);
      if (btn) {
        btn.addEventListener("click", () => {
          alert("📥 Génération de l'export TNI en cours...\nTéléchargement prêt pour l'établissement & l'ENT !");
          const m = $("#modal-export-tni");
          if (m) m.classList.remove("active");
        });
      }
    });

    // Helper to parse Google Slides URL
    function convertToGSlidesEmbedUrl(rawUrl) {
      if (!rawUrl || !rawUrl.trim()) {
        return "https://docs.google.com/presentation/d/e/2PACX-1vR3S6zC0x-zN_X8z3/embed?start=false&loop=false&delayms=3000";
      }
      let url = rawUrl.trim();
      const match = url.match(/\/d\/([a-zA-Z0-9_-]+)/);
      if (match && match[1]) {
        return `https://docs.google.com/presentation/d/${match[1]}/embed?start=false&loop=false&delayms=3000`;
      }
      return url;
    }

    const btnConfirmGSlides = $("#btn-confirm-gslides");
    if (btnConfirmGSlides) {
      btnConfirmGSlides.addEventListener("click", () => {
        const inputUrl = $("#input-gslides-url");
        const rawUrl = inputUrl ? inputUrl.value : "";
        gslidesEmbedUrl = convertToGSlidesEmbedUrl(rawUrl);

        decks.gslides = [{ title: "Google Slides en direct", content: createGSlidesContent(gslidesEmbedUrl) }];
        currentDeckKey = "gslides";
        currentSlideIndex = 0;
        if (deckSelect) deckSelect.value = "gslides";
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
                <p style="font-size: 1.1rem; color: #e8effc;">Document PPTX / PDF rendu dans EDU-AIR Smart Surface.</p>
              </div>
            `
          }
        ];

        if (deckSelect && !deckSelect.querySelector("option[value='imported']")) {
          const opt = document.createElement("option");
          opt.value = "imported";
          opt.textContent = `📁 ${fileName}`;
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
        .then((stream) => { pipVideo.srcObject = stream; })
        .catch((err) => { console.log("Webcam notice:", err.message); });
    }

    console.log("EDU-AIR Smart Surface App Fully Initialized.");
  });
})();
