"""Carrier plug-and-play + Peer IR flush/shadow + continuations."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_surface import Continuation, Op, Surface, open_carrier
from cek_surface.carrier import MemoryCarrier, SubprocessNdjsonCarrier, open_carrier
from cek_surface.continuation import match_continuation, resolve_args
from cek_surface.kernel import KernelResult


def test_open_carrier_default_subprocess():
    c = open_carrier("subprocess")
    assert isinstance(c, SubprocessNdjsonCarrier)
    # minimal apply refuse path
    reply = c.apply({"kind": "authority_refusal", "ops": [], "error": "x"})
    assert reply.get("type") == "applied"
    c.close()


def test_memory_carrier_roundtrip():
    mem = MemoryCarrier()

    def handler(msg):
        if msg["type"] == "apply":
            return [{"type": "applied", "receipt": {"landed": msg["result"].get("ops") or [], "failed": []}, "world": {"ok": True}}]
        if msg["type"] == "chrome":
            return [{"type": "chrome_applied", "world": {"chrome": msg["chrome"]}}]
        return [{"type": "events", "events": []}]

    mem.peer_handler = handler
    r = mem.apply({"kind": "ok", "ops": [{"ns": "sys", "name": "noop", "payload": {}}]})
    assert r["type"] == "applied"
    assert r["world"]["ok"] is True
    ch = mem.chrome({"op": "pending", "target": "b"})
    assert ch["world"]["chrome"]["op"] == "pending"
    mem.close()


def test_surface_memory_carrier():
    mem = MemoryCarrier()

    def handler(msg):
        if msg["type"] == "apply":
            ops = (msg.get("result") or {}).get("ops") or []
            return [{"type": "applied", "receipt": {"landed": ops, "failed": []}, "world": {"n": len(ops)}}]
        return [{"type": "chrome_applied", "world": {}}]

    mem.peer_handler = handler
    s = Surface(carrier_kind="memory")
    s.peer = __import__("cek_surface.session", fromlist=["PeerSession"]).PeerSession(carrier=mem)

    @s.action("x")
    def x(ctx):
        return [Op.log_append("hi"), Op.ui_toast("t")]

    out = s.submit("x", {}, auto_mint=True, drain_async=False)
    assert out["result"]["kind"] == "ok"
    assert out["world"]["n"] == 2
    s.close()


def test_shadow_cleared_on_apply():
    s = Surface()
    @s.action("boot")
    def boot(ctx):
        return [Op.noop()]
    s.submit("boot", {}, auto_mint=True, drain_async=False)
    s.ensure_peer().chrome({"op": "pending", "target": "btn", "on": True})
    # authority apply clears shadows
    out = s.submit("boot", {}, auto_mint=True, drain_async=False)
    chrome = (out.get("world") or {}).get("chrome") or {}
    # shadows map should be empty after beforeAuthorityApply
    shadows = chrome.get("shadows") or {}
    assert shadows == {} or not shadows
    s.close()


def test_continuation_search_slots():
    cont = Continuation(
        event="timer.fired:search-debounce",
        action="search.commit",
        cap="CAP",
        args_from={"q": "store:search.pending"},
        static_args={"ms": 0},
    )
    args = resolve_args(cont, store={"search.pending": "widget"}, event={"type": "timer.fired", "id": "search-debounce"})
    assert args == {"q": "widget", "ms": 0}
    m = match_continuation([cont], {"type": "timer.fired", "id": "search-debounce"})
    assert m and m.action == "search.commit"


def test_websocket_opt_in_missing_dep():
    try:
        import websockets  # noqa: F401
        # if installed, just ensure factory accepts kind
        # don't open real connection
        assert open_carrier  # factory exists
    except ImportError:
        try:
            open_carrier("websocket", url="ws://127.0.0.1:9")
            assert False, "should require websockets"
        except ImportError as e:
            assert "websockets" in str(e).lower() or "pip install" in str(e)


if __name__ == "__main__":
    test_open_carrier_default_subprocess()
    test_memory_carrier_roundtrip()
    test_surface_memory_carrier()
    test_shadow_cleared_on_apply()
    test_continuation_search_slots()
    test_websocket_opt_in_missing_dep()
    print("carrier+ir ok")
