"""Vectors + policy + continuation + perception."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_surface import Op, Surface
from cek_surface.continuation import Continuation, match_continuation, resolve_args
from cek_surface.ops import as_wire
from cek_surface.policy import SurfacePolicy


def test_vectors_pack():
    pack = json.loads((ROOT / "vectors" / "surface_core.json").read_text())
    assert pack["pack"] == "cek-surface-core"
    # continuation case
    c = next(x for x in pack["cases"] if x["id"] == "continuation_slot_resolve")
    cont = Continuation.from_dict(c["continuation"])
    args = resolve_args(cont, store=c["store"], event=c["event"])
    assert args == c["expect_args"]
    # morph shape (declared catalog)
    t = next(x for x in pack["cases"] if x["id"] == "morph_op_shape")
    op = Op.ui_morph("shell", {"tag": "div"})
    d = op.to_dict()
    assert [d["ns"], d["name"]] == t["expect_ns_name"]


def test_policy_rate_and_nav():
    p = SurfacePolicy(max_intents_per_sec=3, navigate_prefixes=("/shop",))
    assert p.check_action("a").allow
    assert p.check_action("a").allow
    assert p.check_action("a").allow
    assert not p.check_action("a").allow
    from cek_surface.ops import navigate_to
    ops = as_wire(navigate_to("/evil"))
    assert not p.check_ops(ops).allow
    ops2 = as_wire(navigate_to("/shop/x"))
    assert p.check_ops(ops2).allow


def test_policy_deny_is_dispatch_error():
    s = Surface(policy=SurfacePolicy(max_intents_per_sec=1), carrier_kind="memory")

    @s.action("ping")
    def ping(ctx):
        return [Op.log_append("p")]

    first = s.submit("ping", {}, cap=s.mint("ping"), drain_async=False)
    second = s.submit("ping", {}, cap=s.mint("ping"), drain_async=False)
    assert first["result"]["kind"] == "ok"
    assert second["result"]["kind"] == "dispatch_error"
    assert second["result"]["ops"] == []
    assert "rate" in (second["result"]["error"] or "")
    s.close()


def test_refuse_and_once():
    s = Surface()
    @s.action("ping")
    def ping(ctx):
        return [Op.log_append("p")]
    r = s.submit("ping", {}, cap=None, drain_async=False)
    assert r["result"]["kind"] == "authority_refusal"
    assert r["result"]["ops"] == []
    args = {}
    cap = s.mint("ping", once=True, args=args)
    r1 = s.submit("ping", args, cap=cap, drain_async=False)
    r2 = s.submit("ping", args, cap=cap, drain_async=False)
    assert r1["result"]["kind"] == "ok"
    assert r2["result"]["kind"] == "authority_refusal"
    s.close()


def test_mark_pending():
    s = Surface()
    @s.action("noop_act")
    def noop_act(ctx):
        return [Op.log_append("noop")]
    s.submit("noop_act", {}, auto_mint=True, drain_async=False)
    reply = s.ensure_peer().perception({"op": "pending", "target": "btn", "on": True})
    assert reply.get("type") == "perception_applied"
    perception = (reply.get("world") or {}).get("perception") or {}
    assert perception.get("busy") is not None or perception.get("shadows") is not None
    s.close()


def test_continuation_match():
    conts = [Continuation(event="timer.fired:d1", action="x", cap="c", args_from={"q": "store:q"})]
    m = match_continuation(conts, {"type": "timer.fired", "id": "d1"})
    assert m and m.action == "x"
    args = resolve_args(m, store={"q": "hi"}, event={})
    assert args["q"] == "hi"


if __name__ == "__main__":
    test_vectors_pack()
    test_policy_rate_and_nav()
    test_policy_deny_is_dispatch_error()
    test_refuse_and_once()
    test_mark_pending()
    test_continuation_match()
    print("roadmap ok")
