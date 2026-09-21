"""Big-target toolbar projected on the wall in touch mode.

The whole point of wall mode is that the teacher never has to walk back to
the PC. Without an on-wall toolbar, switching tools or advancing a slide
still meant reaching for the keyboard or the control dock -- this module is
the fix: four large buttons (thumb-sized, no precision required) rendered
along the bottom of the projected surface by ``edu_air.overlay`` and
hit-tested here, in ``ClassroomSession.handle_touch_event``
(``classroom.py``), against the exact same rectangles.

Pure geometry, no Qt -- one source of truth shared by the painter and the
touch router so they can never disagree about where a button lives.

Each button fires an already-registered, already-safe classroom action
(see ``edu_air.safety``) through the normal ``ClassroomSession.execute()``
path -- the toolbar is a shortcut onto the existing action catalogue, never
a new capability or a way around the safety gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import intent as ci

Rect = tuple[float, float, float, float]  # x0, y0, x1, y1, normalized [0..1]


@dataclass(frozen=True)
class WallToolbarButton:
    action: str
    label_key: str
    rect: Rect


# A row of four big buttons along the bottom edge -- each spans ~20% of the
# width with generous margins/gaps, easy to hit without precision aiming.
_COUNT = 4
_MARGIN = 0.04
_GAP = 0.02
_BTN_W = (1.0 - 2 * _MARGIN - (_COUNT - 1) * _GAP) / _COUNT
_Y0 = 0.89
_Y1 = 0.99


def _rect(index: int) -> Rect:
    x0 = _MARGIN + index * (_BTN_W + _GAP)
    return (x0, _Y0, x0 + _BTN_W, _Y1)


# Labels reuse existing i18n keys (btn.next_slide / tool.draw / tool.erase /
# btn.board_add) rather than duplicating translated strings for the same
# concepts under new keys.
WALL_TOOLBAR_BUTTONS: list[WallToolbarButton] = [
    WallToolbarButton(ci.NEXT_SLIDE, "btn.next_slide", _rect(0)),
    WallToolbarButton(ci.ANNOTATION_DRAW, "tool.draw", _rect(1)),
    WallToolbarButton(ci.ANNOTATION_ERASE, "tool.erase", _rect(2)),
    WallToolbarButton(ci.BOARD_ADD_PAGE, "btn.board_add", _rect(3)),
]


def hit_test(pos_norm: tuple[float, float]) -> Optional[str]:
    """The action of the toolbar button containing ``pos_norm``, or None
    when the touch lands elsewhere on the board (a normal ink stroke)."""
    x, y = pos_norm
    for btn in WALL_TOOLBAR_BUTTONS:
        x0, y0, x1, y1 = btn.rect
        if x0 <= x <= x1 and y0 <= y <= y1:
            return btn.action
    return None
