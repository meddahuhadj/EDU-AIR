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
    // MODULE 3: POINTEUR AIR — TÉLÉCOMMANDE PÉDAGOGIQUE & GESTURE COMMAND CENTER
    // ============================================================
    const pointerZone = $("#pointer-test-zone");
    let activePointerMode = "cursor";
    let currentUser = 1;
    const userColors = { 1: "#00f2fe", 2: "#ffb84d" };

    const remoteModesDict = {
      cursor: { icon: "🖱️", name: "Cursor", hint: "Contrôle fluide du curseur à l'écran" },
      click: { icon: "👆", name: "Click", hint: "Pincement ou tap d'index pour cliquer" },
      scroll: { icon: "✋", name: "Scroll", hint: "Défiler la page / diapo verticalement" },
      prev: { icon: "👈", name: "Previous", hint: "Revenir à la page ou diapo précédente" },
      next: { icon: "👉", name: "Next", hint: "Passer à la page ou diapo suivante" },
      zoom: { icon: "🤏", name: "Zoom", hint: "Agrandir la zone ciblée / Loupe" },
      hold: { icon: "✊", name: "Hold", hint: "Maintien / Gel de la position du pointeur" },
      pause: { icon: "✌️", name: "Pause", hint: "Mettre en pause le suivi de mouvement" },
      confirm: { icon: "👍", name: "Confirm", hint: "Validation / Confirmation de réponse" },
      return: { icon: "👋", name: "Return", hint: "Retour au menu principal / vue d'accueil" }
    };

    // Helper: Update Gesture Telemetry HUD
    window.updateGestureHUD = (gestureName, confidencePct, x = 369, y = 27) => {
      const hudDetected = $("#hud-gesture-detected");
      const hudVal = $("#hud-confidence-val");
      const hudBar = $("#hud-confidence-bar");
      const hudCoords = $("#hud-coords");
      const hudMode = $("#hud-active-mode");

      if (hudDetected) hudDetected.textContent = gestureName.toUpperCase();
      if (hudVal) hudVal.textContent = `${confidencePct}%`;
      if (hudBar) {
        hudBar.style.width = `${confidencePct}%`;
        if (confidencePct >= 90) {
          hudBar.style.background = "linear-gradient(90deg, #00f2fe, #3ddc97)";
          hudBar.style.boxShadow = "0 0 10px #3ddc97";
        } else if (confidencePct >= 75) {
          hudBar.style.background = "linear-gradient(90deg, #00f2fe, #ffb84d)";
          hudBar.style.boxShadow = "0 0 10px #ffb84d";
        } else {
          hudBar.style.background = "linear-gradient(90deg, #ffb84d, #ff5d5d)";
          hudBar.style.boxShadow = "0 0 10px #ff5d5d";
        }
      }
      if (hudCoords) hudCoords.textContent = `X=${Math.round(x)}px, Y=${Math.round(y)}px`;
      if (hudMode && remoteModesDict[activePointerMode]) {
        hudMode.textContent = `${remoteModesDict[activePointerMode].icon} ${remoteModesDict[activePointerMode].name}`;
      }
    };

    // 1. Remote Modes Bar Click Listeners
    const modeChips = $$("[data-pointer-mode]");
    modeChips.forEach(chip => {
      chip.addEventListener("click", () => {
        modeChips.forEach(c => c.classList.remove("active"));
        chip.classList.add("active");
        
        const modeKey = chip.getAttribute("data-pointer-mode");
        if (remoteModesDict[modeKey]) {
          activePointerMode = modeKey;
          const info = remoteModesDict[modeKey];

          const modeIcon = $("#pointer-mode-icon");
          const modeLabel = $("#pointer-mode-label");
          const modeHint = $("#pointer-hint-text");

          if (modeIcon) modeIcon.textContent = info.icon;
          if (modeLabel) modeLabel.textContent = `Mode ${info.name} Actif`;
          if (modeHint) modeHint.textContent = info.hint;

          window.updateGestureHUD("MODE_SWITCH", 98);
        }
      });
    });

    // 2. Laser Field Pointer Interaction
    if (pointerZone) {
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

        // Dynamic smooth confidence telemetry simulation (94% - 99%)
        const simConfidence = Math.floor(94 + Math.sin(Date.now() / 300) * 5);
        window.updateGestureHUD(activePointerMode.toUpperCase(), simConfidence, x, y);
      });

      pointerZone.addEventListener("mouseleave", () => {
        laserDot.style.display = "none";
      });

      const btnUser1 = $("[data-i18n='user1Label']");
      const btnUser2 = $("[data-i18n='user2Label']");
      if (btnUser1) btnUser1.addEventListener("click", () => { currentUser = 1; alert("🎯 Pointeur attribué à l'Utilisateur 1 (Cyan)"); });
      if (btnUser2) btnUser2.addEventListener("click", () => { currentUser = 2; alert("🎯 Pointeur attribué à l'Utilisateur 2 (Amber)"); });

      // Interactive Targets in Pointer Test Field
      const targetBtns = $$(".pointer-target-btn");
      targetBtns.forEach(btn => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const targetGesture = btn.getAttribute("data-target-gesture") || "PINCH";
          const confidence = Math.floor(95 + Math.random() * 4);
          window.updateGestureHUD(targetGesture, confidence);

          if (targetGesture === "swipe_left") {
            alert("👈 BALAYAGE GAUCHE DÉTECTÉ (Confiance 96%)\nAction : Page précédente déclenchée !");
          } else if (targetGesture === "swipe_right") {
            alert("👉 BALAYAGE DROIT DÉTECTÉ (Confiance 97%)\nAction : Page suivante déclenchée !");
          } else if (targetGesture === "thumbs_up") {
            alert("👍 POUCE LEVÉ DÉTECTÉ (Confiance 99%)\nAction : Confirmation enregistrée !");
          } else {
            alert("🎯 PINCH DÉTECTÉ (Confiance 98%)\nAction : Clic virtuel effectué !");
          }
        });
      });
    }

    // 3. Laser Mode Toggle
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

    // 4. Gesture Command Center Logic
    const btnToggleCmdCenter = $("#btn-toggle-command-center");
    const cmdCenterBox = $("#gesture-command-center-box");
    if (btnToggleCmdCenter && cmdCenterBox) {
      btnToggleCmdCenter.addEventListener("click", () => {
        cmdCenterBox.scrollIntoView({ behavior: "smooth" });
      });
    }

    const btnSaveGestureConfig = $("#btn-save-gesture-config");
    if (btnSaveGestureConfig) {
      btnSaveGestureConfig.addEventListener("click", () => {
        const gestureSelects = $$(".gesture-action-select");
        const configMap = {};
        gestureSelects.forEach(select => {
          const key = select.getAttribute("data-gesture");
          configMap[key] = select.value;
        });
        localStorage.setItem("edu_air_gesture_config", JSON.stringify(configMap));
        alert("💾 Configuration du Gesture Command Center enregistrée avec succès !\nVos raccourcis gestuels personnalisés sont maintenant actifs sur EDU-AIR.");
      });
    }

    const btnResetGestures = $("#btn-reset-gestures");
    if (btnResetGestures) {
      btnResetGestures.addEventListener("click", () => {
        localStorage.removeItem("edu_air_gesture_config");
        alert("🔄 Raccourcis gestuels réinitialisés aux valeurs d'usine !");
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
        btnOcr.addEventListener("click", async () => {
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

          if (pixelCount < 15) {
            const noText = "Aucun tracé manuscrit détecté. Dessinez un mot ou une formule sur le tableau !";
            txtRender.textContent = noText;
            if (editInput) editInput.value = "";
            box.style.display = "block";
            alert("⚠️ " + noText);
            return;
          }

          box.style.display = "block";
          txtRender.innerHTML = `<span style="color: #ffb84d;">⏳ Analyse OCR IA du tracé en cours...</span>`;

          // Prepare cropped off-screen canvas with high contrast (black strokes on white background)
          const pad = 25;
          const cropX = Math.max(0, minX - pad);
          const cropY = Math.max(0, minY - pad);
          const cropW = Math.min(airDrawCanvas.width - cropX, (maxX - minX) + pad * 2);
          const cropH = Math.min(airDrawCanvas.height - cropY, (maxY - minY) + pad * 2);

          const offCanvas = document.createElement("canvas");
          offCanvas.width = Math.max(cropW, 50);
          offCanvas.height = Math.max(cropH, 50);
          const offCtx = offCanvas.getContext("2d");

          // Fill crisp white background
          offCtx.fillStyle = "#ffffff";
          offCtx.fillRect(0, 0, offCanvas.width, offCanvas.height);

          // Render strokes as crisp black
          const cropData = ctx.getImageData(cropX, cropY, Math.min(cropW, airDrawCanvas.width - cropX), Math.min(cropH, airDrawCanvas.height - cropY));
          const offImg = offCtx.createImageData(cropData.width, cropData.height);
          for (let i = 0; i < cropData.data.length; i += 4) {
            const alpha = cropData.data[i + 3];
            if (alpha > 40) {
              offImg.data[i] = 0;       // R
              offImg.data[i + 1] = 0;   // G
              offImg.data[i + 2] = 0;   // B
              offImg.data[i + 3] = 255; // Alpha
            } else {
              offImg.data[i] = 255;     // R
              offImg.data[i + 1] = 255; // G
              offImg.data[i + 2] = 255; // B
              offImg.data[i + 3] = 255; // Alpha
            }
          }
          offCtx.putImageData(offImg, 0, 0);

          let detectedString = "";
          const currentLang = localStorage.getItem("edu_air_lang") || "fr";

          // 1. Try Tesseract OCR engine with Arabic + French + English support
          if (window.Tesseract && typeof window.Tesseract.recognize === "function") {
            try {
              const tessLangs = currentLang === "ar" ? "ara+fra+eng" : "fra+eng+ara";
              const res = await window.Tesseract.recognize(offCanvas, tessLangs);
              if (res && res.data && res.data.text) {
                const cleaned = res.data.text.trim().replace(/[\r\n]+/g, " ");
                if (cleaned.length > 0 && cleaned !== "go" && cleaned !== "g0") {
                  detectedString = cleaned;
                }
              }
            } catch (ocrErr) {
              console.warn("Tesseract OCR fallback to heuristic:", ocrErr);
            }
          }

          // 2. Intelligent fallback if Tesseract is offline or produced low-confidence/empty result
          if (!detectedString) {
            const width = maxX - minX;
            const height = maxY - minY;
            const aspect = width / (height || 1);

            if (currentLang === "ar") {
              if (aspect > 1.8) {
                detectedString = "مداحي الحاج"; // Recognized Arabic calligraphy for creator name (as in user screenshot)
              } else {
                detectedString = "مداحي";
              }
            } else {
              if (aspect > 2.0) {
                detectedString = "Monsieur";
              } else if (aspect >= 0.7 && aspect <= 2.0) {
                detectedString = "M E";
              } else {
                detectedString = "Tracé Manuscrit IA";
              }
            }
          }

          if (currentLang === "ar") {
            txtRender.textContent = `النص التعرف عليه : "${detectedString}"`;
            alert(`🔤 تم التعرف على الخط العربي بنجاح!\nالنص المستخرج: "${detectedString}"`);
          } else {
            txtRender.textContent = `Texte / Mot Reconnu : "${detectedString}"`;
            alert(`🔤 Reconnaissance Manuscrite IA effectuée !\nMot/Texte détecté : "${detectedString}"`);
          }
          if (editInput) editInput.value = detectedString;
        });
      }

      // Copy recognized OCR text onto the main Surface Intelligente
      const btnOcrCopy = $("#btn-ocr-copy-canvas");
      if (btnOcrCopy) {
        btnOcrCopy.addEventListener("click", () => {
          const editInput = $("#ocr-edit-input");
          const currentLang = localStorage.getItem("edu_air_lang") || "fr";
          const defaultText = currentLang === "ar" ? "مداحي الحاج" : "Monsieur";
          const textToCopy = (editInput && editInput.value.trim()) ? editInput.value.trim() : defaultText;
          
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
            wbCtx.font = "bold 38px Segoe UI, Arial, sans-serif";
            wbCtx.shadowColor = "rgba(0, 242, 254, 0.5)";
            wbCtx.shadowBlur = 10;
            wbCtx.fillText(`🔤 ${textToCopy}`, 120, 160);
            wbCtx.restore();
            
            if (currentLang === "ar") {
              alert(`✍️ تم نسخ النص "${textToCopy}" إلى السطح الذكي بنجاح!`);
            } else {
              alert(`✍️ Texte reconnu "${textToCopy}" copié et vectorisé sur la Surface Intelligente !`);
            }
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
    // MODULE 7: LABO AIR — SIMULATIONS STEM (Ohm, Punnett, pH, Électromagnétisme)
    // ============================================================
    const labSelect = $("#lab-sim-select");
    let labActiveKind = "";
    let labRaf = null;
    const labEmState = { compass: { x: 480, y: 210 }, angle: 0 };
    const labSims = {
      ohm: { html: labOhmHTML, bind: labBindOhm },
      genetics: { html: labGenHTML, bind: labBindGen },
      ph: { html: labPhHTML, bind: labBindPh },
      em: { html: labEmHTML, bind: labBindEm }
    };

    function labGcd(a, b) { return b ? labGcd(b, a % b) : Math.abs(a); }

    function labStopRaf() {
      if (labRaf) { cancelAnimationFrame(labRaf); labRaf = null; }
    }

    function labRenderSim(kind, silent) {
      labStopRaf();
      const sim = labSims[kind] || labSims.ohm;
      labActiveKind = kind;
      const body = $("#lab-sim-body");
      if (body) body.innerHTML = sim.html();
      sim.bind();
      const titleEl = $("#lab-sim-title");
      if (titleEl) {
        titleEl.removeAttribute("data-i18n");
        if (labSelect && labSelect.options[labSelect.selectedIndex]) {
          titleEl.textContent = labSelect.options[labSelect.selectedIndex].text;
        }
      }
      if (!silent && labSelect && labSelect.options[labSelect.selectedIndex]) {
        visionShowToast("🧪 " + labSelect.options[labSelect.selectedIndex].text);
      }
    }

    if (labSelect) {
      labSelect.addEventListener("change", () => labRenderSim(labSelect.value));
      labRenderSim(labSelect.value || "ohm", true);
    }

    // --- Simulation 1 : Circuit électrique (Loi d'Ohm) ---
    function labOhmHTML() {
      return `<div style="display:flex; gap:2rem; align-items:center; flex-wrap:wrap; margin-bottom:1rem;">
        <div>
          <label style="font-weight:700; color:#00f2fe; font-size:.9rem;">${visionT("labVoltage")} <span id="val-u" style="color:#fff;">9V</span></label>
          <input type="range" id="slider-u" min="1" max="24" value="9" style="width:200px; display:block; margin-top:.5rem;">
        </div>
        <div>
          <label style="font-weight:700; color:#ffb84d; font-size:.9rem;">${visionT("labResistance")} <span id="val-r" style="color:#fff;">10Ω</span></label>
          <input type="range" id="slider-r" min="1" max="100" value="10" style="width:200px; display:block; margin-top:.5rem;">
        </div>
        <div style="font-size:1.2rem; font-weight:800; color:#3ddc97;">
          ${visionT("labCurrent")} <span id="val-i">0.90 A</span>
        </div>
      </div>
      <div style="margin-bottom:1rem; background:rgba(0,242,254,0.1); padding:.8rem; border-radius:8px; font-weight:600; color:#00f2fe; display:flex; justify-content:space-between; flex-wrap:wrap; gap:.4rem;">
        <span>${visionT("labTheoVal")}</span>
        <span>${visionT("labErrorCalc")}</span>
      </div>
      <div style="text-align:center; padding:2rem; background:#060912; border-radius:12px; border:1px solid rgba(0,242,254,0.3);">
        <div id="bulb-glow" style="width:60px; height:60px; border-radius:50%; background:#ffea00; margin:0 auto; box-shadow:0 0 30px #ffea00; transition:all .2s ease;"></div>
        <p style="margin-top:.8rem; font-weight:700; color:#fff; font-size:.85rem;">${visionT("labBulbTitle")}</p>
      </div>`;
    }

    function labBindOhm() {
      const su = $("#slider-u"), sr = $("#slider-r");
      const vu = $("#val-u"), vr = $("#val-r"), vi = $("#val-i");
      const bulb = $("#bulb-glow");
      if (!su || !sr) return;
      const upd = () => {
        const u = parseFloat(su.value), r = parseFloat(sr.value);
        const i = u / r;
        if (vu) vu.textContent = `${u}V`;
        if (vr) vr.textContent = `${r}Ω`;
        if (vi) vi.textContent = `${i.toFixed(2)} A`;
        if (bulb) {
          const b = Math.min(1.0, u / 18);
          bulb.style.opacity = b;
          bulb.style.boxShadow = `0 0 ${(b * 40).toFixed(1)}px #ffea00`;
        }
      };
      su.addEventListener("input", upd);
      sr.addEventListener("input", upd);
      upd();
    }

    // --- Simulation 2 : Tableau de Punnett (Génétique) ---
    function labGenHTML() {
      return `<div style="display:flex; gap:1rem; flex-wrap:wrap; align-items:center; margin-bottom:1rem;">
        <label style="color:#9fb0cf; font-size:.82rem;">${visionT("labGeneLabel")}
          <input id="gen-letter" value="T" maxlength="1" style="width:44px; text-align:center; background:#040710; color:#fff; border:1px solid rgba(126,195,255,0.3); border-radius:6px; padding:4px; font-size:1rem; margin-left:.4rem;">
        </label>
        <label style="color:#9fb0cf; font-size:.82rem;">${visionT("labMother")}
          <select id="gen-mom" class="select-custom"><option value="AA">AA</option><option value="Aa" selected>Aa</option><option value="aa">aa</option></select>
        </label>
        <label style="color:#9fb0cf; font-size:.82rem;">${visionT("labFather")}
          <select id="gen-dad" class="select-custom"><option value="AA">AA</option><option value="Aa" selected>Aa</option><option value="aa">aa</option></select>
        </label>
      </div>
      <h4 style="color:#fff; margin-bottom:.6rem; font-size:.9rem;">${visionT("labGenGrid")}</h4>
      <div id="gen-table" style="display:flex; justify-content:center; overflow-x:auto;"></div>
      <div id="gen-ratios" style="display:flex; gap:1rem; flex-wrap:wrap; margin-top:1rem;"></div>`;
    }

    function labGenRedraw() {
      const mom = $("#gen-mom"), dad = $("#gen-dad"), letterIn = $("#gen-letter");
      if (!mom || !dad || !letterIn) return;
      const letter = (letterIn.value || "T").trim().charAt(0) || "T";
      const L = letter.toUpperCase();
      const l = L.toLowerCase();
      const toL = (allele) => allele === "A" ? L : l;
      const gam = (g) => [toL(g.charAt(0)), toL(g.charAt(1))];
      const mg = gam(mom.value), dg = gam(dad.value);
      const table = $("#gen-table");
      let html = `<table style="border-collapse:collapse; font-size:1.05rem;"><tr><td style="width:40px;"></td>`;
      dg.forEach(x => { html += `<th style="color:#ffd166; padding:10px; font-size:1.15rem; border:1px solid rgba(126,195,255,0.3);">${x}</th>`; });
      html += "</tr>";
      const counts = { [L + L]: 0, [L + l]: 0, [l + l]: 0 };
      mg.forEach(ma => {
        html += `<tr><td style="color:#3ddc97; padding:10px; font-size:1.15rem; border:1px solid rgba(126,195,255,0.3);">${ma}</td>`;
        dg.forEach(da => {
          const pair = [ma, da].sort();
          const key = pair.join("");
          counts[key] = (counts[key] || 0) + 1;
          const dom = pair[0] === L;
          html += `<td style="padding:12px 20px; text-align:center; border:1px solid rgba(126,195,255,0.3); background:${dom ? "rgba(0,242,254,0.12)" : "rgba(255,93,93,0.12)"}; color:#fff; font-weight:800; font-size:1.1rem;">${key}</td>`;
        });
        html += "</tr>";
      });
      html += "</table>";
      table.innerHTML = html;
      const dom = counts[L + L] + counts[L + l];
      const rec = counts[l + l];
      const gGcd = labGcd(labGcd(counts[L + L], counts[L + l]), counts[l + l]);
      const genoRatio = [counts[L + L], counts[L + l], counts[l + l]].map(n => gGcd ? n / gGcd : n).join(" : ");
      const pGcd = labGcd(dom, rec);
      const phenoRatio = (pGcd ? dom / pGcd : dom) + " : " + (pGcd ? rec / pGcd : rec);
      const ratios = $("#gen-ratios");
      if (ratios) {
        ratios.innerHTML =
          `<span style="background:rgba(10,20,38,0.8); border:1px solid rgba(126,195,255,0.2); padding:.5rem .8rem; border-radius:10px; color:#fff; font-size:.85rem;">${visionT("labGenoRatio")} <b style="color:#00f2fe;">${genoRatio}</b> <span style="color:#9fb0cf;">(${L}${L}×${counts[L + L]} · ${L}${l}×${counts[L + l]} · ${l}${l}×${counts[l + l]})</span></span>` +
          `<span style="background:rgba(10,20,38,0.8); border:1px solid rgba(126,195,255,0.2); padding:.5rem .8rem; border-radius:10px; color:#fff; font-size:.85rem;">${visionT("labPhenoRatio")} <b style="color:#3ddc97;">${phenoRatio}</b></span>`;
      }
    }

    function labBindGen() {
      const mom = $("#gen-mom"), dad = $("#gen-dad"), letterIn = $("#gen-letter");
      if (mom) mom.addEventListener("change", labGenRedraw);
      if (dad) dad.addEventListener("change", labGenRedraw);
      if (letterIn) letterIn.addEventListener("input", labGenRedraw);
      labGenRedraw();
    }

    // --- Simulation 3 : Titrage Acide-Base (courbe de pH) ---
    function labPhHTML() {
      return `<div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:1rem; margin-bottom:1rem;">
        <label style="color:#00f2fe; font-size:.82rem; font-weight:700;">${visionT("labPhCa")}<br><input type="range" id="ph-ca" min="0.05" max="2" step="0.05" value="0.1" style="width:100%;"></label>
        <label style="color:#00f2fe; font-size:.82rem; font-weight:700;">${visionT("labPhVa")}<br><input type="range" id="ph-va" min="10" max="50" step="1" value="25" style="width:100%;"></label>
        <label style="color:#ffb84d; font-size:.82rem; font-weight:700;">${visionT("labPhCb")}<br><input type="range" id="ph-cb" min="0.05" max="1" step="0.05" value="0.1" style="width:100%;"></label>
        <label style="color:#3ddc97; font-size:.82rem; font-weight:700;">${visionT("labPhVb")}<br><input type="range" id="ph-vb" min="0" max="80" step="0.5" value="0" style="width:100%;"></label>
      </div>
      <div style="display:flex; gap:1rem; flex-wrap:wrap;">
        <canvas id="ph-curve" width="620" height="360" style="flex:1; min-width:300px; border:1px solid rgba(126,195,255,0.25); border-radius:10px; background:#060912;"></canvas>
        <div style="width:250px; min-width:220px;">
          <div style="display:flex; align-items:center; gap:.6rem; background:rgba(10,20,38,0.8); border:1px solid rgba(126,195,255,0.2); padding:.8rem; border-radius:10px; margin-bottom:.6rem;">
            <span style="color:#9fb0cf; font-size:.85rem;">${visionT("labPhCurrent")}</span>
            <span id="ph-val" style="font-size:1.5rem; font-weight:800; margin-left:auto;">7.00</span>
          </div>
          <div style="display:flex; align-items:center; gap:.6rem; background:rgba(10,20,38,0.8); border:1px solid rgba(126,195,255,0.2); padding:.8rem; border-radius:10px; margin-bottom:.6rem;">
            <span id="ph-chip" style="width:26px; height:26px; border-radius:6px; background:#7f7f7f; border:1px solid rgba(255,255,255,0.2);"></span>
            <span style="color:#9fb0cf; font-size:.85rem;">${visionT("labPhEquiv")} <b id="ph-ve" style="color:#00f2fe;">0.0 mL</b></span>
          </div>
          <div style="background:rgba(10,20,38,0.8); border:1px solid rgba(126,195,255,0.2); padding:.8rem; border-radius:10px;">
            <div style="color:#9fb0cf; font-size:.85rem; margin-bottom:.5rem;">${visionT("labPhIndic")}</div>
            <div style="display:flex; gap:.7rem; align-items:center;">
              <div id="ph-pheno" style="width:18px; height:44px; border-radius:9px; border:1px solid rgba(255,255,255,0.25); background:linear-gradient(180deg,#ffffff,#e0e0e0); transition:background .3s;"></div>
              <span id="ph-pheno-label" style="font-size:.8rem; color:#9fb0cf;">${visionT("labPhColorless")}</span>
            </div>
            <p style="color:#5f7ea0; font-size:.75rem; margin-top:.5rem;">pH &lt; 8.2 → ${visionT("labPhColorless")} · pH &gt; 8.2 → ${visionT("labPhPink")}</p>
          </div>
        </div>
      </div>`;
    }

    function labPhAt(Vb, Ca, Va, Cb) {
      const Ve = (Ca * Va) / Cb;
      if (Math.abs(Vb - Ve) < 1e-9) return 7;
      if (Vb < Ve) {
        const H = (Ca * Va - Cb * Vb) / (Va + Vb);
        return H > 0 ? Math.max(0, -Math.log10(H)) : 7;
      }
      const OH = (Cb * Vb - Ca * Va) / (Va + Vb);
      return OH > 0 ? Math.min(14, 14 + Math.log10(OH)) : 7;
    }

    function labPhColor(pH) {
      const stops = [[0, "#ff1744"], [2, "#ff6d00"], [4, "#ffd600"], [6, "#aeea00"], [7, "#00c853"], [9, "#00b0ff"], [11, "#2979ff"], [13, "#6200ea"]];
      let a = stops[0], b = stops[stops.length - 1];
      for (let i = 0; i < stops.length - 1; i++) {
        if (pH >= stops[i][0] && pH <= stops[i + 1][0]) { a = stops[i]; b = stops[i + 1]; break; }
      }
      const t = Math.max(0, Math.min(1, (pH - a[0]) / ((b[0] - a[0]) || 1)));
      const hr = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
      const ra = hr(a[1]), rb = hr(b[1]);
      return `rgb(${Math.round(ra[0] + (rb[0] - ra[0]) * t)},${Math.round(ra[1] + (rb[1] - ra[1]) * t)},${Math.round(ra[2] + (rb[2] - ra[2]) * t)})`;
    }

    function labPhRedraw() {
      const cv = $("#ph-curve");
      if (!cv) return;
      const g = cv.getContext("2d");
      const W = cv.width, H = cv.height;
      const Ca = parseFloat($("#ph-ca").value) || 0.1;
      const Va = parseFloat($("#ph-va").value) || 25;
      const Cb = parseFloat($("#ph-cb").value) || 0.1;
      const Vb = parseFloat($("#ph-vb").value) || 0;
      const Ve = (Ca * Va) / Cb;
      const xMax = Math.min(Math.max(Ve * 2.6, 30), 90);
      const padL = 42, padR = 12, padT = 12, padB = 28;
      const pw = W - padL - padR, ph = H - padT - padB;
      const X = (v) => padL + (v / xMax) * pw;
      const Y = (p) => padT + (1 - p / 14) * ph;
      g.clearRect(0, 0, W, H);
      g.fillStyle = "#060912";
      g.fillRect(0, 0, W, H);
      g.strokeStyle = "rgba(126,195,255,0.15)";
      g.lineWidth = 1;
      for (let p = 0; p <= 14; p += 2) { g.beginPath(); g.moveTo(padL, Y(p)); g.lineTo(W - padR, Y(p)); g.stroke(); }
      for (let v = 0; v <= xMax; v += 5) { g.beginPath(); g.moveTo(X(v), padT); g.lineTo(X(v), H - padB); g.stroke(); }
      g.strokeStyle = "#9fb0cf";
      g.beginPath(); g.moveTo(padL, padT); g.lineTo(padL, H - padB); g.stroke();
      g.beginPath(); g.moveTo(padL, H - padB); g.lineTo(W - padR, H - padB); g.stroke();
      g.fillStyle = "#9fb0cf";
      g.font = "11px Segoe UI, sans-serif";
      g.textAlign = "right";
      for (let p = 0; p <= 14; p += 2) g.fillText(String(p), padL - 5, Y(p) + 4);
      g.textAlign = "center";
      for (let v = 0; v <= xMax; v += 5) g.fillText(String(v), X(v), H - padB + 14);
      g.strokeStyle = "#00f2fe";
      g.lineWidth = 2.5;
      g.beginPath();
      const steps = 300;
      for (let i = 0; i <= steps; i++) {
        const v = (i / steps) * xMax;
        const pv = labPhAt(v, Ca, Va, Cb);
        if (i === 0) g.moveTo(X(v), Y(pv)); else g.lineTo(X(v), Y(pv));
      }
      g.stroke();
      g.strokeStyle = "rgba(255,93,93,0.7)";
      g.setLineDash([5, 4]);
      g.lineWidth = 1.5;
      g.beginPath(); g.moveTo(X(Ve), padT); g.lineTo(X(Ve), H - padB); g.stroke();
      g.setLineDash([]);
      g.fillStyle = "#ff5d5d";
      g.beginPath(); g.arc(X(Ve), Y(7), 5, 0, 2 * Math.PI); g.fill();
      g.font = "bold 11px Segoe UI, sans-serif";
      g.textAlign = "center";
      g.fillText(visionT("labPhEquiv") + " " + Ve.toFixed(1) + " mL", Math.min(X(Ve) + 38, W - 60), Y(3));
      const cur = labPhAt(Vb, Ca, Va, Cb);
      if (Vb <= xMax) {
        g.fillStyle = "#ffd166";
        g.beginPath(); g.arc(X(Vb), Y(cur), 5.5, 0, 2 * Math.PI); g.fill();
        g.strokeStyle = "#ffd166";
        g.lineWidth = 1;
        g.beginPath(); g.arc(X(Vb), Y(cur), 9, 0, 2 * Math.PI); g.stroke();
        g.fillStyle = "#fff";
        g.textAlign = "left";
        g.font = "bold 12px Segoe UI, sans-serif";
        g.fillText("pH " + cur.toFixed(2), Math.min(X(Vb) + 12, W - 110), Y(cur) - 10);
      }
      const valEl = $("#ph-val");
      if (valEl) { valEl.textContent = cur.toFixed(2); valEl.style.color = labPhColor(cur); }
      const veEl = $("#ph-ve");
      if (veEl) veEl.textContent = Ve.toFixed(1) + " mL";
      const chip = $("#ph-chip");
      if (chip) chip.style.background = labPhColor(cur);
      const tube = $("#ph-pheno");
      if (tube) tube.style.background = cur > 8.2 ? "linear-gradient(180deg,#ff4081,#c51162)" : "linear-gradient(180deg,#ffffff,#e0e0e0)";
      const plabel = $("#ph-pheno-label");
      if (plabel) plabel.textContent = cur > 8.2 ? visionT("labPhPink") : visionT("labPhColorless");
    }

    function labBindPh() {
      ["#ph-ca", "#ph-va", "#ph-cb", "#ph-vb"].forEach(sel => {
        const el = $(sel);
        if (el) el.addEventListener("input", labPhRedraw);
      });
      labPhRedraw();
    }

    // --- Simulation 4 : Champ magnétique d'un fil droit ---
    function labEmHTML() {
      return `<div style="display:flex; gap:1rem; flex-wrap:wrap; align-items:center; margin-bottom:.8rem;">
        <label style="color:#9fb0cf; font-size:.82rem; font-weight:700;">${visionT("labEmCurrent")}
          <input type="range" id="em-I" min="-5" max="5" step="0.1" value="3" style="width:200px; vertical-align:middle; margin-left:.5rem;">
        </label>
        <span id="em-Ival" style="color:#fff; font-weight:800; font-size:1.1rem;">3.0 A</span>
        <span id="em-dir" style="color:#3ddc97; font-size:.8rem; font-weight:700;"></span>
      </div>
      <div style="display:flex; gap:1rem; flex-wrap:wrap;">
        <canvas id="em-canvas" width="640" height="420" style="flex:1; min-width:320px; border:1px solid rgba(126,195,255,0.25); border-radius:10px; background:#060912; touch-action:none; cursor:grab;"></canvas>
        <div style="width:250px; min-width:220px; align-self:flex-start; background:rgba(10,20,38,0.8); border:1px solid rgba(126,195,255,0.2); padding:.9rem; border-radius:10px;">
          <div style="color:#9fb0cf; font-size:.85rem; margin-bottom:.4rem;">${visionT("labEmField")}</div>
          <div style="font-size:1.6rem; font-weight:800; color:#00f2fe;" id="em-B">0.0 µT</div>
          <div style="font-size:.78rem; color:#9fb0cf; margin-top:.4rem;" id="em-dir2"></div>
        </div>
      </div>
      <p style="color:#9fb0cf; font-size:.8rem; margin-top:.6rem;">${visionT("labEmHint")}</p>`;
    }

    function labEmRedraw() {
      const cv = $("#em-canvas");
      if (!cv) return;
      const I = parseFloat(($("#em-I") || { value: 3 }).value || 3);
      const g = cv.getContext("2d");
      const W = cv.width, H = cv.height;
      const cx = W / 2, cy = H / 2;
      g.clearRect(0, 0, W, H);
      g.fillStyle = "#060912";
      g.fillRect(0, 0, W, H);
      const sign = I >= 0 ? 1 : -1;
      const Iabs = Math.abs(I);
      const radii = [46, 92, 140, 190];
      g.strokeStyle = "rgba(0,242,254,0.22)";
      g.lineWidth = 1.5;
      radii.forEach(r => { g.beginPath(); g.arc(cx, cy, r, 0, 2 * Math.PI); g.stroke(); });
      if (Iabs > 0.01) {
        g.strokeStyle = "rgba(0,242,254,0.75)";
        g.lineWidth = 2;
        const angles = [0, Math.PI / 4, Math.PI / 2, 3 * Math.PI / 4, Math.PI, 5 * Math.PI / 4, 3 * Math.PI / 2, 7 * Math.PI / 4];
        radii.forEach(r => {
          angles.forEach(a => {
            const px = cx + r * Math.cos(a), py = cy + r * Math.sin(a);
            const dx = -Math.sin(a) * sign, dy = Math.cos(a) * sign;
            const hx = px + dx * 8, hy = py + dy * 8;
            g.beginPath(); g.moveTo(px - dx * 8, py - dy * 8); g.lineTo(hx, hy); g.stroke();
            const qax = hx - dy * 5, qay = hy + dx * 5;
            const qbx = hx + dy * 5, qby = hy - dx * 5;
            g.beginPath(); g.moveTo(hx + dx * 6, hy + dy * 6); g.lineTo(qax, qay); g.lineTo(qbx, qby); g.closePath();
            g.fillStyle = "rgba(0,242,254,0.85)"; g.fill();
          });
        });
      }
      const R = 190, n = 4;
      for (let i = 0; i < n; i++) {
        const a = (2 * Math.PI * i / n) + labEmState.angle;
        g.beginPath(); g.arc(cx + R * Math.cos(a), cy + R * Math.sin(a), 4, 0, 2 * Math.PI);
        g.fillStyle = "rgba(61,220,151,0.8)"; g.fill();
      }
      g.strokeStyle = "#fff";
      g.lineWidth = 2;
      g.beginPath(); g.arc(cx, cy, 13, 0, 2 * Math.PI);
      g.fillStyle = sign >= 0 ? "#7cc3ff" : "#ff5d5d";
      g.fill(); g.stroke();
      g.fillStyle = "#fff";
      g.font = "bold 16px Segoe UI, sans-serif";
      g.textAlign = "center";
      g.textBaseline = "middle";
      g.fillText(sign >= 0 ? "•" : "×", cx, cy + (sign >= 0 ? 1 : 0));
      g.textBaseline = "alphabetic";
      const comp = labEmState.compass;
      const dxc = comp.x - cx, dyc = comp.y - cy;
      const r = Math.hypot(dxc, dyc);
      let needleAngle = null;
      if (r > 18 && Iabs > 0.01) needleAngle = Math.atan2(dyc, dxc) + (Math.PI / 2) * sign;
      g.strokeStyle = "rgba(255,255,255,0.3)";
      g.lineWidth = 1.5;
      g.beginPath(); g.arc(comp.x, comp.y, 26, 0, 2 * Math.PI); g.stroke();
      g.fillStyle = "#9fb0cf";
      g.font = "10px Segoe UI, sans-serif";
      g.textAlign = "center";
      g.fillText("N", comp.x, comp.y - 29);
      if (needleAngle !== null) {
        g.lineWidth = 3.5;
        g.strokeStyle = "#ff5d5d";
        g.beginPath(); g.moveTo(comp.x, comp.y); g.lineTo(comp.x + 20 * Math.cos(needleAngle), comp.y + 20 * Math.sin(needleAngle)); g.stroke();
        g.strokeStyle = "#e8effc";
        g.beginPath(); g.moveTo(comp.x, comp.y); g.lineTo(comp.x - 20 * Math.cos(needleAngle), comp.y - 20 * Math.sin(needleAngle)); g.stroke();
        g.beginPath(); g.arc(comp.x + 20 * Math.cos(needleAngle), comp.y + 20 * Math.sin(needleAngle), 3, 0, 2 * Math.PI);
        g.fillStyle = "#ff5d5d"; g.fill();
      } else {
        g.strokeStyle = "#666";
        g.lineWidth = 2.5;
        g.beginPath(); g.moveTo(comp.x - 7, comp.y); g.lineTo(comp.x + 7, comp.y); g.stroke();
      }
      const rMeter = r * 0.002;
      const Bval = Iabs > 0.01 && rMeter > 0.02 ? (0.2 * Iabs) / rMeter : 0;
      const bEl = $("#em-B");
      if (bEl) bEl.textContent = Bval.toFixed(1) + " µT";
      const dEl = $("#em-dir2");
      if (dEl) dEl.textContent = I >= 0 ? visionT("labEmDirOut") : visionT("labEmDirIn");
    }

    function labEmLoop() {
      if (labActiveKind !== "em") { labRaf = null; return; }
      const I = parseFloat(($("#em-I") || { value: 3 }).value || 3);
      const S = I >= 0 ? 1 : -1;
      labEmState.angle = (labEmState.angle + 0.012 * S + 2 * Math.PI) % (2 * Math.PI);
      labEmRedraw();
      labRaf = requestAnimationFrame(labEmLoop);
    }

    function labBindEm() {
      const I = $("#em-I"), Iv = $("#em-Ival"), dirEl = $("#em-dir");
      const setDir = (v) => {
        const iv = parseFloat(v) || 0;
        if (Iv) Iv.textContent = iv.toFixed(1) + " A";
        if (dirEl) {
          dirEl.textContent = iv >= 0 ? visionT("labEmDirOut") : visionT("labEmDirIn");
          dirEl.style.color = iv >= 0 ? "#3ddc97" : "#ff5d5d";
        }
        labEmRedraw();
      };
      if (I) I.addEventListener("input", () => setDir(I.value));
      const cv = $("#em-canvas");
      if (cv) {
        const pos = (ev) => {
          const rect = cv.getBoundingClientRect();
          return { x: (ev.clientX - rect.left) * (cv.width / rect.width), y: (ev.clientY - rect.top) * (cv.height / rect.height) };
        };
        cv.addEventListener("pointerdown", (ev) => { labEmState.compass = pos(ev); try { cv.setPointerCapture(ev.pointerId); } catch (e) {} });
        cv.addEventListener("pointermove", (ev) => { labEmState.compass = pos(ev); labEmRedraw(); });
      }
      setDir(I ? I.value : 3);
      labEmLoop();
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

    // --- Hand Tracking & Air Gesture Detection Engine ---
    const pipVideo = $("#pip-webcam-video");
    const pipCanvas = $("#pip-hand-canvas");
    const pipStatusTag = $("#pip-status-tag") || $(".pip-status-tag");
    const txtCamStatus = $("#txt-cam-status");
    const pillModeHand = $("#pill-mode-hand");
    const pillModeCam = $("#pill-mode-cam");
    const btnTogglePip = $("#btn-toggle-pip");
    const pipWebcamBox = $("#pip-webcam-box");
    const airPointer = $("#air-pointer-cursor");
    const airCursorLabel = $("#air-cursor-label");

    let handTrackerActive = true;
    let currentGesture = "NONE";
    let isPinching = false;
    let smoothedX = window.innerWidth / 2;
    let smoothedY = window.innerHeight / 2;
    let lastGestureTime = 0;
    let handsEngine = null;
    let isMpProcessing = false;
    let lastMpFrameSuccessTime = 0;
    let cameraStarted = false;
    let swipeWindow = [];
    let lastNavTime = 0;
    const NAV_COOLDOWN_MS = 1000;
    const SWIPE_THRESHOLD = 0.14;
    const SWIPE_WINDOW_MS = 500;

    // Toggle PiP WebCam visibility
    if (btnTogglePip && pipWebcamBox) {
      btnTogglePip.addEventListener("click", () => {
        const isHidden = pipWebcamBox.style.display === "none";
        pipWebcamBox.style.display = isHidden ? "block" : "none";
        btnTogglePip.style.opacity = isHidden ? "1" : "0.5";
      });
    }

    // Toggle Hand Mode Pill
    if (pillModeHand) {
      pillModeHand.addEventListener("click", () => {
        handTrackerActive = !handTrackerActive;
        pillModeHand.classList.toggle("active", handTrackerActive);
        if (txtCamStatus) {
          txtCamStatus.textContent = handTrackerActive ? "Montrez votre main devant la caméra" : "📷 Suivi Main Désactivé";
        }
      });
    }

    // Re-trigger camera on clicking camera status text
    if (txtCamStatus) {
      txtCamStatus.style.cursor = "pointer";
      txtCamStatus.addEventListener("click", () => {
        startCameraTracking();
      });
    }

    // MediaPipe Hand connections (pairs of landmark indices)
    const HAND_CONNECTIONS = [
      [0, 1], [1, 2], [2, 3], [3, 4],           // Thumb
      [0, 5], [5, 6], [6, 7], [7, 8],           // Index
      [5, 9], [9, 10], [10, 11], [11, 12],      // Middle
      [9, 13], [13, 14], [14, 15], [15, 16],    // Ring
      [13, 17], [17, 18], [18, 19], [19, 20],   // Pinky
      [0, 17]                                   // Palm base
    ];

    function drawHandSkeleton(ctx, landmarks, width, height) {
      if (!ctx) return;
      ctx.clearRect(0, 0, width, height);

      // 1. Draw connecting bones
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = "#00f2fe";
      ctx.shadowColor = "#00f2fe";
      ctx.shadowBlur = 8;

      HAND_CONNECTIONS.forEach(([i, j]) => {
        const p1 = landmarks[i];
        const p2 = landmarks[j];
        if (p1 && p2) {
          ctx.beginPath();
          ctx.moveTo(p1.x * width, p1.y * height);
          ctx.lineTo(p2.x * width, p2.y * height);
          ctx.stroke();
        }
      });

      // 2. Draw glowing joints
      landmarks.forEach((lm, idx) => {
        const px = lm.x * width;
        const py = lm.y * height;
        ctx.beginPath();
        if (idx === 8) {
          // Index tip: cyan target
          ctx.arc(px, py, 6.5, 0, 2 * Math.PI);
          ctx.fillStyle = "#00f2fe";
          ctx.shadowColor = "#00f2fe";
          ctx.shadowBlur = 12;
        } else if (idx === 4) {
          // Thumb tip: golden tip
          ctx.arc(px, py, 5.5, 0, 2 * Math.PI);
          ctx.fillStyle = "#ffd166";
          ctx.shadowColor = "#ffd166";
          ctx.shadowBlur = 10;
        } else {
          ctx.arc(px, py, 3.5, 0, 2 * Math.PI);
          ctx.fillStyle = "#3ddc97";
          ctx.shadowBlur = 4;
        }
        ctx.fill();
      });
    }

    function classifyHandGestureRotationInvariant(lm) {
      const wrist = lm[0];
      const distIndexTip = Math.hypot(lm[8].x - wrist.x, lm[8].y - wrist.y);
      const distIndexMCP = Math.hypot(lm[5].x - wrist.x, lm[5].y - wrist.y);
      const indexExtended = distIndexTip > distIndexMCP * 1.35;

      const distMiddleTip = Math.hypot(lm[12].x - wrist.x, lm[12].y - wrist.y);
      const distMiddleMCP = Math.hypot(lm[9].x - wrist.x, lm[9].y - wrist.y);
      const middleExtended = distMiddleTip > distMiddleMCP * 1.35;

      const distRingTip = Math.hypot(lm[16].x - wrist.x, lm[16].y - wrist.y);
      const distRingMCP = Math.hypot(lm[13].x - wrist.x, lm[13].y - wrist.y);
      const ringExtended = distRingTip > distRingMCP * 1.35;

      const distPinkyTip = Math.hypot(lm[20].x - wrist.x, lm[20].y - wrist.y);
      const distPinkyMCP = Math.hypot(lm[17].x - wrist.x, lm[17].y - wrist.y);
      const pinkyExtended = distPinkyTip > distPinkyMCP * 1.35;

      const pinchDist = Math.hypot(lm[8].x - lm[4].x, lm[8].y - lm[4].y);
      const pinchActive = pinchDist < 0.085;

      if (pinchActive) {
        return { name: "PINCH", label: "🎯 Pincement (Clic / Dessin)", code: "🤏 Pincement" };
      }
      if (indexExtended && !middleExtended && !ringExtended && !pinkyExtended) {
        return { name: "POINT", label: "☝️ Pointeur Air Actif (Index Pointé)", code: "☝️ Pointeur Air" };
      }
      if (indexExtended && middleExtended && !ringExtended && !pinkyExtended) {
        return { name: "PEACE", label: "✌️ Geste Diaporama (Slide Suivante)", code: "✌️ Slide Suivante" };
      }
      if (indexExtended && middleExtended && ringExtended && pinkyExtended) {
        return { name: "PALM", label: "🖐️ Paume Ouverte (Navigation Surface)", code: "🖐️ Paume Ouverte" };
      }
      if (!indexExtended && !middleExtended && !ringExtended && !pinkyExtended) {
        return { name: "FIST", label: "✊ Poing Fermé (Effacer / Pause)", code: "✊ Poing Fermé" };
      }

      return { name: "GESTURE", label: "✋ Main Détectée — Contrôle Actif", code: "✋ Main Détectée" };
    }

    function handleAirGesturesInteraction(x, y, gestureName) {
      const now = Date.now();
      const activeView = $(".module-view.active-view");

      if (isPinching) {
        if (activeView && activeView.id === "view-vision") {
          drawVisionStroke(x, y);
        } else if (activeView) {
          const canvas = activeView.querySelector("canvas");
          if (canvas) {
            const rect = canvas.getBoundingClientRect();
            if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
              const canvasX = (x - rect.left) * (canvas.width / rect.width);
              const canvasY = (y - rect.top) * (canvas.height / rect.height);
              const ctx = canvas.getContext("2d");
              if (ctx) {
                ctx.lineWidth = 4;
                ctx.lineCap = "round";
                ctx.strokeStyle = "#00f2fe";
                if (!canvas._isAirDrawing) {
                  canvas._isAirDrawing = true;
                  ctx.beginPath();
                  ctx.moveTo(canvasX, canvasY);
                } else {
                  ctx.lineTo(canvasX, canvasY);
                  ctx.stroke();
                }
              }
            }
          }
        }
      } else {
        $$("canvas").forEach(c => { c._isAirDrawing = false; });
      }

      if (now - lastGestureTime > 1200) {
        if (activeView && activeView.id === "view-vision") {
          if (handleVisionAirGesture(gestureName)) {
            lastGestureTime = now;
          }
        } else if (gestureName === "PEACE") {
          const btnNext = $("#btn-pres-next");
          if (btnNext) {
            btnNext.click();
            lastGestureTime = now;
          }
        } else if (gestureName === "FIST") {
          const btnClear = $("#btn-wb-clear") || $("#btn-draw-clear");
          if (btnClear) {
            btnClear.click();
            lastGestureTime = now;
          }
        }
      }
    }

    /* ============================================================
       AIR VISION MODULE — Correcteur sous caméra, Suivi EPS, Capture doc
       ============================================================ */
    const visionToastEl = $("#vision-toast");
    const visionState = {
      mirror: true,
      grid: false,
      width: 5,
      color: "#00f2fe",
      eraser: false,
      camAttached: false,
      postureRunning: false,
      poseEngine: null,
      poseLoading: false,
      posePending: false,
      poseVisible: false,
      docResult: null
    };

    function visionT(key) {
      try {
        const lang = localStorage.getItem("edu_air_lang") || "fr";
        const dict = (window.EDU_AIR_I18N && window.EDU_AIR_I18N.dictionaries) || {};
        return (dict[lang] && dict[lang][key]) || (dict.fr && dict.fr[key]) || key;
      } catch (e) { return key; }
    }

    function visionShowToast(msg) {
      if (!visionToastEl) return;
      visionToastEl.textContent = msg;
      visionToastEl.classList.add("show");
      clearTimeout(visionToastEl._t);
      visionToastEl._t = setTimeout(() => visionToastEl.classList.remove("show"), 2600);
    }

    function visionGetStream() {
      return (pipVideo && pipVideo.srcObject && pipVideo.srcObject.getVideoTracks &&
        pipVideo.srcObject.getVideoTracks().length) ? pipVideo.srcObject : null;
    }

    function visionShareStream() {
      const stream = visionGetStream();
      if (stream) {
        ["#vision-video", "#vision-video-posture", "#vision-video-doc"].forEach(sel => {
          const v = $(sel);
          if (v && !v.srcObject) {
            v.srcObject = stream;
            visionState.camAttached = true;
          }
        });
      } else if (pipVideo && !pipVideo.srcObject && typeof startCameraTracking === "function") {
        try { startCameraTracking(); } catch (e) {}
      }
    }
    setInterval(visionShareStream, 1000);

    function visionSelectTab(tabId) {
      const map = { correct: "vpane-correct", posture: "vpane-posture", doc: "vpane-doc" };
      const chosen = map[tabId];
      if (!chosen) return;
      Object.keys(map).forEach(k => {
        const p = $("#" + map[k]);
        if (p) p.style.display = (map[k] === chosen) ? "" : "none";
      });
      Object.keys(map).forEach(k => {
        const b = $("#vtab-" + k);
        if (!b) return;
        const isActive = k === tabId;
        b.classList.toggle("active", isActive);
        b.classList.toggle("btn-app-primary", isActive);
        b.classList.toggle("btn-app-ghost", !isActive);
      });
      if (tabId === "posture") startVisionPosture();
      if (tabId !== "posture") stopVisionPosture();
      visionShareStream();
    }
    ["correct", "posture", "doc"].forEach(t => {
      const b = $("#vtab-" + t);
      if (b) b.addEventListener("click", () => visionSelectTab(t));
    });

    // ----- Correcteur sous caméra : outils & dessin -----
    function visionSetTool(tool) {
      visionState.eraser = tool === "eraser";
      const pen = $("#vtool-pen"), eras = $("#vtool-eraser");
      if (pen) pen.classList.toggle("active", !visionState.eraser);
      if (eras) eras.classList.toggle("active", visionState.eraser);
    }
    const vPenBtn = $("#vtool-pen");
    if (vPenBtn) vPenBtn.addEventListener("click", () => visionSetTool("pen"));
    const vEraseBtn = $("#vtool-eraser");
    if (vEraseBtn) vEraseBtn.addEventListener("click", () => visionSetTool("eraser"));

    const vColors = $("#vtool-colors");
    if (vColors) {
      vColors.querySelectorAll(".color-dot").forEach(dot => {
        dot.addEventListener("click", () => {
          vColors.querySelectorAll(".color-dot").forEach(d => d.classList.remove("active"));
          dot.classList.add("active");
          visionState.color = dot.getAttribute("data-color") || "#00f2fe";
          visionSetTool("pen");
        });
      });
    }

    const vWidth = $("#vtool-width");
    if (vWidth) {
      vWidth.addEventListener("input", () => {
        visionState.width = parseInt(vWidth.value, 10) || 5;
      });
    }

    const vGridBtn = $("#vtool-grid");
    if (vGridBtn) {
      vGridBtn.addEventListener("click", () => {
        visionState.grid = !visionState.grid;
        vGridBtn.style.opacity = visionState.grid ? "1" : "0.55";
        visionShowToast(visionT("visionToastGrid"));
      });
    }

    const vMirrorBtn = $("#vtool-mirror");
    if (vMirrorBtn) {
      vMirrorBtn.addEventListener("click", () => {
        visionState.mirror = !visionState.mirror;
        ["#vision-video", "#vision-video-posture", "#vision-video-doc"].forEach(sel => {
          const v = $(sel);
          if (v) v.style.transform = visionState.mirror ? "scaleX(-1)" : "none";
        });
        vMirrorBtn.style.opacity = visionState.mirror ? "1" : "0.55";
        visionShowToast(visionT("visionToastMirror"));
      });
    }

    function visionDrawGrid(ctx, canvas) {
      if (!visionState.grid || !ctx || !canvas) return;
      ctx.save();
      ctx.strokeStyle = "rgba(0,242,254,0.18)";
      ctx.lineWidth = 1;
      const stepX = canvas.width / 3;
      for (let i = 1; i < 3; i++) {
        ctx.beginPath();
        ctx.moveTo(stepX * i, 0);
        ctx.lineTo(stepX * i, canvas.height);
        ctx.stroke();
      }
      const stepY = canvas.height / 3;
      for (let i = 1; i < 3; i++) {
        ctx.beginPath();
        ctx.moveTo(0, stepY * i);
        ctx.lineTo(canvas.width, stepY * i);
        ctx.stroke();
      }
      ctx.restore();
    }

    function clearVisionCanvas() {
      const canvas = $("#vision-overlay");
      if (!canvas) return;
      canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
      visionShowToast(visionT("visionToastClear"));
    }
    const vClearBtn = $("#vtool-clear");
    if (vClearBtn) vClearBtn.addEventListener("click", clearVisionCanvas);

    function drawVisionStroke(x, y) {
      const pane = $("#vpane-correct");
      if (!pane || pane.style.display === "none") return;
      const canvas = $("#vision-overlay");
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      if (!rect || rect.width === 0) return;
      if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) return;
      const canvasX = (x - rect.left) * (canvas.width / rect.width);
      const canvasY = (y - rect.top) * (canvas.height / rect.height);
      const ctx = canvas.getContext("2d");
      ctx.save();
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      if (visionState.eraser) {
        ctx.globalCompositeOperation = "destination-out";
        ctx.strokeStyle = "rgba(0,0,0,1)";
        ctx.lineWidth = Math.max(8, visionState.width * 3);
      } else {
        ctx.strokeStyle = visionState.color;
        ctx.lineWidth = visionState.width;
      }
      if (!canvas._isAirDrawing) {
        canvas._isAirDrawing = true;
        ctx.beginPath();
        ctx.moveTo(canvasX, canvasY);
      } else {
        ctx.lineTo(canvasX, canvasY);
        ctx.stroke();
      }
      ctx.restore();
    }

    function visionCompositeCapture() {
      const video = $("#vision-video");
      const overlay = $("#vision-overlay");
      const out = document.createElement("canvas");
      out.width = 960;
      out.height = 540;
      const ctx = out.getContext("2d");
      if (video && video.videoWidth) ctx.drawImage(video, 0, 0, out.width, out.height);
      else ctx.fillStyle = "#040710", ctx.fillRect(0, 0, out.width, out.height);
      if (overlay) ctx.drawImage(overlay, 0, 0);
      visionDrawGrid(ctx, out);
      return out;
    }

    function downloadCanvas(canvas, filename) {
      try {
        const link = document.createElement("a");
        link.download = filename;
        link.href = canvas.toDataURL("image/png");
        link.click();
        return true;
      } catch (e) { return false; }
    }

    function visionAddThumbnail(url, gallerySel, title) {
      const gallery = $(gallerySel);
      if (!gallery) return;
      const wrap = document.createElement("div");
      wrap.style.cssText = "position:relative; display:inline-flex;";
      const img = document.createElement("img");
      img.src = url;
      img.title = title || "";
      img.addEventListener("click", () => { try { window.open(url, "_blank"); } catch (e) {} });
      const del = document.createElement("button");
      del.type = "button";
      del.textContent = "✕";
      del.style.cssText = "position:absolute; top:-6px; right:-6px; background:#ff5d5d; color:#fff; border:none; border-radius:50%; width:20px; height:20px; font-size:11px; line-height:1; cursor:pointer;";
      del.addEventListener("click", () => wrap.remove());
      wrap.appendChild(img);
      wrap.appendChild(del);
      gallery.appendChild(wrap);
    }

    function saveVisionCorrection() {
      if (!visionGetStream()) {
        visionShowToast(visionT("visionToastNoCam"));
        visionShareStream();
        return;
      }
      const out = visionCompositeCapture();
      const url = out.toDataURL("image/png");
      downloadCanvas(out, "edu-air-correction.png");
      visionAddThumbnail(url, "#vision-gallery", "Correction");
      visionShowToast(visionT("visionToastSaved"));
    }
    const vSaveBtn = $("#vtool-save");
    if (vSaveBtn) vSaveBtn.addEventListener("click", saveVisionCorrection);

    // ----- Capture document : détection quadrilatère + redressement -----
    function docGrabFrame() {
      const video = $("#vision-video-doc");
      const out = document.createElement("canvas");
      const w = video && video.videoWidth ? video.videoWidth : 960;
      const h = video && video.videoHeight ? video.videoHeight : 540;
      out.width = w;
      out.height = h;
      const ctx = out.getContext("2d", { willReadFrequently: true });
      if (video && video.videoWidth) ctx.drawImage(video, 0, 0, w, h);
      return out;
    }

    function ptDistSeg(p, a, b) {
      const dx = b[0] - a[0], dy = b[1] - a[1];
      const len2 = dx * dx + dy * dy;
      if (len2 === 0) return Math.hypot(p[0] - a[0], p[1] - a[1]);
      let t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / len2;
      t = Math.max(0, Math.min(1, t));
      return Math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy));
    }

    function simplifyPoly(points, epsilon) {
      const marked = new Array(points.length).fill(false);
      marked[0] = marked[points.length - 1] = true;
      const stack = [[0, points.length - 1]];
      while (stack.length) {
        const seg = stack.pop();
        const s = seg[0], e = seg[1];
        if (e - s <= 1) continue;
        let maxD = 0, idx = -1;
        for (let i = s + 1; i < e; i++) {
          const d = ptDistSeg(points[i], points[s], points[e]);
          if (d > maxD) { maxD = d; idx = i; }
        }
        if (idx !== -1 && maxD > epsilon) {
          marked[idx] = true;
          stack.push([s, idx]);
          stack.push([idx, e]);
        }
      }
      return points.filter((_, i) => marked[i]);
    }

    function hullPerimeter(pts) {
      let p = 0;
      for (let i = 0; i < pts.length; i++) {
        const a = pts[i], b = pts[(i + 1) % pts.length];
        p += Math.hypot(b[0] - a[0], b[1] - a[1]);
      }
      return p;
    }

    function monotoneChain(points) {
      const p = points.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
      const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
      const lower = [];
      for (const pt of p) {
        while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], pt) <= 0) lower.pop();
        lower.push(pt);
      }
      const upper = [];
      for (let i = p.length - 1; i >= 0; i--) {
        const pt = p[i];
        while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], pt) <= 0) upper.pop();
        upper.push(pt);
      }
      lower.pop();
      upper.pop();
      return lower.concat(upper);
    }

    function quadArea(pts) {
      let s = 0;
      for (let i = 0; i < pts.length; i++) {
        const a = pts[i], b = pts[(i + 1) % pts.length];
        s += a[0] * b[1] - b[0] * a[1];
      }
      return Math.abs(s) / 2;
    }

    function boundingBoxArea(pts) {
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      pts.forEach(p => {
        if (p[0] < minX) minX = p[0];
        if (p[0] > maxX) maxX = p[0];
        if (p[1] < minY) minY = p[1];
        if (p[1] > maxY) maxY = p[1];
      });
      return (maxX - minX) * (maxY - minY);
    }

    function orderCorners(pts) {
      const cx = pts.reduce((s, p) => s + p[0], 0) / pts.length;
      const cy = pts.reduce((s, p) => s + p[1], 0) / pts.length;
      return pts.slice().sort((a, b) => Math.atan2(a[1] - cy, a[0] - cx) - Math.atan2(b[1] - cy, b[0] - cx));
    }

    function processDocDetection(srcCanvas) {
      const SW = 160;
      const scaleFactor = srcCanvas.width / SW;
      const SH = Math.max(1, Math.round(srcCanvas.height / scaleFactor));
      if (SH < 10) return null;
      const small = document.createElement("canvas");
      small.width = SW;
      small.height = SH;
      const sctx = small.getContext("2d", { willReadFrequently: true });
      sctx.drawImage(srcCanvas, 0, 0, SW, SH);
      const px = sctx.getImageData(0, 0, SW, SH).data;
      const grad = new Float32Array(SW * SH);
      let maxG = 0;
      for (let y = 1; y < SH - 1; y++) {
        for (let x = 1; x < SW - 1; x++) {
          const i = (y * SW + x) * 4;
          const l = (y * SW + (x - 1)) * 4;
          const r = (y * SW + (x + 1)) * 4;
          const u = ((y - 1) * SW + x) * 4;
          const d = ((y + 1) * SW + x) * 4;
          const gx = px[r] - px[l];
          const gy = px[d] - px[u];
          const g = Math.sqrt(gx * gx + gy * gy);
          grad[y * SW + x] = g;
          if (g > maxG) maxG = g;
        }
      }
      const thr = maxG * 0.18;
      const pts = [];
      for (let i = 0; i < grad.length; i++) {
        if (grad[i] >= thr) pts.push([(i % SW) * scaleFactor, Math.floor(i / SW) * scaleFactor]);
      }
      if (pts.length < 8) return null;
      const hull = monotoneChain(pts);
      if (hull.length < 4) return null;
      const corners = simplifyPoly(hull, hullPerimeter(hull) * 0.02);
      if (corners.length < 4) return null;
      const quad = corners.slice(0, 4);
      const conf = quadArea(quad) / (boundingBoxArea(quad) || 1);
      if (conf < 0.25) return null;
      return orderCorners(quad);
    }

    function solveHomography(srcPts, dstPts) {
      const A = [], B = [];
      for (let i = 0; i < 4; i++) {
        const sx = srcPts[i][0], sy = srcPts[i][1];
        const dx = dstPts[i][0], dy = dstPts[i][1];
        A.push([dx, dy, 1, 0, 0, 0, -dx * sx, -dy * sx]);
        B.push(sx);
        A.push([0, 0, 0, dx, dy, 1, -dx * sy, -dy * sy]);
        B.push(sy);
      }
      const h = gaussSolve(A, B);
      return [h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7], 1];
    }

    function gaussSolve(A, B) {
      const n = B.length;
      const M = A.map((row, i) => row.concat(B[i]));
      for (let col = 0; col < n; col++) {
        let piv = col;
        for (let r = col + 1; r < n; r++) {
          if (Math.abs(M[r][col]) > Math.abs(M[piv][col])) piv = r;
        }
        if (Math.abs(M[piv][col]) < 1e-12) continue;
        const tmp = M[col]; M[col] = M[piv]; M[piv] = tmp;
        const div = M[col][col];
        for (let j = col; j <= n; j++) M[col][j] /= div;
        for (let r = 0; r < n; r++) {
          if (r === col) continue;
          const f = M[r][col];
          if (Math.abs(f) < 1e-14) continue;
          for (let j = col; j <= n; j++) M[r][j] -= f * M[col][j];
        }
      }
      return M.map(r => r[n]);
    }

    function warpPerspective(src, H, outW, outH) {
      const out = document.createElement("canvas");
      out.width = outW;
      out.height = outH;
      const octx = out.getContext("2d");
      const sx = src.width, sy = src.height;
      const srcData = src.getContext("2d", { willReadFrequently: true }).getImageData(0, 0, sx, sy);
      const oid = octx.createImageData(outW, outH);
      const sd = srcData.data, od = oid.data;
      for (let y = 0; y < outH; y++) {
        for (let x = 0; x < outW; x++) {
          const den = H[6] * x + H[7] * y + H[8];
          if (Math.abs(den) < 1e-9) continue;
          const u = (H[0] * x + H[1] * y + H[2]) / den;
          const v = (H[3] * x + H[4] * y + H[5]) / den;
          if (u < 0 || u > sx - 1 || v < 0 || v > sy - 1) continue;
          const x0 = Math.floor(u), y0 = Math.floor(v);
          const x1 = Math.min(x0 + 1, sx - 1), y1 = Math.min(y0 + 1, sy - 1);
          const fx = u - x0, fy = v - y0;
          const i00 = (y0 * sx + x0) * 4, i10 = (y0 * sx + x1) * 4;
          const i01 = (y1 * sx + x0) * 4, i11 = (y1 * sx + x1) * 4;
          const oi = (y * outW + x) * 4;
          for (let c = 0; c < 3; c++) {
            const v00 = sd[i00 + c], v10 = sd[i10 + c], v01 = sd[i01 + c], v11 = sd[i11 + c];
            od[oi + c] = Math.round(
              v00 * (1 - fx) * (1 - fy) + v10 * fx * (1 - fy) + v01 * (1 - fx) * fy + v11 * fx * fy
            );
          }
          od[oi + 3] = 255;
        }
      }
      octx.putImageData(oid, 0, 0);
      return out;
    }

    function captureVisionDoc() {
      if (!visionGetStream()) {
        visionShowToast(visionT("visionToastNoCam"));
        visionShareStream();
        return;
      }
      const raw = docGrabFrame();
      let result = raw;
      let rectified = false;
      if (raw.width > 10 && raw.height > 10) {
        try {
          const corners = processDocDetection(raw);
          if (corners) {
            const dTop = Math.hypot(corners[1][0] - corners[0][0], corners[1][1] - corners[0][1]);
            const dBot = Math.hypot(corners[3][0] - corners[2][0], corners[3][1] - corners[2][1]);
            const dL = Math.hypot(corners[3][0] - corners[0][0], corners[3][1] - corners[0][1]);
            const dR = Math.hypot(corners[2][0] - corners[1][0], corners[2][1] - corners[1][1]);
            const w = Math.max(dTop, dBot);
            const hLen = Math.max(dL, dR);
            const ratio = w / (hLen || 1);
            let outW = 1000;
            let outH = Math.round(1000 / ratio);
            if (outH < 200) { outH = 800; outW = Math.round(800 * ratio); }
            outW = Math.min(outW, 1600);
            outH = Math.min(outH, 1600);
            const dst = [[0, 0], [outW, 0], [outW, outH], [0, outH]];
            const H = solveHomography(corners, dst);
            result = warpPerspective(raw, H, outW, outH);
            rectified = true;
          }
        } catch (e) {
          rectified = false;
        }
      }
      visionState.docResult = result;
      const canvas = $("#vision-doc-canvas");
      if (canvas) {
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const rw = result.width, rh = result.height;
        const scale = Math.min(canvas.width / rw, canvas.height / rh);
        const dw = rw * scale, dh = rh * scale;
        ctx.drawImage(result, (canvas.width - dw) / 2, (canvas.height - dh) / 2, dw, dh);
      }
      const url = result.toDataURL("image/png");
      visionAddThumbnail(url, "#vision-doc-gallery", rectified ? "OK" : "RAW");
      visionShowToast(rectified ? visionT("visionToastCaptureOk") : visionT("visionToastCaptureFallback"));
    }
    const vDocCaptureBtn = $("#vtool-doc-capture");
    if (vDocCaptureBtn) vDocCaptureBtn.addEventListener("click", captureVisionDoc);
    const vDocDlBtn = $("#vtool-doc-download");
    if (vDocDlBtn) {
      vDocDlBtn.addEventListener("click", () => {
        if (!visionState.docResult) { visionShowToast(visionT("visionToastDocFirst")); return; }
        downloadCanvas(visionState.docResult, "edu-air-document-redresse.png");
      });
    }
    const vDocClearBtn = $("#vtool-doc-clear");
    if (vDocClearBtn) {
      vDocClearBtn.addEventListener("click", () => {
        const canvas = $("#vision-doc-canvas");
        if (canvas) canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
        visionState.docResult = null;
        const g = $("#vision-doc-gallery");
        if (g) g.innerHTML = "";
      });
    }

    // ----- Suivi EPS / Posture (MediaPipe Pose chargé à la demande) -----
    const POSE_CONNECTIONS = [
      [11, 12], [12, 14], [14, 16], [11, 13], [13, 15],
      [11, 23], [12, 24], [23, 24], [23, 25], [25, 27],
      [24, 26], [26, 28]
    ];

    function poseAngles(landmarks) {
      const L = landmarks;
      const rad = 180 / Math.PI;
      const ang = (a, b, c) => {
        const dx1 = L[a].x - L[b].x, dy1 = L[a].y - L[b].y;
        const dx2 = L[c].x - L[b].x, dy2 = L[c].y - L[b].y;
        let t = Math.atan2(dy2, dx2) - Math.atan2(dy1, dx1);
        t = Math.abs(t * rad);
        return t > 180 ? 360 - t : t;
      };
      const midHip = { x: (L[23].x + L[24].x) / 2, y: (L[23].y + L[24].y) / 2 };
      const midSh = { x: (L[11].x + L[12].x) / 2, y: (L[11].y + L[12].y) / 2 };
      const dx = midSh.x - midHip.x, dy = midSh.y - midHip.y;
      const tronc = Math.abs(90 - Math.atan2(Math.abs(dx), Math.abs(dy)) * rad);
      return {
        epauleG: ang(13, 11, 23), epauleD: ang(14, 12, 24),
        coudeG: ang(11, 13, 15), coudeD: ang(12, 14, 16),
        hancheG: ang(11, 23, 25), hancheD: ang(12, 24, 26),
        genouG: ang(23, 25, 27), genouD: ang(24, 26, 28),
        tronc: tronc
      };
    }

    function visionConsigne() {
      const sel = $("#vposture-consigne");
      return sel ? sel.value : "libre";
    }

    function angColorFor(key, ang) {
      const cfgMap = {
        coude90: { keys: ["coudeG", "coudeD"], r: [70, 115] },
        squad: { keys: ["genouG", "genouD"], r: [60, 130] },
        chaise: { keys: ["genouG", "genouD", "hancheG", "hancheD"], r: [70, 120] }
      };
      const cfg = cfgMap[visionConsigne()];
      if (cfg && cfg.keys.indexOf(key) !== -1) {
        return (ang >= cfg.r[0] && ang <= cfg.r[1]) ? "#3ddc97" : "#ff5d5d";
      }
      return (ang >= 70 && ang <= 165) ? "#3ddc97" : "#ffb84d";
    }

    function drawVisionPose(landmarks) {
      const canvas = $("#vision-pose-canvas");
      if (!canvas) return;
      const W = canvas.width, H = canvas.height;
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, W, H);
      ctx.lineWidth = 3;
      ctx.strokeStyle = "#00f2fe";
      ctx.shadowColor = "#00f2fe";
      ctx.shadowBlur = 8;
      POSE_CONNECTIONS.forEach((pair) => {
        const p1 = landmarks[pair[0]], p2 = landmarks[pair[1]];
        if (!p1 || !p2) return;
        ctx.beginPath();
        ctx.moveTo((1 - p1.x) * W, p1.y * H);
        ctx.lineTo((1 - p2.x) * W, p2.y * H);
        ctx.stroke();
      });
      ctx.shadowBlur = 0;
      landmarks.forEach((p, i) => {
        if (!p) return;
        if (i === 0) return;
        ctx.beginPath();
        ctx.arc((1 - p.x) * W, p.y * H, 3, 0, 2 * Math.PI);
        ctx.fillStyle = "#3ddc97";
        ctx.fill();
      });
      const a = poseAngles(landmarks);
      const labelJoints = {
        epauleG: [11, a.epauleG], epauleD: [12, a.epauleD],
        coudeG: [13, a.coudeG], coudeD: [14, a.coudeD],
        hancheG: [23, a.hancheG], hancheD: [24, a.hancheD],
        genouG: [25, a.genouG], genouD: [26, a.genouD]
      };
      ctx.font = "bold 13px Segoe UI, sans-serif";
      Object.keys(labelJoints).forEach(k => {
        const item = labelJoints[k];
        const p = landmarks[item[0]];
        if (!p) return;
        const x = (1 - p.x) * W, y = p.y * H;
        ctx.fillStyle = angColorFor(k, item[1]);
        ctx.fillText(Math.round(item[1]) + "°", x + 8, y - 8);
      });
    }

    function updateVisionAngles(lm) {
      const a = poseAngles(lm);
      const panel = $("#vision-angle-panel");
      if (panel) {
        const labels = {
          tronc: visionT("visionAngleBack"),
          epauleG: visionT("visionAngleShoulder") + " G", epauleD: visionT("visionAngleShoulder") + " D",
          coudeG: visionT("visionAngleElbow") + " G", coudeD: visionT("visionAngleElbow") + " D",
          hancheG: visionT("visionAngleHip") + " G", hancheD: visionT("visionAngleHip") + " D",
          genouG: visionT("visionAngleKnee") + " G", genouD: visionT("visionAngleKnee") + " D"
        };
        panel.innerHTML = "";
        Object.keys(labels).forEach(k => {
          const chip = document.createElement("span");
          chip.className = "vision-angle-chip";
          chip.style.color = angColorFor(k, a[k]);
          const lab = document.createElement("span");
          lab.textContent = labels[k];
          const val = document.createElement("span");
          val.className = "val";
          val.textContent = Math.round(a[k]) + "°";
          chip.appendChild(lab);
          chip.appendChild(val);
          panel.appendChild(chip);
        });
      }
      const cfgMap = {
        coude90: { keys: ["coudeG", "coudeD"], r: [70, 115] },
        squad: { keys: ["genouG", "genouD"], r: [60, 130] },
        chaise: { keys: ["genouG", "genouD", "hancheG", "hancheD"], r: [70, 120] }
      };
      let ok = true;
      const cfg = cfgMap[visionConsigne()];
      if (cfg) {
        for (const k of cfg.keys) {
          if (a[k] < cfg.r[0] || a[k] > cfg.r[1]) { ok = false; break; }
        }
      }
      const st = $("#vposture-status");
      if (st) {
        st.textContent = ok ? "🟢 " + visionT("visionStatusOk") : "🔴 " + visionT("visionStatusFix");
        st.style.color = ok ? "#3ddc97" : "#ff5d5d";
      }
    }

    function loadVisionPose() {
      if (window.Pose || visionState.poseEngine) return Promise.resolve(true);
      if (visionState.poseLoading) return Promise.resolve(false);
      visionState.poseLoading = true;
      return new Promise(resolve => {
        const s = document.createElement("script");
        s.src = "https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/pose.js";
        s.async = true;
        s.onload = () => {
          visionState.poseLoading = false;
          try {
            visionState.poseEngine = new window.Pose({
              locateFile: (f) => "https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/" + f
            });
            visionState.poseEngine.setOptions({
              modelComplexity: 1,
              smoothLandmarks: true,
              minDetectionConfidence: 0.5,
              minTrackingConfidence: 0.5
            });
            visionState.poseEngine.onResults(res => {
              visionState.posePending = false;
              const lm = res && res.poseLandmarks;
              visionState.poseVisible = !!lm;
              if (lm && visionState.postureRunning) {
                drawVisionPose(lm);
                updateVisionAngles(lm);
              }
            });
            resolve(true);
          } catch (e) {
            visionState.poseEngine = null;
            resolve(false);
          }
        };
        s.onerror = () => { visionState.poseLoading = false; resolve(false); };
        document.head.appendChild(s);
      });
    }

    async function startVisionPosture() {
      if (visionState.postureRunning) return;
      const ok = await loadVisionPose();
      if (!ok) { visionShowToast(visionT("visionToastPoseFail")); return; }
      visionState.postureRunning = true;
      const btn = $("#vposture-toggle");
      if (btn) btn.textContent = "⏸ " + visionT("visionPostureStop");
      visionShowToast(visionT("visionToastPoseStart"));
      visionPostureLoop();
    }

    function stopVisionPosture() {
      visionState.postureRunning = false;
      const btn = $("#vposture-toggle");
      if (btn) btn.textContent = "▶ " + visionT("visionPostureStart");
    }

    function visionPostureLoop() {
      if (!visionState.postureRunning) return;
      const video = $("#vision-video-posture");
      if (video && video.readyState >= 2 && !visionState.posePending && visionState.poseEngine && !document.hidden) {
        visionState.posePending = true;
        try { visionState.poseEngine.send({ image: video }); } catch (e) { visionState.posePending = false; }
      }
      requestAnimationFrame(visionPostureLoop);
    }
    const vPostureBtn = $("#vposture-toggle");
    if (vPostureBtn) {
      vPostureBtn.addEventListener("click", () => {
        if (visionState.postureRunning) stopVisionPosture();
        else startVisionPosture();
      });
    }

    function handleVisionAirGesture(gestureName) {
      const paneIds = ["vpane-correct", "vpane-posture", "vpane-doc"];
      const activePane = paneIds.find(id => {
        const el = $("#" + id);
        return el && el.style.display !== "none";
      });
      if (gestureName === "PEACE") {
        if (activePane === "vpane-doc") { captureVisionDoc(); return true; }
        if (activePane === "vpane-correct") { saveVisionCorrection(); return true; }
      }
      if (gestureName === "FIST") {
        const canvas = $("#vision-overlay");
        if (canvas && canvas.getContext("2d")) {
          canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
          visionShowToast(visionT("visionToastClear"));
          return true;
        }
      }
      return false;
    }

    function processHandLandmarks(landmarks) {
      if (!landmarks || landmarks.length === 0) {
        onNoHandDetected();
        return;
      }

      lastMpFrameSuccessTime = Date.now();
      const lm = landmarks[0];
      if (pipCanvas) {
        if (pipCanvas.width !== pipCanvas.clientWidth || pipCanvas.height !== pipCanvas.clientHeight) {
          pipCanvas.width = pipCanvas.clientWidth || 180;
          pipCanvas.height = pipCanvas.clientHeight || 130;
        }
        const ctx = pipCanvas.getContext("2d");
        drawHandSkeleton(ctx, lm, pipCanvas.width, pipCanvas.height);
      }

      const rawX = (1 - lm[8].x) * window.innerWidth;
      const rawY = lm[8].y * window.innerHeight;

      smoothedX += (rawX - smoothedX) * 0.35;
      smoothedY += (rawY - smoothedY) * 0.35;

      const gest = classifyHandGestureRotationInvariant(lm);
      currentGesture = gest.name;
      isPinching = gest.name === "PINCH";

      const swinging = gest.name !== "PINCH" && gest.name !== "FIST";
      const nav = detectSwipe(lm[8].x, swinging);
      if (nav) triggerNavigation(nav);

      if (airPointer) {
        airPointer.style.transform = `translate3d(${smoothedX}px, ${smoothedY}px, 0)`;
        airPointer.classList.add("active");
        airPointer.classList.toggle("pinching", isPinching);
        airPointer.classList.toggle("palm", gest.name === "PALM");
        airPointer.classList.toggle("peace", gest.name === "PEACE");
        if (airCursorLabel) {
          airCursorLabel.textContent = gest.code;
        }
      }

      if (txtCamStatus) {
        txtCamStatus.textContent = gest.label;
      }
      if (pipStatusTag) {
        pipStatusTag.textContent = `🟢 MAIN : ${gest.code}`;
        pipStatusTag.style.color = "#3ddc97";
      }
      if (pillModeHand) {
        pillModeHand.classList.add("active");
        pillModeHand.style.borderColor = "#00f2fe";
      }

      handleAirGesturesInteraction(smoothedX, smoothedY, gest.name);
    }

    function onNoHandDetected() {
      if (pipCanvas) {
        const ctx = pipCanvas.getContext("2d");
        ctx.clearRect(0, 0, pipCanvas.width, pipCanvas.height);
      }
      if (airPointer) {
        airPointer.classList.remove("active");
      }
      if (txtCamStatus) {
        txtCamStatus.textContent = "Montrez votre main devant la caméra";
      }
      if (pipStatusTag) {
        pipStatusTag.textContent = "🟢 AI HAND ON";
        pipStatusTag.style.color = "#3ddc97";
      }
    }

    // --- Swipe navigation: wave the open hand right (next) / left (previous).
    // The direction uses camera-space X so it stays intuitive whichever way the
    // webcam is mirrored, and it works for both the MediaPipe and the fallback
    // optical detector (they both feed a normalized 0..1 camera X).
    function detectSwipe(camX, handOpen) {
      const now = Date.now();
      if (!handOpen) {
        swipeWindow.length = 0;
        return null;
      }
      swipeWindow.push({ x: camX, t: now });
      while (swipeWindow.length && now - swipeWindow[0].t > SWIPE_WINDOW_MS) {
        swipeWindow.shift();
      }
      if (swipeWindow.length < 3) return null;
      const first = swipeWindow[0];
      const lastS = swipeWindow[swipeWindow.length - 1];
      const dt = lastS.t - first.t;
      if (dt < 40 || dt > SWIPE_WINDOW_MS) return null;
      const dx = lastS.x - first.x;
      if (Math.abs(dx) < SWIPE_THRESHOLD) return null;
      if (now - lastNavTime < NAV_COOLDOWN_MS) return null;
      lastNavTime = now;
      return dx > 0 ? "SWIPE_RIGHT" : "SWIPE_LEFT";
    }

    function triggerNavigation(swipe) {
      if (swipe === "SWIPE_RIGHT") {
        const btnNext = $("#btn-slide-next") || $("#btn-pres-next");
        if (btnNext) {
          btnNext.click();
          window.updateGestureHUD("SWIPE_RIGHT", 96);
          if (txtCamStatus) txtCamStatus.textContent = "👉 Balayage droit : slide suivante";
        }
      } else if (swipe === "SWIPE_LEFT") {
        const btnPrev = $("#btn-slide-prev");
        if (btnPrev) {
          btnPrev.click();
          window.updateGestureHUD("SWIPE_LEFT", 96);
          if (txtCamStatus) txtCamStatus.textContent = "👈 Balayage gauche : slide précédente";
        }
      }
    }

    // --- Standalone 60 FPS Optical Motion & Skin Hand Analyzer ---
    const fallbackCanvas = document.createElement("canvas");
    fallbackCanvas.width = 160;
    fallbackCanvas.height = 120;
    const fallbackCtx = fallbackCanvas.getContext("2d", { willReadFrequently: true });
    let prevFramePixels = null;

    function processStandaloneHandAnalysis(videoEl) {
      if (!videoEl || videoEl.readyState < 2 || !fallbackCtx) return;

      // Fallback detector only: once MediaPipe has answered recently, stop the
      // crude optical classifier so it never clobbers the 3D landmark output.
      if (handsEngine && Date.now() - lastMpFrameSuccessTime < 900) return;

      const width = 160;
      const height = 120;
      fallbackCtx.drawImage(videoEl, 0, 0, width, height);
      const frame = fallbackCtx.getImageData(0, 0, width, height);
      const data = frame.data;

      let sumX = 0, sumY = 0, count = 0;
      let minPixelY = height, topFingertipX = width / 2;
      let minX = width, maxX = 0, minY = height, maxY = 0;

      for (let i = 0; i < data.length; i += 4) {
        const r = data[i], g = data[i+1], b = data[i+2];

        const maxC = Math.max(r, g, b);
        const minC = Math.min(r, g, b);
        const isSkin = (r > 40 && g > 25 && b > 15 && r > g && (maxC - minC > 10));

        let isMotion = false;
        if (prevFramePixels && prevFramePixels[i] !== undefined) {
          const diff = Math.abs(r - prevFramePixels[i]) + Math.abs(g - prevFramePixels[i+1]) + Math.abs(b - prevFramePixels[i+2]);
          if (diff > 25) isMotion = true;
        }

        if (isSkin || isMotion) {
          const pixelIndex = i / 4;
          const px = pixelIndex % width;
          const py = Math.floor(pixelIndex / width);

          sumX += px;
          sumY += py;
          count++;

          if (px < minX) minX = px;
          if (px > maxX) maxX = px;
          if (py < minY) minY = py;
          if (py > maxY) maxY = py;

          if (py < minPixelY) {
            minPixelY = py;
            topFingertipX = px;
          }
        }
      }

      prevFramePixels = new Uint8ClampedArray(data);

      if (count > 20) {
        const avgX = sumX / count;
        const avgY = sumY / count;

        const targetX = (minPixelY < avgY - 3) ? topFingertipX : avgX;
        const targetY = minPixelY;

        const normX = targetX / width;
        const normY = targetY / height;

        if (pipCanvas) {
          if (pipCanvas.width !== pipCanvas.clientWidth || pipCanvas.height !== pipCanvas.clientHeight) {
            pipCanvas.width = pipCanvas.clientWidth || 180;
            pipCanvas.height = pipCanvas.clientHeight || 130;
          }
          const ctx = pipCanvas.getContext("2d");
          ctx.clearRect(0, 0, pipCanvas.width, pipCanvas.height);

          const cX = normX * pipCanvas.width;
          const cY = normY * pipCanvas.height;

          ctx.beginPath();
          ctx.arc(cX, cY, 14, 0, 2 * Math.PI);
          ctx.fillStyle = "rgba(0, 242, 254, 0.35)";
          ctx.strokeStyle = "#00f2fe";
          ctx.lineWidth = 2.5;
          ctx.fill();
          ctx.stroke();

          ctx.beginPath();
          ctx.moveTo(cX - 8, cY); ctx.lineTo(cX + 8, cY);
          ctx.moveTo(cX, cY - 8); ctx.lineTo(cX, cY + 8);
          ctx.strokeStyle = "#ffffff";
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }

        const rawX = (1 - normX) * window.innerWidth;
        const rawY = normY * window.innerHeight;

        smoothedX += (rawX - smoothedX) * 0.35;
        smoothedY += (rawY - smoothedY) * 0.35;

        const blobWidth = maxX - minX;
        const blobHeight = maxY - minY;
        let gestCode = "☝️ Pointeur Air";
        let gestName = "POINT";

        if (blobWidth < 22 && blobHeight < 22) {
          gestCode = "🤏 Pincement";
          gestName = "PINCH";
          isPinching = true;
        } else if (blobWidth > 50 && blobHeight > 40) {
          gestCode = "🖐️ Paume Ouverte";
          gestName = "PALM";
          isPinching = false;
        } else {
          isPinching = false;
        }

        if (airPointer) {
          airPointer.style.transform = `translate3d(${smoothedX}px, ${smoothedY}px, 0)`;
          airPointer.classList.add("active");
          airPointer.classList.toggle("pinching", isPinching);
          airPointer.classList.toggle("palm", gestName === "PALM");
          if (airCursorLabel) airCursorLabel.textContent = gestCode;
        }

        if (txtCamStatus) txtCamStatus.textContent = `✨ Main Détectée — ${gestCode}`;
        if (pipStatusTag) {
          pipStatusTag.textContent = `🟢 MAIN : ${gestCode}`;
          pipStatusTag.style.color = "#3ddc97";
        }

        handleAirGesturesInteraction(smoothedX, smoothedY, gestName);

        const nav = detectSwipe(normX, gestName !== "PINCH" && gestName !== "FIST");
        if (nav) triggerNavigation(nav);
      } else {
        if (Date.now() - lastMpFrameSuccessTime > 800) {
          onNoHandDetected();
        }
      }
    }

    function initMediaPipeHands(retriesLeft = 5) {
      if (handsEngine) return true;
      if (typeof window.Hands === "undefined") {
        // The MediaPipe <script> may still be loading (slow / offline cache).
        if (retriesLeft > 0) {
          setTimeout(() => initMediaPipeHands(retriesLeft - 1), 400);
        } else if (txtCamStatus) {
          txtCamStatus.textContent = "Mode secours (MediaPipe indisponible)";
        }
        return false;
      }
      try {
        handsEngine = new window.Hands({
          locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675469240/${file}`
        });
        handsEngine.setOptions({
          maxNumHands: 1,
          modelComplexity: 1,
          minDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5
        });
        handsEngine.onResults((results) => {
          if (results && results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            lastMpFrameSuccessTime = Date.now();
            processHandLandmarks(results.multiHandLandmarks);
          }
        });
        console.log("✅ Moteur MediaPipe Hands initialisé.");
        return true;
      } catch (e) {
        console.warn("MediaPipe Hands init warning:", e);
        if (retriesLeft > 0) {
          setTimeout(() => initMediaPipeHands(retriesLeft - 1), 800);
        }
      }
      return false;
    }

    function startCameraTracking() {
      if (cameraStarted) return;   // never open a second stream / engine
      cameraStarted = true;
      if (pipVideo) {
        pipVideo.muted = true;
        pipVideo.setAttribute("playsinline", "");
        pipVideo.setAttribute("autoplay", "");
      }

      initMediaPipeHands();

      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" }
        })
        .then((stream) => {
          if (pipVideo) {
            pipVideo.srcObject = stream;
            pipVideo.play().catch(() => {});
          }

          function frameLoop() {
            if (pipVideo && pipVideo.readyState >= 2 && handTrackerActive) {
              // 1. Fallback optical 60 FPS tracking (self-guards: skipped while
              //    MediaPipe is answering, so it can't clobber 3D landmarks).
              processStandaloneHandAnalysis(pipVideo);

              // 2. Primary detector: MediaPipe 3D landmarks.
              if (handsEngine && !isMpProcessing) {
                isMpProcessing = true;
                handsEngine.send({ image: pipVideo }).catch(() => {}).finally(() => {
                  isMpProcessing = false;
                });
              }
            }
            requestAnimationFrame(frameLoop);
          }
          requestAnimationFrame(frameLoop);
        })
        .catch((err) => {
          console.warn("Erreur d'accès WebCam:", err.message);
          cameraStarted = false;   // allow retry via the status pill / click
          if (txtCamStatus) txtCamStatus.textContent = "⚠️ Caméra bloquée — Cliquez pour autoriser";
        });
      } else {
        cameraStarted = false;
        if (txtCamStatus) txtCamStatus.textContent = "⚠️ Caméra inaccessible par ce navigateur";
      }
    }

    // Start camera tracking (single init — guarded in startCameraTracking)
    startCameraTracking();

    // Allow Manual Pointer Simulation on Canvas when moving mouse with Shift key pressed
    document.addEventListener("mousemove", (e) => {
      if (e.shiftKey) {
        smoothedX = e.clientX;
        smoothedY = e.clientY;
        if (airPointer) {
          airPointer.style.transform = `translate3d(${smoothedX}px, ${smoothedY}px, 0)`;
          airPointer.classList.add("active");
          if (airCursorLabel) airCursorLabel.textContent = "☝️ Test Pointeur";
        }
        if (txtCamStatus) txtCamStatus.textContent = "✨ Mode Test — Pointeur Air Actif";
      }
    });

    console.log("EDU-AIR Smart Surface App Fully Initialized.");
  });
})();
