"""Multi-page interactive whiteboard (TNI mode) — pure geometry, no Qt.

The wall/contactless layers draw into a single ``AnnotationModel``. This
module lifts that into a real digital whiteboard: an unlimited series of
pages, each carrying its own ink and a background (blank / grid / ruled
lines), plus page navigation, per-page undo and whole-board export helpers.

Model-only by construction so the exact same state machine is exercised by
the classroom session, the demo runner and the unit tests. The PySide6
overlay (``edu_air.ui``) only ever talks to :class:`WhiteboardModel` and
never stores ink itself.
"""

from __future__ import annotations

from typing import Optional

from .annotation import (AnnotationModel, Stroke, TOOL_NONE)
from .config import AnnotationSettings, BoardSettings, SETTINGS

BG_BLANK = "blank"
BG_GRID = "grid"
BG_LINES = "lines"

BACKGROUNDS = (BG_BLANK, BG_GRID, BG_LINES)


def validate_background(name: str) -> str:
    """Map an arbitrary string onto a known background (blank fallback)."""
    return name if name in BACKGROUNDS else BG_BLANK


def background_lines(name: str, w: int, h: int, step_norm: float) -> list:
    """Geometry for the board background in pixel coordinates.

    Returns a list of ``(x1, y1, x2, y2)`` straight line segments:
    a grid paints both a vertical and a horizontal set, ruled-lines paint
    only the horizontal set, blank returns ``[]``. ``step_norm`` is the
    spacing as a fraction of the board dimension.
    """
    name = validate_background(name)
    if name == BG_BLANK or step_norm <= 0:
        return []
    step = max(1.0, step_norm * max(w, h))
    lines: list = []
    if name == BG_GRID:
        x = step
        while x < w:
            lines.append((x, 0.0, x, float(h)))
            x += step
    y = step
    while y < h:
        lines.append((0.0, y, float(w), y))
        y += step
    return lines


class BoardPage:
    """One whiteboard page: its ink model plus its background skin."""

    __slots__ = ("index", "background", "model")

    def __init__(self, index: int, model: AnnotationModel,
                 background: str = BG_BLANK) -> None:
        self.index = index
        self.background = validate_background(background)
        self.model = model


class WhiteboardModel:
    """Multi-page whiteboard held by the classroom session (``session.board``).

    ``session.annotation`` stays the *current* page's ``AnnotationModel`` so
    every existing gesture/touch drawing path keeps working unchanged.
    """

    def __init__(self,
                 board_settings: BoardSettings | None = None,
                 annotation_settings: AnnotationSettings | None = None) -> None:
        self.settings = board_settings or SETTINGS.board
        self._annotation_settings = annotation_settings or SETTINGS.annotation
        self._pagelimit = max(1, int(getattr(self.settings, "max_pages", 60)))
        self._pages: list[BoardPage] = [
            BoardPage(0, AnnotationModel(self._annotation_settings),
                      background=self.settings.default_background)]
        self._current = 0
        self.tool: str = self._annotation_settings.default_tool
        self.dirty = False

    # ---- tooling (board-global: one marker set for the whole TNI) ----------
    def set_tool(self, tool: str) -> str:
        """Select the active marker for the whole whiteboard ('' invalid ->
        none). Also applies to the current page and any page visited later."""
        if tool not in ("none", "point", "draw", "highlight", "erase"):
            tool = TOOL_NONE
        self.tool = tool
        self._sync_current_tool()
        return self.tool

    def _sync_current_tool(self) -> None:
        self.current.model.tool = self.tool

    # ---- page model access ------------------------------------------------
    @property
    def pages(self) -> list[BoardPage]:
        return self._pages

    @property
    def current_index(self) -> int:
        return self._current

    @property
    def page_count(self) -> int:
        return len(self._pages)

    @property
    def current(self) -> BoardPage:
        return self._pages[self._current]

    @property
    def annotation(self) -> AnnotationModel:
        """The current page's ink model (compat with the legacy session API)."""
        model = self.current.model
        if model.tool != self.tool:
            # A legacy direct ``set_tool`` on the page model turned into the
            # board-wide selection, so the next page inherits it too.
            self.tool = model.tool
        return model

    def dirty_mark(self) -> None:
        self.dirty = True

    # ---- navigation ---------------------------------------------------------
    def goto(self, index: int) -> bool:
        """Jump to ``index`` (clamped). Returns True when a real page changed."""
        if index < 0 or index >= len(self._pages) or index == self._current:
            return False
        self._current = index
        self._sync_current_tool()
        self.dirty = True
        return True

    def next_page(self) -> bool:
        """Advance one page; on the last page a fresh blank page is created
        (natural whiteboard behaviour — swiping "next" at the end of the pad
        gives you a new sheet)."""
        if self._current + 1 < len(self._pages):
            return self.goto(self._current + 1)
        if len(self._pages) >= self._pagelimit:
            return False
        self.add_page()
        return True

    def prev_page(self) -> bool:
        return self.goto(self._current - 1)

    # ---- edition ------------------------------------------------------------
    def add_page(self, background: str | None = None, copy_current: bool = False) -> int:
        """Append a fresh page and switch to it. Returns its index."""
        if len(self._pages) >= self._pagelimit:
            return self._current
        if copy_current:
            model = AnnotationModel(self._annotation_settings)
            for s in self.current.model.strokes:
                model.strokes.append(
                    Stroke(tool=s.tool, color=s.color, width=s.width,
                           points=list(s.points), highlight=s.highlight))
        else:
            model = AnnotationModel(self._annotation_settings)
        self._pages.append(BoardPage(len(self._pages), model,
                                     background=background or self.settings.default_background))
        self._current = len(self._pages) - 1
        self._sync_current_tool()
        self.dirty = True
        return self._current

    def delete_page(self) -> bool:
        """Remove the current page. Refuses to delete the last remaining page."""
        if len(self._pages) <= 1:
            return False
        del self._pages[self._current]
        self._current = min(self._current, len(self._pages) - 1)
        self.current.index = self._current
        self._sync_current_tool()
        self.dirty = True
        return True

    def set_background(self, name: str) -> bool:
        """Change the current page's background skin (invalid -> blank)."""
        bg = validate_background(name)
        if bg == self.current.background:
            return False
        self.current.background = bg
        self.dirty = True
        return True

    def clear_current(self) -> int:
        return self.current.model.clear()

    def undo(self) -> Optional[Stroke]:
        return self.current.model.undo()

    def geometry(self, w: int, h: int) -> list[dict]:
        return self.current.model.geometry(w, h)

    # ---- persistence ---------------------------------------------------------
    def as_dict(self) -> dict:
        """Serializable snapshot (page count, backgrounds, ink coordinates)."""
        pages = []
        for pg in self._pages:
            pages.append({
                "background": pg.background,
                "strokes": [
                    {"tool": s.tool, "color": s.color, "width": s.width,
                     "highlight": s.highlight, "points": list(s.points)}
                    for s in pg.model.strokes
                ],
            })
        return {"current": self._current, "pages": pages}

    def load_dict(self, data: dict) -> None:
        """Restore a board previously saved with :meth:`as_dict`.

        Builds the new page list locally before committing it: a malformed
        field partway through a hand-edited/corrupted file must not leave
        ``self._pages`` half-replaced (the exception -- caught by
        :meth:`load_nb` -- still leaves the current board intact)."""
        data = data or {}
        pages = data.get("pages") or []
        new_pages: list[BoardPage] = []
        for i, raw in enumerate(pages):
            model = AnnotationModel(self._annotation_settings)
            for s in raw.get("strokes", []):
                model.strokes.append(
                    Stroke(tool=s.get("tool", "draw"), color=s.get("color", "#ff0000"),
                           width=float(s.get("width", 3.0)), highlight=bool(s.get("highlight", False)),
                           points=[tuple(float(v) for v in p) for p in s.get("points", [])]))
            new_pages.append(BoardPage(i, model, background=raw.get("background", "blank")))
        if not new_pages:
            new_pages.append(BoardPage(0, AnnotationModel(self._annotation_settings),
                                       background=self.settings.default_background))
        self._pages = new_pages
        cur = int(data.get("current", 0))
        self._current = min(max(0, cur), len(self._pages) - 1)
        self._sync_current_tool()
        self.dirty = True

    def save_nb(self, path) -> "Path":
        """Write the whole notebook (all pages) as JSON. Returns the path."""
        import json
        from pathlib import Path
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.as_dict(), ensure_ascii=False, indent=1),
                     encoding="utf-8")
        return p

    def load_nb(self, path) -> bool:
        """Restore a notebook saved with :meth:`save_nb`. Returns False when
        the file is missing or unreadable (the board is then left untouched)."""
        import json
        from pathlib import Path
        p = Path(path)
        if not p.is_file():
            return False
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "pages" not in data:
                return False
            self.load_dict(data)
        except (ValueError, OSError, TypeError):
            # Syntactically valid JSON with a malformed field (e.g. a
            # hand-edited stroke width that isn't a number) must not crash
            # the app -- load_dict() calls float()/int() on untrusted input.
            return False
        return True