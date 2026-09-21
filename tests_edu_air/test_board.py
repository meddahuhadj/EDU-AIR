"""Multi-page interactive whiteboard (TNI) — model + classroom wiring."""

from __future__ import annotations

import pytest

from hadj_no_touch.gestures import gesture_engine as ge

from edu_air.board import (
    BG_BLANK, BG_GRID, BG_LINES, WhiteboardModel, background_lines,
    validate_background,
)
from edu_air.classroom import ClassroomSession, RecordingBackend
from edu_air.config import BoardSettings, PresentationSettings
from edu_air import intent as ci
from edu_air import voice as cvoice
from edu_air.presentation import PresentationController, RecordingDriver
from edu_air.demo import DemoSession, board_script


def make_session(mode: str = "demo") -> tuple[ClassroomSession, RecordingBackend]:
    backend = RecordingBackend()
    pres = PresentationController(driver=RecordingDriver(),
                                  settings=PresentationSettings())
    sess = ClassroomSession(backend=backend, presentation=pres)
    sess.set_mode(mode)
    return sess, backend


def make_board() -> WhiteboardModel:
    return WhiteboardModel(BoardSettings())


def filled_board() -> tuple[WhiteboardModel, int]:
    """A board with one stroke on page 1; page 2 stays blank."""
    board = WhiteboardModel(BoardSettings())
    board.annotation.set_tool("draw")
    board.annotation.begin((0.1, 0.1))
    board.annotation.move((0.2, 0.2))
    board.annotation.finish()
    page1_strokes = board.annotation.count
    board.add_page()
    return board, page1_strokes


# ---------------------------------------------------------------------------
# Model: pages / backgrounds.
# ---------------------------------------------------------------------------
def test_board_starts_single_blank_page():
    board = WhiteboardModel(BoardSettings())
    assert board.page_count == 1
    assert board.current_index == 0
    assert board.current.background == BG_BLANK
    # the annotation surface works like the legacy model
    board.annotation.set_tool("draw")
    board.annotation.begin((0.5, 0.5))
    board.annotation.finish()
    assert board.annotation.count == 1


def test_add_page_focuses_new_empty_ink():
    board, page1_strokes = filled_board()
    assert board.page_count == 2
    assert board.current_index == 1
    assert board.annotation.count == 0          # new page, fresh ink
    assert board.pages[0].model.count == page1_strokes


def test_pages_keep_independent_ink():
    board, page1_strokes = filled_board()
    board.goto(0)
    assert board.annotation.count == page1_strokes
    board.goto(1)
    assert board.annotation.count == 0


def test_navigation_prev_clamps_at_first_page():
    board = WhiteboardModel(BoardSettings())
    assert board.prev_page() is False            # cannot go before page 1
    # "next page" on the last page creates a fresh blank sheet
    assert board.next_page() is True
    assert board.current_index == 1
    assert board.page_count == 2
    assert board.next_page() is True
    assert board.current_index == 2
    assert board.page_count == 3
    assert board.prev_page() is True
    assert board.current_index == 1


def test_goto_clamps_and_ignores_same_page():
    board = WhiteboardModel(BoardSettings())
    board.add_page()
    assert board.goto(-5) is False
    assert board.current_index == 1
    assert board.goto(99) is False
    assert board.current_index == 1
    assert board.goto(1) is False
    assert board.goto(0) is True


def test_delete_never_removes_the_last_page():
    board = WhiteboardModel(BoardSettings())
    assert board.delete_page() is False
    assert board.page_count == 1


def test_delete_adjusts_current_index():
    board = filled_board()[0]
    assert board.page_count == 2
    assert board.delete_page() is True
    assert board.page_count == 1
    assert board.current_index == 0
    with pytest.raises(IndexError):
        _ = board.pages[1]


def test_set_background_validates_unknown_name():
    board = WhiteboardModel(BoardSettings())
    assert board.set_background(BG_GRID) is True
    assert board.current.background == BG_GRID
    assert board.set_background("flaming-gridzzz") is True   # falls back to blank
    assert board.current.background == BG_BLANK


# ---------------------------------------------------------------------------
# Model: undo / clear / geometry.
# ---------------------------------------------------------------------------
def test_undo_removes_only_the_last_stroke_of_current_page():
    board = WhiteboardModel(BoardSettings())
    board.annotation.set_tool("draw")
    for _ in range(3):
        board.annotation.begin((0.5, 0.5))
        board.annotation.finish()
    assert board.annotation.count == 3
    assert board.undo() is not None
    assert board.annotation.count == 2
    board.add_page()
    assert board.undo() is None               # empty page: nothing to undo
    with pytest.raises(IndexError):
        _ = board.pages[0].model.strokes[2]


def test_clear_current_only_touches_the_current_page():
    board, page1_strokes = filled_board()
    assert board.clear_current() == 0
    assert board.annotation.count == 0
    assert board.pages[0].model.count == page1_strokes


def test_background_geometry_shape():
    assert background_lines(BG_BLANK, 100, 100, 0.1) == []
    assert background_lines(BG_GRID, 100, 100, 0.0) == []
    grid = background_lines(BG_GRID, 100, 100, 0.1)
    assert len(grid) > 2
    line = background_lines(BG_LINES, 100, 100, 0.2)
    assert len(line) == 4
    assert all(x1 == 0 and x2 == 100 for (x1, y1, x2, y2) in line)


def test_serialization_roundtrip():
    board = filled_board()[0]
    board.set_background(BG_GRID)
    clone = WhiteboardModel(BoardSettings())
    clone.load_dict(board.as_dict())
    assert clone.page_count == board.page_count
    assert clone.current_index == board.current_index
    for a, b in zip(clone.pages, board.pages):
        assert a.background == b.background
        assert a.model.count == b.model.count


# ---------------------------------------------------------------------------
# Classroom integration.
# ---------------------------------------------------------------------------
def test_session_annotation_forwards_to_current_board_page():
    sess, _ = make_session()
    sess.annotation.set_tool("draw")
    sess.annotation.begin((0.5, 0.5))
    sess.annotation.finish()
    assert sess.board.annotation.count == 1
    sess.handle_gesture(ge.GestureEvent(kind=ge.DRAG_START, x=0.5, y=0.5))
    sess.handle_gesture(ge.GestureEvent(kind=ge.DRAG_UPDATE, x=0.6, y=0.5))
    sess.handle_gesture(ge.GestureEvent(kind=ge.DRAG_END, x=0.6, y=0.5))
    assert sess.annotation.count == 2
    assert sess.status.stroke_count == 2
    assert sess.status.board_page == 1
    assert sess.status.board_pages == 1


def test_session_board_execute_updates_status():
    sess, _ = make_session()
    assert sess.status.board_page == 1
    sess.execute(ci.ClassroomIntent(ci.BOARD_NEXT_PAGE, source="ui"))
    assert sess.board.current_index == 1
    assert sess.status.board_page == 2
    assert sess.status.board_pages == 2
    assert sess.status.last_command == ci.BOARD_NEXT_PAGE


def test_session_swipe_in_board_domain_navigates_pages_not_slides():
    sess, _ = make_session("demo")
    sess.execute(ci.ClassroomIntent(ci.BOARD_ADD_PAGE, source="ui"))
    sess.handle_gesture(ge.GestureEvent(kind=ge.SWIPE_LEFT, x=0.5, y=0.5,
                                        confidence=0.9))
    assert sess.board.current_index == 2          # 0 -> 1 (add) -> 2 (swipe)
    assert sess.presentation.state == "idle"      # never started a real deck
    # once a real deck is started, slide navigation takes back over
    sess.execute(ci.ClassroomIntent(ci.PRESENTATION_START, source="ui"))
    sess.handle_gesture(ge.GestureEvent(kind=ge.SWIPE_LEFT, x=0.5, y=0.5,
                                        confidence=0.9))
    assert sess.presentation.active
    assert sess.status.current_slide == 2
    assert sess.board.current_index == 2


def test_session_undo_and_delete_through_execute():
    sess, _ = make_session("demo")
    sess.annotation.set_tool("draw")
    sess.annotation.begin((0.5, 0.5))
    sess.annotation.finish()
    sess.execute(ci.ClassroomIntent(ci.BOARD_UNDO, source="ui"))
    assert sess.board.annotation.count == 0
    sess.execute(ci.ClassroomIntent(ci.BOARD_ADD_PAGE, source="ui"))
    assert sess.board.page_count == 2
    sess.execute(ci.ClassroomIntent(ci.BOARD_NEXT_PAGE, source="ui"))
    assert sess.board.current_index == 2
    assert sess.board.annotation.count == 0
    sess.execute(ci.ClassroomIntent(ci.BOARD_DELETE_PAGE, source="ui"))
    assert sess.board.page_count == 2             # the fresh sheet removed
    assert sess.board.current_index == 1
    assert sess.status.board_page == 2


# ---------------------------------------------------------------------------
# Voice.
# ---------------------------------------------------------------------------
def test_voice_board_page_commands_map():
    r = cvoice.parse("new page", "en")
    assert r.intent == cvoice.BOARD_ADD_PAGE
    r2 = cvoice.parse("next board page", "en")
    assert r2.intent == cvoice.BOARD_NEXT_PAGE
    r3 = cvoice.parse("nouvelle page", "fr")
    assert r3.intent == cvoice.BOARD_ADD_PAGE
    r4 = cvoice.parse("grid background", "en")
    assert r4.intent == cvoice.BOARD_BACKGROUND


def test_voice_navigation_advances_board_pages_in_board_domain():
    sess, _ = make_session("demo")
    sess.execute(ci.ClassroomIntent(ci.BOARD_ADD_PAGE, source="ui"))
    assert sess.board.current_index == 1
    # generic navigation lands on the board pages while the board has focus
    sess.handle_voice_text("précédente", "fr")
    assert sess.board.current_index == 0
    sess.handle_voice_text("suivant", "fr")
    assert sess.board.current_index == 1
    sess.handle_voice_text("الصفحة التالية", "ar")
    assert sess.board.current_index == 2


def test_voice_board_background_picks_the_skin():
    sess, _ = make_session("demo")
    sess.set_language("en")
    d = sess.handle_voice_text("grid background")
    assert d is not None and d.action == ci.BOARD_BACKGROUND
    assert sess.board.current.background == BG_GRID
    d2 = sess.handle_voice_text("ruled lines")
    assert sess.board.current.background == BG_LINES
    d3 = sess.handle_voice_text("blank page")
    assert sess.board.current.background == BG_BLANK


def test_route_swaps_generic_nav_only_in_board_domain():
    e = ci.ClassroomIntentEngine(language="en")
    i = e.from_voice(cvoice.parse("next slide", "en"))
    assert i is not None and i.action == ci.NEXT_SLIDE
    assert e.route(i, quiz_active=False) is not None
    board_routed = e.route(i, quiz_active=False, domain="board",
                           presentation_active=False)
    assert board_routed is not None
    assert board_routed.action == ci.BOARD_NEXT_PAGE
    # real deck running: slide nav stays slide nav
    deck_routed = e.route(i, quiz_active=False, domain="board",
                          presentation_active=True)
    assert deck_routed is not None
    assert deck_routed.action == ci.NEXT_SLIDE


def test_board_action_blocked_during_quiz_but_pointer_allowed():
    e = ci.ClassroomIntentEngine(language="en")
    add_page = e.from_voice(cvoice.parse("new page", "en"))
    assert e.route(add_page, quiz_active=True) is None
    ptr = e.from_voice(cvoice.parse("show the pointer", "en"))
    assert e.route(ptr, quiz_active=True) is not None


# ---------------------------------------------------------------------------
# Scripted TNI demo.
# ---------------------------------------------------------------------------
def assert_board_demo_end_state(sess):
    assert sess.board.page_count == 2
    assert sess.board.current_index == 1
    assert sess.board.pages[0].model.count == 1          # ink kept on page 1
    assert sess.board.pages[1].model.count == 1          # re-drawn page 2
    assert sess.board.pages[1].background == BG_GRID
    assert sess.status.board_page == 2
    assert sess.status.board_pages == 2
    assert sess.status.board_background == BG_GRID
    assert sess.pending_count == 0                        # demo auto-approves
    assert sess.domain == "board"


@pytest.mark.parametrize("lang", ["en", "fr"])
def test_tni_demo_script_runs_end_to_end(lang):
    sess, _ = make_session("demo")
    DemoSession(sess, board_script(lang), lang).run_all()
    assert_board_demo_end_state(sess)


# ---------------------------------------------------------------------------
# Notebook persistence.
# ---------------------------------------------------------------------------
def test_save_load_roundtrip(tmp_path):
    board, _ = filled_board()
    board.set_background(BG_GRID)
    board.add_page()
    board.annotation.set_tool("draw")
    board.annotation.begin((0.1, 0.2))
    board.annotation.move((0.5, 0.6))
    board.annotation.finish()
    path = board.save_nb(tmp_path / "nb.json")
    assert path.is_file()

    fresh = make_board()
    assert fresh.load_nb(path) is True
    assert fresh.page_count == board.page_count
    assert fresh.current_index == board.current_index
    assert [p.background for p in fresh.pages] == ["blank", BG_GRID, "blank"]
    assert fresh.pages[2].model.count == 1
    assert len(fresh.pages[0].model.strokes[0].points) == 2


def test_save_load_roundtrip_unicode(tmp_path):
    board = make_board()
    board.set_background(BG_LINES)
    path = board.save_nb(tmp_path / "carnet" / "leçon.json")
    fresh = make_board()
    assert fresh.load_nb(path)
    assert fresh.pages[0].background == BG_LINES


def test_load_nb_missing_file_returns_false(tmp_path):
    assert make_board().load_nb(tmp_path / "absent.json") is False


def test_load_nb_corrupt_file_is_ignored(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{not json", encoding="utf-8")
    assert make_board().load_nb(p) is False


def test_load_nb_with_a_non_numeric_stroke_width_does_not_crash(tmp_path):
    """Syntactically valid JSON with a malformed field (e.g. a hand-edited
    stroke width that isn't a number) must not crash the app -- and the
    board being loaded into must be left exactly as it was before."""
    p = tmp_path / "typo.json"
    p.write_text(
        '{"pages": [{"background": "blank", "strokes": '
        '[{"tool": "draw", "width": "thick", "points": [[0.1, 0.1]]}]}]}',
        encoding="utf-8")
    board = make_board()
    board.set_background(BG_GRID)
    assert board.load_nb(p) is False
    assert board.current.background == BG_GRID
    assert board.page_count == 1


# ---------------------------------------------------------------------------
# Safety.
# ---------------------------------------------------------------------------
def test_safety_board_actions_registered():
    registry = sess_registry()
    for action in (ci.BOARD_NEXT_PAGE, ci.BOARD_PREV_PAGE, ci.BOARD_ADD_PAGE,
                   ci.BOARD_CLEAR_PAGE, ci.BOARD_DELETE_PAGE,
                   ci.BOARD_BACKGROUND, ci.BOARD_UNDO):
        assert registry.known(action), action


def sess_registry():
    from edu_air.safety import ClassroomActionRegistry
    return ClassroomActionRegistry()


def test_delete_page_requires_confirmation_in_real_mode():
    from edu_air.safety import ClassroomActionRegistry, ClassroomSafetyEngine
    eng = ClassroomSafetyEngine(registry=ClassroomActionRegistry(),
                                confirmation_level="smart")
    d = eng.decide(ci.BOARD_DELETE_PAGE)
    assert d.requires_confirmation
    d2 = eng.decide(ci.BOARD_NEXT_PAGE)
    assert not d2.requires_confirmation


def test_delete_page_pending_flow_in_session():
    sess, _ = make_session("real")
    sess.auto_approve = False
    sess.execute(ci.ClassroomIntent(ci.BOARD_ADD_PAGE, source="ui"))
    d = sess.execute(ci.ClassroomIntent(ci.BOARD_DELETE_PAGE, source="ui"))
    assert d.requires_confirmation
    assert sess.pending_count == 1
    assert sess.board.page_count == 2
    sess.approve_pending()
    assert sess.board.page_count == 1