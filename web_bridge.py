"""EDU-AIR Web Bridge — WebSocket server (port 8765).

Connects the Vercel web UI to the local EDU-AIR Python engine.
When the web page detects a gesture or voice command, it sends a JSON
message here; this server translates it into a real classroom action.

Usage (from the project root):
    py -3.12 web_bridge.py          # bridge only (no desktop window)
    py -3.12 web_bridge.py --full   # bridge + full desktop classroom window

Then open https://edu-air-smart-surface.vercel.app in the browser.
The page will auto-connect and switch the badge from DEMO to RÉEL.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import threading
import time
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [bridge] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("edu_air.bridge")

# ── Try to import websockets (pure-Python, no binary deps) ──────────────────
try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    print(
        "\n[EDU-AIR Bridge] 'websockets' package not found.\n"
        "  Install with:  py -3.12 -m pip install websockets\n",
        file=sys.stderr,
    )
    raise SystemExit(1)

# ── Import EDU-AIR classroom session ────────────────────────────────────────
try:
    from edu_air.classroom import ClassroomSession, RealBackend, DemoBackend
    from edu_air import intent as ci
    _IMPORT_OK = True
except Exception as exc:
    log.warning("EDU-AIR classroom not importable (%s) — running in echo mode.", exc)
    _IMPORT_OK = False

PORT = 8765
ALLOWED_ORIGINS = ["https://edu-air-smart-surface.vercel.app",
                   "http://localhost", "http://127.0.0.1",
                   "null"]  # allow local file:// tests too

# ── Global session (created once, reused for all connections) ───────────────
_session: ClassroomSession | None = None
_clients: set[WebSocketServerProtocol] = set()


def _get_session() -> ClassroomSession | None:
    global _session
    if _session is None and _IMPORT_OK:
        try:
            backend = RealBackend()
        except Exception:
            backend = DemoBackend()
        _session = ClassroomSession(backend=backend)
        log.info("ClassroomSession created — backend: %s", type(backend).__name__)
    return _session


# ── Action dispatcher ───────────────────────────────────────────────────────
def _dispatch(msg: dict[str, Any]) -> dict[str, Any]:
    """Translate a web message into a classroom action. Return a status dict."""
    action = msg.get("action", "").upper()
    session = _get_session()

    if session is None:
        return {"ok": False, "error": "no_session"}

    try:
        if action == "NEXT_SLIDE":
            r = session.presentation.next_slide()
        elif action == "PREV_SLIDE":
            r = session.presentation.prev_slide()
        elif action == "PRES_START":
            r = session.presentation.start(msg.get("total", 10))
        elif action == "PRES_STOP":
            r = session.presentation.stop()
        elif action == "PAUSE":
            r = session.presentation.pause()
        elif action == "SCROLL_DOWN":
            r = session.presentation.scroll_down()
        elif action == "SCROLL_UP":
            r = session.presentation.scroll_up()
        elif action == "ZOOM_IN":
            r = session.presentation.zoom_in()
        elif action == "ZOOM_OUT":
            r = session.presentation.zoom_out()
        elif action == "POINTER":
            # raw_norm from browser webcam
            raw = msg.get("raw", None)
            if raw:
                session.update_pointer(tuple(raw))
            return {"ok": True, "action": "POINTER"}
        elif action == "ANNOTATION_CLEAR":
            session.annotation.clear()
            return {"ok": True, "action": "ANNOTATION_CLEAR"}
        elif action == "VOICE":
            text = msg.get("text", "")
            if text:
                session.handle_voice_text(text)
            return {"ok": True, "action": "VOICE", "text": text}
        elif action == "PING":
            return {
                "ok": True,
                "action": "PONG",
                "mode": session.mode,
                "slide": session.presentation.slide_index,
                "total": session.presentation.total_slides,
                "profile": getattr(session, "auto_profile", "general"),
            }
        else:
            return {"ok": False, "error": f"unknown_action:{action}"}

        return {
            "ok": True,
            "action": action,
            "command": r.command,
            "key": r.key,
            "mode": session.mode,
            "slide": session.presentation.slide_index,
        }
    except Exception as exc:
        log.exception("Dispatch error for %s", action)
        return {"ok": False, "error": str(exc)}


# ── WebSocket handler ───────────────────────────────────────────────────────
async def _handler(ws: WebSocketServerProtocol) -> None:
    origin = ws.request_headers.get("Origin", "null")
    if not any(origin.startswith(o) for o in ALLOWED_ORIGINS):
        log.warning("Rejected origin: %s", origin)
        await ws.close(1008, "Origin not allowed")
        return

    _clients.add(ws)
    log.info("✅ Web client connected — %s (total: %d)", origin, len(_clients))

    # Greet the new client immediately
    session = _get_session()
    greeting = {
        "type": "connected",
        "mode": session.mode if session else "no_session",
        "bridge_version": "1.0",
        "slide": session.presentation.slide_index if session else 0,
    }
    await ws.send(json.dumps(greeting))

    try:
        async for raw_msg in ws:
            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError:
                await ws.send(json.dumps({"ok": False, "error": "invalid_json"}))
                continue

            result = _dispatch(msg)
            await ws.send(json.dumps(result))

            # Broadcast status updates to all connected clients (slide sync)
            if result.get("ok") and result.get("action") not in ("PONG", "POINTER"):
                await _broadcast(result)

    except websockets.exceptions.ConnectionClosedOK:
        pass
    except Exception as exc:
        log.error("Client error: %s", exc)
    finally:
        _clients.discard(ws)
        log.info("Client disconnected (total: %d)", len(_clients))


async def _broadcast(data: dict) -> None:
    if not _clients:
        return
    msg = json.dumps(data)
    await asyncio.gather(*(c.send(msg) for c in list(_clients)), return_exceptions=True)


# ── Main ─────────────────────────────────────────────────────────────────────
async def run_bridge() -> None:
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  EDU-AIR Web Bridge  —  ws://localhost:%d", PORT)
    log.info("  Open: https://edu-air-smart-surface.vercel.app")
    log.info("  The web page will auto-connect and switch to 🔴 RÉEL")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    async with websockets.serve(_handler, "localhost", PORT):
        log.info("Bridge listening on ws://localhost:%d …  (Ctrl+C to stop)", PORT)
        await asyncio.Future()  # run forever


def main() -> None:
    full_mode = "--full" in sys.argv

    if full_mode:
        # Launch the desktop window in a separate thread
        def _launch_desktop():
            import edu_air_main
            edu_air_main.main(["--real"])

        t = threading.Thread(target=_launch_desktop, daemon=True)
        t.start()
        time.sleep(1.5)  # give Qt time to start

    try:
        asyncio.run(run_bridge())
    except KeyboardInterrupt:
        log.info("Bridge stopped.")


if __name__ == "__main__":
    main()
