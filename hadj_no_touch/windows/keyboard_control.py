"""Real Windows keyboard control (keybd_event / key codes + Unicode SendInput)."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import time

from ..logging_setup import get_logger

log = get_logger("windows.keyboard")

user32 = ctypes.windll.user32

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_EXTENDEDKEY = 0x0001

VK = {
    "BACK": 0x08, "BACKSPACE": 0x08, "BS": 0x08,
    "TAB": 0x09, "CLEAR": 0x0C,
    "ENTER": 0x0D, "RETURN": 0x0D,
    "SHIFT": 0x10, "LSHIFT": 0xA0, "RSHIFT": 0xA1,
    "CTRL": 0x11, "CONTROL": 0x11, "LCTRL": 0xA2, "RCTRL": 0xA3,
    "ALT": 0x12, "OPTION": 0x12, "LALT": 0xA4, "RALT": 0xA5, "ALTGR": 0xA5,
    "ESC": 0x1B, "ESCAPE": 0x1B,
    "SPACE": 0x20,
    "PAGEUP": 0x21, "PGUP": 0x21, "PAGE_UP": 0x21, "PRIOR": 0x21,
    "PAGEDOWN": 0x22, "PGDN": 0x22, "PGDOWN": 0x22, "PAGE_DOWN": 0x22, "NEXT": 0x22,
    "END": 0x23, "HOME": 0x24,
    "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28,
    "PRINTSCREEN": 0x2C, "PRTSCN": 0x2C,
    "INSERT": 0x2D, "INS": 0x2D,
    "DELETE": 0x2E, "DEL": 0x2E,
    "WIN": 0x5B, "LWIN": 0x5B, "RWIN": 0x5C, "CMD": 0x5B, "COMMAND": 0x5B, "SUPER": 0x5B, "MENU": 0x5D,
    "CAPSLOCK": 0x14, "NUMLOCK": 0x90, "SCROLLLOCK": 0x91,
    "PAUSE": 0x13, "BREAK": 0x13,
    "BACKSLASH": 0xDC, "\\": 0xDC,
    "SLASH": 0xBF, "/": 0xBF,
    "SEMICOLON": 0xBA, ";": 0xBA,
    "QUOTE": 0xDE, "'": 0xDE,
    "COMMA": 0xBC, ",": 0xBC,
    "PERIOD": 0xBE, ".": 0xBE,
    "MINUS": 0xBD, "-": 0xBD, "_": 0xBD,
    "EQUAL": 0xBB, "=": 0xBB, "+": 0xBB,
    "TILDE": 0xC0, "`": 0xC0, "~": 0xC0,
    "OPENBRACKET": 0xDB, "[": 0xDB, "{": 0xDB,
    "CLOSEBRACKET": 0xDD, "]": 0xDD, "}": 0xDD,
}

for _i in range(1, 25):
    VK[f"F{_i}"] = 0x70 + (_i - 1)


def _vk(name: str) -> int:
    if name in VK:
        return VK[name]
    n = name.upper().replace(" ", "").replace("_", "")
    if n in VK:
        return VK[n]
    if len(n) == 1 and n.isalpha():
        return ord(n.upper())
    if len(n) == 1 and n.isdigit():
        return ord(n)
    if len(n) == 1:
        return ord(n)
    log.warning("Unknown key name: %r", name)
    return 0


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wt.WORD),
        ("wScan", wt.WORD),
        ("dwFlags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wt.LONG),
        ("dy", wt.LONG),
        ("mouseData", wt.DWORD),
        ("dwFlags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wt.DWORD),
        ("wParamL", wt.WORD),
        ("wParamH", wt.WORD),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", _KEYBDINPUT),
        ("mi", _MOUSEINPUT),
        ("hi", _HARDWAREINPUT),
    ]

class _INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wt.DWORD),
        ("ii", _INPUT_UNION),
    ]

try:
    user32.keybd_event.argtypes = [wt.BYTE, wt.BYTE, wt.DWORD, ctypes.c_size_t]
    user32.keybd_event.restype = None
    user32.MapVirtualKeyW.argtypes = [wt.UINT, wt.UINT]
    user32.MapVirtualKeyW.restype = wt.UINT
    user32.SendInput.argtypes = [wt.UINT, ctypes.POINTER(_INPUT), ctypes.c_int]
    user32.SendInput.restype = wt.UINT
except Exception:
    pass


def _send_key(vk: int, up: bool, scan: int = 0, is_unicode: bool = False, extended: bool = False) -> None:
    if scan == 0 and not is_unicode and vk:
        try:
            scan = user32.MapVirtualKeyW(vk & 0xFFFF, 0)
        except Exception:
            scan = 0

    flags = 0
    if up:
        flags |= KEYEVENTF_KEYUP
    if is_unicode:
        flags |= KEYEVENTF_UNICODE
    # Extended keys: arrows, page up/down, home, end, insert, delete, windows key
    if extended or vk in (0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0x5B, 0x5C):
        flags |= KEYEVENTF_EXTENDEDKEY

    # 1. Try SendInput with full 64-bit union structure
    try:
        inp = _INPUT()
        inp.type = 1
        inp.ii.ki.wVk = vk & 0xFFFF
        inp.ii.ki.wScan = scan & 0xFFFF
        inp.ii.ki.dwFlags = flags
        inp.ii.ki.time = 0
        inp.ii.ki.dwExtraInfo = 0
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))
    except Exception:
        pass

    # 2. Universal keybd_event fallback with hardware scan code
    try:
        user32.keybd_event(vk & 0xFF, scan & 0xFF, flags, 0)
    except Exception:
        pass


def tap(name: str, modifiers: list[str] | None = None, repeat: int = 1) -> None:
    vk = _vk(name)
    if not vk:
        log.warning("Cannot tap unknown key: %r", name)
        return
    mods = [("LCTRL" if m.upper() in ("CTRL", "CONTROL") else m.upper()) for m in (modifiers or [])]
    mod_vks = []
    for m in mods:
        mvk = _vk(m)
        if mvk:
            _send_key(mvk, False, extended=(m == "WIN"))
            mod_vks.append((m, mvk))
    for _ in range(max(1, repeat)):
        _send_key(vk, False)
        time.sleep(0.035)
        _send_key(vk, True)
        time.sleep(0.020)
    for m, mvk in reversed(mod_vks):
        _send_key(mvk, True, extended=(m == "WIN"))


def press(name: str, hold_ms: int = 500) -> None:
    vk = _vk(name)
    if not vk:
        log.warning("Cannot press unknown key: %r", name)
        return
    _send_key(vk, False)
    time.sleep(hold_ms / 1000.0)
    _send_key(vk, True)


def type_text(text: str) -> None:
    """Type arbitrary text (Unicode) by sending KEYEVENTF_UNICODE events."""
    for ch in text:
        code = ord(ch)
        _send_key(0, False, scan=code, is_unicode=True)
        _send_key(0, True, scan=code, is_unicode=True)


def hotkey(*names: str) -> None:
    name = names[-1]
    mods = list(names[:-1])
    tap(name, mods)