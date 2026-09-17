"""EDU-AIR — Contactless Interactive Classroom.

Transforms HADJ NO-TOUCH AI into a touchless classroom interaction system.
A teacher stands in front of a projected display and drives it entirely with
hand gestures and voice:

    PROJECTOR + COMPUTER + WEBCAM   (no touchscreen required)

Core pipeline:

    Camera -> Hand Tracking -> Gesture Engine -> Context Engine
             -> Classroom Intent -> Safety Gate -> Computer Control

The package reuses the hardened low-level infrastructure from
``hadj_no_touch`` (camera, MediaPipe hand tracking, gesture engine, speech
recognition, Win32 mouse/keyboard) and adds the classroom-specific layer:
presentation control, interactive pointer, air annotation, voice quizzes,
projector calibration, accessibility and a classroom HUD.

Two operating modes are provided:
  * real mode  — gestures & voice drive the real computer (after the safety
                 gate approves each action);
  * demo mode  — a fully simulated classroom: synthetic hands, a scripted
                 voice sequence and a virtual slide deck. Nothing touches
                 the OS. Safe for training, tests and showcases.

All classroom actions must be registered in the approved-action catalogue
(see ``edu_air.safety``). Unknown actions are denied by default — natural
language can never execute arbitrary computer commands.
"""

from __future__ import annotations

__version__ = "1.0.0"
APP_NAME = "EDU-AIR"
APP_TAGLINE = "Contactless Interactive Classroom"
MIN_PYTHON = (3, 10)