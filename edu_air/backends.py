"""OS backend abstraction for ``ClassroomSession``.

The classroom session never calls Win32 directly -- every OS action (key,
wheel, cursor move, click) goes through one of these three interchangeable
backends: the real one (HADJ Win32), the demo one (forgets every request,
so demo mode can never touch the OS by construction), and the recording one
(tests / the report). Extracted out of ``classroom.py`` as a standalone,
dependency-light module so it can be read and reasoned about on its own.
"""

from __future__ import annotations


class ClassroomBackend:
    """Thin seam over the computer the classroom controls."""

    def key(self, name: str, modifiers: list[str] | None = None) -> None:
        raise NotImplementedError

    def wheel(self, amount: int) -> None:
        raise NotImplementedError

    def move_cursor(self, x: int, y: int) -> None:
        raise NotImplementedError

    def click_left(self, x: int | None = None, y: int | None = None) -> None:
        raise NotImplementedError

    def click_right(self, x: int | None = None, y: int | None = None) -> None:
        raise NotImplementedError


class RealBackend(ClassroomBackend):
    def __init__(self) -> None:
        from hadj_no_touch.windows import keyboard_control, mouse_control
        self._kc = keyboard_control
        self._mc = mouse_control

    def key(self, name, modifiers=None):
        self._kc.tap(name, modifiers)

    def wheel(self, amount):
        self._mc.scroll(amount)

    def move_cursor(self, x, y):
        self._mc.move_to(int(x), int(y))

    def click_left(self, x=None, y=None):
        self._mc.click_left(x, y)

    def click_right(self, x=None, y=None):
        self._mc.click_right(x, y)


class DemoBackend(ClassroomBackend):
    """Forgets every request — demo mode never touches the OS."""

    def key(self, name, modifiers=None):
        pass

    def wheel(self, amount):
        pass

    def move_cursor(self, x, y):
        pass

    def click_left(self, x=None, y=None):
        pass

    def click_right(self, x=None, y=None):
        pass


class RecordingBackend(ClassroomBackend):
    """Records every request for tests / the report."""

    def __init__(self) -> None:
        self.keys: list[tuple[str, list]] = []
        self.wheels: list[int] = []
        self.cursor_moves: list[tuple[int, int]] = []
        self.left_clicks: list[tuple[int, int]] = []
        self.right_clicks: list[tuple[int, int]] = []

    def key(self, name, modifiers=None):
        self.keys.append((name, list(modifiers or [])))

    def wheel(self, amount):
        self.wheels.append(amount)

    def move_cursor(self, x, y):
        self.cursor_moves.append((int(x), int(y)))

    def click_left(self, x=None, y=None):
        self.left_clicks.append((int(x) if x is not None else None,
                                 int(y) if y is not None else None))

    def click_right(self, x=None, y=None):
        self.right_clicks.append((int(x) if x is not None else None,
                                  int(y) if y is not None else None))

    @property
    def key_sequence(self) -> list[str]:
        return [name for name, _ in self.keys]
