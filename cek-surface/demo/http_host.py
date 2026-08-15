#!/usr/bin/env python3
"""HTTP Host for browser_shop.html — browser is the Peer.

  python3 demo/http_host.py [port]
  open http://127.0.0.1:8765/   (no ?mock=1 required)

Host only composes + verifies Caps. Browser applies Result.ops and
submits continuation Intents (timer.fired → pre-minted Cap).
"""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cek_surface.carrier import MemoryCarrier
from cek_surface.session import PeerSession
from shop_app import build_shop


def _echo_memory() -> MemoryCarrier:
    mem = MemoryCarrier()

    def handler(msg):
        if msg.get("type") == "apply":
            ops = (msg.get("result") or {}).get("ops") or []
            return [
                {
                    "type": "applied",
                    "receipt": {"landed": ops, "failed": []},
                    "world": {},
                }
            ]
        return [{"type": "chrome_applied", "world": {}}]

    mem.peer_handler = handler
    return mem


SURFACE = build_shop(carrier_kind="memory")
SURFACE.peer = PeerSession(carrier=_echo_memory())
print("kernel:", type(SURFACE.kernel).__name__, getattr(SURFACE.kernel, "name", ""))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "content-type")

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("content-type", content_type)
        self.send_header("cache-control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            body = (ROOT / "demo" / "browser_shop.html").read_bytes()
            body = body.replace(b"../js/browser_peer.mjs", b"/js/browser_peer.mjs")
            body = body.replace(b"'../js/browser_peer.mjs'", b"'/js/browser_peer.mjs'")
            body = body.replace(b"from '../js/browser_peer.mjs'", b"from '/js/browser_peer.mjs'")
            self._send(200, body, "text/html; charset=utf-8")
            return
        if path == "/health":
            self._send(
                200,
                json.dumps({"ok": True, "kernel": type(SURFACE.kernel).__name__}).encode(),
                "application/json",
            )
            return
        if path.startswith("/js/"):
            fp = ROOT / path.lstrip("/")
            if not fp.exists() or not fp.is_file():
                self.send_error(404)
                return
            self._send(200, fp.read_bytes(), "text/javascript; charset=utf-8")
            return
        self.send_error(404)

    def do_POST(self):
        if urlparse(self.path).path != "/cek/submit":
            self.send_error(404)
            return
        n = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(n)
        data = json.loads(raw.decode("utf-8") or "{}")
        action = data.get("action") or ""
        args = data.get("args") or {}
        cap = data.get("cap") or None
        # Browser is the Peer: no subprocess apply, no drain.
        out = SURFACE.submit(
            action,
            args,
            cap=cap,
            auto_mint=not bool(cap),
            drain_async=False,
        )
        body = json.dumps(
            {
                "result": out["result"],
                "world": out.get("world"),
                "continuations": out.get("continuations") or [],
            }
        ).encode()
        self._send(200, body, "application/json")


def main() -> int:
    host = os.environ.get("CEK_HOST", "0.0.0.0")
    port = int(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CEK_PORT", "8765"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"cek-surface HTTP Host http://{host}:{port}/")
    print("  real Surface.submit (no ?mock=1 required)")
    print(f"  mock UI only: http://{host}:{port}/?mock=1")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
