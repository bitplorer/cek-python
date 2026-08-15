#!/usr/bin/env python3
"""Minimal HTTP Host for browser_shop.html — opt-in carrier alternative to WS.

  python3 demo/http_host.py
  open http://127.0.0.1:8765/  (serves HTML + POST /cek/submit)
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from shop_app import build_shop

SURFACE = build_shop()
# Prefer real cek_host package
print("kernel:", type(SURFACE.kernel).__name__, getattr(SURFACE.kernel, "name", ""))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "content-type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            body = (ROOT / "demo" / "browser_shop.html").read_bytes()
            # rewrite import path for served root
            body = body.replace(b"../js/browser_peer.mjs", b"/js/browser_peer.mjs")
            body = body.replace(b"'../js/browser_peer.mjs'", b"'/js/browser_peer.mjs'")
            body = body.replace(b'from \'../js/browser_peer.mjs\'', b"from '/js/browser_peer.mjs'")
            self.send_response(200)
            self.send_header("content-type", "text/html; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(body)
            return
        if path.startswith("/js/"):
            fp = ROOT / path.lstrip("/")
            if not fp.exists():
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("content-type", "text/javascript")
            self._cors()
            self.end_headers()
            self.wfile.write(fp.read_bytes())
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
        # subprocess peer still used for apply truth; browser also applies client-side
        out = SURFACE.submit(action, args, auto_mint=True, drain_async=True)
        body = json.dumps({"result": out["result"], "world": out.get("world")}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    httpd = HTTPServer(("127.0.0.1", port), Handler)
    print(f"cek-surface HTTP Host http://127.0.0.1:{port}/")
    print(f"  mock UI only: http://127.0.0.1:{port}/?mock=1")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
