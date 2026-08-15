"""P1: HTTP Host /cek/submit is real Surface.submit (no mock). Submit requires a Cap."""

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


def _post(port: int, path: str, payload: dict) -> dict:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    body = json.dumps(payload).encode()
    conn.request("POST", path, body=body, headers={"content-type": "application/json"})
    res = conn.getresponse()
    raw = res.read()
    conn.close()
    assert res.status == 200, raw
    return json.loads(raw.decode())


def _mint(port: int, action: str, args: dict | None = None, once: bool = False) -> str:
    data = _post(port, "/cek/mint", {"action": action, "args": args or {}, "once": once})
    assert data.get("cap"), data
    return data["cap"]


def _submit(port: int, action: str, args: dict | None = None, cap: str | None = None) -> dict:
    return _post(port, "/cek/submit", {"action": action, "args": args or {}, "cap": cap})


def test_http_host_real_submit():
    httpd, port = _serve()
    try:
        missing = _submit(port, "shop.boot", {})
        assert missing["result"]["kind"] == "authority_refusal"
        assert missing["result"]["ops"] == []

        boot = _submit(port, "shop.boot", {}, cap=_mint(port, "shop.boot"))
        assert boot["result"]["kind"] == "ok"
        assert boot["result"]["ops"]

        typed = _submit(
            port,
            "search.type",
            {"q": "Widget", "ms": 0},
            cap=_mint(port, "search.type", {"q": "Widget", "ms": 0}),
        )
        assert typed["result"]["kind"] == "ok"
        conts = typed.get("continuations") or typed["result"].get("continuations") or []
        assert conts and conts[0]["action"] == "search.commit"
        cap = conts[0]["cap"]

        committed = _submit(port, "search.commit", {"q": "Widget", "ms": 0}, cap=cap)
        assert committed["result"]["kind"] == "ok"
        ops = committed["result"]["ops"]
        morph = next(o for o in ops if o["ns"] == "ui.dom" and o["name"] == "morph")
        children = (morph.get("payload") or {}).get("patch", {}).get("children") or []
        assert children, "Host must project catalog hits"
        assert any("Widget" in (c.get("text") or "") for c in children)

        replay = _submit(port, "search.commit", {"q": "Widget", "ms": 0}, cap=cap)
        assert replay["result"]["kind"] == "authority_refusal"
        assert replay["result"]["ops"] == []

        cart = _submit(port, "cart.add", {"id": "sku-1"}, cap=_mint(port, "cart.add", {"id": "sku-1"}))
        assert cart["result"]["kind"] == "ok"
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    test_http_host_real_submit()
    print("http host ok")
