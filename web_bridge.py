"""EDU-AIR Web Bridge — WebSocket (port 8765) + HTTP server (port 8080).

Deux services en un :
  1. Serveur HTTP → sert l'app EDU-AIR localement sur http://localhost:8080
     (Depuis HTTP, ws://localhost:8765 est autorisé par Chrome)
  2. WebSocket    → traduit les gestes/voix du navigateur en actions réelles

Usage:
    py -3.12 web_bridge.py          # HTTP + WebSocket
    py -3.12 web_bridge.py --full   # HTTP + WebSocket + fenêtre bureau

Ouvrez ensuite:  http://localhost:8080
Le badge passe automatiquement de DEMO → 🔴 RÉEL
"""

from __future__ import annotations

import asyncio
import http.server
import json
import logging
import os
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

try:
    import websockets
except ImportError:
    print(
        "\n[EDU-AIR Bridge] 'websockets' package not found.\n"
        "  Install with:  py -3.12 -m pip install websockets\n",
        file=sys.stderr,
    )
    raise SystemExit(1)

try:
    from edu_air.classroom import ClassroomSession, RealBackend, DemoBackend
    _IMPORT_OK = True
except Exception as exc:
    log.warning("EDU-AIR classroom not importable (%s) — echo mode.", exc)
    _IMPORT_OK = False

WS_PORT   = 8765
HTTP_PORT = 8080

# Root of the web files (same folder as this script)
WEB_ROOT = os.path.dirname(os.path.abspath(__file__))

_session = None
_clients: set = set()


def _get_session():
    global _session
    if _session is None and _IMPORT_OK:
        try:
            backend = RealBackend()
        except Exception:
            backend = DemoBackend()
        _session = ClassroomSession(backend=backend)
        log.info("ClassroomSession — backend: %s", type(backend).__name__)
    return _session


# ── Action dispatcher ──────────────────────────────────────────────────────
def _dispatch(msg: dict) -> dict:
    action = msg.get("action", "").upper()
    session = _get_session()
    if session is None:
        return {"ok": False, "error": "no_session"}
    try:
        if action == "NEXT_SLIDE":   r = session.presentation.next_slide()
        elif action == "PREV_SLIDE": r = session.presentation.prev_slide()
        elif action == "PRES_START": r = session.presentation.start(msg.get("total", 10))
        elif action == "PRES_STOP":  r = session.presentation.stop()
        elif action == "PAUSE":      r = session.presentation.pause()
        elif action == "SCROLL_DOWN":r = session.presentation.scroll_down()
        elif action == "SCROLL_UP":  r = session.presentation.scroll_up()
        elif action == "ZOOM_IN":    r = session.presentation.zoom_in()
        elif action == "ZOOM_OUT":   r = session.presentation.zoom_out()
        elif action == "VOICE":
            session.handle_voice_text(msg.get("text", ""))
            return {"ok": True, "action": "VOICE"}
        elif action == "PING":
            return {
                "ok": True, "action": "PONG",
                "mode": session.mode,
                "slide": session.presentation.slide_index,
                "total": session.presentation.total_slides,
            }
        else:
            return {"ok": False, "error": f"unknown:{action}"}

        return {
            "ok": True, "action": action, "key": r.key,
            "mode": session.mode,
            "slide": session.presentation.slide_index,
        }
    except Exception as exc:
        log.exception("Dispatch error %s", action)
        return {"ok": False, "error": str(exc)}


# ── WebSocket handler ──────────────────────────────────────────────────────
async def _ws_handler(ws) -> None:
    _clients.add(ws)
    log.info("✅ Client connecté (total: %d)", len(_clients))
    session = _get_session()
    await ws.send(json.dumps({
        "type": "connected",
        "mode": session.mode if session else "no_session",
        "bridge_version": "1.1",
    }))
    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except Exception:
                await ws.send(json.dumps({"ok": False, "error": "invalid_json"}))
                continue
            result = _dispatch(msg)
            await ws.send(json.dumps(result))
            if result.get("ok") and result.get("action") not in ("PONG", "POINTER"):
                await _broadcast(result)
    except Exception:
        pass
    finally:
        _clients.discard(ws)
        log.info("Client déconnecté (total: %d)", len(_clients))


async def _broadcast(data: dict) -> None:
    if not _clients:
        return
    msg = json.dumps(data)
    await asyncio.gather(*(c.send(msg) for c in list(_clients)), return_exceptions=True)


# ── HTTP server (serves local files) ──────────────────────────────────────
class _CORSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass  # suppress HTTP logs


def _run_http_server():
    server = http.server.HTTPServer(("localhost", HTTP_PORT), _CORSHandler)
    log.info("🌐 HTTP server → http://localhost:%d", HTTP_PORT)
    server.serve_forever()


# ── Main ──────────────────────────────────────────────────────────────────
async def run_bridge() -> None:
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  EDU-AIR Bridge v1.1")
    log.info("  🌐 Ouvrez → http://localhost:%d", HTTP_PORT)
    log.info("  🔌 WebSocket → ws://localhost:%d", WS_PORT)
    log.info("  Le badge passera automatiquement 🔴 RÉEL")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Start HTTP server in background thread
    t = threading.Thread(target=_run_http_server, daemon=True)
    t.start()

    async with websockets.serve(_ws_handler, "localhost", WS_PORT):
        log.info("Bridge actif — Ctrl+C pour arrêter")
        await asyncio.Future()


def main() -> None:
    if "--full" in sys.argv:
        def _desktop():
            import edu_air_main
            edu_air_main.main([])
        threading.Thread(target=_desktop, daemon=True).start()
        time.sleep(1.5)

    try:
        asyncio.run(run_bridge())
    except KeyboardInterrupt:
        log.info("Bridge arrêté.")


if __name__ == "__main__":
    main()
