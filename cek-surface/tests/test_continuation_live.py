"""P1: timer.fired → pre-minted Cap → search.commit (fail closed)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))
sys.path.insert(0, str(ROOT / "demo"))

from shop_app import build_shop
from cek_surface import Surface
from cek_surface.carrier import MemoryCarrier
from cek_surface.session import PeerSession


def _memory_surface() -> Surface:
    s = build_shop(carrier_kind="memory")
    mem = MemoryCarrier()

    def handler(msg):
        if msg.get("type") == "apply":
            ops = (msg.get("result") or {}).get("ops") or []
            return [{"type": "applied", "receipt": {"landed": ops, "failed": []}, "world": {"n": len(ops)}}]
        return [{"type": "chrome_applied", "world": {}}]

    mem.peer_handler = handler
    s.peer = PeerSession(carrier=mem)
    return s


def test_live_continuation_commit():
    s = _memory_surface()
    try:
        boot = s.submit("shop.boot", {}, auto_mint=True, drain_async=False)
        assert boot["result"]["kind"] == "ok"

        typed = s.submit("search.type", {"q": "Widget", "ms": 5}, auto_mint=True, drain_async=False)
        assert typed["result"]["kind"] == "ok"
        conts = typed.get("continuations") or []
        assert len(conts) == 1
        assert conts[0]["action"] == "search.commit"
        assert conts[0]["event"] == "timer.fired:search-debounce"
        cap = conts[0]["cap"]
        assert cap

        r1 = s.handle_event({"type": "timer.fired", "id": "search-debounce"})
        assert r1 is not None
        assert r1.kind == "ok"
        assert r1.ops, "search.commit must project ops under the continuation Cap"
        names = [f"{o['ns']}.{o['name']}" for o in r1.ops]
        assert "ui.dom.morph" in names
        hits = s.store.get("search.results") or []
        assert any("Widget" in (it.get("title") or "") for it in hits)

        # once Cap burned — replay refuses with zero ops
        r2 = s.kernel.submit(
            "search.commit",
            {"q": "Widget", "ms": 0},
            cap,
            project_ops=[{"ns": "sys", "name": "noop", "payload": {}}],
        )
        assert r2.kind == "authority_refusal"
        assert r2.ops == []

        # continuation consumed — bare timer does not compose
        r3 = s.handle_event({"type": "timer.fired", "id": "search-debounce"})
        assert r3 is None
    finally:
        s.close()


def test_live_continuation_via_subprocess_drain():
    s = build_shop()
    try:
        s.submit("shop.boot", {}, auto_mint=True, drain_async=False)
        out = s.submit("search.type", {"q": "Gadget", "ms": 15}, auto_mint=True, drain_async=True)
        assert out["result"]["kind"] == "ok"
        followups = out.get("followups") or []
        assert followups, "timer.fired must drain into search.commit"
        kinds = [(f.get("result") or {}).get("kind") for f in followups]
        assert "ok" in kinds
        assert any((f.get("event") or {}).get("id") == "search-debounce" for f in followups) or any(
            (f.get("event") or {}).get("type") == "timer.fired" for f in followups
        )
        hits = s.store.get("search.results") or []
        assert any(it.get("id") == "sku-3" for it in hits)
    finally:
        s.close()


def test_refuse_without_cap_still_empty_ops():
    s = _memory_surface()
    try:
        r = s.submit("search.commit", {"q": "Widget"}, cap=None, drain_async=False)
        assert r["result"]["kind"] == "authority_refusal"
        assert r["result"]["ops"] == []
    finally:
        s.close()


def test_peer_does_not_mint():
    s = _memory_surface()
    try:
        assert not hasattr(s.ensure_peer(), "mint")
        assert not hasattr(s.ensure_peer().carrier, "mint")
    finally:
        s.close()


if __name__ == "__main__":
    test_live_continuation_commit()
    test_live_continuation_via_subprocess_drain()
    test_refuse_without_cap_still_empty_ops()
    test_peer_does_not_mint()
    print("continuation live ok")
