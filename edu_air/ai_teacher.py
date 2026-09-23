"""AI Pedagogical Assistant & Classroom Copilot Module for EDU-AIR.

Provides pure Python logic for generating lesson plans, clarifying concepts,
formulating quiz questions, and providing real-time teaching copilot advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LessonPlan:
    subject: str
    topic: str
    target_cycle: str  # e.g., "Cycle 4", "Lycée", "Collège"
    objectives: List[str]
    sections: List[Dict[str, str]]
    quiz_questions: List[Dict[str, str]]
    keywords: List[str]


PRESET_LESSONS: Dict[str, LessonPlan] = {
    "math_geometry": LessonPlan(
        subject="Mathématiques",
        topic="Géométrie et aires des figures usuel",
        target_cycle="Cycle 4 (4ème / 3ème)",
        objectives=[
            "Reconnaître et tracer les figures géométriques élémentaires",
            "Calculer l'aire et le périmètre d'un cercle et d'un rectangle",
            "Utiliser la formule de Pythagore sur des exemples interactifs",
        ],
        sections=[
            {"title": "1. Introduction aux Formes Ususelles", "content": "Rappel des définitions du cercle, rectangle et triangle."},
            {"title": "2. Démonstration Interactive", "content": "Traçage aérien avec EDU-AIR et calcul d'aire en temps réel."},
            {"title": "3. Application Pratique", "content": "Exercices guidés par l'enseignant au tableau projete."},
        ],
        quiz_questions=[
            {"q": "Quelle est la formule de l'aire d'un cercle ?", "a": "π × r²", "opts": ["2 × π × r", "π × r²", "4 × π × r²", "π × d"]},
            {"q": "Combien de côtés possède un rectangle ?", "a": "4", "opts": ["3", "4", "5", "6"]},
        ],
        keywords=["géométrie", "cercle", "aire", "périmètre", "pythagore"]
    ),
    "science_water": LessonPlan(
        subject="Physique-Chimie / SVT",
        topic="La Molécule d'Eau H₂O et ses Propriétés",
        target_cycle="Collège & Lycée",
        objectives=[
            "Comprendre la structure moléculaire H₂O",
            "Identifier les liaisons covalentes simples et l'angle de liaison (104.5°)",
            "Visualiser la polarité de la molécule en 3D",
        ],
        sections=[
            {"title": "1. Structure Atomique", "content": "1 atome d'oxygène central et 2 atomes d'hydrogène."},
            {"title": "2. Manipulation 3D Air-Touch", "content": "Rotation et zoom gestuel sur la molécule H₂O."},
            {"title": "3. États de la Matière", "content": "Passage liquide, solide (glace) et gazeux (vapeur)."},
        ],
        quiz_questions=[
            {"q": "Quel est l'angle de liaison dans la molécule d'eau ?", "a": "104.5°", "opts": ["90°", "104.5°", "120°", "180°"]},
            {"q": "Combien d'atomes d'hydrogène comporte H₂O ?", "a": "2", "opts": ["1", "2", "3", "4"]},
        ],
        keywords=["chimie", "eau", "h2o", "molécule", "atomes"]
    ),
}


class AITeacherCopilot:
    """Classroom AI Copilot for interactive teaching guidance."""

    def __init__(self, lang: str = "fr"):
        self.lang = lang
        self.history: List[Dict[str, str]] = []

    def generate_lesson(self, subject: str, topic: str, target_cycle: str = "Cycle 4") -> LessonPlan:
        # Match preset if available or build generic
        key = f"{subject.lower()}_{topic.lower()}"
        for preset_key, preset in PRESET_LESSONS.items():
            if preset_key in key or topic.lower() in preset.topic.lower():
                return preset

        return LessonPlan(
            subject=subject,
            topic=topic,
            target_cycle=target_cycle,
            objectives=[
                f"Comprendre les notions clés de : {topic}",
                "Appliquer les méthodes dans des exercices interactifs",
                "Valider l'acquisition des compétences via un quiz rapide"
            ],
            sections=[
                {"title": f"1. Découverte de {topic}", "content": "Présentation visuelle et interactive du sujet."},
                {"title": "2. Activité Interactive", "content": "Manipulation gestuelle et annotation au tableau."},
                {"title": "3. Synthèse & Bilan", "content": "Mise en commun des résultats avec la classe."},
            ],
            quiz_questions=[
                {"q": f"Question de vérification sur {topic}", "a": "Option A (Bonne réponse)", "opts": ["Option A (Bonne réponse)", "Option B", "Option C", "Option D"]}
            ],
            keywords=[subject.lower(), topic.lower()]
        )

    def answer_question(self, question: str) -> str:
        q_lower = question.lower()
        self.history.append({"role": "user", "text": question})

        if "cercle" in q_lower or "aire" in q_lower:
            reply = "L'aire d'un cercle se calcule avec la formule A = π × r², où r est le rayon du cercle. Le périmètre (ou circonférence) est P = 2 × π × r."
        elif "eau" in q_lower or "h2o" in q_lower:
            reply = "La molécule d'eau H₂O est composée d'un atome d'oxygène lié à deux atomes d'hydrogène. L'angle entre les deux liaisons est d'environ 104,5°."
        elif "geste" in q_lower or "pince" in q_lower:
            reply = "Pour faire un clic avec EDU-AIR, rapproche le pouce et l'index (geste de pince). Pour déplacer un objet, maintiens la pince et déplace ta main."
        else:
            reply = f"Excellente question sur '{question}'. EDU-AIR recommande d'utiliser le module d'annotation ou le visualiseur 3D pour illustrer ce concept en direct."

        self.history.append({"role": "assistant", "text": reply})
        return reply
