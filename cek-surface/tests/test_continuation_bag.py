"""A refused handling must not arm or republish a once-Cap."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import Host
from cek_host.lineage import MemoryLineageBackend
from cek_surface import Surface
from cek_surface.carrier import MemoryCarrier
from cek_surface.ops import Op
from cek_surface.session import PeerSession


def _surface(**kw) -> Surface:
    mem = MemoryCarrier()
    s = Surface(carrier_kind="memory", **kw)
    s.peer = PeerSession(carrier=mem)
    s._mem = mem  # type: ignore[attr-defined]
    return s


def test_refusal_keeps_armed_continuation_and_store():
    s = _surface(kernel=Host(lineage=MemoryLineageBackend(down=True)))
    try:
        armed = s.mint_continuation("timer.fired:keep", "keep.act")
        s.last_continuations = [armed]
        s.store["kept"] = "yes"

        @s.action("boom")
        def boom(ctx):
            ctx.store["kept"] = "no"
            ctx.store["new"] = "x"
            ctx.continuations = [s.mint_continuation("timer.fired:new", "new.act")]
            return [Op.kv_set("k", 1)]

        out = s.submit(
            "boom",
            {},
            cap=s.mint("boom", once=True),
            activity_id="act-x",
            drain_async=False,
        )
        assert out["result"]["kind"] == "authority_refusal"
        assert out["continuations"] == []
        assert [c.event for c in s.last_continuations] == ["timer.fired:keep"]
        assert s.store == {"kept": "yes"}
    finally:
        s.close()


def test_drain_does_not_republish_sibling_once_cap():
    s = _surface()
    try:
        a = s.mint_continuation("timer.fired:a", "act.a")
        b = s.mint_continuation("timer.fired:b", "act.b")
        s.last_continuations = [a, b]

        @s.action("act.a")
        def act_a(ctx):
            return [Op.kv_set("k", 1)]

        s._mem.peer_push({"type": "timer.fired", "id": "a"})
        followups = s.drain_events()
        assert len(followups) == 1
        result = followups[0]["result"]
        assert result["kind"] == "ok"
        assert result.get("continuations") in (None, [])
        assert [c.event for c in s.last_continuations] == ["timer.fired:b"]
    finally:
        s.close()


def test_idempotent_replay_does_not_mint_another_cap():
    s = _surface()
    try:
        @s.action("tick")
        def tick(ctx):
            ctx.store["log"] = list(ctx.store.get("log") or []) + ["x"]
            ctx.continuations = [s.mint_continuation("timer.fired:new", "new.act")]
            return [Op.kv_set("k", 1)]

        cap = s.mint("tick", once=True)
        first = s.submit("tick", {"k": 1}, cap=cap, idempotency_key="same", drain_async=False)
        assert first["result"]["kind"] == "ok"
        assert len(first["continuations"]) == 1
        assert s.store["log"] == ["x"]

        again = s.submit("tick", {"k": 1}, cap=cap, idempotency_key="same", drain_async=False)
        assert again["result"]["kind"] == "ok"
        assert again["continuations"] == []
        assert again["result"]["ops"] == first["result"]["ops"]
        assert s.store["log"] == ["x"]
        assert [c.event for c in s.last_continuations] == ["timer.fired:new"]
    finally:
        s.close()
