/* ==================================================================
   EDU-AIR SMART SURFACE — internationalization engine + dictionaries
   Import BEFORE app.js. Exposes window.i18n
   ================================================================== */
(function(){
"use strict";

var SUPPORTED = ["en","fr","ar","nl"];

var DICT = {
  en:{
    "app.name":"EDU-AIR SMART SURFACE",
    "nav.dashboard":"Dashboard","nav.surface":"Smart surface","nav.pointer":"Air pointer",
    "nav.draw":"Air draw","nav.threed":"Air 3D","nav.vision":"Air vision","nav.lab":"Air lab",
    "nav.quiz":"Air quiz","nav.presentation":"Air presentation","nav.teacher":"AI teacher",
    "nav.calibration":"Calibration","nav.history":"History","nav.settings":"Settings",
    "nav.privacy":"Privacy","nav.security":"Security",
    "status.camera":"Camera","status.hand":"Hand","status.voice":"Voice","status.ai":"AI",
    "status.calibration":"Calibration","status.surface":"Surface",
    "mode.safe":"Safe mode","mode.guarded":"Guarded","mode.unsafe":"Unsafe",
    "demo.badge":"Demo","demo.live":"Live",
    "dash.title":"Dashboard",
    "lede":"Zero-contact AI teaching: calibrate once, then point, draw, quiz and teach in mid-air.",
    "a11y.skip":"Skip to content",
    "smart.save":"Save","smart.clear":"Clear",
    "pointer.enable":"Enable air pointer","pointer.click":"Simulate click",
    "draw.enable":"Enable air draw",
    "threed.fonts":"3D","threed.home":"Reset view","threed.auto":"Auto-rotate",
    "vision.start":"Start air vision",
    "lab.begin":"Start lab","lab.reset":"Reset",
    "quiz.new":"New quiz","quiz.addq":"+ Add question","quiz.import":"Import CSV/JSON","quiz.importOk":"Questions imported — check them, then save.","quiz.importBad":"Couldn't read any question from that file.","quiz.save":"Save quiz","quiz.close":"Close",
    "presentation.prev":"Prev","presentation.next":"Next",
    "teacher.placeholder":"Ask your AI teacher…",
    "calibration.begin":"Begin","calibration.reset":"Reset","calibration.auto":"Auto",
    "calib.sweetSpot":"Sweet spot — keep your hand inside while pointing",
    "history.clear":"Clear history",
    "danger.cancel":"Cancel","danger.confirm":"Confirm","danger.emergency":"Emergency stop",

    "pointer.title":"Air pointer","pointer.lede":"Move your index finger through the air to control the cursor without ever touching the screen. In this browser demo, your mouse stands in for the tracked fingertip.",
    "draw.title":"Air draw","draw.lede":"Draw in the air — your hand is the pen. Smart ink recognizes circles, lines, triangles and squares automatically.","draw.aim":"Aim",
    "threed.title":"Air 3D","threed.lede":"Explore 3D models with your hand — rotate, zoom and dissect shapes in mid-air. Drag with the mouse to rotate in this demo.","threed.explode":"Explode","threed.wire":"Wireframe",
    "model.cube":"Cube","model.pyramid":"Pyramid","model.sphere":"Sphere","model.torus":"Torus","model.dna":"DNA","model.heart":"Heart","model.brain":"Brain","model.molecule":"Molecule",
    "model.cube.info":"A regular hexahedron: 6 equal square faces, 12 edges, 8 vertices.","model.pyramid.info":"A square-base pyramid: 4 triangular faces meeting at an apex over a square base.","model.sphere.info":"A perfectly round solid: every point on its surface is the same distance from the center.","model.torus.info":"A ring (donut) shape swept from a circle around an axis outside it.","model.dna.info":"The double helix that carries genetic instructions in nearly every living cell.","model.heart.info":"A four-chambered muscular pump that circulates blood through the body.","model.brain.info":"The command center of the nervous system, with roughly 86 billion neurons.","model.molecule.info":"A ball-and-stick view of atoms held together by chemical bonds.",
    "model.volume":"Volume","model.surface":"Surface area","model.edges":"Edges","model.vertices":"Vertices","model.faces":"Faces",
    "vision.title":"Air vision","vision.lede":"Simulated preview of EDU-AIR's on-device computer vision — the desktop app runs this live from your webcam, fully local, nothing uploaded.",
    "lab.title":"Air lab","lab.lede":"A small real-time physics lab, no risk, no hardware — adjust the sliders and watch the simulation respond live.",
    "lab.circuit":"Circuit","lab.beaker":"Chemistry","lab.pendulum":"Pendulum","lab.wave":"Waves","lab.optics":"Optics","lab.planet":"Planets",
    "lab.voltage":"Voltage","lab.resistance":"Resistance","lab.current":"Current","lab.ph":"pH level","lab.length":"Length","lab.gravity":"Gravity","lab.period":"Period","lab.frequency":"Frequency","lab.amplitude":"Amplitude","lab.objectDist":"Object distance","lab.focal":"Focal length","lab.imageDist":"Image distance","lab.speed":"Orbital speed",
    "quiz.title":"Air quiz","quiz.lede":"Interactive quizzes controlled with hand gestures — answer by pinching in mid-air. Click an option in this demo.","quiz.editTitle":"Build a quiz",
    "presentation.title":"Air presentation","presentation.lede":"Deliver presentations without touching a thing — swipe in air to change slides.",
    "teacher.title":"AI teacher","teacher.lede":"Your AI co-teacher. This demo chat shows example interactions — the desktop app connects it to your live lesson.","teacher.send":"Ask","teacher.placeholder":"Ask your AI teacher anything…","teacher.typing":"Thinking…","teacher.offline":"Live AI unreachable — demo mode reply shown instead.","teacher.live":"LIVE AI","teacher.demo":"DEMO",
    "calibration.title":"Calibration","calibration.lede":"Map your camera to the projection surface for pixel-perfect pointing.","calibration.start":"Start calibration","calibration.close":"Close",
    "calib.guidePlace":"Show your hand, then touch each highlighted corner with your index finger","calib.guideTap":"Hold your index finger on corner {n}","calib.guideHand":"No hand detected — show your hand","calib.guideOrClick":"(or click the corner)","calib.doneText":"Calibration complete — see your score above","calib.doneText2":"Calibration complete — score {s}, average error {e}","calib.notDone":"Not calibrated — pointer uses direct mapping","calib.scored":"Score {s}","calib.noCam":"Enable the camera to calibrate — the calibration catches your fingertip live.","calib.fail":"Calibration failed — the points didn't fit a mapping. Show your hand and try again, or use Auto.","calib.autoNote":"Automatic framing active — no live calibration. Pointer maps directly from camera; for pixel-perfect aiming run the real calibration.","calib.auto":"Automatic framing selected","calib.point":"Point",
    "history.title":"History","history.lede":"Every stroke, every quiz, every session — your local audit trail.",
    "settings.title":"Settings","settings.lang":"Language","settings.sensitivity":"Pointer sensitivity","settings.stability":"Pointer stability (anti-tremble)","settings.confidence":"Gesture detection confidence","settings.primHand":"Primary hand","settings.a11y":"Accessibility","settings.a11yMotion":"Reduce motion","settings.a11yContrast":"High contrast","settings.a11yCursor":"Large cursor","settings.install":"Install app","settings.reset":"Reset all local data","settings.aiMode":"AI teacher mode","settings.aiEndpoint":"Live AI endpoint","settings.aiModeHint":"DEMO: scripted local replies, works offline. LIVE: posts to a server endpoint (api/chat) that calls an LLM — configure EDU_AIR_LLM_KEY on the host.",
    "ai.modeScripted":"Demo (scripted)","ai.modeLive":"Live (real LLM)",
    "privacy.title":"Privacy","privacy.body":"EDU-AIR processes camera and microphone data locally by default — nothing is uploaded or recorded without your say. This web app requests your camera or microphone only when you switch them on, and all processing happens in your browser. Clear all locally stored demo data anytime from Settings.",
    "security.title":"Security","security.body":"Every action passes through a safety gate before it runs: safe actions execute immediately, risky ones ask for confirmation, and unknown or unregistered actions are always blocked. An emergency stop is always one click away.",
    "security.totalActions":"Actions this session","security.confirmed":"Risky actions confirmed","security.emergency":"Emergency stops","security.topCats":"Most active modules",
    "privacy.events":"Logged events","privacy.quizzes":"Quizzes saved","privacy.results":"Quiz results saved","privacy.sessions":"Class sessions saved","privacy.storage":"Local storage used",
    "danger.title":"Safety gate","danger.body":"This action could disrupt an active session. Your safety engine is asking you to confirm.",
    "demo.title":"How to interact","demo.body":"Two ways to interact: <b>real gestures</b> using your webcam (processed locally in your browser, nothing is uploaded) or the <b>synthetic hand engine</b> with keyboard/mouse.","demo.cam":"Use my camera (real gestures)","demo.kb":"Enable keyboard/mouse as hand input","demo.go":"Simulate (keyboard/mouse)",
    "cam.on":"Camera on — move your index finger to point, pinch to click","cam.off":"Camera off","cam.denied":"Camera access denied — allow camera in your browser, or use keyboard/mouse.","cam.unavailable":"No camera found — use keyboard/mouse instead.","cam.error":"Camera error",
    "voice.on":"Voice on — say: next, previous, pointer, draw, clear, quiz, stop…","voice.off":"Voice off","voice.unsupported":"Voice not supported by this browser — use Chrome or Edge.",
    "gesture.pinch":"Pinch","gesture.swipeL":"Swipe left","gesture.swipeR":"Swipe right","gesture.palm":"Palm",
    "cam.hand":"Hand detected","cam.loading":"Loading AI model…","cam.light":"Low light — add lighting","cam.show":"Show your hand in frame","cam.errModel":"Couldn't load the AI model — check your connection","cam.retry":"RETRY",
    "settings.sound":"Sound feedback","settings.lightTheme":"Light mode",
    "dash.strokes":"Strokes","dash.quiz":"Quiz accuracy","dash.topModule":"Top module","dash.hardest":"Hardest question",
    "dash.best":"Best result","dash.perfect":"Perfect runs","dash.exportCSV":"Export quiz results (CSV)","dash.noData":"No quiz results yet","dash.exported":"CSV exported",
    "gam.first":"First quiz","gam.perfect":"Perfect score!","gam.marathon":"10 quizzes done","gam.sharp":"+75% accuracy","conf.reload":"Detection model reloaded","prim.auto":"Auto","prim.left":"Left","prim.right":"Right",
    "tut.title":"Learn the gestures","tut.skip":"Skip","tut.next":"Next","tut.finish":"Start","tut.step1":"Place your hand about 50 cm from the camera and wave","tut.step2":"Pinch thumb and index together to click","tut.step3":"Swipe left or right to change slides",
    "smart.shapes":"Shapes","smart.haptics":"Haptics",
    "welcome":"EDU-AIR ready — wave to interact","air.tap":"Tap","draw.on":"Ink hot","draw.cleared":"Canvas cleared","draw.undo":"Undo stroke","draw.nothing":"Nothing to undo",
    "shape.circle":"Circle","shape.line":"Line","shape.triangle":"Triangle","shape.square":"Square","shape.pentagon":"Pentagon",
    "pointer.on":"Pointer on","pointer.off":"Pointer off","offline.on":"Offline mode on — cached","offline.off":"Online","pwa.install":"Use your browser menu → Install app",
    "draw.off":"Air draw off","vision.stop":"Air vision stopped",
    "draw.traceHit":"Nice trace!","draw.traceMiss":"Not quite — try again","draw.traceLede":"Trace the guide shape — a matching stroke scores a point.",
    "pointer.test":"Precision test","pointer.precision":"Precision","pointer.reaction":"Reaction time","pointer.testDone":"Test complete",
    "history.all":"All","history.empty":"No events yet.","history.cleared":"History cleared","history.search":"Search…","history.export":"Export CSV",
    "quiz.correct":"Correct!","quiz.wrong":"Wrong","quiz.finished":"Quiz finished","quiz.question":"Question","quiz.startFirst":"Create a quiz first","quiz.created":"Quiz created",
    "calib.point":"Point","calib.done":"Calibration complete","calib.score":"Score"
  },
  fr:{
    "app.name":"EDU-AIR SMART SURFACE",
    "nav.dashboard":"Tableau de bord","nav.surface":"Surface intelligente","nav.pointer":"Pointeur air",
    "nav.draw":"Dessin air","nav.threed":"Air 3D","nav.vision":"Vision air","nav.lab":"Labo air",
    "nav.quiz":"Quiz air","nav.presentation":"Présentation air","nav.teacher":"Prof IA",
    "nav.calibration":"Calibrage","nav.history":"Historique","nav.settings":"Réglages",
    "nav.privacy":"Confidentialité","nav.security":"Sécurité",
    "status.camera":"Caméra","status.hand":"Main","status.voice":"Voix","status.ai":"IA",
    "status.calibration":"Calibrage","status.surface":"Surface",
    "mode.safe":"Mode sûr","mode.guarded":"Surveillé","mode.unsafe":"Non sûr",
    "demo.badge":"Démo","demo.live":"En direct",
    "dash.title":"Tableau de bord",
    "lede":"Enseignement sans contact : calibrez une fois, puis pointez, dessinez, interrogez et enseignez en l'air.",
    "a11y.skip":"Aller au contenu",
    "smart.save":"Enregistrer","smart.clear":"Effacer",
    "pointer.enable":"Activer le pointeur air","pointer.click":"Cliquer",
    "draw.enable":"Activer le dessin air",
    "threed.home":"Réinitialiser la vue","threed.auto":"Rotation auto",
    "vision.start":"Lancer la vision air",
    "lab.begin":"Démarrer le labo","lab.reset":"Réinitialiser",
    "quiz.new":"Nouveau quiz","quiz.addq":"+ Ajouter une question","quiz.import":"Importer CSV/JSON","quiz.importOk":"Questions importées — vérifiez-les puis enregistrez.","quiz.importBad":"Aucune question lisible dans ce fichier.","quiz.save":"Enregistrer le quiz","quiz.close":"Fermer",
    "presentation.prev":"Préc","presentation.next":"Suiv",
    "teacher.placeholder":"Posez une question à votre prof IA…",
    "calibration.begin":"Commencer","calibration.reset":"Réinitialiser","calibration.auto":"Auto",
    "history.clear":"Effacer l'historique",
    "danger.cancel":"Annuler","danger.confirm":"Confirmer","danger.emergency":"Arrêt d'urgence",

    "pointer.title":"Pointeur air","pointer.lede":"Déplacez votre index dans l'air pour contrôler le curseur sans jamais toucher l'écran. Dans cette démo navigateur, votre souris remplace le bout du doigt suivi par caméra.",
    "draw.title":"Dessin air","draw.lede":"Dessinez dans l'air — votre main devient le stylo. L'encre intelligente reconnaît automatiquement cercles, lignes, triangles et carrés.","draw.aim":"Visée",
    "threed.title":"Air 3D","threed.lede":"Explorez des modèles 3D avec la main — pivotez, zoomez et disséquez des formes en l'air. Faites glisser la souris pour pivoter dans cette démo.","threed.explode":"Éclater","threed.wire":"Filaire",
    "model.cube":"Cube","model.pyramid":"Pyramide","model.sphere":"Sphère","model.torus":"Tore","model.dna":"ADN","model.heart":"Cœur","model.brain":"Cerveau","model.molecule":"Molécule",
    "model.cube.info":"Un hexaèdre régulier : 6 faces carrées identiques, 12 arêtes, 8 sommets.","model.pyramid.info":"Une pyramide à base carrée : 4 faces triangulaires se rejoignant en un sommet.","model.sphere.info":"Un solide parfaitement rond : chaque point de sa surface est à égale distance du centre.","model.torus.info":"Une forme en anneau engendrée par un cercle tournant autour d'un axe extérieur.","model.dna.info":"La double hélice qui porte les instructions génétiques dans presque toutes les cellules vivantes.","model.heart.info":"Une pompe musculaire à quatre cavités qui fait circuler le sang dans le corps.","model.brain.info":"Le centre de commande du système nerveux, avec environ 86 milliards de neurones.","model.molecule.info":"Une vue boules-et-bâtonnets d'atomes reliés par des liaisons chimiques.",
    "model.volume":"Volume","model.surface":"Surface","model.edges":"Arêtes","model.vertices":"Sommets","model.faces":"Faces",
    "vision.title":"Vision air","vision.lede":"Aperçu simulé de la vision par ordinateur embarquée d'EDU-AIR — l'application de bureau l'exécute en direct depuis votre webcam, entièrement en local, sans envoi de données.",
    "lab.title":"Labo air","lab.lede":"Un petit labo de physique en temps réel, sans risque, sans matériel — ajustez les curseurs et observez la simulation réagir en direct.",
    "lab.circuit":"Circuit","lab.beaker":"Chimie","lab.pendulum":"Pendule","lab.wave":"Ondes","lab.optics":"Optique","lab.planet":"Planètes",
    "lab.voltage":"Tension","lab.resistance":"Résistance","lab.current":"Courant","lab.ph":"Niveau de pH","lab.length":"Longueur","lab.gravity":"Gravité","lab.period":"Période","lab.frequency":"Fréquence","lab.amplitude":"Amplitude","lab.objectDist":"Distance objet","lab.focal":"Distance focale","lab.imageDist":"Distance image","lab.speed":"Vitesse orbitale",
    "quiz.title":"Quiz air","quiz.lede":"Quiz interactifs pilotés par gestes de la main — répondez en pinçant les doigts en l'air. Cliquez une option dans cette démo.","quiz.editTitle":"Créer un quiz",
    "presentation.title":"Présentation air","presentation.lede":"Présentez sans rien toucher — balayez l'air pour changer de diapositive.",
    "teacher.title":"Prof IA","teacher.lede":"Votre co-enseignant IA. Cette discussion de démo montre des exemples d'interaction — l'application de bureau le connecte à votre cours en direct.","teacher.send":"Envoyer","teacher.placeholder":"Posez une question à votre prof IA…","teacher.typing":"Réflexion…","teacher.offline":"IA en direct injoignable — réponse de démonstration affichée à la place.","teacher.live":"IA EN DIRECT","teacher.demo":"DÉMO",
    "calibration.title":"Calibrage","calibration.lede":"Alignez votre caméra sur la surface de projection pour un pointage précis.","calibration.start":"Démarrer le calibrage","calibration.close":"Fermer",
    "calib.guidePlace":"Montrez votre main, puis touchez chaque coin en surbrillance avec votre index","calib.guideTap":"Maintenez votre index sur le coin {n}","calib.guideHand":"Aucune main détectée — montrez votre main","calib.guideOrClick":"(ou cliquez sur le coin)","calib.doneText":"Calibrage terminé — voir votre score ci-dessus","calib.doneText2":"Calibrage terminé — score {s}, erreur moyenne {e}","calib.notDone":"Non calibré — le pointeur utilise le mappage direct","calib.scored":"Score {s}","calib.noCam":"Activez la caméra pour calibrer — le calibrage capture votre index en direct.","calib.fail":"Calibrage impossible — les points ne correspondent pas à un mappage. Montrez votre main et réessayez, ou utilisez Auto.","calib.autoNote":"Cadrage automatique actif — sans calibration en direct. Le pointeur se mappe directement depuis la caméra ; pour un pointage au pixel près, lancez la vraie calibration.","calib.auto":"Cadrage automatique sélectionné","calib.sweetSpot":"Zone idéale — gardez la main dedans pendant le pointage",
    "history.title":"Historique","history.lede":"Chaque trait, chaque quiz, chaque session — votre journal local.",
    "settings.title":"Réglages","settings.lang":"Langue","settings.sensitivity":"Sensibilité du pointeur","settings.stability":"Stabilité du pointeur (anti-tremblement)","settings.confidence":"Seuil de confiance gestes","settings.primHand":"Main principale","settings.a11y":"Accessibilité","settings.a11yMotion":"Réduire les animations","settings.a11yContrast":"Contraste élevé","settings.a11yCursor":"Grand curseur","settings.install":"Installer l'application","settings.reset":"Réinitialiser les données locales","settings.aiMode":"Mode du prof IA","settings.aiEndpoint":"Point de terminaison IA en direct","settings.aiModeHint":"DÉMO : réponses scriptées locales, fonctionne hors-ligne. EN DIRECT : envoie à un point de terminaison serveur (api/chat) qui appelle un LLM — configurez EDU_AIR_LLM_KEY sur l'hôte.",
    "ai.modeScripted":"Démo (scriptée)","ai.modeLive":"En direct (vrai LLM)",
    "privacy.title":"Confidentialité","privacy.body":"Par défaut, EDU-AIR traite la caméra et le micro en local — rien n'est envoyé ni enregistré sans votre accord. Cette application web ne demande votre caméra ou votre micro que lorsque vous les activez, et tout le traitement se fait dans votre navigateur. Effacez à tout moment les données locales de démo depuis Réglages.",
    "security.title":"Sécurité","security.body":"Chaque action passe par une porte de sécurité avant de s'exécuter : les actions sûres s'exécutent immédiatement, les actions à risque demandent une confirmation, et les actions inconnues ou non enregistrées sont toujours bloquées. Un arrêt d'urgence reste à un clic.",
    "security.totalActions":"Actions cette session","security.confirmed":"Actions à risque confirmées","security.emergency":"Arrêts d'urgence","security.topCats":"Modules les plus utilisés",
    "privacy.events":"Événements journalisés","privacy.quizzes":"Quiz enregistrés","privacy.results":"Résultats de quiz enregistrés","privacy.sessions":"Séances de classe enregistrées","privacy.storage":"Stockage local utilisé",
    "danger.title":"Porte de sécurité","danger.body":"Cette action pourrait perturber une session active. Votre moteur de sécurité vous demande de confirmer.",
    "demo.title":"Comment interagir","demo.body":"Deux façons d'interagir : <b>les vrais gestes</b> avec votre webcam (traités localement dans votre navigateur, rien n'est envoyé) ou le <b>moteur de main synthétique</b> avec clavier/souris.","demo.cam":"Utiliser ma caméra (vrais gestes)","demo.kb":"Activer clavier/souris comme entrée main","demo.go":"Simuler (clavier/souris)",
    "cam.on":"Caméra activée — bougez l'index pour pointer, pincez les doigts pour cliquer","cam.off":"Caméra désactivée","cam.denied":"Accès caméra refusé — autorisez la caméra dans le navigateur, ou utilisez clavier/souris.","cam.unavailable":"Aucune caméra trouvée — utilisez plutôt clavier/souris.","cam.error":"Erreur caméra",
    "voice.on":"Voix activée — dites : suivant, précédent, pointeur, dessin, effacer, quiz, stop…","voice.off":"Voix désactivée","voice.unsupported":"Commandes vocales non prises en charge par ce navigateur — utilisez Chrome ou Edge.",
    "gesture.pinch":"Pincer","gesture.swipeL":"Balayer à gauche","gesture.swipeR":"Balayer à droite","gesture.palm":"Paume",
    "cam.hand":"Main détectée","cam.loading":"Chargement du modèle IA…","cam.light":"Éclairage insuffisant — éclairez la scène","cam.show":"Montrez votre main devant la caméra","cam.errModel":"Impossible de charger le modèle IA — vérifiez la connexion","cam.retry":"RÉESSAYER",
    "settings.sound":"Retour sonore","settings.lightTheme":"Mode clair",
    "dash.strokes":"Traces","dash.quiz":"Réussite quiz","dash.topModule":"Module le plus utilisé","dash.hardest":"Question la plus ratée",
    "dash.best":"Meilleur résultat","dash.perfect":"Sans faute","dash.exportCSV":"Exporter les résultats (CSV)","dash.noData":"Pas encore de résultats de quiz","dash.exported":"CSV exporté",
    "gam.first":"Premier quiz","gam.perfect":"Score parfait !","gam.marathon":"10 quiz terminés","gam.sharp":"+75 % de réussite","conf.reload":"Modèle de détection rechargé","prim.auto":"Auto","prim.left":"Gauche","prim.right":"Droite",
    "tut.title":"Apprenez les gestes","tut.skip":"Passer","tut.next":"Suivant","tut.finish":"C'est parti","tut.step1":"Placez la main à ~50 cm de la caméra et faites un signe","tut.step2":"Pincez pouce et index pour cliquer","tut.step3":"Balayez la main à gauche ou à droite pour changer de page",
    "smart.shapes":"Formes","smart.haptics":"Retour haptique",
    "welcome":"EDU-AIR prêt — faites un signe pour interagir","air.tap":"Tap","draw.on":"Encre active","draw.cleared":"Canevas effacé","draw.undo":"Annuler le trait","draw.nothing":"Rien à annuler",
    "shape.circle":"Cercle","shape.line":"Ligne","shape.triangle":"Triangle","shape.square":"Carré","shape.pentagon":"Pentagone",
    "pointer.on":"Pointeur activé","pointer.off":"Pointeur désactivé","offline.on":"Mode hors-ligne activé — en cache","offline.off":"En ligne","pwa.install":"Utilisez le menu du navigateur → Installer l'application",
    "draw.off":"Dessin air désactivé","vision.stop":"Vision air arrêtée",
    "draw.traceHit":"Bien tracé !","draw.traceMiss":"Pas tout à fait — réessaie","draw.traceLede":"Trace la forme guide — un trait correspondant marque un point.",
    "pointer.test":"Test de précision","pointer.precision":"Précision","pointer.reaction":"Temps de réaction","pointer.testDone":"Test terminé",
    "history.all":"Tout","history.empty":"Aucun événement pour l'instant.","history.cleared":"Historique effacé","history.search":"Rechercher…","history.export":"Exporter en CSV",
    "quiz.correct":"Correct !","quiz.wrong":"Faux","quiz.finished":"Quiz terminé","quiz.question":"Question","quiz.startFirst":"Créez d'abord un quiz","quiz.created":"Quiz créé",
    "calib.point":"Point","calib.done":"Calibrage terminé","calib.score":"Score"
  },
  ar:{
    "app.name":"سطح التعليم الذكي",
    "nav.dashboard":"لوحة التحكم","nav.surface":"السطح الذكي","nav.pointer":"مؤشر الهواء",
    "nav.draw":"رسم الهواء","nav.threed":"هواء ثلاثي الأبعاد","nav.vision":"رؤية الهواء","nav.lab":"مختبر الهواء",
    "nav.quiz":"اختبار الهواء","nav.presentation":"عرض الهواء","nav.teacher":"معلّم الذكاء",
    "nav.calibration":"المعايرة","nav.history":"السجل","nav.settings":"الإعدادات",
    "nav.privacy":"الخصوصية","nav.security":"الأمان",
    "status.camera":"الكاميرا","status.hand":"اليد","status.voice":"الصوت","status.ai":"الذكاء",
    "status.calibration":"المعايرة","status.surface":"السطح",
    "mode.safe":"وضع آمن","mode.guarded":"مُحرس","mode.unsafe":"غير آمن",
    "demo.badge":"تجريبي","demo.live":"مباشر",
    "dash.title":"لوحة التحكم",
    "lede":"تدريس بدون لمس: عايِر مرة واحدة ثم أشر واستم واختبر وعلّم في الهواء.",
    "a11y.skip":"تخطَّ إلى المحتوى",
    "smart.save":"حفظ","smart.clear":"مسح",
    "pointer.enable":"تفعيل مؤشر الهواء","pointer.click":"نقرة",
    "draw.enable":"تفعيل رسم الهواء",
    "threed.home":"إعادة ضبط العرض","threed.auto":"دوران تلقائي",
    "vision.start":"بدء رؤية الهواء",
    "lab.begin":"بدء المختبر","lab.reset":"إعادة ضبط",
    "quiz.new":"اختبار جديد","quiz.addq":"+ إضافة سؤال","quiz.import":"استيراد CSV/JSON","quiz.importOk":"تم استيراد الأسئلة — راجعها ثم احفظ.","quiz.importBad":"لا توجد أسئلة مقروءة في هذا الملف.","quiz.save":"حفظ الاختبار","quiz.close":"إغلاق",
    "presentation.prev":"السابق","presentation.next":"التالي",
    "teacher.placeholder":"اسأل معلّمك الذكي…",
    "calibration.begin":"ابدأ","calibration.reset":"إعادة ضبط","calibration.auto":"تلقائي",
    "history.clear":"مسح السجل",
    "danger.cancel":"إلغاء","danger.confirm":"تأكيد","danger.emergency":"إيقاف طارئ",

    "pointer.title":"مؤشر الهواء","pointer.lede":"حرّك سبابتك في الهواء للتحكم بالمؤشر دون لمس الشاشة أبدًا. في هذا العرض التجريبي بالمتصفح، تحل الفأرة محل طرف الإصبع المتتبَّع بالكاميرا.",
    "draw.title":"رسم الهواء","draw.lede":"ارسم في الهواء — يدك هي القلم. يتعرّف الحبر الذكي تلقائيًا على الدوائر والخطوط والمثلثات والمربعات.","draw.aim":"التصويب",
    "threed.title":"هواء ثلاثي الأبعاد","threed.lede":"استكشف نماذج ثلاثية الأبعاد بيدك — أدر وكبّر وفكك الأشكال في الهواء. اسحب بالفأرة للتدوير في هذا العرض.","threed.explode":"تفكيك","threed.wire":"إطار سلكي",
    "model.cube":"مكعب","model.pyramid":"هرم","model.sphere":"كرة","model.torus":"حلقة","model.dna":"الحمض النووي","model.heart":"القلب","model.brain":"الدماغ","model.molecule":"جزيء",
    "model.cube.info":"سداسي وجوه منتظم: 6 أوجه مربعة متساوية، 12 حرفًا، 8 رؤوس.","model.pyramid.info":"هرم ذو قاعدة مربعة: 4 أوجه مثلثة تلتقي عند قمة واحدة.","model.sphere.info":"مجسم مستدير تمامًا: كل نقطة على سطحه تبعد المسافة نفسها عن المركز.","model.torus.info":"شكل حلقي ناتج عن دوران دائرة حول محور خارجي.","model.dna.info":"اللولب المزدوج الذي يحمل التعليمات الوراثية في كل خلية حية تقريبًا.","model.heart.info":"مضخة عضلية ذات أربع حجرات تُجري الدم في الجسم.","model.brain.info":"مركز قيادة الجهاز العصبي، ويضم نحو 86 مليار خلية عصبية.","model.molecule.info":"عرض بالكرات والقضبان لذرات مترابطة بروابط كيميائية.",
    "model.volume":"الحجم","model.surface":"المساحة السطحية","model.edges":"الحواف","model.vertices":"الرؤوس","model.faces":"الأوجه",
    "vision.title":"رؤية الهواء","vision.lede":"معاينة محاكاة لرؤية الحاسوب المدمجة في EDU-AIR — يشغّلها التطبيق المكتبي مباشرة من كاميرتك، محليًا بالكامل دون رفع أي بيانات.",
    "lab.title":"مختبر الهواء","lab.lede":"مختبر فيزياء صغير في الوقت الحقيقي، بلا خطر وبلا عتاد — حرّك أشرطة التمرير وشاهد المحاكاة تستجيب مباشرة.",
    "lab.circuit":"دائرة","lab.beaker":"كيمياء","lab.pendulum":"بندول","lab.wave":"موجات","lab.optics":"بصريات","lab.planet":"كواكب",
    "lab.voltage":"الجهد","lab.resistance":"المقاومة","lab.current":"التيار","lab.ph":"مستوى الحموضة","lab.length":"الطول","lab.gravity":"الجاذبية","lab.period":"الدور","lab.frequency":"التردد","lab.amplitude":"السعة","lab.objectDist":"مسافة الجسم","lab.focal":"البعد البؤري","lab.imageDist":"مسافة الصورة","lab.speed":"السرعة المدارية",
    "quiz.title":"اختبار الهواء","quiz.lede":"اختبارات تفاعلية تُدار بإيماءات اليد — أجب بقرص الأصابع في الهواء. انقر خيارًا في هذا العرض.","quiz.editTitle":"إنشاء اختبار",
    "presentation.title":"عرض الهواء","presentation.lede":"قدّم عرضك دون لمس أي شيء — امسح في الهواء لتغيير الشرائح.",
    "teacher.title":"معلّم الذكاء","teacher.lede":"معلّمك المساعد بالذكاء الاصطناعي. تعرض هذه المحادثة التجريبية أمثلة تفاعل — يربطه التطبيق المكتبي بدرسك المباشر.","teacher.send":"إرسال","teacher.placeholder":"اسأل معلّمك الذكي…","teacher.typing":"جارٍ التفكير…","teacher.offline":"الذكاء المباشر غير متاح — عُرض رد تجريبي بدلًا من ذلك.","teacher.live":"ذكاء مباشر","teacher.demo":"تجريبي",
    "calibration.title":"المعايرة","calibration.lede":"طابِق كاميرتك مع سطح العرض لتأشير دقيق.","calibration.start":"بدء المعايرة","calibration.close":"إغلاق",
    "calib.guidePlace":"أظهر يدك، ثم المس كل زاوية مضيئة بسبابتك","calib.guideTap":"أبقِ سبابتك على الزاوية {n}","calib.guideHand":"لم يتم رصد يد — أظهر يدك","calib.guideOrClick":"(أو انقر على الزاوية)","calib.doneText":"اكتملت المعايرة — راجع النتيجة أعلاه","calib.doneText2":"اكتملت المعايرة — النتيجة {s}، متوسط الخطأ {e}","calib.notDone":"غير معاير — المؤشر يستخدم التطابق المباشر","calib.scored":"النتيجة {s}","calib.noCam":"فعِّل الكاميرا للمعايرة — تلتقط المعايرة سبابتك مباشرةً.","calib.fail":"فشلت المعايرة — النقاط لا تناسب تطابقًا. أظهر يدك وأعد المحاولة، أو استخدم تلقائي.","calib.autoNote":"التهيئة التلقائية نشطة — بلا معايرة مباشرة. يترابط المؤشر مباشرةً من الكاميرا؛ للحصول على تأشير دقيق نفّذ المعايرة الحقيقية.","calib.auto":"تم اختيار التهيئة التلقائية","calib.sweetSpot":"المنطقة المثالية — أبقِ يدك داخلها أثناء التأشير",
    "history.title":"السجل","history.lede":"كل خط، كل اختبار، كل جلسة — سجلّك المحلي.",
    "settings.title":"الإعدادات","settings.lang":"اللغة","settings.sensitivity":"حساسية المؤشر","settings.stability":"ثبات المؤشر (مضاد للاهتزاز)","settings.confidence":"عتبة الثقة في الإيماءات","settings.primHand":"اليد الرئيسية","settings.a11y":"إمكانية الوصول","settings.a11yMotion":"تقليل الحركة","settings.a11yContrast":"تباين عالٍ","settings.a11yCursor":"مؤشر كبير","settings.install":"تثبيت التطبيق","settings.reset":"إعادة ضبط البيانات المحلية","settings.aiMode":"وضع المعلّم الذكي","settings.aiEndpoint":"نقطة الوصل للذكاء المباشر","settings.aiModeHint":"تجريبي: ردود محلية مكتوبة، يعمل دون اتصال. مباشر: يرسل إلى نقطة وصل خادم (api/chat) تستدعي نموذج لغوي — اضبط EDU_AIR_LLM_KEY على الخادم.",
    "ai.modeScripted":"تجريبي (مكتوب)","ai.modeLive":"مباشر (نموذج حقيقي)",
    "privacy.title":"الخصوصية","privacy.body":"تعالج EDU-AIR الكاميرا والميكروفون محليًا افتراضيًا — لا شيء يُرفع أو يُسجَّل دون موافقتك. لا يطلب هذا التطبيق الويب كاميرتك أو ميكروفونك إلا عند تشغيلهما، ويتم كل المعالجة داخل متصفحك. امسح بيانات العرض المحلية في أي وقت من الإعدادات.",
    "security.title":"الأمان","security.body":"تمر كل إجراء عبر بوابة أمان قبل تنفيذه: الإجراءات الآمنة تُنفَّذ فورًا، والإجراءات الخطرة تطلب تأكيدًا، والإجراءات غير المعروفة أو غير المسجّلة تُحظر دائمًا. زر الإيقاف الطارئ متاح دومًا بنقرة واحدة.",
    "security.totalActions":"إجراءات هذه الجلسة","security.confirmed":"إجراءات خطرة مؤكَّدة","security.emergency":"إيقافات طارئة","security.topCats":"الوحدات الأكثر استخدامًا",
    "privacy.events":"أحداث مسجَّلة","privacy.quizzes":"اختبارات محفوظة","privacy.results":"نتائج اختبارات محفوظة","privacy.sessions":"حصص محفوظة","privacy.storage":"التخزين المحلي المستخدَم",
    "danger.title":"بوابة الأمان","danger.body":"قد يعطّل هذا الإجراء جلسة نشطة. يطلب محرك الأمان تأكيدك.",
    "demo.title":"كيف تتفاعل","demo.body":"طريقتان للتفاعل: <b>إيماءات حقيقية</b> بكاميرتك (تُعالج محليًا في متصفحك، لا يُرفع شيء) أو <b>محرك اليد الاصطناعية</b> بالفأرة/لوحة المفاتيح.","demo.cam":"استخدم كاميرتي (إيماءات حقيقية)","demo.kb":"تفعيل لوحة المفاتيح/الفأرة كإدخال يدوي","demo.go":"محاكاة (فأرة/لوحة مفاتيح)",
    "cam.on":"الكاميرا مفعّلة — حرّك سبابتك للتأشير واضغط بأصبعيك للنقر","cam.off":"الكاميرا معطّلة","cam.denied":"تم رفض الوصول إلى الكاميرا — اسمح بالكاميرا في المتصفح أو استخدم الفأرة/لوحة المفاتيح.","cam.unavailable":"لم يتم العثور على كاميرا — استخدم الفأرة/لوحة المفاتيح بدلًا من ذلك.","cam.error":"خطأ في الكاميرا",
    "voice.on":"الصوت مفعّل — قل: التالي، السابق، المؤشر، الرسم، امسح، اختبار، توقف…","voice.off":"الصوت معطّل","voice.unsupported":"الأوامر الصوتية غير مدعومة في هذا المتصفح — استخدم كروم أو إيدج.",
    "gesture.pinch":"قرص","gesture.swipeL":"مسح لليسار","gesture.swipeR":"مسح لليمين","gesture.palm":"راحة",
    "cam.hand":"تم رصد اليد","cam.loading":"جارٍ تحميل نموذج AI…","cam.light":"الإضاءة ضعيفة — حسّن الإضاءة","cam.show":"أظهر يدك أمام الكاميرا","cam.errModel":"تعذّر تحميل نموذج AI — تحقق من الاتصال","cam.retry":"إعادة المحاولة",
    "settings.sound":"التغذية الصوتية","settings.lightTheme":"الوضع الفاتح",
    "dash.strokes":"الخطوط","dash.quiz":"نجاح الاختبار","dash.topModule":"الوحدة الأكثر استخدامًا","dash.hardest":"السؤال الأكثر خطأ",
    "dash.best":"أفضل نتيجة","dash.perfect":"إجابات مثالية","dash.exportCSV":"تصدير النتائج (CSV)","dash.noData":"لا توجد نتائج اختبار بعد","dash.exported":"تم تصدير CSV",
    "gam.first":"أول اختبار","gam.perfect":"درجة مثالية!","gam.marathon":"10 اختبارات مكتملة","gam.sharp":"دقة +75%","conf.reload":"أُعيد تحميل نموذج الكشف","prim.auto":"تلقائي","prim.left":"يسار","prim.right":"يمين",
    "tut.title":"تعلّم الإيماءات","tut.skip":"تخطَّ","tut.next":"التالي","tut.finish":"ابدأ","tut.step1":"ضع يدك على بعد 50 سم تقريبًا ولوّح بها","tut.step2":"اقرص الإبهام والسبابة للنقر","tut.step3":"امسح يسارًا أو يمينًا لتغيير الشريحة",
    "smart.shapes":"الأشكال","smart.haptics":"الاهتزاز اللمسي",
    "welcome":"EDU-AIR جاهز — لوّح للتفاعل","air.tap":"نقرة","draw.on":"الحبر جاهز","draw.cleared":"تم مسح اللوحة","draw.undo":"تراجع عن الخط","draw.nothing":"لا شيء للتراجع عنه",
    "shape.circle":"دائرة","shape.line":"خط","shape.triangle":"مثلث","shape.square":"مربع","shape.pentagon":"خماسي",
    "pointer.on":"المؤشر مفعّل","pointer.off":"المؤشر معطّل","offline.on":"وضع عدم الاتصال مفعّل — مخزَّن مؤقتًا","offline.off":"متصل","pwa.install":"استخدم قائمة المتصفح ← تثبيت التطبيق",
    "draw.off":"رسم الهواء معطّل","vision.stop":"توقفت رؤية الهواء",
    "draw.traceHit":"رسم رائع!","draw.traceMiss":"ليس تمامًا — حاول مجددًا","draw.traceLede":"تتبّع الشكل الدليل — الخط المطابق يسجّل نقطة.",
    "pointer.test":"اختبار الدقة","pointer.precision":"الدقة","pointer.reaction":"زمن الاستجابة","pointer.testDone":"اكتمل الاختبار",
    "history.all":"الكل","history.empty":"لا أحداث بعد.","history.cleared":"تم مسح السجل","history.search":"بحث…","history.export":"تصدير CSV",
    "quiz.correct":"إجابة صحيحة!","quiz.wrong":"إجابة خاطئة","quiz.finished":"انتهى الاختبار","quiz.question":"سؤال","quiz.startFirst":"أنشئ اختبارًا أولًا","quiz.created":"تم إنشاء الاختبار",
    "calib.point":"نقطة","calib.done":"اكتملت المعايرة","calib.score":"النتيجة"
  },
  nl:{
    "app.name":"EDU-AIR SMART SURface",
    "nav.dashboard":"Dashboard","nav.surface":"Smart surface","nav.pointer":"Lucht-aanwijzer",
    "nav.draw":"Lucht-ontwerp","nav.threed":"Lucht-3D","nav.vision":"Lucht-visie","nav.lab":"Lucht-lab",
    "nav.quiz":"Lucht-quiz","nav.presentation":"Lucht-presentatie","nav.teacher":"AI-leraar",
    "nav.calibration":"Kalibratie","nav.history":"Geschiedenis","nav.settings":"Instellingen",
    "nav.privacy":"Privacy","nav.security":"Beveiliging",
    "status.camera":"Camera","status.hand":"Hand","status.voice":"Stem","status.ai":"AI",
    "status.calibration":"Kalibratie","status.surface":"Oppervlak",
    "mode.safe":"Veilige modus","mode.guarded":"Bewaakt","mode.unsafe":"Onveilig",
    "demo.badge":"Demo","demo.live":"Live",
    "dash.title":"Dashboard",
    "lede":"Contactloos lesgeven: kalibreer één keer, wijs, teken, quiz en geef les in de lucht.",
    "a11y.skip":"Ga naar inhoud",
    "smart.save":"Opslaan","smart.clear":"Wissen",
    "pointer.enable":"Lucht-aanwijzer inschakelen","pointer.click":"Simuleer klik",
    "draw.enable":"Lucht-ontwerp inschakelen",
    "threed.home":"Weergave resetten","threed.auto":"Auto-rotatie",
    "vision.start":"Lucht-visie starten",
    "lab.begin":"Lab starten","lab.reset":"Resetten",
    "quiz.new":"Nieuwe quiz","quiz.addq":"+ Vraag toevoegen","quiz.import":"CSV/JSON importeren","quiz.importOk":"Vragen geïmporteerd — controleer ze en sla daarna op.","quiz.importBad":"Geen leesbare vraag in dit bestand.","quiz.save":"Quiz opslaan","quiz.close":"Sluiten",
    "presentation.prev":"Vorige","presentation.next":"Volgende",
    "teacher.placeholder":"Vraag uw AI-leraar…",
    "calibration.begin":"Start","calibration.reset":"Resetten","calibration.auto":"Auto",
    "calib.sweetSpot":"Ideale zone — houd uw hand erbinnen tijdens het aanwijzen",
    "history.clear":"Geschiedenis wissen",
    "danger.cancel":"Annuleren","danger.confirm":"Bevestigen","danger.emergency":"Noodstop",

    "pointer.title":"Lucht-aanwijzer","pointer.lede":"Beweeg uw wijsvinger door de lucht om de cursor te besturen zonder het scherm aan te raken. In deze browserdemo vervangt uw muis de gevolgde vingertop.",
    "draw.title":"Lucht-ontwerp","draw.lede":"Teken in de lucht — uw hand is de pen. Slimme inkt herkent automatisch cirkels, lijnen, driehoeken en vierkanten.","draw.aim":"Richten",
    "threed.title":"Lucht-3D","threed.lede":"Verken 3D-modellen met uw hand — draai, zoom en ontleed vormen in de lucht. Sleep met de muis om te draaien in deze demo.","threed.explode":"Uit elkaar","threed.wire":"Draadframe",
    "model.cube":"Kubus","model.pyramid":"Piramide","model.sphere":"Bol","model.torus":"Torus","model.dna":"DNA","model.heart":"Hart","model.brain":"Brein","model.molecule":"Molecuul",
    "model.cube.info":"Een regelmatig hexaëder: 6 gelijke vierkante vlakken, 12 ribben, 8 hoekpunten.","model.pyramid.info":"Een piramide met vierkant grondvlak: 4 driehoekige zijvlakken die samenkomen in een top.","model.sphere.info":"Een perfect rond lichaam: elk punt op het oppervlak ligt even ver van het middelpunt.","model.torus.info":"Een ringvorm ontstaan door een cirkel te laten draaien om een as erbuiten.","model.dna.info":"De dubbele helix die genetische instructies draagt in bijna elke levende cel.","model.heart.info":"Een gespierde pomp met vier kamers die het bloed door het lichaam laat circuleren.","model.brain.info":"Het commandocentrum van het zenuwstelsel, met ongeveer 86 miljard neuronen.","model.molecule.info":"Een bal-en-staaf-weergave van atomen verbonden door chemische bindingen.",
    "model.volume":"Volume","model.surface":"Oppervlakte","model.edges":"Ribben","model.vertices":"Hoekpunten","model.faces":"Vlakken",
    "vision.title":"Lucht-visie","vision.lede":"Gesimuleerde preview van EDU-AIR's on-device computervisie — de desktopapp voert dit live uit vanaf uw webcam, volledig lokaal, zonder uploads.",
    "lab.title":"Lucht-lab","lab.lede":"Een klein realtime natuurkundelab, zonder risico, zonder hardware — verstel de schuifregelaars en zie de simulatie live reageren.",
    "lab.circuit":"Circuit","lab.beaker":"Scheikunde","lab.pendulum":"Slinger","lab.wave":"Golven","lab.optics":"Optica","lab.planet":"Planeten",
    "lab.voltage":"Spanning","lab.resistance":"Weerstand","lab.current":"Stroom","lab.ph":"pH-niveau","lab.length":"Lengte","lab.gravity":"Zwaartekracht","lab.period":"Periode","lab.frequency":"Frequentie","lab.amplitude":"Amplitude","lab.objectDist":"Objectafstand","lab.focal":"Brandpuntsafstand","lab.imageDist":"Beeldafstand","lab.speed":"Baansnelheid",
    "quiz.title":"Lucht-quiz","quiz.lede":"Interactieve quizzen bestuurd met handgebaren — antwoord door in de lucht te knijpen. Klik een optie in deze demo.","quiz.editTitle":"Quiz maken",
    "presentation.title":"Lucht-presentatie","presentation.lede":"Presenteer zonder iets aan te raken — veeg in de lucht om van dia te wisselen.",
    "teacher.title":"AI-leraar","teacher.lede":"Uw AI-medeleraar. Deze demochat toont voorbeeldinteracties — de desktopapp koppelt hem aan uw live les.","teacher.send":"Verstuur","teacher.placeholder":"Vraag uw AI-leraar iets…","teacher.typing":"Denkt na…","teacher.offline":"Live-AI onbereikbaar — demonstratieantwoord getoond.","teacher.live":"LIVE AI","teacher.demo":"DEMO",
    "calibration.title":"Kalibratie","calibration.lede":"Breng uw camera in lijn met het projectieoppervlak voor nauwkeurig aanwijzen.","calibration.start":"Kalibratie starten","calibration.close":"Sluiten",
    "calib.guidePlace":"Toon uw hand en raak daarna elke heldere hoek aan met uw wijsvinger","calib.guideTap":"Houd uw wijsvinger op hoek {n}","calib.guideHand":"Geen hand gedetecteerd — toon uw hand","calib.guideOrClick":"(of klik op de hoek)","calib.doneText":"Kalibratie voltooid — zie uw score hierboven","calib.doneText2":"Kalibratie voltooid — score {s}, gemiddelde fout {e}","calib.notDone":"Niet gekalibreerd — aanwijzer gebruikt directe mapping","calib.scored":"Score {s}","calib.noCam":"Activeer de camera om te kalibreren — de kalibratie vangt uw vingertop live.","calib.fail":"Kalibratie mislukt — de punten passen niet in een mapping. Toon uw hand en probeer opnieuw, of gebruik Auto.","calib.autoNote":"Automatische kadrering actief — zonder livekalibratie. De aanwijzer mapt direct vanaf de camera; gebruik voor pixelprecieze doelen de echte kalibratie.","calib.auto":"Automatische kadrering geselecteerd","calib.sweetSpot":"Ideale zone — houd uw hand erbinnen tijdens het aanwijzen",
    "history.title":"Geschiedenis","history.lede":"Elke streek, elke quiz, elke sessie — uw lokale logboek.",
    "settings.title":"Instellingen","settings.lang":"Taal","settings.sensitivity":"Aanwijzergevoeligheid","settings.stability":"Aanwijzerstabiliteit (anti-tremor)","settings.confidence":"Gebaardetectie-vertrouwen","settings.primHand":"Primaire hand","settings.a11y":"Toegankelijkheid","settings.a11yMotion":"Beweging beperken","settings.a11yContrast":"Hoog contrast","settings.a11yCursor":"Grote cursor","settings.install":"App installeren","settings.reset":"Lokale gegevens resetten","settings.aiMode":"AI-leraar-modus","settings.aiEndpoint":"Live AI-eindpunt","settings.aiModeHint":"DEMO: geschreven lokale antwoorden, werkt offline. LIVE: stuurt naar een server-eindpunt (api/chat) dat een LLM aanroept — configureer EDU_AIR_LLM_KEY op de host.",
    "ai.modeScripted":"Demo (gescript)","ai.modeLive":"Live (echte LLM)",
    "privacy.title":"Privacy","privacy.body":"EDU-AIR verwerkt camera en microfoon standaard lokaal — niets wordt geüpload of opgenomen zonder uw toestemming. Deze webapp vraagt alleen om uw camera of microfoon wanneer u ze inschakelt, en alle verwerking gebeurt in uw browser. Wis lokale demogegevens op elk moment via Instellingen.",
    "security.title":"Beveiliging","security.body":"Elke actie doorloopt een veiligheidspoort voordat ze wordt uitgevoerd: veilige acties lopen meteen door, risicovolle acties vragen bevestiging, en onbekende of niet-geregistreerde acties worden altijd geblokkeerd. Een noodstop is altijd één klik verwijderd.",
    "security.totalActions":"Acties deze sessie","security.confirmed":"Bevestigde risicovolle acties","security.emergency":"Noodstops","security.topCats":"Meest gebruikte modules",
    "privacy.events":"Gelogde gebeurtenissen","privacy.quizzes":"Opgeslagen quizzen","privacy.results":"Opgeslagen quizresultaten","privacy.sessions":"Opgeslagen lessessies","privacy.storage":"Gebruikte lokale opslag",
    "danger.title":"Veiligheidspoort","danger.body":"Deze actie kan een actieve sessie verstoren. Uw veiligheidsmotor vraagt om bevestiging.",
    "demo.title":"Hoe wilt u interactie","demo.body":"Twee manieren om te interageren: <b>echte gebaren</b> met uw webcam (lokaal verwerkt in uw browser, niets wordt geüpload) of de <b>synthetische handmotor</b> met toetsenbord/muis.","demo.cam":"Gebruik mijn camera (echte gebaren)","demo.kb":"Toetsenbord/muis als handinvoer inschakelen","demo.go":"Simuleren (toetsenbord/muis)",
    "cam.on":"Camera aan — beweeg uw wijsvinger om te wijzen, knijp om te klikken","cam.off":"Camera uit","cam.denied":"Cameratoegang geweigerd — sta camera toe in de browser of gebruik muis/toetsenbord.","cam.unavailable":"Geen camera gevonden — gebruik in plaats daarvan muis/toetsenbord.","cam.error":"Camerafout",
    "voice.on":"Stem aan — zeg: volgende, vorige, aanwijzer, tekenen, wissen, quiz, stop…","voice.off":"Stem uit","voice.unsupported":"Spraakopdrachten niet ondersteund door deze browser — gebruik Chrome of Edge.",
    "gesture.pinch":"Knijpen","gesture.swipeL":"Veeg naar links","gesture.swipeR":"Veeg naar rechts","gesture.palm":"Handpalm",
    "cam.hand":"Hand gedetecteerd","cam.loading":"AI-model laden…","cam.light":"Weinig licht — voeg verlichting toe","cam.show":"Toon uw hand voor de camera","cam.errModel":"Kan het AI-model niet laden — controleer de verbinding","cam.retry":"OPNIEUW",
    "settings.sound":"Geluidsfeedback","settings.lightTheme":"Lichte modus",
    "dash.strokes":"Streken","dash.quiz":"Quizzescore","dash.topModule":"Meest gebruikte module","dash.hardest":"Meest fout beantwoorde vraag",
    "dash.best":"Beste resultaat","dash.perfect":"Zonder fouten","dash.exportCSV":"Quizresultaten exporteren (CSV)","dash.noData":"Nog geen quizresultaten","dash.exported":"CSV geëxporteerd",
    "gam.first":"Eerste quiz","gam.perfect":"Perfecte score!","gam.marathon":"10 quizzes afgerond","gam.sharp":"+75% nauwkeurigheid","conf.reload":"Detectiemodel herladen","prim.auto":"Auto","prim.left":"Links","prim.right":"Rechts",
    "tut.title":"Leer de gebaren","tut.skip":"Overslaan","tut.next":"Volgende","tut.finish":"Start","tut.step1":"Plaats uw hand ~50 cm van de camera en zwaai","tut.step2":"Knijp duim en wijsvinger samen om te klikken","tut.step3":"Veeg links of rechts om van dia te wisselen",
    "smart.shapes":"Vormen","smart.haptics":"Trilfeedback",
    "welcome":"EDU-AIR klaar — zwaai om te beginnen","air.tap":"Tik","draw.on":"Inkt actief","draw.cleared":"Bord gewist","draw.undo":"Streek ongedaan maken","draw.nothing":"Niets om ongedaan te maken",
    "shape.circle":"Cirkel","shape.line":"Lijn","shape.triangle":"Driehoek","shape.square":"Vierkant","shape.pentagon":"Vijfhoek",
    "pointer.on":"Aanwijzer aan","pointer.off":"Aanwijzer uit","offline.on":"Offline modus aan — gecachet","offline.off":"Online","pwa.install":"Gebruik browsermenu → App installeren",
    "draw.off":"Lucht-ontwerp uit","vision.stop":"Lucht-visie gestopt",
    "draw.traceHit":"Mooi getraceerd!","draw.traceMiss":"Niet helemaal — probeer opnieuw","draw.traceLede":"Volg de gidsvorm — een passende streek levert een punt op.",
    "pointer.test":"Precisietest","pointer.precision":"Precisie","pointer.reaction":"Reactietijd","pointer.testDone":"Test voltooid",
    "history.all":"Alles","history.empty":"Nog geen gebeurtenissen.","history.cleared":"Geschiedenis gewist","history.search":"Zoeken…","history.export":"CSV exporteren",
    "quiz.correct":"Correct!","quiz.wrong":"Fout","quiz.finished":"Quiz voltooid","quiz.question":"Vraag","quiz.startFirst":"Maak eerst een quiz","quiz.created":"Quiz gemaakt",
    "calib.point":"Punt","calib.done":"Kalibratie voltooid","calib.score":"Score"
  }
};

/* -------- i18n engine -------- */
var SYMBOLS = {en:"ltr",fr:"ltr",nl:"ltr",ar:"rtl"};
var current = "en";
var onLangChange = [];

function t(key, lang){
  lang = lang || current;
  var d = DICT[lang] || DICT.en;
  return d[key] != null ? d[key] : (DICT.en[key] != null ? DICT.en[key] : key);
}
function apply(){
  document.documentElement.setAttribute("data-i18n-lang", current);
  document.documentElement.setAttribute("dir", SYMBOLS[current] || "ltr");
  document.querySelectorAll("[data-i18n-html]").forEach(function(el){
    var k = el.getAttribute("data-i18n-html");
    if(k) el.innerHTML = t(k);
  });
  document.querySelectorAll("[data-i18n-attr]").forEach(function(el){
    var map = el.getAttribute("data-i18n-attr").trim();
    var pairs = map.split(",");
    var langVal = (DICT[current] && DICT[current]["attr.lang"]) ? DICT[current]["attr.lang"] : null;
    pairs.forEach(function(p){
      var i = p.indexOf(":");
      if(i<0) return;
      var attr = p.slice(0,i);
      if(attr === "placeholder"){
        var host = el.getAttribute("data-i18n-placeholder-key");
        if(host) el.setAttribute("placeholder", t(host));
      }
    });
  });
  document.querySelectorAll("[data-i18n-placeholder-key]").forEach(function(el){
    el.setAttribute("placeholder", t(el.getAttribute("data-i18n-placeholder-key")));
  });
  document.querySelectorAll(".langbtn[data-lang]").forEach(function(b){
    b.setAttribute("data-state", b.getAttribute("data-lang")===current ? "active" : "");
  });
  document.querySelectorAll(".dt-btn[data-sort]").forEach(function(){/* noop */});
  notify();
}
function notify(){
  onLangChange.forEach(function(fn){ try{fn(current);}catch(e){} });
}
function setLang(lang){
  if(SUPPORTED.indexOf(lang) < 0) lang = "en";
  current = lang;
  try{ localStorage.setItem("edu-air-lang", lang); }catch(e){}
  apply();
}
function init(){
  var saved = null;
  try{ saved = localStorage.getItem("edu-air-lang"); }catch(e){}
  var nav = (navigator.language || "en").slice(0,2).toLowerCase();
  if(saved && SUPPORTED.indexOf(saved)>=0){ current = saved; }
  else if(SUPPORTED.indexOf(nav)>=0){ current = nav; }
  else{ current = "en"; }
  apply();
}

window.i18n = {
  SUPPORTED: SUPPORTED,
  t: t,
  apply: apply,
  setLang: setLang,
  init: init,
  current: function(){ return current; },
  dir: function(){ return SYMBOLS[current] || "ltr"; },
  isRTL: function(){ return (SYMBOLS[current]||"ltr")==="rtl"; },
  onChange: function(fn){ onLangChange.push(fn); },
  onReady: function(fn){ fn(); }
};

/* boot */
if(typeof document !== "undefined" && document.readyState !== "loading"){ init(); }
else if(typeof document !== "undefined"){ document.addEventListener("DOMContentLoaded", init); }
})();
