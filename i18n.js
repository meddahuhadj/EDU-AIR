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
    "demo.badge":"Demo",
    "dash.title":"Dashboard",
    "lede":"Zero-contact AI teaching: calibrate once, then point, draw, quiz and teach in mid-air.",
    "a11y.skip":"Skip to content",
    "smart.save":"Save","smart.clear":"Clear",
    "pointer.enable":"Enable air pointer","pointer.click":"Simulate click",
    "draw.enable":"Enable air draw",
    "threed.fonts":"3D","threed.home":"Reset view","threed.auto":"Auto-rotate",
    "vision.start":"Start air vision",
    "lab.begin":"Start lab","lab.reset":"Reset",
    "quiz.new":"New quiz","quiz.addq":"+ Add question","quiz.save":"Save quiz","quiz.close":"Close",
    "presentation.prev":"Prev","presentation.next":"Next",
    "teacher.placeholder":"Ask your AI teacher…",
    "calibration.begin":"Begin","calibration.reset":"Reset","calibration.auto":"Auto",
    "history.clear":"Clear history",
    "danger.cancel":"Cancel","danger.confirm":"Confirm","danger.emergency":"Emergency stop",

    "pointer.title":"Air pointer","pointer.lede":"Move your index finger through the air to control the cursor without ever touching the screen. In this browser demo, your mouse stands in for the tracked fingertip.",
    "draw.title":"Air draw","draw.lede":"Draw in the air — your hand is the pen. Smart ink recognizes circles, lines, triangles and squares automatically.","draw.aim":"Aim",
    "threed.title":"Air 3D","threed.lede":"Explore 3D models with your hand — rotate, zoom and dissect shapes in mid-air. Drag with the mouse to rotate in this demo.","threed.explode":"Explode","threed.wire":"Wireframe",
    "vision.title":"Air vision","vision.lede":"Simulated preview of EDU-AIR's on-device computer vision — the desktop app runs this live from your webcam, fully local, nothing uploaded.",
    "lab.title":"Air lab","lab.lede":"A small real-time physics lab, no risk, no hardware — adjust the sliders and watch the simulation respond live.",
    "lab.circuit":"Circuit","lab.beaker":"Chemistry","lab.pendulum":"Pendulum","lab.wave":"Waves","lab.optics":"Optics","lab.planet":"Planets",
    "lab.voltage":"Voltage","lab.resistance":"Resistance","lab.current":"Current","lab.ph":"pH level","lab.length":"Length","lab.gravity":"Gravity","lab.period":"Period","lab.frequency":"Frequency","lab.amplitude":"Amplitude","lab.objectDist":"Object distance","lab.focal":"Focal length","lab.imageDist":"Image distance","lab.speed":"Orbital speed",
    "quiz.title":"Air quiz","quiz.lede":"Interactive quizzes controlled with hand gestures — answer by pinching in mid-air. Click an option in this demo.","quiz.editTitle":"Build a quiz",
    "presentation.title":"Air presentation","presentation.lede":"Deliver presentations without touching a thing — swipe in air to change slides.",
    "teacher.title":"AI teacher","teacher.lede":"Your AI co-teacher. This demo chat shows example interactions — the desktop app connects it to your live lesson.","teacher.send":"Ask","teacher.placeholder":"Ask your AI teacher anything…",
    "calibration.title":"Calibration","calibration.lede":"Map your camera to the projection surface for pixel-perfect pointing.","calibration.start":"Start calibration","calibration.close":"Close",
    "history.title":"History","history.lede":"Every stroke, every quiz, every session — your local audit trail.",
    "settings.title":"Settings","settings.lang":"Language","settings.sensitivity":"Pointer sensitivity","settings.a11y":"Accessibility","settings.a11yMotion":"Reduce motion","settings.a11yContrast":"High contrast","settings.a11yCursor":"Large cursor","settings.install":"Install app","settings.reset":"Reset all local data",
    "privacy.title":"Privacy","privacy.body":"EDU-AIR processes camera and microphone data locally by default — nothing is uploaded or recorded without your say. This web demo never requests your camera; it runs entirely on simulated and mouse-driven input. Clear all locally stored demo data anytime from Settings.",
    "security.title":"Security","security.body":"Every action passes through a safety gate before it runs: safe actions execute immediately, risky ones ask for confirmation, and unknown or unregistered actions are always blocked. An emergency stop is always one click away.",
    "danger.title":"Safety gate","danger.body":"This action could disrupt an active session. Your safety engine is asking you to confirm.",
    "demo.title":"Simulation mode","demo.body":"No camera hardware detected — running the synthetic hand engine. This is a faithful simulation so you can explore every feature.","demo.kb":"Enable keyboard/mouse as hand input","demo.go":"Enter smart surface",
    "smart.shapes":"Shapes","smart.haptics":"Haptics",
    "welcome":"EDU-AIR ready — wave to interact","air.tap":"Tap","draw.on":"Ink hot","draw.cleared":"Canvas cleared","draw.undo":"Undo stroke","draw.nothing":"Nothing to undo",
    "shape.circle":"Circle","shape.line":"Line","shape.triangle":"Triangle","shape.square":"Square","shape.pentagon":"Pentagon",
    "pointer.on":"Pointer on","pointer.off":"Pointer off","offline.on":"Offline mode on — cached","offline.off":"Online","pwa.install":"Use your browser menu → Install app",
    "draw.off":"Air draw off","vision.stop":"Air vision stopped",
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
    "demo.badge":"Démo",
    "dash.title":"Tableau de bord",
    "lede":"Enseignement sans contact : calibrez une fois, puis pointez, dessinez, interrogez et enseignez en l'air.",
    "a11y.skip":"Aller au contenu",
    "smart.save":"Enregistrer","smart.clear":"Effacer",
    "pointer.enable":"Activer le pointeur air","pointer.click":"Cliquer",
    "draw.enable":"Activer le dessin air",
    "threed.home":"Réinitialiser la vue","threed.auto":"Rotation auto",
    "vision.start":"Lancer la vision air",
    "lab.begin":"Démarrer le labo","lab.reset":"Réinitialiser",
    "quiz.new":"Nouveau quiz","quiz.addq":"+ Ajouter une question","quiz.save":"Enregistrer le quiz","quiz.close":"Fermer",
    "presentation.prev":"Préc","presentation.next":"Suiv",
    "teacher.placeholder":"Posez une question à votre prof IA…",
    "calibration.begin":"Commencer","calibration.reset":"Réinitialiser","calibration.auto":"Auto",
    "history.clear":"Effacer l'historique",
    "danger.cancel":"Annuler","danger.confirm":"Confirmer","danger.emergency":"Arrêt d'urgence",

    "pointer.title":"Pointeur air","pointer.lede":"Déplacez votre index dans l'air pour contrôler le curseur sans jamais toucher l'écran. Dans cette démo navigateur, votre souris remplace le bout du doigt suivi par caméra.",
    "draw.title":"Dessin air","draw.lede":"Dessinez dans l'air — votre main devient le stylo. L'encre intelligente reconnaît automatiquement cercles, lignes, triangles et carrés.","draw.aim":"Visée",
    "threed.title":"Air 3D","threed.lede":"Explorez des modèles 3D avec la main — pivotez, zoomez et disséquez des formes en l'air. Faites glisser la souris pour pivoter dans cette démo.","threed.explode":"Éclater","threed.wire":"Filaire",
    "vision.title":"Vision air","vision.lede":"Aperçu simulé de la vision par ordinateur embarquée d'EDU-AIR — l'application de bureau l'exécute en direct depuis votre webcam, entièrement en local, sans envoi de données.",
    "lab.title":"Labo air","lab.lede":"Un petit labo de physique en temps réel, sans risque, sans matériel — ajustez les curseurs et observez la simulation réagir en direct.",
    "lab.circuit":"Circuit","lab.beaker":"Chimie","lab.pendulum":"Pendule","lab.wave":"Ondes","lab.optics":"Optique","lab.planet":"Planètes",
    "lab.voltage":"Tension","lab.resistance":"Résistance","lab.current":"Courant","lab.ph":"Niveau de pH","lab.length":"Longueur","lab.gravity":"Gravité","lab.period":"Période","lab.frequency":"Fréquence","lab.amplitude":"Amplitude","lab.objectDist":"Distance objet","lab.focal":"Distance focale","lab.imageDist":"Distance image","lab.speed":"Vitesse orbitale",
    "quiz.title":"Quiz air","quiz.lede":"Quiz interactifs pilotés par gestes de la main — répondez en pinçant les doigts en l'air. Cliquez une option dans cette démo.","quiz.editTitle":"Créer un quiz",
    "presentation.title":"Présentation air","presentation.lede":"Présentez sans rien toucher — balayez l'air pour changer de diapositive.",
    "teacher.title":"Prof IA","teacher.lede":"Votre co-enseignant IA. Cette discussion de démo montre des exemples d'interaction — l'application de bureau le connecte à votre cours en direct.","teacher.send":"Envoyer","teacher.placeholder":"Posez une question à votre prof IA…",
    "calibration.title":"Calibrage","calibration.lede":"Alignez votre caméra sur la surface de projection pour un pointage précis.","calibration.start":"Démarrer le calibrage","calibration.close":"Fermer",
    "history.title":"Historique","history.lede":"Chaque trait, chaque quiz, chaque session — votre journal local.",
    "settings.title":"Réglages","settings.lang":"Langue","settings.sensitivity":"Sensibilité du pointeur","settings.a11y":"Accessibilité","settings.a11yMotion":"Réduire les animations","settings.a11yContrast":"Contraste élevé","settings.a11yCursor":"Grand curseur","settings.install":"Installer l'application","settings.reset":"Réinitialiser les données locales",
    "privacy.title":"Confidentialité","privacy.body":"Par défaut, EDU-AIR traite la caméra et le micro en local — rien n'est envoyé ni enregistré sans votre accord. Cette démo web ne demande jamais votre caméra ; elle fonctionne entièrement avec des entrées simulées ou pilotées par la souris. Effacez à tout moment les données locales de démo depuis Réglages.",
    "security.title":"Sécurité","security.body":"Chaque action passe par une porte de sécurité avant de s'exécuter : les actions sûres s'exécutent immédiatement, les actions à risque demandent une confirmation, et les actions inconnues ou non enregistrées sont toujours bloquées. Un arrêt d'urgence reste à un clic.",
    "danger.title":"Porte de sécurité","danger.body":"Cette action pourrait perturber une session active. Votre moteur de sécurité vous demande de confirmer.",
    "demo.title":"Mode simulation","demo.body":"Aucune caméra détectée — le moteur de main synthétique prend le relais. C'est une simulation fidèle pour explorer toutes les fonctions.","demo.kb":"Activer clavier/souris comme entrée main","demo.go":"Entrer dans la surface intelligente",
    "smart.shapes":"Formes","smart.haptics":"Retour haptique",
    "welcome":"EDU-AIR prêt — faites un signe pour interagir","air.tap":"Tap","draw.on":"Encre active","draw.cleared":"Canevas effacé","draw.undo":"Annuler le trait","draw.nothing":"Rien à annuler",
    "shape.circle":"Cercle","shape.line":"Ligne","shape.triangle":"Triangle","shape.square":"Carré","shape.pentagon":"Pentagone",
    "pointer.on":"Pointeur activé","pointer.off":"Pointeur désactivé","offline.on":"Mode hors-ligne activé — en cache","offline.off":"En ligne","pwa.install":"Utilisez le menu du navigateur → Installer l'application",
    "draw.off":"Dessin air désactivé","vision.stop":"Vision air arrêtée",
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
    "demo.badge":"تجريبي",
    "dash.title":"لوحة التحكم",
    "lede":"تدريس بدون لمس: عايِر مرة واحدة ثم أشر واستم واختبر وعلّم في الهواء.",
    "a11y.skip":"تخطَّ إلى المحتوى",
    "smart.save":"حفظ","smart.clear":"مسح",
    "pointer.enable":"تفعيل مؤشر الهواء","pointer.click":"نقرة",
    "draw.enable":"تفعيل رسم الهواء",
    "threed.home":"إعادة ضبط العرض","threed.auto":"دوران تلقائي",
    "vision.start":"بدء رؤية الهواء",
    "lab.begin":"بدء المختبر","lab.reset":"إعادة ضبط",
    "quiz.new":"اختبار جديد","quiz.addq":"+ إضافة سؤال","quiz.save":"حفظ الاختبار","quiz.close":"إغلاق",
    "presentation.prev":"السابق","presentation.next":"التالي",
    "teacher.placeholder":"اسأل معلّمك الذكي…",
    "calibration.begin":"ابدأ","calibration.reset":"إعادة ضبط","calibration.auto":"تلقائي",
    "history.clear":"مسح السجل",
    "danger.cancel":"إلغاء","danger.confirm":"تأكيد","danger.emergency":"إيقاف طارئ",

    "pointer.title":"مؤشر الهواء","pointer.lede":"حرّك سبابتك في الهواء للتحكم بالمؤشر دون لمس الشاشة أبدًا. في هذا العرض التجريبي بالمتصفح، تحل الفأرة محل طرف الإصبع المتتبَّع بالكاميرا.",
    "draw.title":"رسم الهواء","draw.lede":"ارسم في الهواء — يدك هي القلم. يتعرّف الحبر الذكي تلقائيًا على الدوائر والخطوط والمثلثات والمربعات.","draw.aim":"التصويب",
    "threed.title":"هواء ثلاثي الأبعاد","threed.lede":"استكشف نماذج ثلاثية الأبعاد بيدك — أدر وكبّر وفكك الأشكال في الهواء. اسحب بالفأرة للتدوير في هذا العرض.","threed.explode":"تفكيك","threed.wire":"إطار سلكي",
    "vision.title":"رؤية الهواء","vision.lede":"معاينة محاكاة لرؤية الحاسوب المدمجة في EDU-AIR — يشغّلها التطبيق المكتبي مباشرة من كاميرتك، محليًا بالكامل دون رفع أي بيانات.",
    "lab.title":"مختبر الهواء","lab.lede":"مختبر فيزياء صغير في الوقت الحقيقي، بلا خطر وبلا عتاد — حرّك أشرطة التمرير وشاهد المحاكاة تستجيب مباشرة.",
    "lab.circuit":"دائرة","lab.beaker":"كيمياء","lab.pendulum":"بندول","lab.wave":"موجات","lab.optics":"بصريات","lab.planet":"كواكب",
    "lab.voltage":"الجهد","lab.resistance":"المقاومة","lab.current":"التيار","lab.ph":"مستوى الحموضة","lab.length":"الطول","lab.gravity":"الجاذبية","lab.period":"الدور","lab.frequency":"التردد","lab.amplitude":"السعة","lab.objectDist":"مسافة الجسم","lab.focal":"البعد البؤري","lab.imageDist":"مسافة الصورة","lab.speed":"السرعة المدارية",
    "quiz.title":"اختبار الهواء","quiz.lede":"اختبارات تفاعلية تُدار بإيماءات اليد — أجب بقرص الأصابع في الهواء. انقر خيارًا في هذا العرض.","quiz.editTitle":"إنشاء اختبار",
    "presentation.title":"عرض الهواء","presentation.lede":"قدّم عرضك دون لمس أي شيء — امسح في الهواء لتغيير الشرائح.",
    "teacher.title":"معلّم الذكاء","teacher.lede":"معلّمك المساعد بالذكاء الاصطناعي. تعرض هذه المحادثة التجريبية أمثلة تفاعل — يربطه التطبيق المكتبي بدرسك المباشر.","teacher.send":"إرسال","teacher.placeholder":"اسأل معلّمك الذكي…",
    "calibration.title":"المعايرة","calibration.lede":"طابِق كاميرتك مع سطح العرض لتأشير دقيق.","calibration.start":"بدء المعايرة","calibration.close":"إغلاق",
    "history.title":"السجل","history.lede":"كل خط، كل اختبار، كل جلسة — سجلّك المحلي.",
    "settings.title":"الإعدادات","settings.lang":"اللغة","settings.sensitivity":"حساسية المؤشر","settings.a11y":"إمكانية الوصول","settings.a11yMotion":"تقليل الحركة","settings.a11yContrast":"تباين عالٍ","settings.a11yCursor":"مؤشر كبير","settings.install":"تثبيت التطبيق","settings.reset":"إعادة ضبط البيانات المحلية",
    "privacy.title":"الخصوصية","privacy.body":"تعالج EDU-AIR الكاميرا والميكروفون محليًا افتراضيًا — لا شيء يُرفع أو يُسجَّل دون موافقتك. لا يطلب هذا العرض التجريبي كاميرتك أبدًا؛ فهو يعمل بالكامل بإدخال محاكى أو عبر الفأرة. امسح بيانات العرض المحلية في أي وقت من الإعدادات.",
    "security.title":"الأمان","security.body":"تمر كل إجراء عبر بوابة أمان قبل تنفيذه: الإجراءات الآمنة تُنفَّذ فورًا، والإجراءات الخطرة تطلب تأكيدًا، والإجراءات غير المعروفة أو غير المسجّلة تُحظر دائمًا. زر الإيقاف الطارئ متاح دومًا بنقرة واحدة.",
    "danger.title":"بوابة الأمان","danger.body":"قد يعطّل هذا الإجراء جلسة نشطة. يطلب محرك الأمان تأكيدك.",
    "demo.title":"وضع المحاكاة","demo.body":"لم يتم رصد كاميرا — يعمل محرك اليد الاصطناعية. هذه محاكاة أمينة لاستكشاف جميع الميزات.","demo.kb":"تفعيل لوحة المفاتيح/الفأرة كإدخال يدوي","demo.go":"الدخول إلى السطح الذكي",
    "smart.shapes":"الأشكال","smart.haptics":"الاهتزاز اللمسي",
    "welcome":"EDU-AIR جاهز — لوّح للتفاعل","air.tap":"نقرة","draw.on":"الحبر جاهز","draw.cleared":"تم مسح اللوحة","draw.undo":"تراجع عن الخط","draw.nothing":"لا شيء للتراجع عنه",
    "shape.circle":"دائرة","shape.line":"خط","shape.triangle":"مثلث","shape.square":"مربع","shape.pentagon":"خماسي",
    "pointer.on":"المؤشر مفعّل","pointer.off":"المؤشر معطّل","offline.on":"وضع عدم الاتصال مفعّل — مخزَّن مؤقتًا","offline.off":"متصل","pwa.install":"استخدم قائمة المتصفح ← تثبيت التطبيق",
    "draw.off":"رسم الهواء معطّل","vision.stop":"توقفت رؤية الهواء",
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
    "demo.badge":"Demo",
    "dash.title":"Dashboard",
    "lede":"Contactloos lesgeven: kalibreer één keer, wijs, teken, quiz en geef les in de lucht.",
    "a11y.skip":"Ga naar inhoud",
    "smart.save":"Opslaan","smart.clear":"Wissen",
    "pointer.enable":"Lucht-aanwijzer inschakelen","pointer.click":"Simuleer klik",
    "draw.enable":"Lucht-ontwerp inschakelen",
    "threed.home":"Weergave resetten","threed.auto":"Auto-rotatie",
    "vision.start":"Lucht-visie starten",
    "lab.begin":"Lab starten","lab.reset":"Resetten",
    "quiz.new":"Nieuwe quiz","quiz.addq":"+ Vraag toevoegen","quiz.save":"Quiz opslaan","quiz.close":"Sluiten",
    "presentation.prev":"Vorige","presentation.next":"Volgende",
    "teacher.placeholder":"Vraag uw AI-leraar…",
    "calibration.begin":"Start","calibration.reset":"Resetten","calibration.auto":"Auto",
    "history.clear":"Geschiedenis wissen",
    "danger.cancel":"Annuleren","danger.confirm":"Bevestigen","danger.emergency":"Noodstop",

    "pointer.title":"Lucht-aanwijzer","pointer.lede":"Beweeg uw wijsvinger door de lucht om de cursor te besturen zonder het scherm aan te raken. In deze browserdemo vervangt uw muis de gevolgde vingertop.",
    "draw.title":"Lucht-ontwerp","draw.lede":"Teken in de lucht — uw hand is de pen. Slimme inkt herkent automatisch cirkels, lijnen, driehoeken en vierkanten.","draw.aim":"Richten",
    "threed.title":"Lucht-3D","threed.lede":"Verken 3D-modellen met uw hand — draai, zoom en ontleed vormen in de lucht. Sleep met de muis om te draaien in deze demo.","threed.explode":"Uit elkaar","threed.wire":"Draadframe",
    "vision.title":"Lucht-visie","vision.lede":"Gesimuleerde preview van EDU-AIR's on-device computervisie — de desktopapp voert dit live uit vanaf uw webcam, volledig lokaal, zonder uploads.",
    "lab.title":"Lucht-lab","lab.lede":"Een klein realtime natuurkundelab, zonder risico, zonder hardware — verstel de schuifregelaars en zie de simulatie live reageren.",
    "lab.circuit":"Circuit","lab.beaker":"Scheikunde","lab.pendulum":"Slinger","lab.wave":"Golven","lab.optics":"Optica","lab.planet":"Planeten",
    "lab.voltage":"Spanning","lab.resistance":"Weerstand","lab.current":"Stroom","lab.ph":"pH-niveau","lab.length":"Lengte","lab.gravity":"Zwaartekracht","lab.period":"Periode","lab.frequency":"Frequentie","lab.amplitude":"Amplitude","lab.objectDist":"Objectafstand","lab.focal":"Brandpuntsafstand","lab.imageDist":"Beeldafstand","lab.speed":"Baansnelheid",
    "quiz.title":"Lucht-quiz","quiz.lede":"Interactieve quizzen bestuurd met handgebaren — antwoord door in de lucht te knijpen. Klik een optie in deze demo.","quiz.editTitle":"Quiz maken",
    "presentation.title":"Lucht-presentatie","presentation.lede":"Presenteer zonder iets aan te raken — veeg in de lucht om van dia te wisselen.",
    "teacher.title":"AI-leraar","teacher.lede":"Uw AI-medeleraar. Deze demochat toont voorbeeldinteracties — de desktopapp koppelt hem aan uw live les.","teacher.send":"Verstuur","teacher.placeholder":"Vraag uw AI-leraar iets…",
    "calibration.title":"Kalibratie","calibration.lede":"Breng uw camera in lijn met het projectieoppervlak voor nauwkeurig aanwijzen.","calibration.start":"Kalibratie starten","calibration.close":"Sluiten",
    "history.title":"Geschiedenis","history.lede":"Elke streek, elke quiz, elke sessie — uw lokale logboek.",
    "settings.title":"Instellingen","settings.lang":"Taal","settings.sensitivity":"Aanwijzergevoeligheid","settings.a11y":"Toegankelijkheid","settings.a11yMotion":"Beweging beperken","settings.a11yContrast":"Hoog contrast","settings.a11yCursor":"Grote cursor","settings.install":"App installeren","settings.reset":"Lokale gegevens resetten",
    "privacy.title":"Privacy","privacy.body":"EDU-AIR verwerkt camera en microfoon standaard lokaal — niets wordt geüpload of opgenomen zonder uw toestemming. Deze webdemo vraagt nooit om uw camera; ze werkt volledig met gesimuleerde of muisgestuurde invoer. Wis lokale demogegevens op elk moment via Instellingen.",
    "security.title":"Beveiliging","security.body":"Elke actie doorloopt een veiligheidspoort voordat ze wordt uitgevoerd: veilige acties lopen meteen door, risicovolle acties vragen bevestiging, en onbekende of niet-geregistreerde acties worden altijd geblokkeerd. Een noodstop is altijd één klik verwijderd.",
    "danger.title":"Veiligheidspoort","danger.body":"Deze actie kan een actieve sessie verstoren. Uw veiligheidsmotor vraagt om bevestiging.",
    "demo.title":"Simulatiemodus","demo.body":"Geen camerahardware gedetecteerd — de synthetische handmotor neemt het over. Dit is een getrouwe simulatie om alle functies te verkennen.","demo.kb":"Toetsenbord/muis als handinvoer inschakelen","demo.go":"Naar smart surface",
    "smart.shapes":"Vormen","smart.haptics":"Trilfeedback",
    "welcome":"EDU-AIR klaar — zwaai om te beginnen","air.tap":"Tik","draw.on":"Inkt actief","draw.cleared":"Bord gewist","draw.undo":"Streek ongedaan maken","draw.nothing":"Niets om ongedaan te maken",
    "shape.circle":"Cirkel","shape.line":"Lijn","shape.triangle":"Driehoek","shape.square":"Vierkant","shape.pentagon":"Vijfhoek",
    "pointer.on":"Aanwijzer aan","pointer.off":"Aanwijzer uit","offline.on":"Offline modus aan — gecachet","offline.off":"Online","pwa.install":"Gebruik browsermenu → App installeren",
    "draw.off":"Lucht-ontwerp uit","vision.stop":"Lucht-visie gestopt",
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
