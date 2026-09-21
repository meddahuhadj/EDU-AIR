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
  quiz: { active:null, qi:0, score:0, total:0 },
  pres: { i:0, slides:[
    {t:"EDU-AIR SMART SURFACE", b:"A contactless AI-powered interactive whiteboard. No touch frame, no special sensor."},
    {t:"Air pointer", b:"Your hand becomes the cursor — pinch to click, hold to drag."},
    {t:"Air draw", b:"Freehand ink with automatic shape recognition, right in mid-air."},
    {t:"Safety by default", b:"Every action passes a safety gate: safe · confirm · critical. Nothing unregistered ever runs."},
    {t:"Works with what you already have", b:"Any PC + webcam + projector. No new hardware to buy or install."}
  ]},
  calib: { pts:[], targets:[], score:0 },
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
  var order = ["stCam","stHand","stVoice","stAI","stCalib","stSurface"];
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
  on($("btnMic"),"click", function(){
    var b = $("btnMic"); var on_ = b.getAttribute("data-state") !== "on";
    b.setAttribute("data-state", on_?"on":"off");
    setChip("stVoice", on_?"on":"off");
    logEv("voice", {on:on_});
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
  var pad = { svg:svg, strokes:[], redo:[], tool:opts.tool||"pen", color:opts.color||"#00e5ff", size:opts.size||4, shapes: !!opts.shapes, enabled: opts.enabled!==false, current:null, onStroke:opts.onStroke };
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
  function drawOne(st){
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
    svg.appendChild(el);
  }
  function renderAll(){
    while(svg.firstChild) svg.removeChild(svg.firstChild);
    pad.strokes.forEach(drawOne);
    if(pad.current) drawOne(pad.current);
  }
  function eraseAt(p){
    var before = pad.strokes.length;
    pad.strokes = pad.strokes.filter(function(st){
      return !st.pts.some(function(q){ return Math.hypot(q.x-p.x,q.y-p.y) < 0.035; });
    });
    if(pad.strokes.length !== before){ pad.redo.length=0; renderAll(); }
  }
  function down(ev){
    if(!pad.enabled) return;
    if(pad.tool==="eraser"){ eraseAt(toLocal(ev)); return; }
    pad.current = { tool:pad.tool, color:pad.color, size:pad.size, pts:[toLocal(ev)] };
  }
  function move(ev){
    if(!pad.enabled) return;
    if(pad.tool==="eraser"){ if(ev.buttons) eraseAt(toLocal(ev)); return; }
    if(!pad.current) return;
    var p = toLocal(ev);
    var last = pad.current.pts[pad.current.pts.length-1];
    if(last && Math.hypot(p.x-last.x,p.y-last.y) < 0.003) return;
    pad.current.pts.push(p);
    renderAll();
  }
  function up(){
    if(!pad.current) return;
    var st = pad.current; pad.current = null;
    if(st.pts.length < 2) return;
    if(pad.shapes && st.pts.length >= 8){
      var shape = detectShape(st.pts);
      if(shape) st.shape = shape;
    }
    pad.strokes.push(st); pad.redo.length = 0;
    renderAll();
    if(pad.onStroke) pad.onStroke(st);
  }
  var host = svg.parentNode;
  on(host,"pointerdown", down);
  on(host,"pointermove", move);
  on(host,"pointerup", up);
  on(host,"pointerleave", up);
  pad.undo = function(){ if(!pad.strokes.length) return false; pad.redo.push(pad.strokes.pop()); renderAll(); return true; };
  pad.redoLast = function(){ if(!pad.redo.length) return false; pad.strokes.push(pad.redo.pop()); renderAll(); return true; };
  pad.clear = function(){ pad.strokes=[]; pad.redo=[]; renderAll(); };
  return pad;
}

var boardPad, airDrawPad;

function wireSmartSurface(){
  var svg = $("boardSvg");
  boardPad = makeInkPad(svg, { tool:"pen", color:$("inkColor").value, shapes:$("chkShapes").checked, size:4,
    onStroke: function(st){
      if(navigator.vibrate && $("chkHaptics").checked) navigator.vibrate(8);
      logEv("draw.stroke", {shape: st.shape||null});
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
    S.vision.fps = 0;
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
function renderLabControls(){
  var tab = S.lab.active;
  var host = $("labControls"); if(!host) return;
  host.innerHTML = "";
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
  ctx.strokeStyle="#1b2847"; ctx.strokeRect(0.5,0.5,w-1,h-1);
  if(S.lab.active==="circuit"){
    var I = p.voltage/p.resistance;
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
    var color = ph<7 ? lerpColor([255,77,109],[255,194,75], ph/7) : lerpColor([255,194,75],[0,229,255],(ph-7)/7);
    ctx.strokeStyle="#c7d4ee"; ctx.lineWidth=2;
    var bx=w*0.35, by=h*0.15, bw=w*0.3, bh=h*0.68;
    ctx.beginPath(); ctx.moveTo(bx,by); ctx.lineTo(bx,by+bh); ctx.lineTo(bx+bw,by+bh); ctx.lineTo(bx+bw,by); ctx.stroke();
    ctx.fillStyle = "rgb("+color.join(",")+")";
    ctx.fillRect(bx+3, by+bh*0.35, bw-6, bh*0.65-3);
    if(readout) readout.textContent = t("lab.ph")+": "+ph.toFixed(1)+ (ph<7?" (acid)":ph>7?" (base)":" (neutral)");
  } else if(S.lab.active==="pendulum"){
    var L = p.length/100, g = p.gravity;
    var omega = Math.sqrt(g/L);
    var theta = 0.6*Math.cos(omega*dt);
    var pivX=w/2, pivY=h*0.12, len=Math.min(h*0.7, L*180);
    var bobX = pivX + Math.sin(theta)*len, bobY = pivY + Math.cos(theta)*len;
    ctx.strokeStyle="#7cf7ff"; ctx.lineWidth=2;
    ctx.beginPath(); ctx.moveTo(pivX,pivY); ctx.lineTo(bobX,bobY); ctx.stroke();
    ctx.fillStyle="#00e5ff"; ctx.beginPath(); ctx.arc(bobX,bobY,10,0,Math.PI*2); ctx.fill();
    ctx.fillStyle="#7c8db3"; ctx.beginPath(); ctx.arc(pivX,pivY,3,0,Math.PI*2); ctx.fill();
    var T = 2*Math.PI*Math.sqrt(L/g);
    if(readout) readout.textContent = t("lab.period")+": "+T.toFixed(2)+" s";
  } else if(S.lab.active==="wave"){
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
    var cx=w/2, cy=h/2;
    ctx.fillStyle="#ffc24b"; ctx.beginPath(); ctx.arc(cx,cy,10,0,Math.PI*2); ctx.fill();
    [[40,2.2,"#00e5ff"],[70,1.4,"#7cf7ff"],[100,0.9,"#ff4d6d"]].forEach(function(pl,i){
      var r=pl[0]*Math.min(w,h)/260, speed=pl[1]*p.speed;
      ctx.strokeStyle="rgba(124,247,255,.2)"; ctx.beginPath(); ctx.arc(cx,cy,r,0,Math.PI*2); ctx.stroke();
      var a = dt*speed;
      var x=cx+Math.cos(a)*r, y=cy+Math.sin(a)*r*0.55;
      ctx.fillStyle=pl[2]; ctx.beginPath(); ctx.arc(x,y,6,0,Math.PI*2); ctx.fill();
    });
    if(readout) readout.textContent = t("lab.speed")+": "+p.speed.toFixed(1)+"×";
  }
}
function lerpColor(a,b,f){ f=clamp(f,0,1); return [Math.round(a[0]+(b[0]-a[0])*f), Math.round(a[1]+(b[1]-a[1])*f), Math.round(a[2]+(b[2]-a[2])*f)]; }

/* ---------------------------------------------------------------- */
/* air quiz                                                           */
/* ---------------------------------------------------------------- */
function wireAirQuiz(){
  on($("btnQuizNew"),"click", function(){ openQuizEditor(); });
  on($("btnQuizAddQ"),"click", function(){ addQuizQuestionRow(); });
  on($("btnQuizSave"),"click", function(){ saveQuizFromEditor(); });
  on($("btnQuizEditClose"),"click", function(){ hideModal("modalQuizEdit"); });
}
function openQuizEditor(){
  var host = $("qeditor"); host.innerHTML = "";
  addQuizQuestionRow();
  showModal("modalQuizEdit");
}
function addQuizQuestionRow(){
  var host = $("qeditor");
  var idx = host.children.length;
  var row = document.createElement("div"); row.className = "qrow";
  var q = document.createElement("input"); q.type="text"; q.placeholder = t("quiz.question")+" "+(idx+1); q.className="q-text";
  row.appendChild(q);
  var opts = document.createElement("div"); opts.className="row row-wrap";
  ["A","B","C","D"].forEach(function(letter,i){
    var wrap = document.createElement("label"); wrap.className="btbtn sml qopt";
    var radio = document.createElement("input"); radio.type="radio"; radio.name="correct-"+idx; radio.value=i; if(i===0) radio.checked=true;
    var input = document.createElement("input"); input.type="text"; input.placeholder=letter; input.className="q-opt";
    wrap.appendChild(radio); wrap.appendChild(input);
    opts.appendChild(wrap);
  });
  row.appendChild(opts);
  host.appendChild(row);
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
  S.quiz = { active: quiz, qi:0, score:0, total: questions.length };
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
    host.innerHTML = '<p class="lede">'+esc(t("quiz.finished"))+' — '+S.quiz.score+'/'+S.quiz.total+'</p>';
    if(scoreEl) scoreEl.textContent = S.quiz.score+" / "+S.quiz.total;
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
      toast(ok?"quiz.correct":"quiz.wrong", ok?"ok":"warn");
      logEv("quiz.answer", {ok:ok});
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
  if(host) host.innerHTML = '<div class="pres-slide"><h3>'+esc(slide.t)+'</h3><p>'+esc(slide.b)+'</p></div>';
  var count = $("presCount"); if(count) count.textContent = (i+1)+" / "+S.pres.slides.length;
}
function wireAirPresentation(){
  on($("btnPresPrev"),"click", function(){ S.pres.i = clamp(S.pres.i-1,0,S.pres.slides.length-1); renderPresentation(); logEv("pres.prev",{}); });
  on($("btnPresNext"),"click", function(){ S.pres.i = clamp(S.pres.i+1,0,S.pres.slides.length-1); renderPresentation(); logEv("pres.next",{}); });
  on(document,"keydown", function(e){
    if(S.view!=="air-presentation") return;
    if(e.key==="ArrowRight"){ $("btnPresNext").click(); }
    if(e.key==="ArrowLeft"){ $("btnPresPrev").click(); }
  });
}

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
  d.textContent = text;
  host.appendChild(d);
  host.scrollTop = host.scrollHeight;
}
function wireAiTeacher(){
  function send(){
    var input = $("teachInput");
    var msg = input.value.trim();
    if(!msg) return;
    addChatBubble(msg, "me");
    input.value = "";
    logEv("teacher.ask", {});
    setTimeout(function(){ addChatBubble(teacherReply(msg), "ai"); }, 450);
  }
  on($("btnTeachSend"),"click", send);
  on($("teachInput"),"keydown", function(e){ if(e.key==="Enter") send(); });
}

/* ---------------------------------------------------------------- */
/* calibration                                                        */
/* ---------------------------------------------------------------- */
function calibTargets(w,h){
  return [ [w*0.08,h*0.12],[w*0.92,h*0.12],[w*0.5,h*0.5],[w*0.08,h*0.88],[w*0.92,h*0.88] ];
}
function drawCalib(canvas, collected, active){
  var ctx = canvas.getContext("2d");
  var w = canvas.width, h = canvas.height;
  ctx.clearRect(0,0,w,h);
  if(!w||!h) return;
  var targets = calibTargets(w,h);
  targets.forEach(function(pt,i){
    var done = i < collected;
    var isActive = i === collected && active;
    ctx.strokeStyle = done ? "#00e5ff" : isActive ? "#ffc24b" : "#4a5a7d";
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(pt[0]-10,pt[1]); ctx.lineTo(pt[0]+10,pt[1]); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(pt[0],pt[1]-10); ctx.lineTo(pt[0],pt[1]+10); ctx.stroke();
    ctx.beginPath(); ctx.arc(pt[0],pt[1],isActive?14:8,0,Math.PI*2); ctx.stroke();
  });
}
function wireCalibration(){
  var canvasInline = $("canvasCalib"), canvasModal = $("canvasCalibModal");
  function refreshInline(){ resizeCanvas(canvasInline, $("calibWrap")); drawCalib(canvasInline, S.calib.pts.length, false); }
  on($("btnCalibStart"),"click", function(){ showModal("modalCalib"); startCalibWizard(); });
  on($("btnCalibReset"),"click", function(){ S.calib.pts=[]; S.calib.score=0; var s=$("calibScore"); if(s) s.textContent="0%"; refreshInline(); toast("calibration.reset","info"); });
  window.addEventListener("resize", refreshInline);
  refreshInline();

  var wizardActive = false;
  function startCalibWizard(){
    S.calib.pts = []; wizardActive = true;
    resizeCanvas(canvasModal, $("calibStage"));
    drawCalib(canvasModal, 0, true);
    var sc = $("calibScoreModal"); if(sc) sc.textContent = "0%";
  }
  on($("btnCalibBegin"),"click", startCalibWizard);
  on(canvasModal,"click", function(e){
    if(!wizardActive) return;
    var r = canvasModal.getBoundingClientRect();
    var x = e.clientX-r.left, y = e.clientY-r.top;
    var targets = calibTargets(canvasModal.width, canvasModal.height);
    var idx = S.calib.pts.length;
    if(idx >= targets.length) return;
    var tgt = targets[idx];
    if(Math.hypot(x-tgt[0], y-tgt[1]) < 28){
      S.calib.pts.push({x:x,y:y});
      drawCalib(canvasModal, S.calib.pts.length, true);
      var pct = Math.round(S.calib.pts.length/targets.length*100);
      var sc = $("calibScoreModal"); if(sc) sc.textContent = pct+"%";
      if(S.calib.pts.length >= targets.length){
        wizardActive = false; S.calib.score = 100;
        toast("calib.done","ok"); logEv("calib.done",{});
        var s = $("calibScore"); if(s) s.textContent = "100%";
      }
    }
  });
  on($("btnCalibAuto"),"click", function(){
    var targets = calibTargets(canvasModal.width, canvasModal.height);
    S.calib.pts = targets.map(function(p){ return {x:p[0],y:p[1]}; });
    wizardActive = false; S.calib.score = 100;
    drawCalib(canvasModal, targets.length, false);
    var sc = $("calibScoreModal"); if(sc) sc.textContent = "100%";
    var s = $("calibScore"); if(s) s.textContent = "100%";
    toast("calib.done","ok"); logEv("calib.auto",{});
  });
  on($("btnCalibClose"),"click", function(){ hideModal("modalCalib"); refreshInline(); });
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

  host.appendChild(fieldRow("settings.a11yMotion", S.a11y.motion, function(v){ S.a11y.motion=v; document.body.classList.toggle("reduce-motion", v); }));
  host.appendChild(fieldRow("settings.a11yContrast", S.a11y.contrast, function(v){ S.a11y.contrast=v; document.body.classList.toggle("high-contrast", v); }));
  host.appendChild(fieldRow("settings.a11yCursor", S.a11y.cursor, function(v){ S.a11y.cursor=v; document.body.classList.toggle("large-cursor", v); }));

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
function renderDashboard(){
  var stats = $("dashStats");
  if(stats){
    var totalStrokes = (boardPad?boardPad.strokes.length:0) + (airDrawPad?airDrawPad.strokes.length:0);
    var quizLine = S.quiz.active ? (S.quiz.score+" / "+S.quiz.total) : "—";
    stats.innerHTML = [
      ["nav.draw", totalStrokes],
      ["nav.quiz", quizLine],
      ["history.title", S.log.length]
    ].map(function(row){
      return '<div class="stat"><div class="num">'+esc(String(row[1]))+'</div><div class="lbl">'+esc(t(row[0]))+'</div></div>';
    }).join("");
  }
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
  var badge = $("demoBadge"); if(badge) badge.classList.remove("hidden");
  wireTopbar();
  wireNav();
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
  wirePwa();
  startStatusCycle();
  setMode("safe");
  switchView("smart-surface");
  requestAnimationFrame(tick);
  if(window.i18n && window.i18n.onChange){
    window.i18n.onChange(function(){
      labelInstallBtn();
      if(S.view==="settings") renderSettings();
      if(S.view==="privacy") renderStatic("privacyBody","privacy.body");
      if(S.view==="security") renderStatic("secBody","security.body");
      if(S.view==="dashboard") renderDashboard();
      if(S.view==="air-lab") renderLabControls();
      if(S.view==="air-quiz") renderQuiz();
      if(S.view==="air-presentation") renderPresentation();
    });
  }
  toast("welcome","ok");
  logEv("boot", {});
}

if(document.readyState !== "loading") boot();
else document.addEventListener("DOMContentLoaded", boot);

})();
