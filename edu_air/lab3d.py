"""3D Virtual Science & Interactive Lab Module for EDU-AIR.

Provides pure Python model logic for 3D interactive science models (Molecular
structures, Astronomy, Biology, Physics), gesture-based multi-axis rotations,
virtual zooming, part isolation, and exploded views.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ModelPart3D:
    part_id: str
    name_fr: str
    name_en: str
    name_ar: str
    color_hex: str
    relative_pos: Tuple[float, float, float]  # (x, y, z)
    description_fr: str = ""


@dataclass
class LabModel3D:
    model_id: str
    name_fr: str
    name_en: str
    name_ar: str
    category: str  # "chemistry", "biology", "astronomy", "physics"
    parts: List[ModelPart3D] = field(default_factory=list)
    note_fr: str = ""


DEFAULT_MODELS: Dict[str, LabModel3D] = {
    "h2o": LabModel3D(
        model_id="h2o",
        name_fr="Molécule d'Eau (H₂O)",
        name_en="Water Molecule (H₂O)",
        name_ar="جزيء الماء (H₂O)",
        category="chemistry",
        note_fr="Angle de liaison covalent: 104.5°",
        parts=[
            ModelPart3D("oxygen", "Atome d'Oxygène (O)", "Oxygen Atom (O)", "ذرة أكسجين", "#ff4d4d", (0.0, 0.0, 0.0), "Oxygène central (charge -)"),
            ModelPart3D("hydrogen_1", "Atome d'Hydrogène 1 (H)", "Hydrogen Atom 1 (H)", "ذرة هيدروجين 1", "#ffffff", (-0.8, 0.6, 0.0), "Liaison covalente simple"),
            ModelPart3D("hydrogen_2", "Atome d'Hydrogène 2 (H)", "Hydrogen Atom 2 (H)", "ذرة هيدروجين 2", "#ffffff", (0.8, 0.6, 0.0), "Liaison covalente simple"),
        ]
    ),
    "dna": LabModel3D(
        model_id="dna",
        name_fr="Hélice ADN",
        name_en="DNA Double Helix",
        name_ar="الحمض النووي (DNA)",
        category="biology",
        note_fr="Structure en double hélice avec paires A-T et C-G",
        parts=[
            ModelPart3D("strand_a", "Brin 1 (Sucre-Phosphate)", "Strand 1", "الشريط 1", "#4da6ff", (-0.5, 0.0, 0.0)),
            ModelPart3D("strand_b", "Brin 2 (Sucre-Phosphate)", "Strand 2", "الشريط 2", "#33cc66", (0.5, 0.0, 0.0)),
            ModelPart3D("base_pairs", "Paires de Bases Azotées", "Base Pairs", "القواعد النيتروجينية", "#ffcc00", (0.0, 0.0, 0.0)),
        ]
    ),
    "solar_system": LabModel3D(
        model_id="solar_system",
        name_fr="Système Solaire (Schématique)",
        name_en="Solar System (Schematic)",
        name_ar="النظام الشمسي",
        category="astronomy",
        note_fr="Orbites schématiques réduites à but pédagogique",
        parts=[
            ModelPart3D("sun", "Soleil", "Sun", "الشمس", "#ffaa00", (0.0, 0.0, 0.0)),
            ModelPart3D("mercury", "Mercure", "Mercury", "عطارد", "#aaaaaa", (1.2, 0.0, 0.0)),
            ModelPart3D("venus", "Vénus", "Venus", "الزهراء", "#e6b800", (2.0, 0.0, 0.0)),
            ModelPart3D("earth", "Terre", "Earth", "الأرض", "#3399ff", (3.0, 0.0, 0.0)),
            ModelPart3D("mars", "Mars", "Mars", "المريخ", "#ff3300", (4.0, 0.0, 0.0)),
        ]
    ),
}


class Lab3DEngine:
    """Manages virtual 3D viewer state and gesture transformations."""

    def __init__(self, initial_model: str = "h2o"):
        self.models = DEFAULT_MODELS
        self.current_model_id = initial_model if initial_model in self.models else "h2o"
        self.pitch_deg: float = 0.0
        self.yaw_deg: float = 0.0
        self.roll_deg: float = 0.0
        self.zoom_scale: float = 1.0
        self.exploded: bool = False
        self.explode_factor: float = 1.0
        self.isolated_part_id: Optional[str] = None
        self.auto_rotate: bool = False

    @property
    def current_model(self) -> LabModel3D:
        return self.models[self.current_model_id]

    def select_model(self, model_id: str) -> bool:
        if model_id in self.models:
            self.current_model_id = model_id
            self.reset_transform()
            return True
        return False

    def rotate(self, delta_pitch: float, delta_yaw: float, delta_roll: float = 0.0) -> None:
        self.pitch_deg = (self.pitch_deg + delta_pitch) % 360.0
        self.yaw_deg = (self.yaw_deg + delta_yaw) % 360.0
        self.roll_deg = (self.roll_deg + delta_roll) % 360.0

    def zoom(self, factor_delta: float) -> None:
        self.zoom_scale = max(0.2, min(5.0, self.zoom_scale * factor_delta))

    def toggle_exploded(self) -> bool:
        self.exploded = not self.exploded
        self.explode_factor = 2.2 if self.exploded else 1.0
        return self.exploded

    def isolate_part(self, part_id: Optional[str]) -> bool:
        if part_id is None or any(p.part_id == part_id for p in self.current_model.parts):
            self.isolated_part_id = part_id
            return True
        return False

    def reset_transform(self) -> None:
        self.pitch_deg = 0.0
        self.yaw_deg = 0.0
        self.roll_deg = 0.0
        self.zoom_scale = 1.0
        self.exploded = False
        self.explode_factor = 1.0
        self.isolated_part_id = None

    def get_state(self) -> dict:
        return {
            "model_id": self.current_model_id,
            "model_name": self.current_model.name_fr,
            "pitch": self.pitch_deg,
            "yaw": self.yaw_deg,
            "roll": self.roll_deg,
            "zoom": self.zoom_scale,
            "exploded": self.exploded,
            "isolated_part": self.isolated_part_id,
            "part_count": len(self.current_model.parts),
        }
