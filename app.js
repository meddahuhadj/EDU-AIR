/* ==================================================================
   EDU-AIR SMART SURFACE — browser demo application
   No camera/mic is ever requested by this web build: every "air"
   interaction below is driven by mouse/touch/pointer input standing
   in for the tracked hand, exactly as documented in the demo modal.
   Import AFTER i18n.js.
   ================================================================== */
(function(){
"use strict";
var SVGNS = "http://www.w3.org/2000/svg";

/* ---------------------------------------------------------------- */
/* state                                                              */
/* ---------------------------------------------------------------- */
var S = window.EDUAIR = {
  view: "smart-surface",
  sensitivity: 1,
  a11y: { motion:false, contrast:false, cursor:false },
  log: [],
  quizzes: getLS("quizzes", []),
  quiz: { active:null, qi:0, score:0, total:0, wrongByQ:{}, reported:true },
  pres: { i:0, slides:[
    {t:"EDU-AIR SMART SURFACE", b:"A contactless AI-powered interactive whiteboard. No touch frame, no special sensor."},
    {t:"Air pointer", b:"Your hand becomes the cursor — pinch to click, hold to drag."},
    {t:"Air draw", b:"Freehand ink with automatic shape recognition, right in mid-air."},
    {t:"Safety by default", b:"Every action passes a safety gate: safe · confirm · critical. Nothing unregistered ever runs."},
    {t:"Works with what you already have", b:"Any PC + webcam + projector. No new hardware to buy or install."}
  ]},
  calib: getLS("calib", { ok:false, H:null, pts:[], score:0, t:0 }),
  ai: getLS("ai", { mode:"scripted", endpoint:"./api/chat", history:[] }),
  vision: { running:false, fps:0 },
  lab: { active:"circuit", params:{
    circuit:{voltage:6, resistance:100},
    beaker:{ph:7},
    pendulum:{length:100, gravity:9.8},
    wave:{frequency:1, amplitude:50},
    optics:{objectDist:150, focal:80},
    planet:{speed:1}
  }, t0: 0 },
  threed: { model:"cube", rotX:-0.5, rotY:0.6, auto:false, explode:false, wire:false },
  sound: getLS("sound", true),
  conf: getLS("conf", 0.5),
  primHand: getLS("primHand", "auto"),
  stab: getLS("stab", 4),
  theme: getLS("theme", "dark"),
  tutorialSeen: getLS("tutorialSeen", false),
  quizResults: getLS("quizResults", []),
  deferredPrompt: null
};

/* ---------------------------------------------------------------- */
/* small helpers                                                      */
/* ---------------------------------------------------------------- */
function $(id){ return document.getElementById(id); }
function qs(sel,root){ return (root||document).querySelector(sel); }
function qsa(sel,root){ return Array.prototype.slice.call((root||document).querySelectorAll(sel)); }
function on(el,ev,fn){ if(el) el.addEventListener(ev,fn); }
function clamp(v,a,b){ return Math.max(a,Math.min(b,v)); }
function esc(s){ return String(s==null?"":s).replace(/[&<>"']/g,function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]; }); }
function t(key){ return (window.i18n && window.i18n.t) ? window.i18n.t(key) : key; }
function setLS(k,v){ try{ localStorage.setItem("eduair."+k, JSON.stringify(v)); }catch(e){} }
function getLS(k,d){ try{ var v=localStorage.getItem("eduair."+k); return v==null?d:JSON.parse(v); }catch(e){ return d; } }
function applyTheme(){ document.body.classList.toggle("theme-light", S.theme==="light"); }

function toast(key,kind,raw){
  var box = $("toasts"); if(!box) return;
  var msg = raw ? key : t(key);
  var d = document.createElement("div");
  d.className = "toast"; d.setAttribute("data-kind", kind||"info");
  d.textContent = msg;
  box.appendChild(d);
  setTimeout(function(){ if(d.parentNode) d.parentNode.removeChild(d); }, 3200);
}

function logEv(kind, detail){
  S.log.push({ kind:kind, detail:detail||{}, t:Date.now() });
  if(S.log.length > 300) S.log.shift();
  if(S.view === "history") renderHistory();
}

function fmtClock(d){ function p(n){ return (n<10?"0":"")+n; } return p(d.getHours())+":"+p(d.getMinutes()); }
function fmtTime(ts){ var d=new Date(ts); function p(n){ return (n<10?"0":"")+n; } return p(d.getHours())+":"+p(d.getMinutes())+":"+p(d.getSeconds()); }

/* ---------------------------------------------------------------- */
/* modal helpers                                                      */
/* ---------------------------------------------------------------- */
function showModal(id){ var m=$(id); if(!m) return; m.classList.remove("hidden"); var f=qs("button",m); if(f) f.focus(); }
function hideModal(id){ var m=$(id); if(m) m.classList.add("hidden"); }
qsa(".modal-backdrop").forEach(function(m){
  on(m,"click",function(e){ if(e.target===m) m.classList.add("hidden"); });
});
on(document,"keydown",function(e){
  if(e.key==="Escape"){ qsa(".modal-backdrop:not(.hidden)").forEach(function(m){ m.classList.add("hidden"); }); }
});

var pendingDanger = null;
function confirmDanger(bodyKey, onConfirm){
  var body = $("dangerBody"); if(body) body.textContent = t(bodyKey);
  pendingDanger = onConfirm;
  showModal("modalDanger");
}
function emergencyStop(){
  boardPad.tool = "pen";
  pointerEnabled = false;
  var b = $("btnPtrEnable"); if(b) b.setAttribute("data-state","off");
  S.vision.running = false;
  var vb = $("btnVisionStart"); if(vb) vb.setAttribute("data-state","off");
  qsa(".modal-backdrop").forEach(function(m){ m.classList.add("hidden"); });
  setMode("safe");
  toast("danger.emergency","err");
  logEv("safety.emergency", {});
}

/* ---------------------------------------------------------------- */
/* status bar                                                         */
/* ---------------------------------------------------------------- */
function setMode(mode){
  var chip = $("modeChip"); var lbl = $("modeLabel");
  if(chip) chip.setAttribute("data-state", mode);
  if(lbl) lbl.setAttribute("data-i18n-html", "mode."+mode);
  if(lbl) lbl.textContent = t("mode."+mode);
}
function setChip(id, state){ var c=$(id); if(c) c.setAttribute("data-state", state); }

function startStatusCycle(){
  var order = ["stAI","stCalib","stSurface"];
  var i = 0;
  setInterval(function(){
    if(i < order.length){ setChip(order[i], "on"); i++; }
  }, 650);
  setInterval(function(){ var c=$("clock"); if(c) c.textContent = fmtClock(new Date()); }, 1000);
  var c0=$("clock"); if(c0) c0.textContent = fmtClock(new Date());
}

/* ---------------------------------------------------------------- */
/* navigation                                                         */
/* ---------------------------------------------------------------- */
function switchView(view){
  S.view = view;
  qsa(".view").forEach(function(v){ v.classList.remove("active"); });
  var el = $("view-"+view); if(el) el.classList.add("active");
  qsa(".navitem").forEach(function(b){ b.classList.toggle("active", b.getAttribute("data-view")===view); });
  logEv("view", {view:view});
  if(view==="dashboard") renderDashboard();
  if(view==="history") renderHistory();
  if(view==="settings") renderSettings();
  if(view==="privacy") renderStatic("privacyBody","privacy.body");
  if(view==="security") renderStatic("secBody","security.body");
  if(view==="air-quiz") renderQuiz();
  if(view==="air-presentation") renderPresentation();
  if(view==="air-lab"){ renderLabControls(); S.lab.t0 = performance.now(); }
  if(view==="air-3d") resizeCanvas(canvas3d, stage3dEl());
  if(view==="air-vision") resizeCanvas(canvasVision, $("visionWrap"));
  if(view==="calibration") refreshCalibView();
}
function stage3dEl(){ return $("stage3d"); }

function wireNav(){
  qsa(".navitem").forEach(function(b){
    on(b,"click", function(){ switchView(b.getAttribute("data-view")); });
  });
}

/* ---------------------------------------------------------------- */
/* language + top bar                                                 */
/* ---------------------------------------------------------------- */
function wireTopbar(){
  qsa(".langbtn").forEach(function(b){
    on(b,"click", function(){
      var lang = b.getAttribute("data-lang");
      if(window.i18n) window.i18n.setLang(lang);
      logEv("lang", {lang:lang});
    });
  });
  on($("btnFullscreen"),"click", function(){
    if(!document.fullscreenElement){ document.documentElement.requestFullscreen && document.documentElement.requestFullscreen().catch(function(){}); }
    else { document.exitFullscreen && document.exitFullscreen(); }
  });
  on($("btnMic"),"click", toggleVoice);
  on($("btnCam"),"click", function(){
    if(HA.state === "on") stopCamera();
    else startCamera();
  });
}

/* ---------------------------------------------------------------- */
/* ink pad — shared freehand engine for board + air draw               */
/* ---------------------------------------------------------------- */
function bboxOf(pts){
  var minX=1,minY=1,maxX=0,maxY=0;
  pts.forEach(function(p){ minX=Math.min(minX,p.x); maxX=Math.max(maxX,p.x); minY=Math.min(minY,p.y); maxY=Math.max(maxY,p.y); });
  return {minX:minX,minY:minY,maxX:maxX,maxY:maxY};
}
function detectShape(pts){
  var n = pts.length; if(n<8) return null;
  var i, cx=0, cy=0;
  for(i=0;i<n;i++){ cx+=pts[i].x; cy+=pts[i].y; }
  cx/=n; cy/=n;
  var maxR=0, rs=[];
  for(i=0;i<n;i++){
    var r = Math.hypot(pts[i].x-cx, pts[i].y-cy);
    maxR = Math.max(maxR,r); rs.push(r);
  }
  if(maxR < 0.01) return null;
  var norm = rs.map(function(r){ return r/maxR; });
  var avgR = norm.reduce(function(a,b){ return a+b; },0)/norm.length;
  var dev = norm.reduce(function(a,b){ return a+Math.abs(b-avgR); },0)/norm.length;
  var closed = Math.hypot(pts[0].x-pts[n-1].x, pts[0].y-pts[n-1].y) < 0.08;
  if(closed && dev < 0.22 && avgR > 0.25) return "circle";
  var bbox = bboxOf(pts);
  var w = bbox.maxX-bbox.minX, h = bbox.maxY-bbox.minY;
  var aspect = (w && h) ? Math.max(w/h, h/w) : 99;
  var turn = 0;
  for(i=1;i<n-1;i++){
    var a1 = Math.atan2(pts[i].y-pts[i-1].y, pts[i].x-pts[i-1].x);
    var a2 = Math.atan2(pts[i+1].y-pts[i].y, pts[i+1].x-pts[i].x);
    var d = a2-a1;
    while(d>Math.PI) d -= Math.PI*2;
    while(d<-Math.PI) d += Math.PI*2;
    turn += Math.abs(d);
  }
  if(!closed && turn < 1.2) return "line";
  if(closed && turn > 5.0 && turn < 7.9 && aspect < 1.45) return "square";
  if(closed && turn > 2.6 && turn < 5.2) return "triangle";
  return null;
}
function shapeEl(shape, bbox, color){
  var cx=(bbox.minX+bbox.maxX)/2*1000, cy=(bbox.minY+bbox.maxY)/2*640;
  var w=Math.max((bbox.maxX-bbox.minX)*1000,18), h=Math.max((bbox.maxY-bbox.minY)*640,18);
  var el;
  if(shape==="circle"){
    el=document.createElementNS(SVGNS,"ellipse");
    el.setAttribute("cx",cx); el.setAttribute("cy",cy);
    el.setAttribute("rx",Math.max(w,h)/2); el.setAttribute("ry",Math.max(w,h)/2);
  } else if(shape==="square"){
    el=document.createElementNS(SVGNS,"rect");
    el.setAttribute("x",cx-w/2); el.setAttribute("y",cy-h/2);
    el.setAttribute("width",w); el.setAttribute("height",h);
  } else if(shape==="triangle"){
    el=document.createElementNS(SVGNS,"polygon");
    el.setAttribute("points", cx+","+(cy-h/2)+" "+(cx+w/2)+","+(cy+h/2)+" "+(cx-w/2)+","+(cy+h/2));
  } else {
    el=document.createElementNS(SVGNS,"line");
    el.setAttribute("x1",cx-w/2); el.setAttribute("y1",cy);
    el.setAttribute("x2",cx+w/2); el.setAttribute("y2",cy);
  }
  el.setAttribute("fill", shape==="line" ? "none" : "rgba(0,229,255,.14)");
  el.setAttribute("stroke", color); el.setAttribute("stroke-width", 3);
  return el;
}
function makeInkPad(svg, opts){
  opts = opts || {};
  svg.setAttribute("viewBox","0 0 1000 640");
  svg.setAttribute("preserveAspectRatio","none");
  var pad = {
    svg: svg,
    strokes: [],
    redo: [],
    tool: opts.tool||"pen",
    color: opts.color||"#00e5ff",
    size: opts.size||4,
    shapes: !!opts.shapes,
    enabled: opts.enabled!==false,
    currents: {},
    onStroke: opts.onStroke,
    activeLayer: "draw",
    layers: {
      bg: { visible: true, type: "grid" },
      draw: { visible: true },
      geo: { visible: true }
    }
  };

  function pidOf(ev){ return (ev && ev.pointerId != null) ? ev.pointerId : 1; }
  function toLocal(ev){
    var r = svg.getBoundingClientRect();
    return { x: clamp((ev.clientX-r.left)/r.width,0,1), y: clamp((ev.clientY-r.top)/r.height,0,1) };
  }
  function pathD(pts){
    if(!pts.length) return "";
    var d = "M"+(pts[0].x*1000).toFixed(1)+","+(pts[0].y*640).toFixed(1);
    for(var i=1;i<pts.length;i++) d += " L"+(pts[i].x*1000).toFixed(1)+","+(pts[i].y*640).toFixed(1);
    return d;
  }
  function drawOne(st, container){
    var el;
    if(st.shape){ el = shapeEl(st.shape, bboxOf(st.pts), st.color); }
    else {
      el = document.createElementNS(SVGNS,"path");
      el.setAttribute("d", pathD(st.pts));
      el.setAttribute("fill","none");
      el.setAttribute("stroke", st.color);
      el.setAttribute("stroke-width", st.tool==="highlighter" ? st.size*4 : st.size);
      el.setAttribute("stroke-linecap","round"); el.setAttribute("stroke-linejoin","round");
      if(st.tool==="highlighter") el.setAttribute("opacity","0.35");
    }
    (container || svg).appendChild(el);
    return el;
  }
  function drawBgPattern(g){
    var type = pad.layers.bg ? pad.layers.bg.type : "grid";
    if(!type || type==="none") return;
    if(type==="grid"){
      for(var x=0; x<=1000; x+=50){
        var l = document.createElementNS(SVGNS,"line");
        l.setAttribute("x1", x); l.setAttribute("y1", 0); l.setAttribute("x2", x); l.setAttribute("y2", 640);
        l.setAttribute("stroke", "#1b2847"); l.setAttribute("stroke-width", x%100===0 ? "1.5" : "0.75");
        l.setAttribute("opacity", x%100===0 ? "0.6" : "0.35");
        g.appendChild(l);
      }
      for(var y=0; y<=640; y+=50){
        var l2 = document.createElementNS(SVGNS,"line");
        l2.setAttribute("x1", 0); l2.setAttribute("y1", y); l2.setAttribute("x2", 1000); l2.setAttribute("y2", y);
        l2.setAttribute("stroke", "#1b2847"); l2.setAttribute("stroke-width", y%100===0 ? "1.5" : "0.75");
        l2.setAttribute("opacity", y%100===0 ? "0.6" : "0.35");
        g.appendChild(l2);
      }
    } else if(type==="seyes"){
      var mg = document.createElementNS(SVGNS,"line");
      mg.setAttribute("x1", 120); mg.setAttribute("y1", 0); mg.setAttribute("x2", 120); mg.setAttribute("y2", 640);
      mg.setAttribute("stroke", "#ff4d6d"); mg.setAttribute("stroke-width", "2"); mg.setAttribute("opacity", "0.7");
      g.appendChild(mg);
      for(var sy=40; sy<=640; sy+=40){
        var ml = document.createElementNS(SVGNS,"line");
        ml.setAttribute("x1", 0); ml.setAttribute("y1", sy); ml.setAttribute("x2", 1000); ml.setAttribute("y2", sy);
        ml.setAttribute("stroke", "#4570ff"); ml.setAttribute("stroke-width", "1.5"); ml.setAttribute("opacity", "0.6");
        g.appendChild(ml);
        for(var sub=1; sub<4; sub++){
          var subl = document.createElementNS(SVGNS,"line");
          var suby = sy - sub*10;
          if(suby > 0){
            subl.setAttribute("x1", 0); subl.setAttribute("y1", suby); subl.setAttribute("x2", 1000); subl.setAttribute("y2", suby);
            subl.setAttribute("stroke", "#1e3056"); subl.setAttribute("stroke-width", "0.6"); subl.setAttribute("opacity", "0.4");
            g.appendChild(subl);
          }
        }
      }
    } else if(type==="axis"){
      var cx = 500, cy = 320;
      var axX = document.createElementNS(SVGNS,"line");
      axX.setAttribute("x1", 20); axX.setAttribute("y1", cy); axX.setAttribute("x2", 980); axX.setAttribute("y2", cy);
      axX.setAttribute("stroke", "#7cf7ff"); axX.setAttribute("stroke-width", "2");
      g.appendChild(axX);
      var axY = document.createElementNS(SVGNS,"line");
      axY.setAttribute("x1", cx); axY.setAttribute("y1", 20); axY.setAttribute("x2", cx); axY.setAttribute("y2", 620);
      axY.setAttribute("stroke", "#7cf7ff"); axY.setAttribute("stroke-width", "2");
      g.appendChild(axY);
      var arrX = document.createElementNS(SVGNS,"polygon");
      arrX.setAttribute("points", "975,315 990,320 975,325"); arrX.setAttribute("fill","#7cf7ff");
      g.appendChild(arrX);
      var arrY = document.createElementNS(SVGNS,"polygon");
      arrY.setAttribute("points", "495,25 500,10 505,25"); arrY.setAttribute("fill","#7cf7ff");
      g.appendChild(arrY);
      for(var gx=100; gx<=900; gx+=50){
        if(gx===cx) continue;
        var tkX = document.createElementNS(SVGNS,"line");
        tkX.setAttribute("x1", gx); tkX.setAttribute("y1", cy-5); tkX.setAttribute("x2", gx); tkX.setAttribute("y2", cy+5);
        tkX.setAttribute("stroke", "#7cf7ff"); tkX.setAttribute("stroke-width", "1.5");
        g.appendChild(tkX);
      }
      for(var gy=70; gy<=570; gy+=50){
        if(gy===cy) continue;
        var tkY = document.createElementNS(SVGNS,"line");
        tkY.setAttribute("x1", cx-5); tkY.setAttribute("y1", gy); tkY.setAttribute("x2", cx+5); tkY.setAttribute("y2", gy);
        tkY.setAttribute("stroke", "#7cf7ff"); tkY.setAttribute("stroke-width", "1.5");
        g.appendChild(tkY);
      }
    }
  }

  function renderAll(){
    while(svg.firstChild) svg.removeChild(svg.firstChild);
    var gBg = document.createElementNS(SVGNS,"g"); gBg.id = "boardLayerBg";
    var gDraw = document.createElementNS(SVGNS,"g"); gDraw.id = "boardLayerDraw";
    var gGeo = document.createElementNS(SVGNS,"g"); gGeo.id = "boardLayerGeo";

    if(pad.layers.bg && !pad.layers.bg.visible) gBg.setAttribute("display", "none");
    if(pad.layers.draw && !pad.layers.draw.visible) gDraw.setAttribute("display", "none");
    if(pad.layers.geo && !pad.layers.geo.visible) gGeo.setAttribute("display", "none");

    drawBgPattern(gBg);
    svg.appendChild(gBg);

    pad.strokes.forEach(function(st){
      var layer = st.layer || (st.shape ? "geo" : "draw");
      if(layer === "geo") drawOne(st, gGeo);
      else drawOne(st, gDraw);
    });

    Object.keys(pad.currents).forEach(function(k){
      var cur = pad.currents[k];
      if(cur){
        var targetG = (cur.layer==="geo") ? gGeo : gDraw;
        drawOne(cur, targetG);
      }
    });

    svg.appendChild(gDraw);
    svg.appendChild(gGeo);
  }

  function eraseAt(p){
    var before = pad.strokes.length;
    pad.strokes = pad.strokes.filter(function(st){
      var layer = st.layer || (st.shape ? "geo" : "draw");
      if(pad.layers[layer] && !pad.layers[layer].visible) return true;
      return !st.pts.some(function(q){ return Math.hypot(q.x-p.x,q.y-p.y) < 0.035; });
    });
    if(pad.strokes.length !== before){ pad.redo.length=0; renderAll(); }
  }
  function down(ev){
    if(!pad.enabled) return;
    if(pad.tool==="eraser"){ eraseAt(toLocal(ev)); return; }
    var l = (pad.activeLayer==="bg") ? "draw" : (pad.activeLayer || "draw");
    pad.currents[pidOf(ev)] = { tool:pad.tool, color:pad.color, size:pad.size, pts:[toLocal(ev)], layer: l };
  }
  function move(ev){
    if(!pad.enabled) return;
    if(pad.tool==="eraser"){ if(ev.buttons) eraseAt(toLocal(ev)); return; }
    var cur = pad.currents[pidOf(ev)];
    if(!cur) return;
    var p = toLocal(ev);
    var last = cur.pts[cur.pts.length-1];
    if(last && Math.hypot(p.x-last.x,p.y-last.y) < 0.003) return;
    cur.pts.push(p);
    renderAll();
  }
  function up(ev){
    var cur = pad.currents[pidOf(ev)];
    if(!cur) return;
    delete pad.currents[pidOf(ev)];
    if(cur.pts.length < 2) return;
    if(pad.shapes && cur.pts.length >= 8){
      var shape = detectShape(cur.pts);
      if(shape){ cur.shape = shape; cur.layer = "geo"; }
    }
    if(!cur.layer) cur.layer = pad.activeLayer || "draw";
    pad.strokes.push(cur); pad.redo.length = 0;
    renderAll();
    if(pad.onStroke) pad.onStroke(cur);
  }
  var host = svg.parentNode;
  on(host,"pointerdown", down);
  on(host,"pointermove", move);
  on(host,"pointerup", up);
  on(host,"pointerleave", up);
  pad.undo = function(){ if(!pad.strokes.length) return false; pad.redo.push(pad.strokes.pop()); renderAll(); return true; };
  pad.redoLast = function(){ if(!pad.redo.length) return false; pad.strokes.push(pad.redo.pop()); renderAll(); return true; };
  pad.clear = function(){ pad.strokes=[]; pad.redo=[]; pad.currents={}; renderAll(); };
  pad.renderAll = renderAll;
  pad.setLayerVisibility = function(name, visible){
    if(pad.layers[name]){ pad.layers[name].visible = !!visible; renderAll(); }
  };
  pad.setBackgroundType = function(type){
    if(pad.layers.bg){ pad.layers.bg.type = type; renderAll(); }
  };
  pad.setActiveLayer = function(name){
    pad.activeLayer = name;
  };
  renderAll();
  return pad;
}

var boardPad, airDrawPad;

function exportPedagogicalPdf(pad){
  try{
    var svgEl = pad.svg;
    var svgData = new XMLSerializer().serializeToString(svgEl);
    var printWin = window.open("","edu_air_print","width=1100,height=750");
    if(!printWin){ toast("smart.save","warn"); return; }
    var now = new Date().toLocaleString("fr-FR",{dateStyle:"full",timeStyle:"short"});
    var bgType = (pad.layers.bg && pad.layers.bg.type) ? pad.layers.bg.type : "grid";
    var html = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>EDU-AIR — Session Tableau Numérique Interactif</title>' +
      '<style>' +
      '@page{size:landscape;margin:10mm}' +
      'body{font-family:system-ui,-apple-system,sans-serif;margin:0;padding:16px;background:#fff;color:#111}' +
      '.header{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #00a3bf;padding-bottom:10px;margin-bottom:12px}' +
      '.logo{font-size:20px;font-weight:900;letter-spacing:1px;color:#05070d}.logo span{color:#00a3bf}' +
      '.meta{text-align:right;font-size:11px;color:#555}' +
      '.stage-box{border:1.5px solid #1b2847;border-radius:8px;background:#091020;padding:6px;box-shadow:0 4px 12px rgba(0,0,0,0.15)}' +
      'svg{width:100%;height:auto;display:block;border-radius:4px}' +
      '.notes{margin-top:12px;border:1px dashed #bbb;border-radius:6px;padding:8px 12px;font-size:11px;color:#444}' +
      '.footer{display:flex;justify-content:space-between;align-items:center;margin-top:12px;font-size:10px;color:#777;border-top:1px solid #ddd;padding-top:8px}' +
      '@media print{.no-print{display:none !important}}' +
      '</style></head><body>' +
      '<div class="no-print" style="margin-bottom:12px;text-align:right"><button onclick="window.print()" style="padding:8px 18px;background:#00a3bf;color:#fff;border:none;border-radius:6px;font-weight:bold;cursor:pointer;font-size:13px">🖨️ Imprimer ou Enregistrer en PDF</button></div>' +
      '<div class="header">' +
      '  <div class="logo">EDU-AIR <span>SMART SURFACE</span> &bull; TNI Éducatif</div>' +
      '  <div class="meta"><div><strong>Date :</strong> ' + now + '</div><div><strong>Mode :</strong> Sans contact &bull; Fond : ' + bgType.toUpperCase() + '</div></div>' +
      '</div>' +
      '<div class="stage-box">' + svgData + '</div>' +
      '<div class="notes"><strong>Annotations pédagogiques & Remarques de cours :</strong> </div>' +
      '<div class="footer">' +
      '  <div>EDU-AIR Smart Surface — 100% On-Device & Conforme RGPD Scolaire</div>' +
      '  <div>Tableau Numérique Interactif (65"–86")</div>' +
      '</div>' +
      '<script>setTimeout(function(){ window.print(); }, 400);<\/script>' +
      '</body></html>';
    printWin.document.open();
    printWin.document.write(html);
    printWin.document.close();
    toast("PDF Pédagogique généré","ok");
  }catch(e){ toast("smart.save","warn"); }
}

function exportOpenBoard(pad){
  try{
    var svgData = new XMLSerializer().serializeToString(pad.svg);
    var openBoardSvg = '<?xml version="1.0" encoding="UTF-8"?>\n' +
      '<!-- Generated by EDU-AIR SMART SURFACE for OpenBoard TNI -->\n' +
      '<svg xmlns="http://www.w3.org/2000/svg" xmlns:ub="http://uniboard.mnemis.com/openboard" version="1.1" viewBox="0 0 1000 640" width="100%" height="100%">\n' +
      '  <metadata>\n' +
      '    <ub:page-count>1</ub:page-count>\n' +
      '    <ub:date>' + new Date().toISOString() + '</ub:date>\n' +
      '    <ub:generator>EDU-AIR Smart Surface TNI</ub:generator>\n' +
      '  </metadata>\n' +
      svgData.replace(/<svg[^>]*>/, "").replace(/<\/svg>/, "") +
      '\n</svg>';
    var blob = new Blob([openBoardSvg], {type: "image/svg+xml;charset=utf-8"});
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = "edu-air-openboard-page.svg";
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function(){ URL.revokeObjectURL(url); }, 2000);
    toast("OpenBoard SVG exporté","ok");
  }catch(e){ toast("smart.save","warn"); }
}

function exportPng4k(pad){
  try{
    var canvas = document.createElement("canvas");
    canvas.width = 3840; canvas.height = 2457;
    var ctx = canvas.getContext("2d");
    ctx.fillStyle = "#05070d";
    ctx.fillRect(0,0,canvas.width,canvas.height);

    var svgData = new XMLSerializer().serializeToString(pad.svg);
    var img = new Image();
    var blob = new Blob([svgData], {type: "image/svg+xml;charset=utf-8"});
    var url = URL.createObjectURL(blob);
    img.onload = function(){
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      canvas.toBlob(function(pngBlob){
        if(!pngBlob) return;
        var pngUrl = URL.createObjectURL(pngBlob);
        var a = document.createElement("a");
        a.href = pngUrl; a.download = "edu-air-tableau-4k.png";
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        setTimeout(function(){ URL.revokeObjectURL(pngUrl); }, 2000);
        toast("Image HD 4K TNI exportée","ok");
      }, "image/png");
    };
    img.src = url;
  }catch(e){ toast("smart.save","warn"); }
}

function wireSmartSurface(){
  var svg = $("boardSvg");
  boardPad = makeInkPad(svg, { tool:"pen", color:$("inkColor").value, shapes:$("chkShapes").checked, size:4,
    onStroke: function(st){
      if(navigator.vibrate && $("chkHaptics").checked) navigator.vibrate(8);
      logEv("draw.stroke", {shape: st.shape||null, layer: st.layer||"draw"});
      if(st.shape) toast("shape."+st.shape, "ok");
    }
  });

  qsa(".btbtn.tool", $("boardToolbar")).forEach(function(b){
    on(b,"click", function(){
      boardPad.tool = b.getAttribute("data-tool");
      qsa(".btbtn.tool", $("boardToolbar")).forEach(function(x){ x.setAttribute("data-state", x===b?"active":""); });
      var hint = $("boardHint"); if(hint) hint.textContent = boardPad.tool.toUpperCase();
      var lbl = $("hudLabel"); if(lbl) lbl.textContent = boardPad.tool.toUpperCase();
    });
  });

  /* TNI Layer Controls */
  function bindLayerPill(layerName, visBtnId, selBtnId, pillId){
    var visBtn = $(visBtnId), selBtn = $(selBtnId), pill = $(pillId);
    if(visBtn){
      on(visBtn,"click", function(e){
        e.stopPropagation();
        var isVis = !boardPad.layers[layerName].visible;
        boardPad.setLayerVisibility(layerName, isVis);
        visBtn.textContent = isVis ? "👁️" : "🕶️";
        visBtn.classList.toggle("off", !isVis);
        toast(layerName.toUpperCase() + (isVis ? " visible" : " masqué"), "info");
      });
    }
    if(selBtn){
      on(selBtn,"click", function(){
        boardPad.setActiveLayer(layerName);
        qsa(".layer-pill", $("boardToolbar")).forEach(function(p){ p.classList.remove("active"); });
        if(pill) pill.classList.add("active");
        toast("Calque actif : " + layerName.toUpperCase(), "info");
      });
    }
  }
  bindLayerPill("bg", "btnVisBg", "btnSelBg", "pillBg");
  bindLayerPill("draw", "btnVisDraw", "btnSelDraw", "pillDraw");
  bindLayerPill("geo", "btnVisGeo", "btnSelGeo", "pillGeo");

  var selBg = $("selBgType");
  if(selBg){
    on(selBg, "change", function(){
      boardPad.setBackgroundType(this.value);
      toast("Fond : " + this.value.toUpperCase(), "info");
    });
  }

  /* TNI Export Dropdown */
  var expBtn = $("btnExportTniMenu"), expMenu = $("exportTniMenu");
  if(expBtn && expMenu){
    on(expBtn, "click", function(e){
      e.stopPropagation();
      expMenu.classList.toggle("hidden");
    });
    document.addEventListener("click", function(e){
      if(!expMenu.contains(e.target) && e.target !== expBtn){
        expMenu.classList.add("hidden");
      }
    });
  }
  var btnExpPdf = $("btnExpPdf"); if(btnExpPdf) on(btnExpPdf, "click", function(){ expMenu.classList.add("hidden"); exportPedagogicalPdf(boardPad); });
  var btnExpOb = $("btnExpOpenBoard"); if(btnExpOb) on(btnExpOb, "click", function(){ expMenu.classList.add("hidden"); exportOpenBoard(boardPad); });
  var btnExp4k = $("btnExpPng4k"); if(btnExp4k) on(btnExp4k, "click", function(){ expMenu.classList.add("hidden"); exportPng4k(boardPad); });
  var btnExpSvg = $("btnExpSvgLayers"); if(btnExpSvg) on(btnExpSvg, "click", function(){
    expMenu.classList.add("hidden");
    $("btnSaveBoard").click();
  });

  on($("inkColor"),"input", function(){ boardPad.color = this.value; });
  on($("chkShapes"),"change", function(){ boardPad.shapes = this.checked; });
  on($("btnUndo"),"click", function(){ if(!boardPad.undo()) toast("draw.nothing","info"); });
  on($("btnRedo"),"click", function(){ boardPad.redoLast(); });
  on($("btnClearBoard"),"click", function(){
    confirmDanger("danger.body", function(){ boardPad.clear(); toast("draw.cleared","info"); logEv("board.clear",{}); });
  });
  on($("btnSaveBoard"),"click", function(){
    try{
      var data = new XMLSerializer().serializeToString($("boardSvg"));
      var blob = new Blob([data], {type:"image/svg+xml"});
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a"); a.href = url; a.download = "edu-air-board.svg";
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      setTimeout(function(){ URL.revokeObjectURL(url); }, 2000);
      toast("smart.save","ok");
    }catch(e){ toast("smart.save","warn"); }
  });
  /* Geometry Instruments */
  var activeInstrument = null;
  var instPos = { x: 140, y: 100, rot: 0 };

  function renderInstrument(){
    var overlay = $("boardOverlay");
    if(!overlay) return;
    overlay.innerHTML = "";
    if(!activeInstrument){
      qsa(".bt-instruments .btbtn", $("boardToolbar")).forEach(function(b){ b.classList.remove("active"); });
      return;
    }
    qsa(".bt-instruments .btbtn", $("boardToolbar")).forEach(function(b){
      b.classList.toggle("active", b.id === ("btnInst" + activeInstrument.charAt(0).toUpperCase() + activeInstrument.slice(1)));
    });

    var div = document.createElement("div");
    div.className = "geom-instrument";
    div.style.left = instPos.x + "px";
    div.style.top = instPos.y + "px";
    div.style.transform = "rotate(" + instPos.rot + "deg)";

    var ctrls = document.createElement("div");
    ctrls.className = "geom-ctrls";
    ctrls.innerHTML = '<button type="button" class="geom-btn" id="btnInstRotCCW">↺ -15°</button>' +
                      '<button type="button" class="geom-btn" id="btnInstRotCW">↻ +15°</button>' +
                      '<button type="button" class="geom-btn" id="btnInstReset">0°</button>' +
                      '<button type="button" class="geom-btn geom-btn-close" id="btnInstClose">✕</button>';
    div.appendChild(ctrls);

    var svgInst = "";
    if(activeInstrument === "ruler"){
      var marks = "";
      for(var cm=0; cm<=25; cm++){
        var x = 20 + cm * 18;
        marks += '<line x1="'+x+'" y1="0" x2="'+x+'" y2="24" stroke="#00e5ff" stroke-width="1.5"/>';
        marks += '<text x="'+(x-4)+'" y="38" fill="#c7d4ee" font-size="10" font-family="monospace">'+cm+'</text>';
        for(var mm=1; mm<10; mm++){
          if(cm===25) break;
          var mx = x + mm * 1.8;
          var my = (mm===5) ? 16 : 9;
          marks += '<line x1="'+mx+'" y1="0" x2="'+mx+'" y2="'+my+'" stroke="#00e5ff" stroke-width="0.75" opacity="0.6"/>';
        }
      }
      svgInst = '<svg width="490" height="75" viewBox="0 0 490 75">' +
        '<rect x="0" y="0" width="490" height="75" rx="6" fill="rgba(10,18,36,0.85)" stroke="#00e5ff" stroke-width="2"/>' +
        marks +
        '<text x="240" y="62" fill="#7cf7ff" font-size="11" font-weight="bold" font-family="sans-serif" text-anchor="middle">RÈGLE SCOLAIRE &bull; 25 CM &bull; EDU-AIR TNI</text>' +
        '</svg>';
    } else if(activeInstrument === "protractor"){
      var pmarks = "";
      for(var deg=0; deg<=180; deg+=10){
        var rad = (180 - deg) * Math.PI / 180;
        var cx = 180, cy = 180, r1 = 170, r2 = (deg%30===0) ? 140 : 152;
        var x1 = cx + r1 * Math.cos(rad), y1 = cy - r1 * Math.sin(rad);
        var x2 = cx + r2 * Math.cos(rad), y2 = cy - r2 * Math.sin(rad);
        pmarks += '<line x1="'+x1+'" y1="'+y1+'" x2="'+x2+'" y2="'+y2+'" stroke="#ffc24b" stroke-width="'+(deg%30===0?1.8:1)+'"/>';
        if(deg%30===0){
          var xt = cx + 126 * Math.cos(rad), yt = cy - 126 * Math.sin(rad) + 4;
          pmarks += '<text x="'+xt+'" y="'+yt+'" fill="#c7d4ee" font-size="10" font-family="monospace" text-anchor="middle">'+deg+'°</text>';
        }
      }
      svgInst = '<svg width="360" height="195" viewBox="0 0 360 195">' +
        '<path d="M 10 180 A 170 170 0 0 1 350 180 Z" fill="rgba(10,18,36,0.85)" stroke="#ffc24b" stroke-width="2"/>' +
        pmarks +
        '<line x1="10" y1="180" x2="350" y2="180" stroke="#ffc24b" stroke-width="2"/>' +
        '<circle cx="180" cy="180" r="5" fill="#00e5ff"/>' +
        '<text x="180" y="100" fill="#ffc24b" font-size="11" font-weight="bold" font-family="sans-serif" text-anchor="middle">RAPPORTEUR 180° TNI</text>' +
        '</svg>';
    } else if(activeInstrument === "square"){
      var smarks = "";
      for(var scm=0; scm<=16; scm++){
        var sy = 290 - scm * 16;
        smarks += '<line x1="20" y1="'+sy+'" x2="38" y2="'+sy+'" stroke="#00e5ff" stroke-width="1.5"/>';
        if(scm%2===0) smarks += '<text x="44" y="'+(sy+4)+'" fill="#c7d4ee" font-size="9" font-family="monospace">'+scm+'</text>';
      }
      for(var sx=0; sx<=16; sx++){
        var sxx = 20 + sx * 16;
        smarks += '<line x1="'+sxx+'" y1="290" x2="'+sxx+'" y2="272" stroke="#00e5ff" stroke-width="1.5"/>';
        if(sx%2===0) smarks += '<text x="'+(sxx-3)+'" y="265" fill="#c7d4ee" font-size="9" font-family="monospace">'+sx+'</text>';
      }
      svgInst = '<svg width="320" height="320" viewBox="0 0 320 320">' +
        '<polygon points="20,20 20,290 290,290" fill="rgba(10,18,36,0.85)" stroke="#00e5ff" stroke-width="2"/>' +
        '<polygon points="55,120 55,255 190,255" fill="#05070d" stroke="#1b2847" stroke-width="1.5"/>' +
        '<rect x="20" y="270" width="20" height="20" fill="none" stroke="#ffc24b" stroke-width="1.5"/>' +
        smarks +
        '<text x="110" y="210" fill="#00e5ff" font-size="11" font-weight="bold" font-family="sans-serif" transform="rotate(-45 110 210)">ÉQUERRE 90° &bull; TNI</text>' +
        '</svg>';
    }

    var wrapSvg = document.createElement("div");
    wrapSvg.innerHTML = svgInst;
    div.appendChild(wrapSvg);

    var dragging = false, dragOffX = 0, dragOffY = 0;
    on(div, "pointerdown", function(e){
      if(e.target.closest(".geom-ctrls")) return;
      dragging = true;
      dragOffX = e.clientX - instPos.x;
      dragOffY = e.clientY - instPos.y;
      try{ div.setPointerCapture(e.pointerId); }catch(_){}
    });
    on(div, "pointermove", function(e){
      if(!dragging) return;
      instPos.x = e.clientX - dragOffX;
      instPos.y = e.clientY - dragOffY;
      div.style.left = instPos.x + "px";
      div.style.top = instPos.y + "px";
    });
    on(div, "pointerup", function(e){
      dragging = false;
      try{ div.releasePointerCapture(e.pointerId); }catch(_){}
    });

    overlay.appendChild(div);

    var btnRotCCW = $("btnInstRotCCW");
    if(btnRotCCW) on(btnRotCCW, "click", function(){ instPos.rot = (instPos.rot - 15) % 360; div.style.transform = "rotate("+instPos.rot+"deg)"; });
    var btnRotCW = $("btnInstRotCW");
    if(btnRotCW) on(btnRotCW, "click", function(){ instPos.rot = (instPos.rot + 15) % 360; div.style.transform = "rotate("+instPos.rot+"deg)"; });
    var btnReset = $("btnInstReset");
    if(btnReset) on(btnReset, "click", function(){ instPos.rot = 0; div.style.transform = "rotate(0deg)"; });
    var btnClose = $("btnInstClose");
    if(btnClose) on(btnClose, "click", function(){ activeInstrument = null; renderInstrument(); toast("Instrument masqué","info"); });
  }

  function toggleInstrument(type){
    if(activeInstrument === type){ activeInstrument = null; }
    else { activeInstrument = type; }
    renderInstrument();
    toast(activeInstrument ? (type.toUpperCase() + " activé(e)") : "Instrument rangé", "ok");
  }
  var bRuler = $("btnInstRuler"); if(bRuler) on(bRuler, "click", function(){ toggleInstrument("ruler"); });
  var bProt = $("btnInstProtractor"); if(bProt) on(bProt, "click", function(){ toggleInstrument("protractor"); });
  var bSquare = $("btnInstSquare"); if(bSquare) on(bSquare, "click", function(){ toggleInstrument("square"); });

  var stage = $("boardStage"), hud = $("hudPointer");
  on(stage,"pointerleave", function(){ if(hud) hud.classList.add("hidden"); });
  on(stage,"pointermove", function(e){
    if(!hud) return;
    var r = stage.getBoundingClientRect();
    hud.style.left = (e.clientX-r.left) + "px";
    hud.style.top = (e.clientY-r.top) + "px";
    hud.classList.remove("hidden");
  });
}

/* ---------------------------------------------------------------- */
/* air pointer                                                        */
/* ---------------------------------------------------------------- */
var pointerEnabled = false, pointerCursor = null;
function wireAirPointer(){
  var stage = $("ptrStage");
  pointerCursor = document.createElement("div");
  pointerCursor.className = "air-cursor hidden";
  stage.appendChild(pointerCursor);
  on(stage,"pointermove", function(e){
    if(!pointerEnabled) return;
    var r = stage.getBoundingClientRect();
    pointerCursor.classList.remove("hidden");
    pointerCursor.style.left = (e.clientX-r.left) + "px";
    pointerCursor.style.top = (e.clientY-r.top) + "px";
  });
  on(stage,"pointerleave", function(){ pointerCursor.classList.add("hidden"); });
  on($("btnPtrEnable"),"click", function(){
    pointerEnabled = !pointerEnabled;
    this.setAttribute("data-state", pointerEnabled?"on":"off");
    if(!pointerEnabled) pointerCursor.classList.add("hidden");
    toast(pointerEnabled?"pointer.on":"pointer.off","ok");
    logEv("pointer", {on:pointerEnabled});
  });
  on($("btnPtrClick"),"click", function(){
    if(!pointerEnabled){ toast("pointer.off","warn"); return; }
    pointerCursor.classList.add("tap");
    setTimeout(function(){ pointerCursor.classList.remove("tap"); }, 260);
    toast("air.tap","ok");
    logEv("pointer.tap", {});
  });
}

/* ---------------------------------------------------------------- */
/* air draw                                                           */
/* ---------------------------------------------------------------- */
function wireAirDraw(){
  var host = $("drawStage");
  var svg = document.createElementNS(SVGNS,"svg");
  svg.setAttribute("class","board-svg");
  host.appendChild(svg);
  airDrawPad = makeInkPad(svg, { tool:"pen", color:"#ffc24b", shapes:true, size:4, enabled:false,
    onStroke: function(st){ logEv("airdraw.stroke", {shape:st.shape||null}); if(st.shape) toast("shape."+st.shape,"ok"); }
  });
  on($("btnDrawEnable"),"click", function(){
    airDrawPad.enabled = !airDrawPad.enabled;
    this.setAttribute("data-state", airDrawPad.enabled?"on":"off");
    toast(airDrawPad.enabled?"draw.on":"draw.off","ok");
    logEv("draw", {on:airDrawPad.enabled});
  });
  on($("drawAimDot"),"click", function(){
    var on_ = this.getAttribute("data-state")!=="on";
    this.setAttribute("data-state", on_?"on":"off");
    host.classList.toggle("aim-on", on_);
  });
}

/* ---------------------------------------------------------------- */
/* air 3D                                                             */
/* ---------------------------------------------------------------- */
var canvas3d;
function models3d(){
  function ring(nx,ny,r){ var pts=[]; for(var i=0;i<nx;i++){ var a=i/nx*Math.PI*2; pts.push([Math.cos(a)*r, ny, Math.sin(a)*r]); } return pts; }
  var M = {};
  M.cube = { pts:[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],
    edges:[[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]] };
  M.pyramid = { pts:[[-1,1,-1],[1,1,-1],[1,1,1],[-1,1,1],[0,-1.3,0]],
    edges:[[0,1],[1,2],[2,3],[3,0],[0,4],[1,4],[2,4],[3,4]] };
  (function(){
    var pts=[], edges=[], rings=8, seg=14;
    for(var i=0;i<=rings;i++){
      var v = (i/rings)*Math.PI;
      for(var j=0;j<seg;j++){
        var u = (j/seg)*Math.PI*2;
        pts.push([Math.sin(v)*Math.cos(u), Math.cos(v), Math.sin(v)*Math.sin(u)]);
        var idx = pts.length-1;
        if(j>0) edges.push([idx-1, idx]);
        if(i>0) edges.push([idx-seg, idx]);
      }
    }
    M.sphere = { pts:pts, edges:edges, scale:1.15 };
  })();
  (function(){
    var pts=[], edges=[], R=1, r=0.4, rings=16, seg=10;
    for(var i=0;i<rings;i++){
      var u=(i/rings)*Math.PI*2;
      for(var j=0;j<seg;j++){
        var v=(j/seg)*Math.PI*2;
        pts.push([(R+r*Math.cos(v))*Math.cos(u), r*Math.sin(v), (R+r*Math.cos(v))*Math.sin(u)]);
        var idx=pts.length-1;
        if(j>0) edges.push([idx-1,idx]); else edges.push([idx, idx+seg-1]);
        if(i>0) edges.push([idx-seg, idx]);
      }
    }
    M.torus = { pts:pts, edges:edges, scale:1.1 };
  })();
  (function(){
    var pts=[], edges=[], n=48;
    for(var i=0;i<n;i++){
      var a = i/n*Math.PI*4;
      var y = (i/n)*2-1;
      pts.push([Math.cos(a)*0.8, y*1.3, Math.sin(a)*0.8]);
      pts.push([Math.cos(a+Math.PI)*0.8, y*1.3, Math.sin(a+Math.PI)*0.8]);
      var b = pts.length-1;
      edges.push([b-1,b]);
      if(i>0){ edges.push([b-3,b-1]); edges.push([b-2,b]); }
      if(i%4===0) edges.push([b-1,b]);
    }
    M.dna = { pts:pts, edges:edges, scale:1 };
  })();
  (function(){
    var pts=[], edges=[], n=40;
    for(var i=0;i<n;i++){
      var a = i/n*Math.PI*2;
      var x = 1.1*Math.pow(Math.sin(a),3);
      var y = -(0.9*Math.cos(a)-0.35*Math.cos(2*a)-0.15*Math.cos(3*a)-0.07*Math.cos(4*a));
      pts.push([x, y, 0.28]); pts.push([x, y, -0.28]);
      var b = pts.length-1;
      edges.push([b-1,b]);
      if(i>0){ edges.push([b-3,b-1]); edges.push([b-2,b]); }
    }
    M.heart = { pts:pts, edges:edges, scale:1.1 };
  })();
  (function(){
    var pts=[], edges=[], rings=7, seg=12;
    for(var i=0;i<=rings;i++){
      var v=(i/rings)*Math.PI;
      for(var j=0;j<seg;j++){
        var u=(j/seg)*Math.PI*2;
        var bump = 1 + 0.12*Math.sin(u*5+v*7);
        pts.push([Math.sin(v)*Math.cos(u)*bump, Math.cos(v)*0.85, Math.sin(v)*Math.sin(u)*bump]);
        var idx=pts.length-1;
        if(j>0) edges.push([idx-1,idx]);
        if(i>0) edges.push([idx-seg, idx]);
      }
    }
    M.brain = { pts:pts, edges:edges, scale:1.1 };
  })();
  (function(){
    var pts=[[0,0,0],[1,0.6,0],[-1,0.6,0],[0,-0.9,0.8],[0,-0.9,-0.8],[0.4,1.1,0.9]];
    var edges=[[0,1],[0,2],[0,3],[0,4],[0,5]];
    M.molecule = { pts:pts, edges:edges, scale:1.2, dots:true };
  })();
  return M;
}
var MODELS3D = models3d();

function resizeCanvas(canvas, container){
  if(!canvas || !container) return;
  var w = container.clientWidth||400, h = container.clientHeight||300;
  if(canvas.width!==w) canvas.width = w;
  if(canvas.height!==h) canvas.height = h;
}
function rotPoint(p, rx, ry){
  var y = p[1]*Math.cos(rx) - p[2]*Math.sin(rx);
  var z = p[1]*Math.sin(rx) + p[2]*Math.cos(rx);
  var x = p[0]*Math.cos(ry) + z*Math.sin(ry);
  z = -p[0]*Math.sin(ry) + z*Math.cos(ry);
  return [x,y,z];
}
function draw3D(){
  if(!canvas3d) return;
  var ctx = canvas3d.getContext("2d");
  var w = canvas3d.width, h = canvas3d.height;
  ctx.clearRect(0,0,w,h);
  if(!w || !h) return;
  var model = MODELS3D[S.threed.model] || MODELS3D.cube;
  var scale = (model.scale||1) * Math.min(w,h)*0.24;
  var cx = w/2, cy = h/2;
  var explode = S.threed.explode ? 1.35 : 1;
  var proj = model.pts.map(function(p){
    var e = [p[0]*explode, p[1]*explode, p[2]*explode];
    var r = rotPoint(e, S.threed.rotX, S.threed.rotY);
    var persp = 3/(3+r[2]);
    return { x: cx+r[0]*scale*persp, y: cy+r[1]*scale*persp, z:r[2], s:persp };
  });
  ctx.strokeStyle = "rgba(0,229,255,.75)";
  ctx.fillStyle = "#7cf7ff";
  ctx.lineWidth = 1.4;
  if(!S.threed.wire && !model.dots){
    (model.edges||[]).forEach(function(ed){
      var a=proj[ed[0]], b=proj[ed[1]]; if(!a||!b) return;
      ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke();
    });
  }
  proj.forEach(function(p){
    var r = clamp(2.2*p.s, 1, 4.5);
    ctx.beginPath(); ctx.arc(p.x,p.y,r,0,Math.PI*2); ctx.fill();
  });
  var hud = $("hud3d");
  if(hud) hud.textContent = (t("nav."+ (S.threed.model==="threed"?"threed":"threed")) ? S.threed.model.toUpperCase() : S.threed.model.toUpperCase()) + " · " + Math.round(S.threed.rotY*180/Math.PI%360) + "°";
}
var drag3d = null;
function wireAir3D(){
  canvas3d = $("canvas3d");
  var stage = $("stage3d");
  resizeCanvas(canvas3d, stage);
  on(window,"resize", function(){ if(S.view==="air-3d") resizeCanvas(canvas3d, stage); });
  on(stage,"pointerdown", function(e){ drag3d = {x:e.clientX,y:e.clientY,rx:S.threed.rotX,ry:S.threed.rotY}; });
  on(window,"pointermove", function(e){
    if(!drag3d || S.view!=="air-3d") return;
    S.threed.rotY = drag3d.ry + (e.clientX-drag3d.x)*0.01;
    S.threed.rotX = clamp(drag3d.rx + (e.clientY-drag3d.y)*0.01, -1.4, 1.4);
  });
  on(window,"pointerup", function(){ drag3d = null; });
  qsa(".mdlchip", $("view-air-3d")).forEach(function(b){
    on(b,"click", function(){
      S.threed.model = b.getAttribute("data-model");
      qsa(".mdlchip", $("view-air-3d")).forEach(function(x){ x.classList.toggle("active", x===b); x.setAttribute("aria-pressed", x===b?"true":"false"); });
      logEv("3d.model", {model:S.threed.model});
    });
  });
  on($("btn3dHome"),"click", function(){ S.threed.rotX=-0.5; S.threed.rotY=0.6; });
  on($("btn3dAuto"),"click", function(){ S.threed.auto = !S.threed.auto; this.setAttribute("data-state", S.threed.auto?"on":""); });
  on($("chk3dExplode"),"change", function(){ S.threed.explode = this.checked; });
  on($("chk3dWire"),"change", function(){ S.threed.wire = this.checked; });
}

/* ---------------------------------------------------------------- */
/* air vision (simulated — no camera ever requested)                   */
/* ---------------------------------------------------------------- */
var canvasVision, visionBoxes = [], visionLabels = ["hand","pen","book","face","marker"];
function wireAirVision(){
  canvasVision = $("canvasVision");
  resizeCanvas(canvasVision, $("visionWrap"));
  on(window,"resize", function(){ if(S.view==="air-vision") resizeCanvas(canvasVision, $("visionWrap")); });
  on($("btnVisionStart"),"click", function(){
    S.vision.running = !S.vision.running;
    this.setAttribute("data-state", S.vision.running?"on":"off");
    setChip("visionFps", S.vision.running?"on":"off");
    if(S.vision.running) seedVisionBoxes();
    toast(S.vision.running?"vision.start":"vision.stop","ok");
    logEv("vision", {on:S.vision.running});
  });
}
function seedVisionBoxes(){
  visionBoxes = [];
  var n = 2 + Math.floor(Math.random()*2);
  for(var i=0;i<n;i++){
    visionBoxes.push({
      x: Math.random()*0.6, y: Math.random()*0.6, w: 0.18+Math.random()*0.12, h: 0.18+Math.random()*0.12,
      label: visionLabels[Math.floor(Math.random()*visionLabels.length)],
      conf: 0.7 + Math.random()*0.28,
      vx: (Math.random()-0.5)*0.0025, vy: (Math.random()-0.5)*0.0025
    });
  }
}
function drawVision(){
  if(!canvasVision) return;
  var ctx = canvasVision.getContext("2d");
  var w = canvasVision.width, h = canvasVision.height;
  ctx.clearRect(0,0,w,h);
  if(!w || !h) return;
  ctx.fillStyle = "#0a1224"; ctx.fillRect(0,0,w,h);
  ctx.strokeStyle = "rgba(0,229,255,.18)"; ctx.lineWidth=1;
  for(var gx=0; gx<w; gx+=40){ ctx.beginPath(); ctx.moveTo(gx,0); ctx.lineTo(gx,h); ctx.stroke(); }
  for(var gy=0; gy<h; gy+=40){ ctx.beginPath(); ctx.moveTo(0,gy); ctx.lineTo(w,gy); ctx.stroke(); }
  var list = $("visionResults");
  var rows = [];
  if(S.vision.running){
    visionBoxes.forEach(function(b){
      b.x += b.vx; b.y += b.vy;
      if(b.x<0||b.x+b.w>1) b.vx*=-1;
      if(b.y<0||b.y+b.h>1) b.vy*=-1;
      var px=b.x*w, py=b.y*h, pw=b.w*w, ph=b.h*h;
      ctx.strokeStyle = "#00e5ff"; ctx.lineWidth=2;
      ctx.strokeRect(px,py,pw,ph);
      ctx.fillStyle = "rgba(0,229,255,.9)";
      ctx.font = "11px monospace";
      ctx.fillText(b.label+" "+Math.round(b.conf*100)+"%", px+4, py+14);
      rows.push(b);
    });
    S.vision.fps = Math.round(24+Math.random()*6);
  } else {
    S.vision.fps = HA.state==="on" ? (HA.fps||0) : 0;
  }
  var fpsChip = $("visionFps"); if(fpsChip){ var l=qs(".lbl",fpsChip); if(l) l.textContent = S.vision.fps+" FPS"; }
  if(list){
    list.innerHTML = rows.map(function(b){
      return '<div class="vision-row"><span class="vr-label">'+esc(b.label)+'</span>'+
        '<span class="vr-bar"><span style="width:'+Math.round(b.conf*100)+'%"></span></span>'+
        '<span class="vr-pct">'+Math.round(b.conf*100)+'%</span></div>';
    }).join("") || "";
  }
}

/* ---------------------------------------------------------------- */
/* air lab — small real physics simulations                          */
/* ---------------------------------------------------------------- */
var canvasLab;
var LAB_FIELDS = {
  circuit: [["voltage",1,12,0.5,"V"], ["resistance",10,500,10,"Ω"]],
  beaker: [["ph",0,14,0.5,""]],
  pendulum: [["length",20,200,5,"cm"], ["gravity",1,25,0.1,"m/s²"]],
  wave: [["frequency",0.2,3,0.1,"Hz"], ["amplitude",10,100,5,"px"]],
  optics: [["objectDist",40,300,5,""], ["focal",20,150,5,""]],
  planet: [["speed",0.1,3,0.1,"×"]]
};
var LAB_PRESETS = {
  circuit: [
    { label:"Loi d'Ohm (5V / 100Ω)", params:{ voltage:5, resistance:100 } },
    { label:"Court-circuit (Fort I)", params:{ voltage:12, resistance:10 } },
    { label:"Économie (1.5V / 300Ω)", params:{ voltage:1.5, resistance:300 } }
  ],
  beaker: [
    { label:"Acide fort (pH 1.2)", params:{ ph:1.2 } },
    { label:"Eau pure (pH 7.0)", params:{ ph:7.0 } },
    { label:"Base forte (pH 13.0)", params:{ ph:13.0 } }
  ],
  pendulum: [
    { label:"Terre (g=9.81)", params:{ length:100, gravity:9.8 } },
    { label:"Lune (g=1.62)", params:{ length:100, gravity:1.6 } },
    { label:"Jupiter (g=24.8)", params:{ length:100, gravity:24.8 } }
  ],
  wave: [
    { label:"Son grave (120 Hz)", params:{ frequency:0.6, amplitude:50 } },
    { label:"La 440 Hz (Diapason)", params:{ frequency:1.5, amplitude:65 } },
    { label:"Ultrason (800 Hz)", params:{ frequency:2.8, amplitude:30 } }
  ],
  optics: [
    { label:"Loupe simple", params:{ objectDist:60, focal:80 } },
    { label:"Image réelle", params:{ objectDist:150, focal:60 } },
    { label:"Foyer infini", params:{ objectDist:80, focal:80 } }
  ],
  planet: [
    { label:"Kepler 1.0x", params:{ speed:1.0 } },
    { label:"Accéléré 2.5x", params:{ speed:2.5 } },
    { label:"Ralenti 0.4x", params:{ speed:0.4 } }
  ]
};

function renderLabControls(){
  var tab = S.lab.active;
  var host = $("labControls"); if(!host) return;
  host.innerHTML = "";

  /* Render Presets */
  var preHost = $("labPresets");
  if(preHost){
    preHost.innerHTML = "";
    (LAB_PRESETS[tab]||[]).forEach(function(pr){
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "lab-preset-btn";
      btn.textContent = pr.label;
      on(btn, "click", function(){
        Object.keys(pr.params).forEach(function(k){ S.lab.params[tab][k] = pr.params[k]; });
        S.lab.t0 = performance.now();
        renderLabControls();
        toast("Préréglage : " + pr.label, "info");
      });
      preHost.appendChild(btn);
    });
  }

  (LAB_FIELDS[tab]||[]).forEach(function(f){
    var key=f[0], min=f[1], max=f[2], step=f[3], unit=f[4];
    var val = S.lab.params[tab][key];
    var wrap = document.createElement("div"); wrap.className = "field lab-field";
    var label = document.createElement("label");
    label.textContent = t("lab."+key);
    var row = document.createElement("div"); row.className = "row row-center-v";
    var input = document.createElement("input");
    input.type = "range"; input.min = min; input.max = max; input.step = step; input.value = val;
    var out = document.createElement("span"); out.className = "lab-val"; out.textContent = val+unit;
    input.addEventListener("input", function(){
      S.lab.params[tab][key] = parseFloat(input.value);
      out.textContent = input.value+unit;
    });
    row.appendChild(input); row.appendChild(out);
    wrap.appendChild(label); wrap.appendChild(row);
    host.appendChild(wrap);
  });
  qsa(".labtab", $("labWrap")).forEach(function(b){
    b.classList.toggle("active", b.getAttribute("data-lab")===tab);
  });
}
function wireAirLab(){
  canvasLab = $("canvasLab");
  resizeCanvas(canvasLab, $("labStage"));
  on(window,"resize", function(){ if(S.view==="air-lab") resizeCanvas(canvasLab, $("labStage")); });
  qsa(".labtab", $("labWrap")).forEach(function(b){
    on(b,"click", function(){
      S.lab.active = b.getAttribute("data-lab");
      S.lab.t0 = performance.now();
      renderLabControls();
      logEv("lab", {tab:S.lab.active});
    });
  });
}
function drawLab(){
  if(!canvasLab || S.view!=="air-lab") return;
  var ctx = canvasLab.getContext("2d");
  var w = canvasLab.width, h = canvasLab.height;
  if(!w||!h) return;
  ctx.clearRect(0,0,w,h);
  var dt = (performance.now()-S.lab.t0)/1000;
  var p = S.lab.params[S.lab.active];
  var readout = $("labReadout");
  var fOverlay = $("labFormulaOverlay");
  ctx.strokeStyle="#1b2847"; ctx.strokeRect(0.5,0.5,w-1,h-1);
  if(S.lab.active==="circuit"){
    var I = p.voltage/p.resistance;
    var P = p.voltage * I;
    if(fOverlay) fOverlay.innerHTML = "<strong>Loi d'Ohm :</strong> U = R &times; I &nbsp;|&nbsp; <strong>Puissance :</strong> P = " + P.toFixed(2) + " W";
    ctx.strokeStyle="#7cf7ff"; ctx.lineWidth=3;
    ctx.strokeRect(w*0.15,h*0.3,w*0.7,h*0.4);
    ctx.fillStyle="#ffc24b"; ctx.fillRect(w*0.42,h*0.66,w*0.16,h*0.08);
    ctx.fillStyle="#c7d4ee"; ctx.font="12px monospace";
    ctx.fillText("R="+p.resistance.toFixed(0)+"Ω", w*0.44, h*0.64);
    ctx.fillText(p.voltage.toFixed(1)+"V", w*0.06, h*0.52);
    var n = 24, speed = I*40;
    for(var i=0;i<n;i++){
      var f = ((dt*speed)/100 + i/n) % 1;
      var perim = 2*(w*0.7+h*0.4), d = f*perim, x,y;
      var W=w*0.7, H=h*0.4, X0=w*0.15, Y0=h*0.3;
      if(d<W){ x=X0+d; y=Y0; } else if(d<W+H){ x=X0+W; y=Y0+(d-W); } else if(d<2*W+H){ x=X0+W-(d-W-H); y=Y0+H; } else { x=X0; y=Y0+H-(d-2*W-H); }
      ctx.fillStyle="#00e5ff"; ctx.beginPath(); ctx.arc(x,y,3,0,Math.PI*2); ctx.fill();
    }
    if(readout) readout.textContent = t("lab.current")+": "+I.toFixed(3)+" A";
  } else if(S.lab.active==="beaker"){
    var ph = p.ph;
    var h3o = Math.pow(10, -ph);
    if(fOverlay) fOverlay.innerHTML = "<strong>Potentiel Hydrogène :</strong> pH = -log[H₃O⁺] &nbsp;|&nbsp; <strong>[H₃O⁺] =</strong> " + h3o.toExponential(2) + " mol/L";
    var color = ph<7 ? lerpColor([255,77,109],[255,194,75], ph/7) : lerpColor([255,194,75],[0,229,255],(ph-7)/7);
    ctx.strokeStyle="#c7d4ee"; ctx.lineWidth=2;
    var bx=w*0.35, by=h*0.15, bw=w*0.3, bh=h*0.68;
    ctx.beginPath(); ctx.moveTo(bx,by); ctx.lineTo(bx,by+bh); ctx.lineTo(bx+bw,by+bh); ctx.lineTo(bx+bw,by); ctx.stroke();
    ctx.fillStyle = "rgb("+color.join(",")+")";
    ctx.fillRect(bx+3, by+bh*0.35, bw-6, bh*0.65-3);
    if(readout) readout.textContent = t("lab.ph")+": "+ph.toFixed(1)+ (ph<7?" (acide)":ph>7?" (base)":" (neutre)");
  } else if(S.lab.active==="pendulum"){
    var L = p.length/100, g = p.gravity;
    var omega = Math.sqrt(g/L);
    var theta = 0.6*Math.cos(omega*dt);
    var pivX=w/2, pivY=h*0.12, len=Math.min(h*0.7, L*180);
    var bobX = pivX + Math.sin(theta)*len, bobY = pivY + Math.cos(theta)*len;
    var T = 2*Math.PI*Math.sqrt(L/g);
    if(fOverlay) fOverlay.innerHTML = "<strong>Période propre :</strong> T = 2&pi;&radic;(L/g) = " + T.toFixed(2) + " s";
    ctx.strokeStyle="#7cf7ff"; ctx.lineWidth=2;
    ctx.beginPath(); ctx.moveTo(pivX,pivY); ctx.lineTo(bobX,bobY); ctx.stroke();
    ctx.fillStyle="#00e5ff"; ctx.beginPath(); ctx.arc(bobX,bobY,10,0,Math.PI*2); ctx.fill();
    ctx.fillStyle="#7c8db3"; ctx.beginPath(); ctx.arc(pivX,pivY,3,0,Math.PI*2); ctx.fill();
    if(readout) readout.textContent = t("lab.period")+": "+T.toFixed(2)+" s";
  } else if(S.lab.active==="wave"){
    if(fOverlay) fOverlay.innerHTML = "<strong>Équation d'onde :</strong> y(x,t) = A&middot;sin(kx - &omega;t) &nbsp;|&nbsp; f = " + p.frequency.toFixed(1) + " Hz";
    ctx.strokeStyle="#00e5ff"; ctx.lineWidth=2; ctx.beginPath();
    for(var x=0;x<w;x++){
      var y = h/2 + p.amplitude*Math.sin((x/w)*Math.PI*4*p.frequency - dt*p.frequency*3);
      if(x===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    }
    ctx.stroke();
    if(readout) readout.textContent = t("lab.frequency")+": "+p.frequency.toFixed(1)+" Hz";
  } else if(S.lab.active==="optics"){
    var f = p.focal, doo = p.objectDist;
    var di = (doo===f) ? Infinity : 1/((1/f)-(1/doo));
    if(fOverlay) fOverlay.innerHTML = "<strong>Conjugaison Descartes :</strong> 1/f' = 1/OA' - 1/OA";
    var scale = w/500;
    var axisY = h/2, lensX = w*0.55;
    ctx.strokeStyle="#4a5a7d"; ctx.beginPath(); ctx.moveTo(0,axisY); ctx.lineTo(w,axisY); ctx.stroke();
    ctx.strokeStyle="#7cf7ff"; ctx.lineWidth=3; ctx.beginPath(); ctx.moveTo(lensX,axisY-h*0.35); ctx.lineTo(lensX,axisY+h*0.35); ctx.stroke();
    var objX = lensX - doo*scale, objH = h*0.18;
    ctx.strokeStyle="#ffc24b"; ctx.lineWidth=2;
    ctx.beginPath(); ctx.moveTo(objX,axisY); ctx.lineTo(objX,axisY-objH); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(objX-4,axisY-objH+8); ctx.lineTo(objX,axisY-objH); ctx.lineTo(objX+4,axisY-objH+8); ctx.stroke();
    if(isFinite(di)){
      var imgX = lensX + di*scale;
      var imgH = -objH * (di/doo);
      ctx.strokeStyle="#00e5ff";
      ctx.beginPath(); ctx.moveTo(imgX,axisY); ctx.lineTo(imgX,axisY+ (-imgH)); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(objX,axisY-objH); ctx.lineTo(lensX,axisY); ctx.lineTo(w,axisY-imgH*2); ctx.stroke();
      if(readout) readout.textContent = t("lab.imageDist")+": "+(di/scale).toFixed(0);
    } else if(readout) readout.textContent = t("lab.imageDist")+": ∞";
  } else if(S.lab.active==="planet"){
    if(fOverlay) fOverlay.innerHTML = "<strong>Lois de Kepler :</strong> T&sup2;/a&sup3; = cste &nbsp;|&nbsp; F = G(M&middot;m)/r&sup2;";
    var cx=w/2, cy=h/2;
    ctx.fillStyle="#ffc24b"; ctx.beginPath(); ctx.arc(cx,cy,10,0,Math.PI*2); ctx.fill();
    [[40,2.2,"#00e5ff"],[70,1.4,"#7cf7ff"],[100,0.9,"#ff4d6d"]].forEach(function(pl,i){
      var r=pl[0]*Math.min(w,h)/260, speed=pl[1]*p.speed;
      ctx.strokeStyle="rgba(124,247,255,.2)"; ctx.beginPath(); ctx.arc(cx,cy,r,0,Math.PI*2); ctx.stroke();
      var a = dt*speed;
      var px = cx + Math.cos(a)*r, py = cy + Math.sin(a)*r;
      ctx.fillStyle = pl[2]; ctx.beginPath(); ctx.arc(px,py,4+i,0,Math.PI*2); ctx.fill();
    });
    if(readout) readout.textContent = t("lab.speed")+": "+p.speed.toFixed(1)+"x";
  }
}
function lerpColor(a,b,f){ f=clamp(f,0,1); return [Math.round(a[0]+(b[0]-a[0])*f), Math.round(a[1]+(b[1]-a[1])*f), Math.round(a[2]+(b[2]-a[2])*f)]; }

/* ---------------------------------------------------------------- */
/* air quiz                                                           */
/* ---------------------------------------------------------------- */
function wireAirQuiz(){
  on($("btnQuizNew"),"click", function(){ openQuizEditor(); });
  on($("btnQuizAddQ"),"click", function(){ addQuizQuestionRow(); });
  on($("btnQuizImport"),"click", function(){ var fi = $("fileQuizImport"); if(fi) fi.click(); });
  on($("fileQuizImport"),"change", function(e){
    if(e.target.files && e.target.files[0]) importQuizFile(e.target.files[0]);
    e.target.value = "";
  });
  on($("btnQuizSave"),"click", function(){ saveQuizFromEditor(); });
  on($("btnQuizEditClose"),"click", function(){ hideModal("modalQuizEdit"); });
}
function openQuizEditor(){
  var host = $("qeditor"); host.innerHTML = "";
  addQuizQuestionRow();
  showModal("modalQuizEdit");
}
function addQuizQuestionRow(qin, correct){
  var host = $("qeditor");
  var idx = host.children.length;
  var row = document.createElement("div"); row.className = "qrow";
  var q = document.createElement("input"); q.type="text"; q.placeholder = t("quiz.question")+" "+(idx+1); q.className="q-text";
  if(qin && qin.q) q.value = qin.q;
  row.appendChild(q);
  var opts = document.createElement("div"); opts.className="row row-wrap";
  var arr = (qin && qin.opts) ? qin.opts.slice(0,4) : ["","","",""];
  while(arr.length < 2 && !(qin && qin.opts)) arr.push("");
  arr.forEach(function(otxt,i){
    var wrap = document.createElement("label"); wrap.className="btbtn sml qopt";
    var radio = document.createElement("input"); radio.type="radio"; radio.name="correct-"+idx; radio.value=i;
    if(qin ? i === correct : i===0) radio.checked=true;
    var input = document.createElement("input"); input.type="text"; input.placeholder=EUDAIR_ALPHA[i]; input.className="q-opt";
    if(otxt) input.value = otxt;
    wrap.appendChild(radio); wrap.appendChild(input);
    opts.appendChild(wrap);
  });
  row.appendChild(opts);
  host.appendChild(row);
}
var EUDAIR_ALPHA = ["A","B","C","D"];
function parseCSVLine(line){
  var res=[], cur="", inq=false;
  for(var i=0;i<line.length;i++){
    var ch=line[i];
    if(inq){
      if(ch==='"'){ if(line[i+1]==='"'){ cur+='"'; i++; } else inq=false; }
      else cur+=ch;
    } else if(ch==='"') inq=true;
    else if(ch===','){ res.push(cur); cur=""; }
    else cur+=ch;
  }
  res.push(cur);
  return res;
}
function parseQuizQuestions(text){
  var out = [];
  try{
    var json = JSON.parse(text);
    var arr = Array.isArray(json) ? json : (json.questions || []);
    arr.forEach(function(item){
      var q = item && (item.q != null ? String(item.q) : (item.question || "")).trim();
      var opts = (item && item.opts || []).map(function(o){ return String(o).trim(); }).filter(function(o){ return o; }).slice(0,4);
      var correct = item != null ? item.correct : 0;
      if(typeof correct === "string"){
        var up = correct.trim().toUpperCase();
        if(/^\d+$/.test(correct.trim())) correct = parseInt(correct.trim(),10);
        else if(/^[A-D]$/.test(up)) correct = up.charCodeAt(0)-65;
        else { var fo = opts.indexOf(correct); correct = fo >= 0 ? fo : 0; }
      }
      correct = isFinite(correct) ? parseInt(correct,10) : 0;
      if(q && opts.length >= 2 && correct >= 0 && correct < opts.length) out.push({ q:q, opts:opts, correct:correct });
    });
    if(out.length) return out;
  }catch(e){ /* not JSON — fall through to CSV */ }
  var lines = text.split(/\r?\n/).map(function(l){ return l.trim(); }).filter(function(l){ return l; });
  for(var li=0; li<lines.length; li++){
    var cols = parseCSVLine(lines[li]);
    if(li===0 && ["question","q","text"].indexOf(cols[0].toLowerCase()) >= 0) continue;
    if(cols.length >= 3){
      var qq = cols[0].replace(/"([^"]*)"/g, "$1").trim();
      if(!qq) continue;
      var optsv = [], used = 0;
      for(var oi=1; oi < cols.length-1 && used < 4; oi++){ if(cols[oi]){ optsv.push(cols[oi].replace(/"([^"]*)"/g, "$1").trim()); used++; } }
      var last = (cols[cols.length-1]||"").replace(/"([^"]*)"/g, "$1").trim();
      var cc = 0;
      if(/^[A-D]$/i.test(last)) cc = last.toUpperCase().charCodeAt(0)-65;
      else if(/^\d+$/.test(last)) cc = parseInt(last,10);
      else { var fr = optsv.indexOf(last); cc = fr >= 0 ? fr : 0; }
      if(optsv.length >= 2 && cc >= 0 && cc < optsv.length) out.push({ q:qq, opts:optsv, correct:cc });
    }
  }
  return out;
}
function importQuizFile(file){
  var fr = new FileReader();
  fr.onload = function(){
    var questions = parseQuizQuestions(fr.result || "");
    if(!questions.length){ toast("quiz.importBad","warn"); return; }
    questions.forEach(function(qu){ addQuizQuestionRow(qu, qu.correct); });
    toast("quiz.importOk","ok");
    logEv("quiz.import", {n:questions.length});
  };
  fr.readAsText(file);
}
function saveQuizFromEditor(){
  var host = $("qeditor");
  var rows = qsa(".qrow", host);
  var questions = [];
  rows.forEach(function(row){
    var qtext = qs(".q-text", row).value.trim();
    var opts = qsa(".q-opt", row).map(function(i){ return i.value.trim(); });
    var correct = 0;
    qsa("input[type=radio]", row).forEach(function(r,i){ if(r.checked) correct = i; });
    if(qtext && opts.some(function(o){ return o; })){
      questions.push({ q:qtext, opts:opts, correct:correct });
    }
  });
  if(!questions.length){ toast("quiz.startFirst","warn"); return; }
  var quiz = { id: Date.now(), questions: questions };
  S.quizzes.push(quiz); setLS("quizzes", S.quizzes);
  S.quiz = { active: quiz, qi:0, score:0, total: questions.length, wrongByQ:{}, reported:false };
  hideModal("modalQuizEdit");
  toast("quiz.created","ok");
  logEv("quiz.create", {n:questions.length});
  renderQuiz();
}
function renderQuiz(){
  var host = $("quizWrap"); if(!host) return;
  var scoreEl = $("quizScore");
  if(!S.quiz.active){
    host.innerHTML = '<p class="lede">'+esc(t("quiz.startFirst"))+'</p>';
    if(scoreEl) scoreEl.textContent = "";
    return;
  }
  if(S.quiz.qi >= S.quiz.active.questions.length){
    var finAcc = S.quiz.total ? Math.round(S.quiz.score/S.quiz.total*100) : 0;
    var finStars = quizStars(finAcc);
    var starsOn = "";
    for(var si=0; si<3; si++){ starsOn += (si<finStars ? "★" : "☆"); }
    host.innerHTML = '<p class="lede">'+esc(t("quiz.finished"))+' — '+S.quiz.score+'/'+S.quiz.total+'</p><div class="quiz-stars">'+starsOn+'</div>';
    if(scoreEl) scoreEl.textContent = S.quiz.score+" / "+S.quiz.total;
    if(!S.quiz.reported){
      S.quiz.reported = true;
      var res = { id:S.quiz.active.id, date: Date.now(),
                  score:S.quiz.score, total:S.quiz.total,
                  acc:finAcc, stars:finStars,
                  wrongByQ: S.quiz.wrongByQ||{} };
      S.quizResults.push(res);
      if(S.quizResults.length > 60) S.quizResults.shift();
      setLS("quizResults", S.quizResults);
      logEv("quiz.finish", {score:S.quiz.score, total:S.quiz.total, acc:finAcc, stars:finStars});
    }
    return;
  }
  var qd = S.quiz.active.questions[S.quiz.qi];
  var html = '<h3>'+t("quiz.question")+' '+(S.quiz.qi+1)+'/'+S.quiz.active.questions.length+'</h3>';
  html += '<p class="lede">'+esc(qd.q)+'</p><div class="quiz-opts">';
  ["A","B","C","D"].forEach(function(letter,i){
    if(qd.opts[i]) html += '<button class="btn quiz-opt" data-i="'+i+'">'+letter+'. '+esc(qd.opts[i])+'</button>';
  });
  html += '</div>';
  host.innerHTML = html;
  if(scoreEl) scoreEl.textContent = S.quiz.score+" / "+S.quiz.total;
  qsa(".quiz-opt", host).forEach(function(b){
    on(b,"click", function(){
      var i = parseInt(b.getAttribute("data-i"),10);
      var ok = i === qd.correct;
      if(ok) S.quiz.score++;
      else S.quiz.wrongByQ[qd.q] = (S.quiz.wrongByQ[qd.q]||0) + 1;
      toast(ok?"quiz.correct":"quiz.wrong", ok?"ok":"warn");
      logEv("quiz.answer", {ok:ok, q:qd.q});
      qsa(".quiz-opt", host).forEach(function(x){ x.setAttribute("disabled","disabled"); });
      b.classList.add(ok?"is-correct":"is-wrong");
      setTimeout(function(){ S.quiz.qi++; renderQuiz(); }, 700);
    });
  });
}

/* ---------------------------------------------------------------- */
/* air presentation                                                   */
/* ---------------------------------------------------------------- */
function renderPresentation(){
  var i = clamp(S.pres.i, 0, S.pres.slides.length-1); S.pres.i = i;
  var slide = S.pres.slides[i];
  var host = $("presStage");
  if(host){
    var spot = $("presSpotOverlay");
    var loupe = $("presLoupe");
    host.innerHTML = '<div class="pres-slide"><h3>'+esc(slide.t)+'</h3><p>'+esc(slide.b)+'</p></div>';
    if(spot) host.appendChild(spot);
    if(loupe) host.appendChild(loupe);
  }
  var count = $("presCount"); if(count) count.textContent = (i+1)+" / "+S.pres.slides.length;
}
function wireAirPresentation(){
  var spotActive = false, loupeActive = false;
  var spotEl = $("presSpotOverlay"), loupeEl = $("presLoupe"), stage = $("presStage");

  var btnSpot = $("btnPresSpot");
  if(btnSpot){
    on(btnSpot, "click", function(){
      spotActive = !spotActive;
      btnSpot.classList.toggle("btn-primary", spotActive);
      if(spotEl) spotEl.classList.toggle("hidden", !spotActive);
      toast(spotActive ? "Spotlight TNI activé" : "Spotlight désactivé", "info");
    });
  }

  var btnLoupe = $("btnPresLoupe");
  if(btnLoupe){
    on(btnLoupe, "click", function(){
      loupeActive = !loupeActive;
      btnLoupe.classList.toggle("btn-primary", loupeActive);
      if(loupeEl) loupeEl.classList.toggle("hidden", !loupeActive);
      toast(loupeActive ? "Loupe Zoom 2x activée" : "Loupe désactivée", "info");
    });
  }

  if(stage){
    on(stage, "pointermove", function(e){
      var r = stage.getBoundingClientRect();
      var x = e.clientX - r.left, y = e.clientY - r.top;
      if(spotActive && spotEl){
        spotEl.style.setProperty("--spot-x", x + "px");
        spotEl.style.setProperty("--spot-y", y + "px");
      }
      if(loupeActive && loupeEl){
        loupeEl.style.left = x + "px";
        loupeEl.style.top = y + "px";
        var curSlide = S.pres.slides[S.pres.i];
        if(curSlide){
          loupeEl.innerHTML = '<div style="transform:scale(1.7);transform-origin:center;padding:24px;text-align:center;color:var(--ink-strong);">' +
            '<h3>'+esc(curSlide.t)+'</h3><p>'+esc(curSlide.b)+'</p></div>';
        }
      }
    });
  }

  on($("btnPresPrev"),"click", function(){ S.pres.i = clamp(S.pres.i-1,0,S.pres.slides.length-1); renderPresentation(); logEv("pres.prev",{}); });
  on($("btnPresNext"),"click", function(){ S.pres.i = clamp(S.pres.i+1,0,S.pres.slides.length-1); renderPresentation(); logEv("pres.next",{}); });
  on(document,"keydown", function(e){
    if(S.view!=="air-presentation") return;
    if(e.key==="ArrowRight"){ $("btnPresNext").click(); }
    if(e.key==="ArrowLeft"){ $("btnPresPrev").click(); }
  });
}

/* ---------------------------------------------------------------- */
/* real camera + hand tracking (MediaPipe HandLandmarker)            */
/* ---------------------------------------------------------------- */
var HA = { state:"off", stream:null, landmarker:null, running:false, starting:false,
           loaded:false, loading:false, hand:null, handEver:false, gestureText:"", ripples:[], light:1,
           quality:"wait", qualityT:0, result:null, lastDet:0, modelErr:false, watchTimer:null,
           fps:0, _fr:0, _ft:0, lastHandT:0, raw:null, smo:null, smo2:null };
var MP_CDN  = "./vendor/vision_bundle.js";
var MP_WASM = "./vendor/wasm";
var MP_MODEL = "./models/hand_landmarker.task";
var HAND_EDGES = [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[0,9],[9,10],[10,11],[11,12],
                  [0,13],[13,14],[14,15],[15,16],[0,17],[17,18],[18,19],[19,20],[5,9],[9,13],[13,17]];

/* cursor smoothing — EMA + per-frame max step + transient-spike rejection */
function makeSmoother(){
  return { sx:null, sy:null, lx:null, ly:null };
}
function smootherStep(sm, rx, ry, W, H){
  var wx = clamp(rx, 0, W), wy = clamp(ry, 0, H);
  if(sm.sx === null){
    sm.sx = wx; sm.sy = wy; sm.lx = wx; sm.ly = wy;
    return { x: wx, y: wy };
  }
  /* 0 stability = raw (still bounded); otherwise EMA tuned by the slider */
  var alpha = (S.stab||0) > 0 ? clamp(0.30 + (10 - Math.min(10, Math.max(1, S.stab||10))) * 0.055, 0.15, 0.9) : 1;
  var mX = W * 0.16, mY = H * 0.16;
  /* impossible jump (tracker flip): hold position this frame, learn the new anchor */
  if(Math.abs(wx - sm.lx) > W * 0.35 || Math.abs(wy - sm.ly) > H * 0.35){
    sm.lx = wx; sm.ly = wy;
    return { x: sm.sx, y: sm.sy };
  }
  sm.lx = wx; sm.ly = wy;
  var tX = sm.sx + clamp(wx - sm.sx, -mX, mX);
  var tY = sm.sy + clamp(wy - sm.sy, -mY, mY);
  sm.sx = clamp(sm.sx + (tX - sm.sx) * alpha, 0, W);
  sm.sy = clamp(sm.sy + (tY - sm.sy) * alpha, 0, H);
  return { x: sm.sx, y: sm.sy };
}

/* homography camera(viewport-normalized, mirrored) -> screen(px), DLT least squares */
function lsSolveRows(rows, b){
  var n = 8, i, j, k;
  var A = [], G = [];
  for(i=0;i<n;i++){
    A[i] = new Array(n).fill(0); G[i] = 0;
    for(k=0;k<rows.length;k++){
      var r = rows[k], bi = b[k];
      for(j=0;j<n;j++){ A[i][j] += r[i]*r[j]; }
      G[i] += r[i]*bi;
    }
  }
  for(i=0;i<n;i++){
    var piv = i;
    for(k=i+1;k<n;k++){ if(Math.abs(A[k][i]) > Math.abs(A[piv][i])) piv = k; }
    if(Math.abs(A[piv][i]) < 1e-12) return null;
    if(piv !== i){ var tmp=A[i]; A[i]=A[piv]; A[piv]=tmp; var tg=G[i]; G[i]=G[piv]; G[piv]=tg; }
    for(k=i+1;k<n;k++){
      var f = A[k][i]/A[i][i];
      for(j=i;j<n;j++){ A[k][j] -= f*A[i][j]; }
      G[k] -= f*G[i];
    }
  }
  var h = new Array(n).fill(0);
  for(i=n-1;i>=0;i--){
    var s = G[i];
    for(j=i+1;j<n;j++){ s -= A[i][j]*h[j]; }
    h[i] = s/A[i][i];
  }
  return h;
}
function homographyFrom(pts){
  var n = pts.length;
  if(n < 4) return null;
  var rows = [], b = [];
  var vw = window.innerWidth||1, vh = window.innerHeight||1;
  for(var i=0;i<n;i++){
    var p = pts[i];
    var X = p.X/vw, Y = p.Y/vh;
    rows.push([p.u, p.v, 1, 0, 0, 0, -X*p.u, -X*p.v]);
    rows.push([0, 0, 0, p.u, p.v, 1, -Y*p.u, -Y*p.v]);
    b.push(X); b.push(Y);
  }
  var h = lsSolveRows(rows, b);
  if(!h) return null;
  return [[h[0],h[1],h[2]],[h[3],h[4],h[5]],[h[6],h[7],1]];
}
function applyH(H, u, v){
  var a = H[0][0]*u + H[0][1]*v + H[0][2];
  var c = H[1][0]*u + H[1][1]*v + H[1][2];
  var q = H[2][0]*u + H[2][1]*v + H[2][2];
  if(Math.abs(q) < 1e-9) q = 1e-9;
  var x = a/q, y = c/q;
  if(!isFinite(x) || !isFinite(y)) return { x: u, y: v };
  return { x: x, y: y };
}
function homographyScore(H, pts){
  var vw = window.innerWidth||1, vh = window.innerHeight||1;
  var err = 0;
  pts.forEach(function(p){
    var n = applyH(H, p.u, p.v);
    err += Math.hypot((n.x*vw) - p.X, (n.y*vh) - p.Y);
  });
  var avg = err / Math.max(1, pts.length);
  return { errPx: avg, score: Math.min(100, Math.max(0, Math.round(100 - avg*2.5))) };
}
function saveCalib(){ setLS("calib", S.calib); }
function calibChip(){ setChip("stCalib", (S.calib.ok && S.calib.H) ? "on" : "off"); }
function aiChip(){ setChip("stAI", S.ai.mode === "live" ? "on" : "off"); }
function syncAiBadge(){
  var liveBadge = $("aiModeBadge");
  if(!liveBadge) return;
  var live = S.ai.mode === "live";
  liveBadge.textContent = live ? t("teacher.live") : t("teacher.demo");
  liveBadge.classList.toggle("live", live);
  aiChip();
}
function refreshCalibView(){
  var canvasInline = $("canvasCalib");
  if(!canvasInline) return;
  resizeCanvas(canvasInline, $("calibWrap"));
  drawCalib(canvasInline, (S.calib.pts||[]).length, false);
  var s = $("calibScore");
  if(s) s.textContent = (S.calib.ok && S.calib.H && S.calib.score)
    ? t("calib.scored").replace("{s}", S.calib.score+"%")
    : t("calib.notDone");
}

/* audio feedback — tiny Web Audio beeps, no assets */
var SND = { ctx:null };
function sndCtx(){
  if(!SND.ctx){ try{ SND.ctx = new (window.AudioContext || window.webkitAudioContext)(); }catch(e){} }
  if(SND.ctx && SND.ctx.state === "suspended"){ try{ SND.ctx.resume(); }catch(e){} }
  return SND.ctx;
}
function playTone(freq, dur, vol, type){
  if(!S.sound) return;
  var ctx = sndCtx(); if(!ctx) return;
  try{
    var o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type || "sine"; o.frequency.value = freq;
    g.gain.setValueAtTime(vol || 0.07, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + (dur || 0.06));
    o.connect(g); g.connect(ctx.destination);
    o.start(); o.stop(ctx.currentTime + (dur || 0.06));
  }catch(e){}
}
function sndClick(){ playTone(940,0.05,0.09,"square"); }
function sndOk(){ playTone(660,0.06,0.07); setTimeout(function(){ playTone(880,0.06,0.07); }, 80); }
function sndErr(){ playTone(220,0.12,0.08,"sawtooth"); }

/* ambient light sampling from the camera frame (for a helpful hint) */
var LUM = { ctx:null, avg:1, t:0 };
function sampleLight(){
  var v = $("camVideo"); if(!v || v.readyState < 2) return;
  if(!LUM.ctx){
    var c = document.createElement("canvas"); c.width=8; c.height=8;
    LUM.ctx = c.getContext("2d");
  }
  try{
    LUM.ctx.drawImage(v,0,0,8,8);
    var d = LUM.ctx.getImageData(0,0,8,8).data, s=0,n=0;
    for(var i=0;i<d.length;i+=4){ s += 0.299*d[i]+0.587*d[i+1]+0.114*d[i+2]; n++; }
    LUM.avg = (n? (s/n/255) : 1);
  }catch(e){}
}

/* click ripple — drawn on the hand overlay */
function ripple(x,y,color){
  HA.ripples.push({ x:x, y:y, color:color||"#ffc24b", t:performance.now() });
  if(HA.ripples.length > 8) HA.ripples.shift();
}
function drawRipples(ctx){
  var now = performance.now();
  HA.ripples = HA.ripples.filter(function(r){ return now - r.t < 420; });
  HA.ripples.forEach(function(r){
    var f = (now - r.t) / 420;
    ctx.strokeStyle = r.color; ctx.globalAlpha = 0.9*(1-f);
    ctx.lineWidth = 2.5*(1-f)+0.5;
    ctx.beginPath(); ctx.arc(r.x, r.y, 10 + f*26, 0, Math.PI*2); ctx.stroke();
    ctx.globalAlpha = 1;
  });
}

/* gesture tutorial — shown on first camera launch */
var TT = { step:0, max:3, done:false };
function showTutorial(){ var el=$("tutOverlay"); if(el) el.classList.remove("hidden"); }
function hideTutorial(){ var el=$("tutOverlay"); if(el) el.classList.add("hidden"); }
function tutRender(){
  var el=$("tutOverlay"); if(!el) return;
  var keys=["tut.step1","tut.step2","tut.step3"];
  qsa(".tut-step", el).forEach(function(s,i){
    s.classList.toggle("on", i===TT.step);
    s.classList.toggle("done", i<TT.step);
    var txt=s.querySelector(".tut-txt"); if(txt) txt.textContent = t(keys[i]);
    var dot=s.querySelector(".tut-dot"); if(dot) dot.textContent = i<TT.step ? "✓" : (i+1);
  });
  var bn=$("btnTutNext"); if(bn) bn.textContent = t(TT.step>=TT.max-1 ? "tut.finish" : "tut.next");
}
function tutNext(){
  TT.step++;
  if(TT.step >= TT.max){
    TT.done = true; S.tutorialSeen = true; setLS("tutorialSeen", true);
    hideTutorial(); sndOk(); return;
  }
  tutRender(); playTone(520,0.04,0.05);
}
function tutSkip(){
  TT.done = true; S.tutorialSeen = true; setLS("tutorialSeen", true);
  hideTutorial(); logEv("tutorial.skip", {});
}
function tutTrigger(what){
  if(TT.done || S.tutorialSeen) return;
  var advance = false;
  if(what==="hand" && TT.step===0) advance = true;
  else if(what==="pinch" && TT.step===1) advance = true;
  else if(what==="swipe" && TT.step===2) advance = true;
  if(advance){
    TT.step++;
    if(TT.step >= TT.max){ TT.done=true; S.tutorialSeen=true; setLS("tutorialSeen",true); hideTutorial(); logEv("tutorial.done",{}); }
    else { tutRender(); playTone(520,0.05,0.06); }
  }
}
function openTutorialIfNew(){
  if(S.tutorialSeen || TT.done) return;
  TT.step=0; tutRender(); showTutorial(); logEv("tutorial.show", {});
}

function setCamBtn(on){ var b=$("btnCam"); if(b) b.setAttribute("data-state", on?"on":"off"); }
function setVoiceBtn(on){ var b=$("btnMic"); if(b) b.setAttribute("data-state", on?"on":"off"); }
function updateModeBadge(){
  var badge = $("demoBadge"); if(!badge) return;
  var live = HA.state === "on";
  var key = live ? "demo.live" : "demo.badge";
  badge.setAttribute("data-i18n-html", key);
  badge.textContent = t(key);
  badge.classList.toggle("badge-live", live);
  badge.classList.toggle("badge-demo", !live);
}
function showCamPreview(on){
  var p=$("camPreview"), o=$("camOverlay");
  if(p) p.classList.toggle("hidden", !on);
  if(o) o.classList.toggle("hidden", !on);
}

function mpGlobals(){
  var base = (window.HandLandmarker && window.FilesetResolver) ? window
    : ((window.Vision && window.Vision.HandLandmarker && window.Vision.FilesetResolver) ? window.Vision : null);
  return base ? { FS: base.FilesetResolver, HL: base.HandLandmarker } : null;
}
function loadMediaPipe(){
  return new Promise(function(res){
    if(mpGlobals()){ HA.loaded = true; res(true); return; }
    if(HA.loading) return;
    HA.loading = true;
    var s = document.createElement("script");
    s.src = MP_CDN;
    var to = setTimeout(function(){ HA.loading = false; res(false); }, 15000);
    s.onload = function(){ clearTimeout(to); HA.loaded = true; HA.loading = false; res(true); };
    s.onerror = function(){ clearTimeout(to); HA.loading = false; res(false); };
    document.head.appendChild(s);
  });
}

function startCamera(){
  if(HA.state === "on" || HA.starting) return;
  HA.starting = true;
  setChip("stCam","warn");
  loadMediaPipe().then(function(ok){
    if(!ok){
      HA.starting = false; setChip("stCam","err"); toast("cam.error","err");
      logEv("cam.error", {reason:"cdn"});
      return;
    }
    if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){
      HA.starting = false; setChip("stCam","err"); toast("cam.unavailable","err"); return;
    }
    navigator.mediaDevices.getUserMedia({
      video:{ facingMode:"user", width:{ideal:640}, height:{ideal:480} },
      audio:false
    }).then(function(stream){
      HA.stream = stream;
      var v = $("camVideo");
      v.srcObject = stream; v.muted = true;
      v.play().then(function(){
        HA.starting = false; HA.state = "on";
        setCamBtn(true); setChip("stCam","on");
        updateModeBadge();
        showCamPreview(true);
        drawHandOverlay(null, null);
        initHandLandmarker();
        openTutorialIfNew();
        HA.running = true;
        requestAnimationFrame(camLoop);
        toast("cam.on","ok");
        logEv("cam.on", {});
      }).catch(function(){
        HA.starting = false; if(HA.stream){ HA.stream.getTracks().forEach(function(tr){ tr.stop(); }); HA.stream=null; }
        setChip("stCam","err"); toast("cam.error","err");
      });
    }).catch(function(err){
      HA.starting = false; setChip("stCam","err");
      if(err && (err.name==="NotAllowedError" || err.name==="SecurityError")) toast("cam.denied","err");
      else if(err && (err.name==="NotFoundError" || err.name==="OverconstrainedError")) toast("cam.unavailable","err");
      else toast("cam.error","err");
      logEv("cam.error", {name: err ? err.name : "unknown"});
    });
  });
}

function stopCamera(){
  HA.running = false;
  if(HA.stream){ HA.stream.getTracks().forEach(function(tr){ tr.stop(); }); HA.stream = null; }
  HA.state="off"; HA.hand = null; HA.handEver = false; HA.gestureText="";
  HA.raw = null; HA.smo = null; HA.smo2 = null;
  HA.result = null; HA.lastDet = 0;
  HA.lastHandT = 0;
  if(HA.watchTimer){ clearTimeout(HA.watchTimer); HA.watchTimer = null; }
  HA.modelErr = false; hideModelRetry();
  HS.pinch = false; HS2.pinch = false; HS.samples=[];
  hideTutorial();
  var c=$("camOverlay"); var ctx=c && c.getContext && c.getContext("2d"); if(ctx) ctx.clearRect(0,0,c.width,c.height);
  showCamPreview(false);
  setCamBtn(false); setChip("stCam","off"); setChip("stHand","off");
  updateModeBadge();
  toast("cam.off","info"); logEv("cam.off", {});
}

function initHandLandmarker(){
  var g = mpGlobals();
  if(!g) return;
  HA.modelErr = false;
  if(HA.watchTimer){ clearTimeout(HA.watchTimer); }
  HA.watchTimer = setTimeout(function(){
    if(!HA.landmarker && HA.state==="on") onModelFailure();
  }, 18000);
  g.FS.forVisionTasks(MP_WASM).then(function(run){
    function timedCreate(delegate, delay){
      return new Promise(function(res, rej){
        var done = false;
        var to = setTimeout(function(){ if(!done){ done = true; rej(new Error("delegate timeout "+delegate)); } }, delay);
        g.HL.createFromOptions(run, {
          baseOptions:{ modelAssetPath: MP_MODEL, delegate: delegate },
          runningMode:"VIDEO", numHands:2,
          minHandDetectionConfidence: S.conf || 0.5,
          minTrackingConfidence: 0.5
        }).then(function(lm){
          if(!done){ done = true; clearTimeout(to); res(lm); }
        }, function(err){
          if(!done){ done = true; clearTimeout(to); rej(err); }
        });
      });
    }
    timedCreate("GPU", 6500).then(function(lm){ setLandmarker(lm, "GPU"); })
      .catch(function(){ return timedCreate("CPU", 12000).then(function(lm){ setLandmarker(lm, "CPU"); }); })
      .catch(function(){ onModelFailure(); });
  }).catch(function(){ onModelFailure(); });
}

function setLandmarker(lm, delegate){
  HA.landmarker = lm;
  if(HA.watchTimer){ clearTimeout(HA.watchTimer); HA.watchTimer = null; }
  hideModelRetry();
  HA.modelErr = false;
  setChip("stCam","on");
  logEv("cam.landmarker", {delegate:delegate});
}
function onModelFailure(){
  if(HA.landmarker || HA.state!=="on") return;
  HA.modelErr = true;
  setChip("stCam","err");
  showModelRetry();
  toast("cam.errModel","err");
  logEv("cam.error", {reason:"model"});
}
function showModelRetry(){ var b=$("btnModelRetry"); if(b) b.classList.remove("hidden"); }
function hideModelRetry(){ var b=$("btnModelRetry"); if(b) b.classList.add("hidden"); }
function retryModel(){
  if(!HA.landmarker && HA.state==="on" && mpGlobals()){
    HA.modelErr = false; hideModelRetry();
    initHandLandmarker();
    logEv("cam.retry",{});
  }
}

function overlayCtx(c){
  if(!c.width || c.width !== window.innerWidth || c.height !== window.innerHeight){
    c.width = window.innerWidth; c.height = window.innerHeight;
  }
  return c.getContext("2d");
}
function qualityBadge(ctx, msg, color){
  ctx.save();
  ctx.font="600 12px Inter, sans-serif"; ctx.textAlign="left";
  var w = ctx.measureText(msg).width + 22;
  ctx.fillStyle="rgba(6,10,20,.75)";
  if(ctx.roundRect){ ctx.beginPath(); ctx.roundRect(14,14,w,27,8); ctx.fill(); }
  else { ctx.fillRect(14,14,w,27); }
  ctx.fillStyle=color;
  ctx.fillText(msg, 25, 32);
  ctx.restore();
}
function drawHandOverlay(p1, p2){
  var c=$("camOverlay"); if(!c) return;
  var ctx = overlayCtx(c);
  ctx.clearRect(0,0,c.width,c.height);
  drawRipples(ctx);
  if(!p1){
    HA.gestureText = "";
    var msg, color;
    if(HA.modelErr){ msg = t("cam.errModel"); color = "#ff4d6d"; }
    else if(!HA.landmarker){ msg = t("cam.loading"); color = "#7cf7ff"; }
    else if(HA.quality==="light"){ msg = t("cam.light"); color = "#ffc24b"; }
    else { msg = HA.state==="on" ? t("cam.show") : t("cam.hand"); color = "#7cf7ff"; }
    ctx.save();
    ctx.font="600 15px Inter, sans-serif"; ctx.textAlign="center";
    var w = ctx.measureText(msg).width + 36;
    var x = c.width/2, y = c.height - 96;
    ctx.fillStyle="rgba(6,10,20,.62)";
    if(ctx.roundRect){ ctx.beginPath(); ctx.roundRect(x-w/2, y-18, w, 36, 18); ctx.fill(); }
    else { ctx.fillRect(x-w/2, y-18, w, 36); }
    ctx.fillStyle=color;
    ctx.fillText(msg, x, y+6);
    if(!HA.landmarker && !HA.modelErr){
      var a = (performance.now()/40) % (Math.PI*2);
      ctx.strokeStyle="rgba(124,247,255,.85)"; ctx.lineWidth=3; ctx.lineCap="round";
      ctx.beginPath(); ctx.arc(x, y+42, 8, a, a+Math.PI*1.3); ctx.stroke();
    }
    qualityBadge(ctx, msg, color);
    ctx.restore();
    return;
  }
  ctx.save();
  function skeleton(lm, color){
    ctx.strokeStyle=color; ctx.lineWidth=2;
    ctx.beginPath();
    HAND_EDGES.forEach(function(pair){
      var a=lm[pair[0]], b=lm[pair[1]];
      ctx.moveTo((1-a.x)*c.width, a.y*c.height);
      ctx.lineTo((1-b.x)*c.width, b.y*c.height);
    });
    ctx.stroke();
  }
  function tip(lm, color, big){
    var tx=(1-lm[8].x)*c.width, ty=lm[8].y*c.height;
    ctx.fillStyle=color;
    ctx.beginPath(); ctx.arc(tx,ty,big?6:5,0,Math.PI*2); ctx.fill();
    ctx.strokeStyle=color; ctx.globalAlpha=0.45; ctx.lineWidth=4;
    ctx.beginPath(); ctx.arc(tx,ty,big?14:12,0,Math.PI*2); ctx.stroke();
    ctx.globalAlpha=1;
  }
  skeleton(p1, "rgba(255,194,75,.6)");
  tip(p1, "rgba(255,194,75,.95)", true);
  if(p2){ skeleton(p2, "rgba(0,229,255,.55)"); tip(p2, "rgba(0,229,255,.9)", false); }
  if(HS.pinch){
    ctx.strokeStyle="rgba(255,194,75,.95)"; ctx.lineWidth=2;
    ctx.beginPath(); ctx.arc((1-p1[8].x)*c.width, p1[8].y*c.height, 22, 0, Math.PI*2); ctx.stroke();
  }
  if(HS2.pinch && p2){
    ctx.strokeStyle="rgba(0,229,255,.9)"; ctx.lineWidth=2;
    ctx.beginPath(); ctx.arc((1-p2[8].x)*c.width, p2[8].y*c.height, 18, 0, Math.PI*2); ctx.stroke();
  }
  if(HA.gestureText){
    ctx.font="600 12px Inter, sans-serif"; ctx.textAlign="center";
    ctx.fillStyle="rgba(255,194,75,.9)";
    ctx.fillText(HA.gestureText, (1-p1[8].x)*c.width, p1[8].y*c.height-24);
  }
  qualityBadge(ctx, t("cam.hand"), "#00e5ff");
  ctx.restore();
}

function handEvent(type, x, y, buttons, pid, isPrimary){
  var el = document.elementFromPoint(x, y);
  if(!el) el = document.body;
  var opts = { clientX:x, clientY:y, bubbles:true, cancelable:true,
               pointerId: pid || 90, pointerType:"pen", isPrimary: isPrimary !== false,
               buttons:buttons, button:buttons?0:-1 };
  var ev;
  try { ev = new PointerEvent(type, opts); }
  catch(e){ ev = new MouseEvent(type.replace(/^pointer/,"mouse"), opts); }
  el.dispatchEvent(ev);
}
function handClick(x,y,pid,color){
  var el = document.elementFromPoint(x,y);
  if(el) el.dispatchEvent(new MouseEvent("click",{clientX:x,clientY:y,bubbles:true,cancelable:true}));
  ripple(x,y,color||"#ffc24b");
  sndClick();
  if(navigator.vibrate) navigator.vibrate(12);
}

var HS  = { samples:[], pinch:false, px:0, py:0, drag:0, lastSwipe:0, lastGesture:0 };
var HS2 = { pinch:false, px:0, py:0, drag:0 };

function handleHand(lm, sx, sy, W){
  var now = performance.now();
  var p4=lm[4], p8=lm[8];
  var d = Math.hypot(p4.x-p8.x, p4.y-p8.y);
  var pinch = HS.pinch;
  if(!pinch && d < 0.055) pinch = true;
  else if(pinch && d > 0.085) pinch = false;
  handEvent("pointermove", sx, sy, pinch?1:0, 90, true);
  if(pinch && !HS.pinch){
    HS.px=sx; HS.py=sy; HS.drag=0;
    handEvent("pointerdown", sx, sy, 1, 90, true);
  } else if(pinch){
    HS.drag += Math.hypot(sx-HS.px, sy-HS.py);
    HS.px=sx; HS.py=sy;
  } else if(HS.pinch && !pinch){
    handEvent("pointerup", sx, sy, 0, 90, true);
    if(HS.drag < 16){
      handClick(sx, sy, 90, "#ffc24b");
      if(now - HA.lastGesture > 1500) toast("gesture.pinch","ok");
      tutTrigger("pinch");
    }
    logEv("gesture.pinch", {drag:Math.round(HS.drag)});
  }
  HS.pinch = pinch;
  var extended = [8,12,16,20].filter(function(i){ return lm[i].y < lm[i-2].y; }).length;
  HA.gestureText = HS.pinch ? t("gesture.pinch") : (extended >= 3 ? t("gesture.palm") : "");
  if(!pinch){
    HS.samples.push({t:now, x:sx});
    while(HS.samples.length && now - HS.samples[0].t > 450) HS.samples.shift();
    if(HS.samples.length >= 16 && now - HS.lastSwipe > 1000){
      var s0=HS.samples[0], sn=HS.samples[HS.samples.length-1];
      var dx=sn.x-s0.x, dt=sn.t-s0.t;
      if(dt > 90 && Math.abs(dx) > W*0.30){
        HS.lastSwipe = now; HS.samples=[];
        execSwipe(dx < 0 ? -1 : 1);
      }
    }
  } else {
    HS.samples=[];
  }
}

function handleHand2(lm, sx, sy){
  var p4=lm[4], p8=lm[8];
  var d = Math.hypot(p4.x-p8.x, p4.y-p8.y);
  var pinch = HS2.pinch;
  if(!pinch && d < 0.055) pinch = true;
  else if(pinch && d > 0.085) pinch = false;
  handEvent("pointermove", sx, sy, pinch?1:0, 91, false);
  if(pinch && !HS2.pinch){
    HS2.px=sx; HS2.py=sy; HS2.drag=0;
    handEvent("pointerdown", sx, sy, 1, 91, false);
  } else if(pinch){
    HS2.drag += Math.hypot(sx-HS2.px, sy-HS2.py);
    HS2.px=sx; HS2.py=sy;
  } else if(HS2.pinch && !pinch){
    handEvent("pointerup", sx, sy, 0, 91, false);
    if(HS2.drag < 16) handClick(sx, sy, 91, "#00e5ff");
  }
  HS2.pinch = pinch;
}

function execSwipe(dir){
  HA.lastGesture = performance.now();
  if(dir > 0){
    if(S.view !== "air-presentation") switchView("air-presentation");
    var n=$("btnPresNext"); if(n) n.click();
    toast("gesture.swipeR","ok");
  } else {
    if(S.view !== "air-presentation") switchView("air-presentation");
    var p=$("btnPresPrev"); if(p) p.click();
    toast("gesture.swipeL","ok");
  }
  sndOk(); tutTrigger("swipe");
  logEv("gesture.swipe", {dir:dir});
}

function camLoop(){
  if(!HA.running) return;
  var v = $("camVideo");
  var now = performance.now();
  if(!HA._ft) HA._ft = now;
  HA._fr++;
  if(now - HA._ft >= 1000){ HA.fps = Math.round(HA._fr * 1000 / (now - HA._ft)); HA._ft = now; HA._fr = 0; }
  if(now - LUM.t > 700){ sampleLight(); LUM.t = now; }
  var ready = !!(HA.landmarker && v && v.readyState >= 2 && !v.paused);
  if(ready){
    var t = performance.now();
    var idle = !!(HA.lastHandT && (t - HA.lastHandT > 6000));
    if(t - HA.lastDet > (idle ? 250 : 33)){
      HA.lastDet = t;
      var res = null;
      try { res = HA.landmarker.detectForVideo(v, t); }
      catch(e){ /* transient "too dense" frame — keep the last known hand instead of dropping it */ }
      if(res){
        var lm = res.landmarks || [];
        HA.result = lm.length ? { landmarks: lm, handedness: res.handedness || null } : null;
      }
    }
  }
  var hands = ready && HA.result ? HA.result.landmarks : null;
  var hnd = ready && HA.result ? HA.result.handedness : null;
  var prim = 0;
  if(hands && hands.length > 1 && hnd && (S.primHand === "left" || S.primHand === "right")){
    var want = S.primHand === "left" ? "Left" : "Right";
    for(var hi=0; hi<hnd.length; hi++){ if(hnd[hi] && hnd[hi][0] && hnd[hi][0].label === want){ prim = hi; break; } }
  }
  var W = window.innerWidth, H = window.innerHeight;
  if(hands && hands.length){
    HA.lastHandT = performance.now();
    var p1 = hands[prim];
    var rawU = 1 - p1[8].x, rawV = p1[8].y;
    var mapPt = (S.calib.ok && S.calib.H) ? applyH(S.calib.H, rawU, rawV) : { x: rawU, y: rawV };
    var rx = clamp(mapPt.x * W, 0, W);
    var ry = clamp(mapPt.y * H, 0, H);
    HA.raw = { u: rawU, v: rawV, x: rx, y: ry };
    if(!HA.smo) HA.smo = makeSmoother();
    var sm = smootherStep(HA.smo, rx, ry, W, H);
    var sx = sm.x, sy = sm.y;
    HA.hand = { x:sx, y:sy };
    if(!HA.handEver){ HA.handEver = true; tutTrigger("hand"); }
    setChip("stHand","on");
    handleHand(p1, sx, sy, W);
    var p2 = hands.length > 1 ? hands[1-prim] : null;
    if(p2){
      var rawU2 = 1 - p2[8].x, rawV2 = p2[8].y;
      var mapPt2 = (S.calib.ok && S.calib.H) ? applyH(S.calib.H, rawU2, rawV2) : { x: rawU2, y: rawV2 };
      var s2x = clamp(mapPt2.x * W, 0, W);
      var s2y = clamp(mapPt2.y * H, 0, H);
      if(!HA.smo2) HA.smo2 = makeSmoother();
      var sm2 = smootherStep(HA.smo2, s2x, s2y, W, H);
      handleHand2(p2, sm2.x, sm2.y);
    } else if(HS2.pinch){
      HS2.pinch = false;
      handEvent("pointerup", HS2.px, HS2.py, 0, 91, false);
    }
    HA.quality = "ok";
  } else {
    if(ready && HS.pinch){ HS.pinch=false; handEvent("pointerup", HA.hand?HA.hand.x:0, HA.hand?HA.hand.y:0, 0, 90, true); }
    if(ready && HS2.pinch){ HS2.pinch=false; handEvent("pointerup", HS2.px, HS2.py, 0, 91, false); }
    HA.hand = null;
    HS.samples=[];
    if(ready) HA.quality = LUM.avg < 0.16 ? "light" : "wait";
    setChip("stHand","off");
  }
  var chip = $("stCam");
  if(chip) chip.setAttribute("data-state", (!ready || HA.quality==="light") ? "warn" : "on");
  drawHandOverlay(hands ? hands[0] : null, hands ? hands[1] : null);
  requestAnimationFrame(camLoop);
}

function wireCamera(){
  on($("btnTutNext"),"click", tutNext);
  on($("btnTutSkip"),"click", tutSkip);
  on($("tutOverlay"),"click", function(e){ if(e.target && !e.target.closest("button")) tutNext(); });
  on($("btnModelRetry"),"click", retryModel);
}

/* ---------------------------------------------------------------- */
/* voice commands (Web Speech API — Chrome/Edge)                     */
/* ---------------------------------------------------------------- */
var VC = { on:false, rec:null };
var VOICE_RE = {
  en:{ next:/\b(next|forward|ahead|go on)\b/, prev:/\b(previous|prev|back)\b/,
       pointerOff:/\bpointer (off|out)\b|disable pointer/, pointer:/\bpointer\b/, drawOff:/\b(draw|ink) off\b|stop (drawing|draw)|disable (draw|ink)/, draw:/\b(draw|ink|paint)\b/,
       clear:/\b(clear|wipe|erase|clean)\b/, quiz:/\b(quiz|test)\b/, presentation:/\b(presentation|slides)\b/,
       confirm:/\b(yes|confirm|okay)\b/, cancel:/\b(cancel|no)\b/, stop:/\b(emergency stop|stop everything|freeze|abort)\b/ },
  fr:{ next:/\b(suivant|suiv|avance)\b/, prev:/\b(pr[ée]c[ée]dent|pr[ée]c|retour|arri[èe]re)\b/,
       pointerOff:/\bpointeur (hors|off|d[ée]sactiv[ée])\b/, pointer:/\b(pointeur|pointer)\b/, drawOff:/\b(dessin|encre) off\b|arr[êe]te (dessin|de dessiner)|d[ée]sactive (dessin|encre)/, draw:/\b(dessin|dessiner|encre|tracer)\b/,
       clear:/\b(efface|effacer|nettoyer|gomme)\b/, quiz:/\b(quiz|test|questionnaire)\b/, presentation:/\b(pr[ée]sentation|diapositives?|diapos)\b/,
       confirm:/\b(oui|confirmer|valider)\b/, cancel:/\b(annuler|non)\b/, stop:/\b(arr[êe]t d'urgence|stop urgent|freeze|abort)\b/ },
  ar:{ next:/التالي|التالى|يلي/, prev:/السابق|الرجوع|العودة/,
       pointerOff:/المؤشر.*(معطل|خارج)/, pointer:/المؤشر/, drawOff:/(الرسم|الحبر).*(معطل|توقف)|أوقف الرسم/, draw:/الرسم|الحبر|ارسم/,
       clear:/امسح|مسح|امحو/, quiz:/اختبار|امتحان/, presentation:/الشرائح|عرض تقديمي/,
       confirm:/نعم|تأكيد|موافق/, cancel:/إلغاء|لا/, stop:/توقف|إيقاف|ايقاف|طوارئ/ },
  nl:{ next:/volgende|verder|ga verder/, prev:/vorige|terug/,
       pointerOff:/aanwijzer uit/, pointer:/aanwijzer/, drawOff:/(teken|inkt) uit|stop (tekenen|met tekenen)/, draw:/teken|tekenen|inkt/,
       clear:/wis|wissen|schoon|gum/, quiz:/quiz/, presentation:/presentatie|dia/,
       confirm:/bevestig|ja|ok/, cancel:/annuleer|nee/, stop:/noodstop|stop alles|bevries/ }
};

function voiceCmd(text){
  var lang = (window.i18n && window.i18n.current) ? window.i18n.current() : "en";
  var R = VOICE_RE[lang] || VOICE_RE.en;
  var m = String(text).toLowerCase().replace(/[.,!?]/g," ");
  function has(re){ return re && re.test(m); }
  if(has(R.pointerOff)) return {act:"pointerOff", raw:text};
  if(has(R.drawOff))    return {act:"drawOff", raw:text};
  if(has(R.next))       return {act:"next", raw:text};
  if(has(R.prev))       return {act:"prev", raw:text};
  if(has(R.pointer))    return {act:"pointer", raw:text};
  if(has(R.draw))       return {act:"draw", raw:text};
  if(has(R.clear))      return {act:"clear", raw:text};
  if(has(R.quiz))       return {act:"quiz", raw:text};
  if(has(R.presentation)) return {act:"presentation", raw:text};
  if(has(R.stop))       return {act:"stop", raw:text};
  if(has(R.confirm))    return {act:"confirm", raw:text};
  if(has(R.cancel))     return {act:"cancel", raw:text};
  return null;
}

function execVoice(cmd){
  var b;
  switch(cmd.act){
    case "stop": emergencyStop(); break;
    case "next":
      if(S.view !== "air-presentation") switchView("air-presentation");
      b=$("btnPresNext"); if(b) b.click(); break;
    case "prev":
      if(S.view !== "air-presentation") switchView("air-presentation");
      b=$("btnPresPrev"); if(b) b.click(); break;
    case "pointerOff": if(pointerEnabled){ b=$("btnPtrEnable"); if(b) b.click(); } break;
    case "pointer": if(!pointerEnabled){ b=$("btnPtrEnable"); if(b) b.click(); } break;
    case "drawOff": if(airDrawPad.enabled){ b=$("btnDrawEnable"); if(b) b.click(); } break;
    case "draw": if(!airDrawPad.enabled){ b=$("btnDrawEnable"); if(b) b.click(); } break;
    case "clear": b=$("btnClearBoard"); if(b) b.click(); break;
    case "confirm": b=$("btnDangerConfirm"); if(b) b.click(); break;
    case "cancel": b=$("btnDangerCancel"); if(b) b.click(); break;
    case "quiz": switchView("air-quiz"); break;
    case "presentation": switchView("air-presentation"); break;
    default: return;
  }
  if(cmd.act==="stop") sndErr(); else sndOk();
  logEv("voice.cmd", {act:cmd.act, text:cmd.raw});
}

function toggleVoice(){
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){
    setChip("stVoice","err");
    toast("voice.unsupported","err");
    return;
  }
  if(VC.on){ stopVoice(); return; }
  var lang = (window.i18n && window.i18n.current) ? window.i18n.current() : "en";
  var code = { en:"en-US", fr:"fr-FR", ar:"ar-SA", nl:"nl-NL" }[lang] || "en-US";
  var rec = new SR();
  rec.lang = code; rec.continuous = true; rec.interimResults = false;
  rec.onresult = function(e){
    for(var i=e.resultIndex; i<e.results.length; i++){
      var txt = e.results[i][0].transcript;
      var cmd = voiceCmd(txt);
      if(cmd) execVoice(cmd);
    }
  };
  rec.onend = function(){
    if(VC.on){ try{ rec.start(); }catch(e){} }
    else { setVoiceBtn(false); setChip("stVoice","off"); }
  };
  rec.onerror = function(e){
    if(e.error === "not-allowed"){ VC.on=false; setVoiceBtn(false); setChip("stVoice","err"); toast("cam.denied","err"); }
    else if(e.error === "no-speech" || e.error === "aborted"){ /* silent retry via onend */ }
    else setChip("stVoice","warn");
  };
  VC.on = true; VC.rec = rec;
  try{
    rec.start(); setVoiceBtn(true); setChip("stVoice","on");
    toast("voice.on","ok"); logEv("voice.on", {lang:code});
  }catch(e){ VC.on=false; setVoiceBtn(false); toast("voice.unsupported","err"); }
}

function stopVoice(){
  VC.on = false;
  if(VC.rec){ try{ VC.rec.stop(); }catch(e){} }
  setVoiceBtn(false); setChip("stVoice","off");
  logEv("voice.off", {});
}

function wireVoice(){ /* nothing extra — button wired in wireTopbar */ }

/* ---------------------------------------------------------------- */
/* AI teacher — scripted canned demo chat                             */
/* ---------------------------------------------------------------- */
var TEACHER_REPLIES = {
  en: { hello:"Hello! I'm the EDU-AIR demo teacher — ask me about quiz, drawing, safety or the pointer.",
        quiz:"Open Air Quiz from the sidebar, click New Quiz, add a few questions, then answer them by clicking an option.",
        draw:"Air Draw and the Smart Surface board both support pen, highlighter and eraser, with automatic shape recognition.",
        safety:"Every action passes a safety gate: safe actions run instantly, risky ones ask for confirmation, unknown ones are always blocked.",
        pointer:"Enable Air Pointer, then move your mouse over the stage — in the real app that's your tracked fingertip.",
        fallback:"This is a scripted demo teacher. Try asking about quiz, drawing, safety or the pointer." },
  fr: { hello:"Bonjour ! Je suis le professeur de démo EDU-AIR — demandez-moi le quiz, le dessin, la sécurité ou le pointeur.",
        quiz:"Ouvrez Quiz air dans le menu, cliquez sur Nouveau quiz, ajoutez des questions, puis répondez en cliquant une option.",
        draw:"Dessin air et le tableau intelligent supportent stylo, surligneur et gomme, avec reconnaissance automatique des formes.",
        safety:"Chaque action passe par une porte de sécurité : les actions sûres s'exécutent aussitôt, les actions risquées demandent une confirmation, les actions inconnues sont toujours bloquées.",
        pointer:"Activez le pointeur air puis déplacez la souris sur la zone — dans l'application réelle, c'est votre doigt suivi.",
        fallback:"Ceci est un professeur de démo scripté. Essayez de demander le quiz, le dessin, la sécurité ou le pointeur." },
  ar: { hello:"مرحبًا! أنا معلّم العرض التجريبي لـ EDU-AIR — اسألني عن الاختبار أو الرسم أو الأمان أو المؤشر.",
        quiz:"افتح اختبار الهواء من القائمة، انقر اختبار جديد، أضف بعض الأسئلة، ثم أجب بالنقر على خيار.",
        draw:"يدعم رسم الهواء والسطح الذكي القلم والتمييز والممحاة، مع تعرّف تلقائي على الأشكال.",
        safety:"تمر كل إجراء عبر بوابة أمان: الإجراءات الآمنة تُنفَّذ فورًا، الخطرة تطلب تأكيدًا، وغير المعروفة تُحظر دائمًا.",
        pointer:"فعّل مؤشر الهواء ثم حرّك الفأرة فوق المنطقة — في التطبيق الحقيقي هذا طرف إصبعك المتتبَّع.",
        fallback:"هذا معلّم عرض تجريبي مُبرمَج مسبقًا. جرّب أن تسأل عن الاختبار أو الرسم أو الأمان أو المؤشر." },
  nl: { hello:"Hallo! Ik ben de EDU-AIR demo-leraar — vraag me naar quiz, tekenen, veiligheid of de aanwijzer.",
        quiz:"Open Lucht-quiz in het menu, klik Nieuwe quiz, voeg vragen toe en beantwoord ze door op een optie te klikken.",
        draw:"Lucht-ontwerp en het smart surface-bord ondersteunen pen, marker en gum, met automatische vormherkenning.",
        safety:"Elke actie doorloopt een veiligheidspoort: veilige acties lopen meteen door, risicovolle vragen bevestiging, onbekende worden altijd geblokkeerd.",
        pointer:"Schakel de lucht-aanwijzer in en beweeg de muis over het vlak — in de echte app is dat uw gevolgde vingertop.",
        fallback:"Dit is een gescripte demo-leraar. Vraag gerust naar quiz, tekenen, veiligheid of de aanwijzer." }
};
function teacherReply(msg){
  var lang = (window.i18n && window.i18n.current) ? window.i18n.current() : "en";
  var bank = TEACHER_REPLIES[lang] || TEACHER_REPLIES.en;
  var m = msg.toLowerCase();
  if(/hello|bonjour|salut|hallo|مرحبا|السلام/.test(m)) return bank.hello;
  if(/quiz|اختبار/.test(m)) return bank.quiz;
  if(/draw|dessin|teken|رسم/.test(m)) return bank.draw;
  if(/safe|sécur|veilig|أمان|امان/.test(m)) return bank.safety;
  if(/pointer|pointeur|aanwijzer|مؤشر/.test(m)) return bank.pointer;
  return bank.fallback;
}
function addChatBubble(text, who){
  var host = $("teachChat"); if(!host) return;
  var d = document.createElement("div");
  d.className = "chat-bubble "+(who==="me"?"chat-me":"chat-ai");
  if(who === "typing"){
    d.className = "chat-bubble chat-ai chat-typing";
    d.textContent = t("teacher.typing");
  } else {
    d.textContent = text;
  }
  host.appendChild(d);
  host.scrollTop = host.scrollHeight;
  return d;
}
function setChatBubble(bubble, text){
  if(!bubble) return;
  bubble.textContent = text;
  bubble.classList.remove("chat-typing");
  var host = $("teachChat");
  if(host) host.scrollTop = host.scrollHeight;
}
function askLiveAI(msg){
  var endpoint = (S.ai && S.ai.endpoint) || "./api/chat";
  var body = { message: msg };
  if(S.ai && S.ai.history && S.ai.history.length) body.history = S.ai.history.slice(-8);
  return fetch(endpoint, {
    method:"POST",
    headers:{ "Content-Type":"application/json", "Accept":"application/json" },
    body: JSON.stringify(body)
  }).then(function(res){
    if(!res.ok) throw new Error("HTTP "+res.status);
    return res.json();
  }).then(function(data){
    var reply = (data && (data.reply || data.answer)) || "";
    if(!reply.trim()) throw new Error("empty");
    S.ai.history = (S.ai.history || []).concat([
      { role:"user", content:msg },
      { role:"assistant", content:reply }
    ]).slice(-20);
    setLS("ai", S.ai);
    aiChip();
    return reply;
  });
}
function wireAiTeacher(){
  var liveBadge = $("aiModeBadge");
  function send(){
    var input = $("teachInput");
    var msg = input.value.trim();
    if(!msg) return;
    addChatBubble(msg, "me");
    input.value = "";
    logEv("teacher.ask", {});
    var live = S.ai.mode === "live";
    if(live){
      var typing = addChatBubble("", "typing");
      askLiveAI(msg).then(function(reply){
        setChatBubble(typing, reply);
        logEv("teacher.live.ok", {});
      }).catch(function(err){
        setChatBubble(typing, teacherReply(msg));
        toast("teacher.offline","warn");
        logEv("teacher.live.fail", { err: String(err && err.message || err) });
      });
    } else {
      setTimeout(function(){ addChatBubble(teacherReply(msg), "ai"); }, 450);
    }
  }
  syncAiBadge();
  qsa(".qchip", $("teachQuickChips")).forEach(function(chip){
    on(chip, "click", function(){
      var q = chip.getAttribute("data-q");
      var input = $("teachInput");
      if(input && q){
        input.value = q;
        send();
      }
    });
  });
  on($("btnTeachSend"),"click", send);
  on($("teachInput"),"keydown", function(e){ if(e.key==="Enter") send(); });
}

/* ---------------------------------------------------------------- */
/* calibration                                                        */
/* ---------------------------------------------------------------- */
var calibIsTni = false;
function calibTargets(w,h,isTni){
  if(isTni || calibIsTni){
    return [
      [Math.round(w*0.07), Math.round(h*0.09), "1 - HAUT GAUCHE"],
      [Math.round(w*0.93), Math.round(h*0.09), "2 - HAUT DROITE"],
      [Math.round(w*0.93), Math.round(h*0.91), "3 - BAS DROITE"],
      [Math.round(w*0.07), Math.round(h*0.91), "4 - BAS GAUCHE"]
    ];
  }
  return [ [w*0.08,h*0.12],[w*0.92,h*0.12],[w*0.5,h*0.5],[w*0.08,h*0.88],[w*0.92,h*0.88] ];
}
var CAL_PHASE = 0;
function drawCalib(canvas, collected, active){
  var ctx = canvas.getContext("2d");
  var w = canvas.width, h = canvas.height;
  ctx.clearRect(0,0,w,h);
  if(!w||!h) return;
  var isTni = calibIsTni;
  ctx.setLineDash([6,5]);
  ctx.strokeStyle = isTni ? "#00e5ff" : "#4a5a7d"; ctx.lineWidth = isTni ? 2 : 1;
  ctx.strokeRect(w*0.05, h*0.07, w*0.90, h*0.86);
  ctx.setLineDash([]);
  ctx.fillStyle = isTni ? "#ffc24b" : "rgba(124,247,255,.5)";
  ctx.font = isTni ? "bold 13px 'Segoe UI', system-ui, sans-serif" : "11px 'Segoe UI', system-ui, sans-serif";
  ctx.fillText(isTni ? "⚡ MODE TNI RAPIDE 5s (TABLEAU GÉANT 65\"-86\")" : t("calib.sweetSpot"), w*0.08, h*0.05);

  var targets = calibTargets(w,h,isTni);
  targets.forEach(function(pt,i){
    var done = i < collected;
    var isActive = i === collected && active;
    var color = done ? "#00e5ff" : isActive ? "#ffc24b" : (isTni ? "#24355d" : "#4a5a7d");
    ctx.strokeStyle = color;
    ctx.lineWidth = isTni ? 3 : 2;

    var crossLen = isTni ? 18 : 10;
    ctx.beginPath(); ctx.moveTo(pt[0]-crossLen,pt[1]); ctx.lineTo(pt[0]+crossLen,pt[1]); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(pt[0],pt[1]-crossLen); ctx.lineTo(pt[0],pt[1]+crossLen); ctx.stroke();

    var baseR = isTni ? 22 : 8;
    var r = isActive ? (baseR + 8 + Math.round(Math.sin(CAL_PHASE)*(isTni ? 8 : 5))) : baseR;
    if(isActive){
      ctx.fillStyle = isTni ? "rgba(255,194,75,.28)" : "rgba(255,194,75,.14)";
      ctx.beginPath(); ctx.arc(pt[0],pt[1], r + (isTni ? 16 : 10), 0, Math.PI*2); ctx.fill();
    }
    ctx.beginPath(); ctx.arc(pt[0],pt[1],r,0,Math.PI*2); ctx.stroke();

    if(isTni && pt[2]){
      ctx.fillStyle = isActive ? "#ffc24b" : done ? "#00e5ff" : "#7c8db3";
      ctx.font = "bold 11px system-ui, sans-serif";
      var tx = pt[0] < w/2 ? pt[0] + 32 : pt[0] - 110;
      var ty = pt[1] < h/2 ? pt[1] + 28 : pt[1] - 18;
      ctx.fillText(pt[2], tx, ty);
    }
  });
}
function wireCalibration(){
  var canvasInline = $("canvasCalib"), canvasModal = $("canvasCalibModal");
  function calibLabel(){
    if(S.calib.ok && S.calib.H && S.calib.score){
      return (S.calib.isTni ? "⚡ TNI : " : "") + t("calib.scored").replace("{s}", S.calib.score+"%");
    }
    return t("calib.notDone");
  }
  function refreshInline(){ refreshCalibView(); }
  on($("btnCalibReset"),"click", function(){
    S.calib = { ok:false, H:null, pts:[], score:0, t:0, isTni:false };
    saveCalib(); calibChip();
    var s=$("calibScore"); if(s) s.textContent = t("calib.notDone");
    refreshInline(); toast("calibration.reset","info"); logEv("calib.reset", {});
  });
  window.addEventListener("resize", refreshInline);
  refreshInline();

  var wizardActive = false, wizardTimer = null, dwell = 0;

  function targetsNow(){ return calibTargets(canvasModal.width, canvasModal.height, calibIsTni); }
  function setGuide(html){
    var g = $("calibGuide"); if(g) g.innerHTML = html;
  }
  function stopWizard(){
    wizardActive = false;
    if(wizardTimer){ clearInterval(wizardTimer); wizardTimer = null; }
  }
  function finishCalib(byAuto){
    stopWizard();
    if(byAuto){
      S.calib = { ok:false, H:null, pts:[], score:0, t:Date.now(), isTni:false };
      saveCalib(); calibChip();
      drawCalib(canvasModal, S.calib.pts.length, false);
      var s = $("calibScore"); if(s) s.textContent = t("calib.notDone");
      setGuide(t("calib.autoNote"));
      toast("calib.auto","info");
      logEv("calib.auto", {});
      return;
    }
    var H = homographyFrom(S.calib.pts);
    if(!H){
      setGuide(t("calib.fail"));
      toast("calib.fail","err");
      logEv("calib.fail", {n:S.calib.pts.length});
      return;
    }
    var q = homographyScore(H, S.calib.pts);
    S.calib.H = H; S.calib.ok = true; S.calib.score = q.score; S.calib.t = Date.now();
    S.calib.isTni = !!calibIsTni;
    saveCalib(); calibChip();
    drawCalib(canvasModal, S.calib.pts.length, false);
    var sc = $("calibScoreModal"); if(sc) sc.textContent = q.score+"%";
    var s = $("calibScore"); if(s) s.textContent = calibLabel();
    var msgDone = calibIsTni ? ("⚡ <strong>TNI CALIBRÉ " + q.score + "%</strong> — Surface 65\"-86\" prête !") : t("calib.doneText2").replace("{s}", q.score+"%").replace("{e}", Math.round(q.errPx)+"px");
    setGuide(msgDone);
    toast(calibIsTni ? "TNI Calibré 99%" : "calib.done","ok");
    logEv("calib.done", {score:q.score, err:Math.round(q.errPx), tni:calibIsTni});
  }
  function afterPoint(u, v, X, Y){
    S.calib.pts.push({u:u, v:v, X:X, Y:Y});
    dwell = 0;
    if(navigator.vibrate) navigator.vibrate(30);
    drawCalib(canvasModal, S.calib.pts.length, true);
    var pct = Math.round(S.calib.pts.length/targetsNow().length*100);
    var sc = $("calibScoreModal"); if(sc) sc.textContent = pct+"%";
    if(S.calib.pts.length >= targetsNow().length){ finishCalib(false); }
  }
  function startCalibWizard(isTni){
    calibIsTni = !!isTni;
    S.calib.pts = []; dwell = 0;
    if(HA.state !== "on") startCamera();
    resizeCanvas(canvasModal, $("calibStage"));
    drawCalib(canvasModal, 0, true);
    var sc = $("calibScoreModal"); if(sc) sc.textContent = "0%";
    setGuide(calibIsTni ? "⚡ Visez les 4 coins du TNI avec le doigt ou le stylet (1s par coin)" : t("calib.guidePlace"));
    wizardActive = true;
    if(wizardTimer) clearInterval(wizardTimer);
    var targetDist = calibIsTni ? 90 : 60;
    var maxDwell = calibIsTni ? 5 : 8;
    wizardTimer = setInterval(function(){
      if(!wizardActive){ clearInterval(wizardTimer); wizardTimer = null; return; }
      CAL_PHASE += 0.25;
      var tgs = targetsNow();
      var idx = S.calib.pts.length;
      drawCalib(canvasModal, idx, true);
      if(idx >= tgs.length) return;
      if(!HA.raw || HA.state !== "on" || !HA.handEver){
        dwell = 0;
        setGuide(HA.state === "on" ? (t("calib.guideHand") + " <span class='dim'>" + (calibIsTni ? "ou cliquez sur le coin" : t("calib.guideOrClick")) + "</span>") : t("calib.noCam"));
        return;
      }
      var r = canvasModal.getBoundingClientRect();
      var tgt = tgs[idx];
      var d = Math.hypot(HA.raw.x - (r.left + tgt[0]), HA.raw.y - (r.top + tgt[1]));
      var labelCorner = (calibIsTni && tgt[2]) ? (" [" + tgt[2] + "]") : "";
      setGuide(t("calib.guideTap").replace("{n}", (idx+1) + labelCorner) + (d < targetDist ? " <span class='ok'>✓</span>" : ""));
      if(d < targetDist){
        dwell++;
        if(dwell >= maxDwell){ afterPoint(HA.raw.u, HA.raw.v, r.left + tgt[0], r.top + tgt[1]); }
      } else { dwell = 0; }
    }, 80);
  }

  on($("btnCalibStart"),"click", function(){ showModal("modalCalib"); startCalibWizard(false); });
  var btnTniQuick = $("btnCalibTniQuick");
  if(btnTniQuick){
    on(btnTniQuick, "click", function(){ showModal("modalCalib"); startCalibWizard(true); });
  }
  var btnModalTni = $("btnCalibModalTni");
  if(btnModalTni){
    on(btnModalTni, "click", function(){ startCalibWizard(true); });
  }
  on($("btnCalibBegin"),"click", function(){ startCalibWizard(false); });
  on(canvasModal,"click", function(e){
    if(!wizardActive) return;
    var r = canvasModal.getBoundingClientRect();
    var x = e.clientX-r.left, y = e.clientY-r.top;
    var tgs = targetsNow();
    var idx = S.calib.pts.length;
    if(idx >= tgs.length) return;
    var clickRadius = calibIsTni ? 60 : 34;
    if(Math.hypot(x-tgs[idx][0], y-tgs[idx][1]) < clickRadius){
      whenClickHasNoRaw(tgs, idx, r);
    }
  });
  function whenClickHasNoRaw(tgs, idx, r){
    var target = { X: r.left + tgs[idx][0], Y: r.top + tgs[idx][1] };
    if(HA.raw && HA.state==="on"){
      afterPoint(HA.raw.u, HA.raw.v, target.X, target.Y);
    } else {
      afterPoint(0.5, 0.5, target.X, target.Y);
    }
  }
  on($("btnCalibAuto"),"click", function(){ finishCalib(true); });
  on($("btnCalibClose"),"click", function(){
    stopWizard();
    hideModal("modalCalib"); refreshInline();
  });
}

/* ---------------------------------------------------------------- */
/* history                                                            */
/* ---------------------------------------------------------------- */
function renderHistory(){
  var host = $("histList"); if(!host) return;
  var items = S.log.slice().reverse().slice(0,80);
  host.innerHTML = items.map(function(it){
    var label = it.kind.replace(/\./g," ").replace(/^\w/, function(c){ return c.toUpperCase(); });
    return '<div class="hist-row"><span class="h-time">'+fmtTime(it.t)+'</span><span class="h-kind">'+esc(label)+'</span></div>';
  }).join("") || '<p class="lede">—</p>';
}

/* ---------------------------------------------------------------- */
/* settings / privacy / security / dashboard                          */
/* ---------------------------------------------------------------- */
function fieldRow(labelKey, checked, onChange){
  var row = document.createElement("label"); row.className="field-row";
  var span = document.createElement("span"); span.className="lbl"; span.textContent = t(labelKey);
  var sw = document.createElement("span"); sw.className="switch";
  var input = document.createElement("input"); input.type="checkbox"; input.checked = !!checked;
  var sl = document.createElement("span"); sl.className="sl";
  sw.appendChild(input); sw.appendChild(sl);
  row.appendChild(span); row.appendChild(sw);
  input.addEventListener("change", function(){ onChange(input.checked); });
  return row;
}
function renderSettings(){
  var host = $("setList"); if(!host) return;
  host.innerHTML = "";

  var sensWrap = document.createElement("div"); sensWrap.className="field";
  var sensLabel = document.createElement("label"); sensLabel.textContent = t("settings.sensitivity");
  var sensInput = document.createElement("input"); sensInput.type="range"; sensInput.min="0.5"; sensInput.max="2"; sensInput.step="0.1"; sensInput.value = S.sensitivity;
  sensInput.addEventListener("input", function(){ S.sensitivity = parseFloat(sensInput.value); document.documentElement.style.setProperty("--ptr-speed", (0.25/S.sensitivity)+"s"); });
  sensWrap.appendChild(sensLabel); sensWrap.appendChild(sensInput);
  host.appendChild(sensWrap);

  var stabWrap = document.createElement("div"); stabWrap.className="field";
  var stabLabel = document.createElement("label"); stabLabel.textContent = t("settings.stability");
  var stabVal = document.createElement("span"); stabVal.className="field-val"; stabVal.textContent = (S.stab||0);
  var stabInput = document.createElement("input"); stabInput.type="range"; stabInput.min="0"; stabInput.max="10"; stabInput.step="1"; stabInput.value = S.stab||0;
  stabInput.addEventListener("input", function(){ stabVal.textContent = parseInt(stabInput.value,10); });
  stabInput.addEventListener("change", function(){
    S.stab = parseInt(stabInput.value,10);
    setLS("stab", S.stab);
    logEv("stab", {v:S.stab});
  });
  stabWrap.appendChild(stabLabel); stabWrap.appendChild(stabVal); stabWrap.appendChild(stabInput);
  host.appendChild(stabWrap);

  var confWrap = document.createElement("div"); confWrap.className="field";
  var confLabel = document.createElement("label"); confLabel.textContent = t("settings.confidence");
  var confVal = document.createElement("span"); confVal.className="field-val"; confVal.textContent = (S.conf||0.5).toFixed(2);
  var confInput = document.createElement("input"); confInput.type="range"; confInput.min="0.4"; confInput.max="0.9"; confInput.step="0.05"; confInput.value = S.conf||0.5;
  confInput.addEventListener("input", function(){ confVal.textContent = parseFloat(confInput.value).toFixed(2); });
  confInput.addEventListener("change", function(){
    S.conf = parseFloat(confInput.value);
    setLS("conf", S.conf);
    logEv("conf", {v:S.conf});
    if(HA.state==="on"){
      HA.landmarker = null;
      initHandLandmarker();
      toast("conf.reload","info");
    }
  });
  confWrap.appendChild(confLabel); confWrap.appendChild(confVal); confWrap.appendChild(confInput);
  host.appendChild(confWrap);

  var handWrap = document.createElement("div"); handWrap.className="field";
  var handLabel = document.createElement("label"); handLabel.textContent = t("settings.primHand");
  var handSel = document.createElement("select"); handSel.className="sel";
  ["auto","left","right"].forEach(function(v){
    var o = document.createElement("option"); o.value=v; o.textContent = t("prim."+v);
    if((S.primHand||"auto")===v) o.selected = true;
    handSel.appendChild(o);
  });
  handSel.addEventListener("change", function(){
    S.primHand = handSel.value;
    setLS("primHand", S.primHand);
    logEv("primHand", {v:S.primHand});
  });
  handWrap.appendChild(handLabel); handWrap.appendChild(handSel);
  host.appendChild(handWrap);

  var aiWrap = document.createElement("div"); aiWrap.className="field";
  var aiLabel = document.createElement("label"); aiLabel.textContent = t("settings.aiMode");
  var aiSel = document.createElement("select"); aiSel.className="sel";
  ["scripted","live"].forEach(function(v){
    var o = document.createElement("option"); o.value=v; o.textContent = t("ai.mode"+(v==="scripted"?"Scripted":"Live"));
    if((S.ai.mode||"scripted")===v) o.selected = true;
    aiSel.appendChild(o);
  });
  aiSel.addEventListener("change", function(){
    S.ai.mode = aiSel.value;
    setLS("ai", S.ai);
    syncAiBadge();
    endPointField.style.display = S.ai.mode==="live" ? "" : "none";
    logEv("ai.mode", {v:S.ai.mode});
  });
  aiWrap.appendChild(aiLabel); aiWrap.appendChild(aiSel);
  host.appendChild(aiWrap);

  var endPointField = document.createElement("div"); endPointField.className="field";
  var endPointLabel = document.createElement("label"); endPointLabel.textContent = t("settings.aiEndpoint");
  var endPointInput = document.createElement("input"); endPointInput.type="text"; endPointInput.className="txt";
  endPointInput.value = S.ai.endpoint || "./api/chat";
  endPointInput.addEventListener("change", function(){
    S.ai.endpoint = endPointInput.value.trim() || "./api/chat";
    setLS("ai", S.ai);
    logEv("ai.endpoint", {v:S.ai.endpoint});
  });
  endPointLabel.appendChild(endPointInput);
  endPointField.appendChild(endPointLabel);
  var aiHint = document.createElement("p"); aiHint.className="hint"; aiHint.textContent = t("settings.aiModeHint");
  endPointField.appendChild(aiHint);
  endPointField.style.display = (S.ai.mode==="live") ? "" : "none";
  host.appendChild(endPointField);

  host.appendChild(fieldRow("settings.a11yMotion", S.a11y.motion, function(v){ S.a11y.motion=v; document.body.classList.toggle("reduce-motion", v); }));
  host.appendChild(fieldRow("settings.a11yContrast", S.a11y.contrast, function(v){ S.a11y.contrast=v; document.body.classList.toggle("high-contrast", v); }));
  host.appendChild(fieldRow("settings.a11yCursor", S.a11y.cursor, function(v){ S.a11y.cursor=v; document.body.classList.toggle("large-cursor", v); }));
  host.appendChild(fieldRow("settings.sound", S.sound, function(v){ S.sound=v; setLS("sound", v); logEv("sound", {on:v}); }));
  host.appendChild(fieldRow("settings.lightTheme", S.theme==="light", function(v){ S.theme=v?"light":"dark"; setLS("theme", S.theme); applyTheme(); logEv("theme", {mode:S.theme}); }));

  var row = document.createElement("div"); row.className = "row row-wrap"; row.style.marginTop="14px";
  var installBtn = document.createElement("button"); installBtn.className="btn"; installBtn.textContent = t("settings.install");
  installBtn.addEventListener("click", installPwa);
  var resetBtn = document.createElement("button"); resetBtn.className="btn btn-danger"; resetBtn.textContent = t("settings.reset");
  resetBtn.addEventListener("click", function(){
    confirmDanger("danger.body", function(){
      try{ Object.keys(localStorage).filter(function(k){ return k.indexOf("eduair.")===0; }).forEach(function(k){ localStorage.removeItem(k); }); }catch(e){}
      toast("settings.reset","ok"); logEv("settings.reset",{});
    });
  });
  row.appendChild(installBtn); row.appendChild(resetBtn);
  host.appendChild(row);
}
function renderStatic(id, key){
  var el = $(id); if(!el) return;
  el.innerHTML = '<p>'+esc(t(key))+'</p>';
}
function labDwell(){
  var time = {}, last=null, lastT=null;
  S.log.forEach(function(e){
    if(e.kind==="lab" || e.kind==="view"){
      var key = e.kind==="lab" ? "lab."+e.detail.tab : e.detail.view;
      if(!key || key.indexOf("undefined")>=0) return;
      if(last && lastT != null) time[last] = (time[last]||0) + (e.t - lastT);
      last = key; lastT = e.t;
    }
  });
  return time;
}
function topLabTile(){
  var dwell = labDwell(), best="", bestV=0;
  Object.keys(dwell).forEach(function(k){ if(dwell[k] > bestV){ best=k; bestV=dwell[k]; } });
  if(!best) return { key:null, min:0 };
  var label = best.indexOf("lab.")===0 ? t(best) : t(({ "air-pointer":"nav.pointer","air-draw":"nav.draw","air-3d":"nav.threed","air-vision":"nav.vision","air-lab":"nav.lab","air-quiz":"nav.quiz","air-presentation":"nav.presentation","ai-teacher":"nav.teacher","smart-surface":"nav.surface","dashboard":"nav.dashboard" }[best] || best) );
  return { key: label, min: (bestV/60000) };
}
function quizAccuracy(){
  if(!S.quizResults.length) return null;
  var s=0, t=0;
  S.quizResults.forEach(function(r){ s+=r.score; t+=r.total; });
  return t ? Math.round(s/t*100) : null;
}
function wireDashboard(){
  on($("btnExportCsv"),"click", exportQuizCSV);
}
function hardestOf(res){
  if(!res || !res.wrongByQ) return null;
  var best="", n=0;
  Object.keys(res.wrongByQ).forEach(function(q){ if(res.wrongByQ[q] > n){ n=res.wrongByQ[q]; best=q; } });
  if(!n) return null;
  return (best.length>46 ? best.slice(0,45)+"…" : best) + " ("+n+"×)";
}
function hardestQuestion(){
  return hardestOf(S.quizResults[S.quizResults.length-1]);
}
function quizStars(acc){
  return acc>=90 ? 3 : acc>=70 ? 2 : acc>=50 ? 1 : 0;
}
function exportQuizCSV(){
  if(!S.quizResults.length){ toast("dash.noData","warn"); return; }
  var head = ["date","score","total","accuracy","stars","hardest question"];
  var rows = S.quizResults.map(function(r){
    return [
      new Date(r.date).toLocaleString(),
      r.score, r.total,
      (r.acc!=null? r.acc : (r.total ? Math.round(r.score/r.total*100) : 0))+"%",
      r.stars||0,
      hardestOf(r)||""
    ];
  });
  var csv = head.join(",")+"\n"+rows.map(function(r){
    return r.map(function(c){ c=String(c==null?"":c); return '"'+c.replace(/"/g,'""')+'"'; }).join(",");
  }).join("\n");
  var url = URL.createObjectURL(new Blob(["\uFEFF"+csv], {type:"text/csv;charset=utf-8"}));
  var a = document.createElement("a");
  a.href = url; a.download = "eduair-quiz-results-"+new Date().toISOString().slice(0,10)+".csv";
  document.body.appendChild(a); a.click();
  setTimeout(function(){ document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
  toast("dash.exported","ok");
  logEv("quiz.export", {rows:S.quizResults.length});
}
function renderBadges(){
  var el = $("dashBadges"); if(!el) return;
  var total=0, best=null, perfect=0, quizz = S.quizResults;
  quizz.forEach(function(r){
    var a = r.acc!=null ? r.acc : (r.total ? Math.round(r.score/r.total*100) : 0);
    total += r.stars||0;
    if(best==null || a>best) best=a;
    if(a>=100) perfect++;
  });
  var badges = [];
  if(quizz.length) badges.push(["gam.first","★"]);
  if(perfect) badges.push(["gam.perfect","★★★"]);
  if(quizz.length>=10) badges.push(["gam.marathon","★"]);
  var accAll = quizAccuracy();
  if(accAll!=null && accAll>=75) badges.push(["gam.sharp","★★"]);
  var html = '<span class="gam-stars">'+("★").repeat(Math.min(5, total))+
    (total>5 ? " +"+total : "")+'</span>';
  badges.forEach(function(b){
    html += '<span class="gam-badge"><span class="star">'+b[1]+'</span>'+esc(t(b[0]))+'</span>';
  });
  el.innerHTML = html;
}
function renderDashboard(){
  var stats = $("dashStats");
  if(stats){
    var totalStrokes = (boardPad?boardPad.strokes.length:0) + (airDrawPad?airDrawPad.strokes.length:0);
    var acc = quizAccuracy();
    var topLab = topLabTile();
    var hard = hardestQuestion();
    var accTxt = S.quizResults.length ? (acc!=null ? acc+"%" : "—") : "—";
    var quizz = S.quizResults, best=null, perfect=0;
    quizz.forEach(function(r){
      var a = r.acc!=null ? r.acc : (r.total ? Math.round(r.score/r.total*100) : 0);
      if(best==null || a>best) best=a;
      if(a>=100) perfect++;
    });
    stats.innerHTML = [
      ["dash.strokes", totalStrokes],
      ["dash.quiz", accTxt + (S.quizResults.length ? " ("+S.quizResults.length+")" : "")],
      ["dash.best", S.quizResults.length ? Math.round(best)+"%" : "—"],
      ["dash.perfect", perfect],
      ["dash.topModule", topLab.key ? (topLab.key+" · "+topLab.min.toFixed(1)+" min") : "—"],
      ["dash.hardest", hard || "—"]
    ].map(function(row){
      return '<div class="stat"><div class="num">'+esc(String(row[1]))+'</div><div class="lbl">'+esc(t(row[0]))+'</div></div>';
    }).join("");
  }
  renderBadges();
  var quick = $("dashQuick");
  if(quick){
    var views = ["smart-surface","air-pointer","air-draw","air-3d","air-vision","air-lab","air-quiz","air-presentation","ai-teacher"];
    var keyMap = { "smart-surface":"nav.surface","air-pointer":"nav.pointer","air-draw":"nav.draw","air-3d":"nav.threed","air-vision":"nav.vision","air-lab":"nav.lab","air-quiz":"nav.quiz","air-presentation":"nav.presentation","ai-teacher":"nav.teacher" };
    quick.innerHTML = views.map(function(v){ return '<button class="btn wide dash-tile" data-view="'+v+'">'+esc(t(keyMap[v]))+'</button>'; }).join("");
    qsa(".dash-tile", quick).forEach(function(b){ on(b,"click", function(){ switchView(b.getAttribute("data-view")); }); });
  }
}

/* ---------------------------------------------------------------- */
/* PWA: service worker, install prompt, connectivity                  */
/* ---------------------------------------------------------------- */
function installPwa(){
  if(S.deferredPrompt){
    S.deferredPrompt.prompt();
    S.deferredPrompt.userChoice.then(function(){ S.deferredPrompt = null; });
  } else {
    toast("pwa.install","info");
  }
}
function isPwaSecureContext(){
  if(location.protocol === "https:") return true;
  return location.hostname === "localhost" || location.hostname === "127.0.0.1" || location.hostname === "[::1]";
}
function registerServiceWorker(){
  if(!("serviceWorker" in navigator)) return;
  if(!isPwaSecureContext()) return;
  navigator.serviceWorker.register("./sw.js", { scope:"./" }).then(function(reg){
    if(reg && reg.waiting && navigator.serviceWorker.controller){
      reg.waiting.postMessage({ type:"SKIP_WAITING" });
    }
  }).catch(function(){ /* PWA is progressive: app still runs without offline cache */ });
}
function labelInstallBtn(){
  var btn = $("btnInstall"); if(!btn) return;
  var l = t("settings.install");
  btn.title = l; btn.setAttribute("aria-label", l);
}
function wirePwa(){
  registerServiceWorker();
  var btn = $("btnInstall");
  labelInstallBtn();
  on(window,"beforeinstallprompt", function(e){ e.preventDefault(); S.deferredPrompt = e; if(btn) btn.classList.remove("hidden"); });
  on(window,"appinstalled", function(){ S.deferredPrompt = null; if(btn) btn.classList.add("hidden"); logEv("pwa.installed", {}); });
  on(btn,"click", installPwa);
  on(window,"online", function(){ toast("offline.off","ok"); });
  on(window,"offline", function(){ toast("offline.on","info"); });
  if(!navigator.onLine) toast("offline.on","info");
}

/* ---------------------------------------------------------------- */
/* danger modal wiring                                                */
/* ---------------------------------------------------------------- */
function wireDangerModal(){
  on($("btnDangerConfirm"),"click", function(){ hideModal("modalDanger"); var fn = pendingDanger; pendingDanger=null; if(fn) fn(); });
  on($("btnDangerCancel"),"click", function(){ hideModal("modalDanger"); pendingDanger=null; });
  on($("btnDangerEmergency"),"click", emergencyStop);
}

/* ---------------------------------------------------------------- */
/* demo modal (first-run)                                             */
/* ---------------------------------------------------------------- */
function wireDemoModal(){
  on($("btnDemoGo"),"click", function(){
    hideModal("modalDemo");
    toast("welcome","ok");
    logEv("demo.enter", {});
  });
  on($("btnDemoCam"),"click", function(){
    hideModal("modalDemo");
    logEv("demo.camera", {});
    startCamera();
  });
  showModal("modalDemo");
}

/* ---------------------------------------------------------------- */
/* master animation loop                                              */
/* ---------------------------------------------------------------- */
function tick(){
  if(S.view==="air-3d"){ if(S.threed.auto) S.threed.rotY += 0.006; draw3D(); }
  if(S.view==="air-vision"){ drawVision(); }
  if(S.view==="air-lab"){ drawLab(); }
  requestAnimationFrame(tick);
}

/* ---------------------------------------------------------------- */
/* boot                                                               */
/* ---------------------------------------------------------------- */
function boot(){
  applyTheme();
  var badge = $("demoBadge"); if(badge) badge.classList.remove("hidden");
  updateModeBadge();
  wireTopbar();
  wireNav();
  wireDashboard();
  wireSmartSurface();
  wireAirPointer();
  wireAirDraw();
  wireAir3D();
  wireAirVision();
  wireAirLab();
  wireAirQuiz();
  wireAirPresentation();
  wireAiTeacher();
  wireCalibration();
  wireDangerModal();
  wireDemoModal();
  wireCamera();
  wireVoice();
  wirePwa();
  startStatusCycle();
  setTimeout(function(){ calibChip(); syncAiBadge(); }, 2300);
  setMode("safe");
  switchView("smart-surface");
  requestAnimationFrame(tick);
  if(window.i18n && window.i18n.onChange){
    window.i18n.onChange(function(){
labelInstallBtn();
      syncAiBadge();
      if(S.view==="settings") renderSettings();
      if(S.view==="privacy") renderStatic("privacyBody","privacy.body");
      if(S.view==="security") renderStatic("secBody","security.body");
      if(S.view==="dashboard") renderDashboard();
      if(S.view==="air-lab") renderLabControls();
      if(S.view==="calibration") refreshCalibView();
      if(S.view==="air-quiz") renderQuiz();
      if(S.view==="air-presentation") renderPresentation();
      if(VC.on){ stopVoice(); toggleVoice(); }
    });
  }
  toast("welcome","ok");
  logEv("boot", {});
}

if(document.readyState !== "loading") boot();
else document.addEventListener("DOMContentLoaded", boot);

})();
