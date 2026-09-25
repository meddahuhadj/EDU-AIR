# EDU-AIR SMART SURFACE — Feuille de route des enrichissements

> Propositions d'enrichissements concrets, interactifs et pédagogiques pour les
> 12 modules de l'application web **EDU-AIR SMART SURFACE**
> (`index.html` + `app.js` + `styles.css`, copies miroir dans `web/`).
> Chaque module est relié à son emplacement de code actuel dans `app.js`.

---

## Correspondance modules ↔ code

| Module | Vue `index.html` | Bloc `app.js` |
|---|---|---|
| 1. Tableau de Bord & Cockpit | `view-dashboard` | `app.js:136` |
| 2. Surface Intelligente (Whiteboard/TNI) | `view-whiteboard` | `app.js:165` |
| 3. Pointeur Air & Raccourcis Gestuels | `view-pointer` | `app.js:697` |
| 4. Dessin Air & Schématisation | `view-draw` | `app.js:869` |
| 5. Air 3D (Manipulateur Holo-Pédagogique) | `view-air3d` | `app.js:1294` |
| 6. Vision Air & Documents / EPS | `view-vision` | *(intégré Draw/Surface)* |
| 7. Labo Air (Simulations Scientifiques) | `view-labo` | `app.js:1515` |
| 8. Quiz Air & Évaluation Interactive | `view-quiz` | `app.js:2765` |
| 9. Présentation Air & Diaporamas | `view-presentation` | `app.js:2808` |
| 10. Professeur IA | `view-profai` | `app.js:3131` |
| 11. Wizard de Calibrage | `view-calib` | `app.js:3193` |
| 12. Historique / Accessibilité | `view-history` | *(partagé)* |

---

## 🌟 Module 1 : Tableau de Bord & Cockpit Enseignant

- [x] **Widgets Temps Réel & Rythme de Cours**
  - Baromètre d'Attention / Énergie de la classe : indicateur visuel rapide
    (jauge circulaire) pour marquer l'état d'avancement du cours (échauffement,
    magistral, pratique, évaluation).
  - Statistiques de Session Instantanées : durée de la leçon, nombre de
    diapositives annotées, quiz complétés, temps passé par élève au tableau.
  - Lanceur de routine de démarrage : bouton 1-clic « Prêt pour la classe » qui
    calibre la caméra, bascule en plein écran et ouvre la diapositive du jour.

## 🎨 Module 2 : Surface Intelligente (Whiteboard TNI)

- [x] **Outil Redo (Rétablir) & Historique Multi-niveaux**
  - Annuler (`Undo`) et rétablir (`Redo`) jusqu'à 30 étapes d'annotations.
  - La pile actuelle est dans `saveWbState()` (`app.js:264`, plafond 25 étapes).
- [x] **Outil Texte & Formules Mathématiques**
  - Encadré textuel typographié posé au clic ou au geste.
  - Formules LaTeX simples (fractions, racines carrées).
- [ ] **Règle & Rapporteur Virtuels Déplaçables par Gestes**
  - Instruments virtuels manipulables (glisser à la main, rotation à deux
    doigts / pincement) pour tracer des droites et mesurer des angles en direct.
- [x] **Post-it Virtuels Magnétiques**
  - Notes autocollantes colorées, déplaçables, pour les brainstormings de classe.

## 🎯 Module 3 : Pointeur Air & Raccourcis Gestuels

- [x] **Mode Laser à Traînée Phosphorescente**
  - Traînée lumineuse néon persistante ~1,5 s qui s'estompe doucement.
- [x] **Menu Circulaire (« Pie Menu ») au Geste Poing/Main Ouverte**
  - Menu radial rapide autour du pointeur : crayon, surligneur, gomme, zoom.
- [x] **Zone Morte & Filtre Anti-Tremblement (Kalman / EMA)**
  - Lissage adaptatif des coordonnées pour éliminer les micro-saccades de détection.

## 🖌️ Module 4 : Dessin Air & Schématisation

- [x] **Gabarits & Diagrammes Éducatifs Prédéfinis**
  - Modèles en filigrane : *Mind Map*, *Diagramme de Venn*, *Repère orthonormé*,
    *Frise chronologique*.
- [x] **Reconnaissance de Formes à la Volée (Snap-to-Shape)**
  - Cercle / rectangle tracé à main levée → lissé en forme vectorielle parfaite
    au relâchement.
- [x] **Export Vectoriel SVG + PNG Haute Résolution**
  - Sauvegarde propre des schémas d'élèves pour les cours imprimés.

## 🧊 Module 5 : Air 3D (Manipulateur Holo-Pédagogique)

- [x] **Nouveaux Modèles 3D Interactifs Animés**
  - Double Hélice d'ADN : rotation 3D continue + mise en évidence des paires de
    bases (A-T, C-G) au survol.
  - Volcan / Coupe Géologique de la Terre : animation de subduction ou éruption,
    écorce / manteau / noyau manipulables au pincement d'air.
  - Moteur Thermique à 4 Temps : cycle admission / compression / explosion /
    échappement contrôlé par la vitesse de rotation de la main.
- [x] **Mode Éclaté (« Exploded View »)**
  - Geste d'écartement des deux mains pour séparer les composants du modèle et
    observer l'intérieur.

## 👁️ Module 6 : Vision Air & Documents / EPS

- [x] **Correction Express de Copies & Détection QCM papier**
  - Cadrâge d'une feuille de QCM, détection des cases noircies, calcul de la
    note en direct.
- [ ] **Coach Posture & Maintien Ergonomique**
  - Alerte discrète si l'élève ou l'enseignant est voûté trop longtemps.
- [ ] **Reconnaissance OCR d'Équations Manuscrites**
  - Capture d'un calcul écrit sur papier pour le résoudre ou le tracer dans le Labo.

## 🔬 Module 7 : Labo Air (Simulations Scientifiques)

- [x] **Simulation Gravitationnelle & Chute des Corps (Galilée / Newton)**
  - Chute libre dans l'air vs dans le vide (frottements on/off).
  - Ajustement de la gravité (g = 9,81 m/s², Lune, Mars).
- [x] **Laboratoire d'Acoustique & Ondes Sonores**
  - Visualisation en direct d'ondes sinusoïdales modulables en fréquence (Hz) et
    amplitude (dB), pilotée au micro ou au geste.
- [x] **Tableau Périodique Dynamique des Éléments**
  - Sélection aérienne d'un élément → configuration électronique (couches
    K, L, M) et propriétés physico-chimiques.

## 📝 Module 8 : Quiz Air & Évaluation Interactive

- [x] **Mode Duel / Face-à-Face 2 Joueurs**
  - Écran scindé gauche/droite, deux élèves répondant chacun par leur geste.
- [x] **Génération Automatique de QCM par Matière & Niveau**
  - Banque pré-chargée (Primaire, Collège, Lycée) + explication pédagogique
    détaillée en cas d'erreur.
- [x] **Effets Sonores & Visuels Gamifiés**
  - Confettis canvas en cas de sans-faute, son de validation / buzz paramétrable.

## 📺 Module 9 : Présentation Air & Diaporamas

- [x] **Diapositives Riches Multi-disciplines**
  - Vidéos, mini-simulateurs et zones masquées à révéler par geste
    (« Scratch to reveal »).
- [x] **Mode Présentateur Double Écran / Volet Notes**
  - Notes de cours pour l'enseignant sur tablette / moniteur secondaire pendant
    que la vue classe ne montre que l'essentiel.
- [x] **Curseur Loupe à Zoom Ajustable** (x2, x3, x4) + inversion de contraste
  pour les élèves malvoyants.

## 🤖 Module 10 : Professeur IA

- [ ] **Générateur Instantané d'Exercices Différenciés**
  - 3 variantes en 1 clic : *Soutien*, *Standard*, *Défi / Approfondissement*.
- [ ] **Synthèse Vocale Pédagogique (TTS)**
  - Lecture à voix haute avec intonation adaptée (langues vivantes, dyslexie).
- [x] **Explications en Langage Simple (« ELI5 »)**
  - Bouton « Explique-moi comme si j'avais 10 ans » de vulgarisation.

## 📜 Module 11 & 12 : Calibrage, Accessibilité & Historique

- [x] **Mode Contraste Élevé & Polices Dyslexie**
  - Bascule 1-clic vers OpenDyslexic et contrastes renforcés pour les salles
    lumineuses.
- [x] **Export PDF Complet du Cahier de Cours**
  - Compilation chronologique automatique de toutes les notes de la journée,
    quiz et schémas → PDF partageable aux élèves absents.

---

## Ordre d'intégration suggéré

| Priorité | Groupe | Modules concernés |
|---|---|---|
| **1** | Dashboard & Whiteboard | M2 (Redo, texte, règle) + M1 (statistiques) |
| **2** | 3D & Simulations | M5 (ADN & coupe de la Terre) + M7 (gravité / chute) |
| **3** | Gamification & Dessin | M8 (duel 2 joueurs) + M4 (gabarits & snap-to-shape) |
| **4** | Au fil de l'eau | M3, M6, M9, M10, M11+M12 |

## Règles d'implémentation

- Toute fonctionnalité ajoutée dans `app.js` doit respecter le **mode sûr**
  (`pill-mode-safe`), le **calibrage** et l'existant i18n (`data-i18n`).
- Les **copies miroir** `web/app.js`, `web/index.html`, `web/styles.css` et
  `web/sw.js` (cache bust) doivent être synchronisées avant tout déploiement
  Vercel / Netlify.
- Chaque ajout sera accompagné de ses états Unité → vérifié en mode sûr → en
  direct, conformément à la politique d'honnêteté du projet (jamais de faux
  réglage, jamais de fonction « à venir » présentée comme active).