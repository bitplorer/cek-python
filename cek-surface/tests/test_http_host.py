"""P1: HTTP Host /cek/submit is real Surface.submit (no mock)."""

from __future__ import annotations

import json
import sys
import threading
from http.client import HTTPConnection
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))
sys.path.insert(0, str(ROOT / "demo"))

from http_host import Handler, SURFACE
from http.server import ThreadingHTTPServer


def _serve():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


def _post(port: int, payload: dict) -> dict:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    body = json.dumps(payload).encode()
    conn.request("POST", "/cek/submit", body=body, headers={"content-type": "application/json"})
    res = conn.getresponse()
    raw = res.read()
    conn.close()
    assert res.status == 200, raw
    return json.loads(raw.decode())


def test_http_host_real_submit():
    httpd, port = _serve()
    try:
        boot = _post(port, {"action": "shop.boot", "args": {}})
        assert boot["result"]["kind"] == "ok"
        assert boot["result"]["ops"]

        typed = _post(port, {"action": "search.type", "args": {"q": "Widget", "ms": 0}})
        assert typed["result"]["kind"] == "ok"
        conts = typed.get("continuations") or typed["result"].get("continuations") or []
        assert conts and conts[0]["action"] == "search.commit"
        cap = conts[0]["cap"]

        committed = _post(
            port,
            {"action": "search.commit", "args": {"q": "Widget", "ms": 0}, "cap": cap},
        )
        assert committed["result"]["kind"] == "ok"
        ops = committed["result"]["ops"]
        morph = next(o for o in ops if o["ns"] == "ui.dom" and o["name"] == "morph")
        children = (morph.get("payload") or {}).get("patch", {}).get("children") or []
        assert children, "Host must project catalog hits"
        assert any("Widget" in (c.get("text") or "") for c in children)

        replay = _post(
            port,
            {"action": "search.commit", "args": {"q": "Widget", "ms": 0}, "cap": cap},
        )
        assert replay["result"]["kind"] == "authority_refusal"
        assert replay["result"]["ops"] == []

        cart = _post(port, {"action": "cart.add", "args": {"id": "sku-1"}})
        assert cart["result"]["kind"] == "ok"
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    test_http_host_real_submit()
    print("http host ok")
