"""wall_toolbar.hit_test(): pure geometry, the single source of truth the
overlay painter and the touch router (ClassroomSession.handle_touch_event)
both read so they can never disagree about where a button lives."""

from __future__ import annotations

from edu_air import intent as ci
from edu_air.wall_toolbar import WALL_TOOLBAR_BUTTONS, hit_test


def test_center_of_the_board_is_not_a_toolbar_button():
    assert hit_test((0.5, 0.5)) is None


def test_a_point_inside_each_button_hits_its_own_action():
    for btn in WALL_TOOLBAR_BUTTONS:
        x0, y0, x1, y1 = btn.rect
        center = ((x0 + x1) / 2, (y0 + y1) / 2)
        assert hit_test(center) == btn.action


def test_buttons_cover_next_draw_erase_and_new_page():
    actions = {btn.action for btn in WALL_TOOLBAR_BUTTONS}
    assert actions == {ci.NEXT_SLIDE, ci.ANNOTATION_DRAW,
                       ci.ANNOTATION_ERASE, ci.BOARD_ADD_PAGE}


def test_buttons_are_all_in_a_bottom_strip_and_never_overlap():
    for btn in WALL_TOOLBAR_BUTTONS:
        x0, y0, x1, y1 = btn.rect
        assert 0.0 <= x0 < x1 <= 1.0
        assert 0.8 <= y0 < y1 <= 1.0  # bottom strip, out of the way of ink
    for i, a in enumerate(WALL_TOOLBAR_BUTTONS):
        for b in WALL_TOOLBAR_BUTTONS[i + 1:]:
            ax0, _, ax1, _ = a.rect
            bx0, _, bx1, _ = b.rect
            assert ax1 <= bx0 or bx1 <= ax0  # no horizontal overlap


def test_a_point_just_above_the_toolbar_strip_is_not_a_button():
    x0, y0, _, _ = WALL_TOOLBAR_BUTTONS[0].rect
    assert hit_test((x0 + 0.01, y0 - 0.05)) is None
