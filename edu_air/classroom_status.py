"""The classroom status snapshot consumed by the HUD / overlay / control
dock -- a single plain dataclass, extracted out of ``classroom.py`` so it
can be read (and imported by the UI layer) without pulling in the whole
session/intent/safety graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .annotation import TOOL_NONE


@dataclass
class ClassroomStatus:
    mode: str = "real"                     # real | demo
    detector: str = ""
    fps: float = 0.0
    # presentation
    presentation_state: str = "idle"       # idle | active | paused
    current_slide: int = 0
    total_slides: int = 0
    # pointer
    pointer_visible: bool = True
    pointer_pos: tuple = (0, 0)
    pointer_tremor: float = 0.0
    pointer_spikes: int = 0
    # interaction
    last_command: str = ""
    last_event: str = ""
    current_interaction: str = "none"
    gesture: str = ""
    control_locked: bool = False
    interaction_mode: str = "contactless"  # contactless | wall
    # classroom timer
    clock_seconds: int = 0
    timer_running: bool = False
    # participation tally
    participation_count: int = 0
    # lesson sequencer
    lesson_progress: str = ""
    # annotation
    annotation_tool: str = TOOL_NONE
    stroke_count: int = 0
    # interactive board (TNI)
    board_page: int = 1
    board_pages: int = 1
    board_background: str = "blank"
    # quiz
    quiz_active: bool = False
    quiz_state: str = "idle"
    quiz_score: tuple = (0, 0)             # (correct, wrong)
    quiz_question_n: int = 0
    quiz_question: str = ""
    quiz_options: list = field(default_factory=list)
    quiz_revealed: bool = False
    # safety
    last_decision: str = ""
    confirmed_required: int = 0
    # environment (traffic light)
    lighting: str = "unknown"          # dark | low | good | bright
    ambient_noise: str = "unknown"     # ok | loud
    hand_visible: bool = False
    performance_mode: bool = False
    calibration_drift: bool = False    # wall-mode homography looks off -> recalibration suggested
