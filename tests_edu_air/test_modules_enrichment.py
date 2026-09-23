"""Unit tests for enriched EDU-AIR interactive modules (geometry, lab3d, ai_teacher, quiz)."""

from __future__ import annotations

import math
import pytest
from edu_air.geometry import GeometryEngine, VirtualRulerProtractor, Point2D
from edu_air.lab3d import Lab3DEngine, DEFAULT_MODELS
from edu_air.ai_teacher import AITeacherCopilot
from edu_air.quiz import QuestionBank, VoiceQuiz, CURRICULUM_BANKS


def test_geometry_circle_recognition():
    # Generate points around a circle
    points = []
    r = 0.2
    cx, cy = 0.5, 0.5
    for i in range(25):
        angle = (i / 24.0) * 2 * math.pi
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

    shape = GeometryEngine.recognize_stroke(points)
    assert shape is not None
    assert shape.shape_type == "circle"
    assert shape.perimeter > 0


def math_cos(angle):
    import math
    return math.cos(angle)


def math_sin(angle):
    import math
    return math.sin(angle)


def test_virtual_ruler_protractor():
    tool = VirtualRulerProtractor(unit="cm")
    d = tool.measure_distance((0.0, 0.0), (0.03, 0.04))
    assert pytest.approx(d, 0.1) == 5.0

    angle = tool.measure_angle((0.0, 0.0), (1.0, 0.0), (0.0, 1.0))
    assert pytest.approx(angle, 0.1) == 90.0


def test_lab3d_engine():
    engine = Lab3DEngine(initial_model="h2o")
    assert engine.current_model.model_id == "h2o"
    assert len(engine.current_model.parts) == 3

    engine.rotate(15.0, 30.0)
    assert engine.pitch_deg == 15.0
    assert engine.yaw_deg == 30.0

    engine.zoom(1.5)
    assert engine.zoom_scale == 1.5

    assert engine.toggle_exploded() is True
    assert engine.exploded is True

    assert engine.select_model("dna") is True
    assert engine.current_model.model_id == "dna"


def test_ai_teacher_copilot():
    copilot = AITeacherCopilot(lang="fr")
    plan = copilot.generate_lesson("Mathématiques", "Géométrie")
    assert plan.subject == "Mathématiques"
    assert len(plan.objectives) > 0

    reply = copilot.answer_question("Comment calculer l'aire d'un cercle ?")
    assert "π" in reply or "rayon" in reply or "A =" in reply


def test_enriched_quiz_banks():
    bank_pc = QuestionBank.load_subject("physique_chimie")
    assert len(bank_pc.questions) >= 2

    bank_cs = QuestionBank.load_subject("computer_science")
    assert len(bank_cs.questions) >= 2

    bank_ar = QuestionBank.load_subject("arabic")
    assert len(bank_ar.questions) >= 2
