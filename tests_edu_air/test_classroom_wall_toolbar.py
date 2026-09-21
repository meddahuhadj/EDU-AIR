"""Wall toolbar wired into ClassroomSession.handle_touch_event: a DOWN
inside a toolbar button fires its action instead of ink, and the rest of
that same physical touch (MOVE/UP) is swallowed so dragging off the
toolbar can never be misread as a stroke."""

from __future__ import annotations

from edu_air.classroom import ClassroomSession, RecordingBackend, MODE_WALL
from edu_air import intent as ci
from edu_air.config import PresentationSettings
from edu_air.presentation import PresentationController, RecordingDriver
from edu_air.touch.events import TouchEvent, TouchState
from edu_air.wall_toolbar import WALL_TOOLBAR_BUTTONS

NEXT_BTN = WALL_TOOLBAR_BUTTONS[0]
DRAW_BTN = WALL_TOOLBAR_BUTTONS[1]
ERASE_BTN = WALL_TOOLBAR_BUTTONS[2]
NEW_PAGE_BTN = WALL_TOOLBAR_BUTTONS[3]


def make_session(mode: str = "demo") -> ClassroomSession:
    backend = RecordingBackend()
    pres = PresentationController(driver=RecordingDriver(), settings=PresentationSettings())
    sess = ClassroomSession(backend=backend, presentation=pres)
    sess.set_mode(mode)
    sess.execute(ci.ClassroomIntent(ci.TOGGLE_WALL_MODE, source="test"))
    assert sess.interaction_mode == MODE_WALL
    return sess


def _center(rect):
    x0, y0, x1, y1 = rect
    return ((x0 + x1) / 2, (y0 + y1) / 2)


def test_tapping_next_advances_the_board_page_not_ink():
    sess = make_session("real")
    sess.domain = "board"
    start_page = sess.board.current_index
    decision = sess.handle_touch_event(
        TouchEvent(x=_center(NEXT_BTN.rect)[0], y=_center(NEXT_BTN.rect)[1],
                   state=TouchState.DOWN))
    assert decision is not None and decision.allowed
    assert sess.board.current_index == start_page + 1
    assert sess.annotation.count == 0


def test_tapping_draw_selects_the_pen_tool():
    sess = make_session("real")
    sess.annotation.set_tool("erase")
    sess.handle_touch_event(TouchEvent(x=_center(DRAW_BTN.rect)[0],
                                       y=_center(DRAW_BTN.rect)[1],
                                       state=TouchState.DOWN))
    assert sess.annotation.tool == "draw"
    assert sess.annotation.count == 0


def test_tapping_erase_selects_the_erase_tool():
    sess = make_session("real")
    sess.annotation.set_tool("draw")
    sess.handle_touch_event(TouchEvent(x=_center(ERASE_BTN.rect)[0],
                                       y=_center(ERASE_BTN.rect)[1],
                                       state=TouchState.DOWN))
    assert sess.annotation.tool == "erase"


def test_tapping_new_page_adds_a_board_page():
    sess = make_session("real")
    start_count = sess.board.page_count
    sess.handle_touch_event(TouchEvent(x=_center(NEW_PAGE_BTN.rect)[0],
                                       y=_center(NEW_PAGE_BTN.rect)[1],
                                       state=TouchState.DOWN))
    assert sess.board.page_count == start_count + 1


def test_move_and_up_after_a_toolbar_tap_never_draw_even_if_tool_is_draw():
    """The finger stays down after tapping "Draw" and slides onto the
    board before lifting -- that drag must not start a stroke; only the
    *next* fresh DOWN should."""
    sess = make_session("real")
    sess.annotation.set_tool("erase")  # so a leaked MOVE would visibly erase/draw
    cx, cy = _center(DRAW_BTN.rect)
    sess.handle_touch_event(TouchEvent(x=cx, y=cy, state=TouchState.DOWN))
    assert sess.annotation.tool == "draw"

    sess.handle_touch_event(TouchEvent(x=0.5, y=0.5, state=TouchState.MOVE))
    assert sess.annotation.count == 0
    assert not sess.annotation.drawing

    sess.handle_touch_event(TouchEvent(x=0.5, y=0.5, state=TouchState.UP))
    assert sess.annotation.count == 0


def test_a_fresh_down_after_a_toolbar_tap_draws_normally():
    sess = make_session("real")
    cx, cy = _center(DRAW_BTN.rect)
    sess.handle_touch_event(TouchEvent(x=cx, y=cy, state=TouchState.DOWN))
    sess.handle_touch_event(TouchEvent(x=cx, y=cy, state=TouchState.UP))

    sess.handle_touch_event(TouchEvent(x=0.3, y=0.3, state=TouchState.DOWN))
    sess.handle_touch_event(TouchEvent(x=0.4, y=0.4, state=TouchState.MOVE))
    sess.handle_touch_event(TouchEvent(x=0.4, y=0.4, state=TouchState.UP))
    assert sess.annotation.count == 1
    assert sess.annotation.strokes[0].points == [(0.3, 0.3), (0.4, 0.4)]


def test_drawing_on_the_board_away_from_the_toolbar_is_unaffected():
    sess = make_session("real")
    sess.annotation.set_tool("draw")
    sess.handle_touch_event(TouchEvent(x=0.5, y=0.5, state=TouchState.DOWN))
    sess.handle_touch_event(TouchEvent(x=0.5, y=0.5, state=TouchState.UP))
    assert sess.annotation.count == 1


def test_toolbar_action_is_safety_gated_like_any_other_action():
    """Toolbar taps go through the normal execute() safety gate, not a
    shortcut around it -- at the default ("smart") confirmation level a
    SAFE-risk action like ANNOTATION_DRAW runs immediately."""
    sess = make_session("real")
    cx, cy = _center(DRAW_BTN.rect)
    decision = sess.handle_touch_event(TouchEvent(x=cx, y=cy, state=TouchState.DOWN))
    assert decision.allowed
    assert not decision.requires_confirmation

    # ...but a stricter operator-chosen level still applies, same as a
    # touch on the dock button would -- the toolbar never bypasses it.
    sess.safety.set_confirmation_level("all")
    sess.handle_touch_event(TouchEvent(x=cx, y=cy, state=TouchState.UP))
    decision2 = sess.handle_touch_event(TouchEvent(x=cx, y=cy, state=TouchState.DOWN))
    assert decision2.allowed
    assert decision2.requires_confirmation
