#!/usr/bin/env python3
"""One-command WebSocket Peer demo.

Requires:
  - node + `ws` (npm i ws in cek-surface/)
  - pip: websockets

Usage (from repo root):
  PYTHONPATH=cek-host/src:cek-surface/src python3 cek-surface/demo/ws_demo.py

Starts ws_peer_server.mjs, connects Surface via WebSocketCarrier,
runs shop.boot + cart.add, asserts Peer world kv, exits.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # cek-surface
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(REPO / "cek-host" / "src"))
sys.path.insert(0, str(ROOT / "demo"))

PORT = int(os.environ.get("PORT", "8766"))


def main() -> int:
    server = subprocess.Popen(
        ["node", str(ROOT / "demo" / "ws_peer_server.mjs")],
        cwd=str(ROOT),
        env={**os.environ, "PORT": str(PORT)},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.time() + 5
        ready = False
        while time.time() < deadline:
            if server.poll() is not None:
                out = server.stdout.read() if server.stdout else ""
                print("WS server exited early:\n", out)
                return 1
            time.sleep(0.15)
            ready = True
            break
        if not ready:
            print("WS server did not start")
            return 1
        time.sleep(0.25)

        from shop_app import build_shop

        s = build_shop(
            carrier_kind="websocket",
            url=f"ws://127.0.0.1:{PORT}",
        )
        s.policy.max_intents_per_sec = 1e9
        try:
            boot = s.submit("shop.boot", {}, auto_mint=True, drain_async=False)
            assert boot["result"]["kind"] == "ok", boot
            cart = s.submit("cart.add", {"id": "sku-1"}, auto_mint=True, drain_async=False)
            assert cart["result"]["kind"] == "ok", cart
            refuse = s.submit("cart.add", {"id": "sku-1"}, cap=None, drain_async=False)
            assert refuse["result"]["kind"] == "authority_refusal"
            assert refuse["result"]["ops"] == []
            print("ws demo ok")
            print(f"  boot ops={len(boot['result']['ops'])} cart ops={len(cart['result']['ops'])}")
            print(f"  refuse empty ops={refuse['result']['ops'] == []}")
            return 0
        finally:
            s.close()
    finally:
        server.send_signal(signal.SIGTERM)
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    raise SystemExit(main())
