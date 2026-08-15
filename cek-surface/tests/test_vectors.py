#!/usr/bin/env python3
"""Golden vector runner — aligns hot Op names + refuse semantics with cek-runtime.

Reads cek-surface/vectors/surface_core.json and executes executable cases.
Notes-only cases are acknowledged without runtime.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))
sys.path.insert(0, str(ROOT / "demo"))

from cek_surface import Op, Surface  # noqa: E402
from cek_surface.carrier import MemoryCarrier  # noqa: E402
from cek_surface.continuation import Continuation, resolve_args  # noqa: E402
from cek_surface.ops import as_wire  # noqa: E402
from cek_surface.session import PeerSession  # noqa: E402

VECTORS = ROOT / "vectors" / "surface_core.json"


def load_cases() -> list[dict]:
    data = json.loads(VECTORS.read_text())
    assert data.get("pack") == "cek-surface-core"
    return list(data["cases"])


def memory_surface() -> Surface:
    from shop_app import build_shop

    s = build_shop(carrier_kind="memory")
    s.policy.max_intents_per_sec = 1e9
    mem = MemoryCarrier()

    def handler(msg):
        if msg.get("type") == "apply":
            ops = (msg.get("result") or {}).get("ops") or []
            world_kv = getattr(handler, "_kv", {})
            if (msg.get("result") or {}).get("kind") == "ok":
                for op in ops:
                    if op.get("ns") == "kv" and op.get("name") == "set":
                        p = op.get("payload") or {}
                        world_kv[p["key"]] = p["value"]
            handler._kv = world_kv
            return [
                {
                    "type": "applied",
                    "receipt": {"landed": ops, "failed": []},
                    "world": {"kv": dict(world_kv)},
                }
            ]
        return [{"type": "chrome_applied", "world": {}}]

    handler._kv = {}
    mem.peer_handler = handler
    s.peer = PeerSession(carrier=mem)
    return s


def run_case(case: dict) -> None:
    cid = case["id"]
    family = case.get("family", "")

    if cid == "refuse_no_cap":
        s = memory_surface()
        out = s.submit("cart.add", {"id": "sku-1"}, cap=None, drain_async=False)
        assert out["result"]["kind"] == "authority_refusal"
        assert out["result"]["ops"] == []
        s.close()
        return

    if cid == "once_second_use":
        s = memory_surface()
        args = case["args"]
        cap = s.mint(case["action"], once=True, args=args, seal_args=True)
        r1 = s.submit(case["action"], args, cap=cap, drain_async=False)
        r2 = s.submit(case["action"], args, cap=cap, drain_async=False)
        assert r1["result"]["kind"] == case["expect_first"]
        assert r2["result"]["kind"] == case["expect_second"]["kind"]
        assert r2["result"]["ops"] == case["expect_second"]["ops"]
        s.close()
        return

    if cid == "sealed_args_mismatch":
        s = memory_surface()
        cap = s.mint(
            case["action"],
            once=False,
            args=case["mint_args"],
            seal_args=True,
        )
        r = s.submit(case["action"], case["submit_args"], cap=cap, drain_async=False)
        assert r["result"]["kind"] == case["expect"]["kind"]
        assert r["result"]["ops"] == case["expect"]["ops"]
        s.close()
        return

    if cid == "expired_cap_refuse":
        from cek_host import Host

        h = Host(secret=b"vector-secret-32-bytes!!!!!!!!")
        tok = h.mint("kv.write", not_after=time.time() - 10)
        r = h.submit(
            action="kv.write",
            args={"key": "a", "value": 1},
            cap=tok,
            project_ops=[{"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}}],
        )
        assert r.kind == "authority_refusal" and r.ops == [], r
        return

    if cid == "action_mismatch_refuse":
        from cek_host import Host

        h = Host(secret=b"vector-secret-32-bytes!!!!!!!!")
        tok = h.mint("cart.add")
        r = h.submit(
            action="cart.remove",
            args={},
            cap=tok,
            project_ops=[{"ns": "sys", "name": "noop", "payload": {}}],
        )
        assert r.kind == "authority_refusal" and r.ops == [], r
        return

    if cid == "peer_dispatch_error_no_mutate":
        s = memory_surface()
        h = s.peer.carrier.peer_handler
        h._kv = {}
        h({"type": "apply", "result": case["peer_result"]})
        for k, v in (case.get("expect_peer_kv") or {}).items():
            assert h._kv.get(k) == v
        assert h._kv == {}
        s.close()
        return

    if "expect_wire_keys" in case:
        op = case["op"]
        assert set(op.keys()) == set(case["expect_wire_keys"])
        return

    if "expect_ns_name" in case:
        op = case["op"]
        assert [op["ns"], op["name"]] == case["expect_ns_name"]
        return

    if cid == "peer_kv_set_lands":
        s = memory_surface()
        reply = s.peer.carrier.apply(case["peer_result"])
        assert reply["type"] == "applied"
        assert reply["world"]["kv"] == case["expect_peer_kv"]
        s.close()
        return

    if cid == "peer_refusal_no_mutate":
        s = memory_surface()
        s.peer.carrier.apply(
            {"kind": "ok", "ops": [{"ns": "kv", "name": "set", "payload": {"key": "keep", "value": 1}}]}
        )
        reply = s.peer.carrier.apply(case["peer_result"])
        assert reply["world"]["kv"].get("keep") == 1
        s.close()
        return

    if cid == "continuation_slot_resolve":
        cont = Continuation.from_dict(case["continuation"])
        args = resolve_args(cont, store=case["store"], event=case["event"])
        assert args == case["expect_args"]
        return

    if cid == "hot_op_catalog":
        catalog = {
            ("kv", "set"): Op.kv_set("k", 1),
            ("kv", "delete"): Op.kv_delete("k"),
            ("kv", "merge"): Op.kv_merge("k", {"a": 1}),
            ("ui.dom", "morph"): Op.ui_morph("t", {"tag": "div"}),
            ("ui.dom", "set_text"): Op.ui_set_text("t", "x"),
            ("ui.dom", "remove"): Op.ui_remove("t"),
            ("ui", "toast"): Op.ui_toast("hi"),
            ("ui", "busy"): Op.ui_busy("t", True),
            ("ui", "focus"): Op.ui_focus("t"),
            ("nav", "push"): Op.nav_push("/x"),
            ("nav", "replace"): Op.nav_replace("/x"),
            ("nav", "back"): Op.nav_back(),
            ("timer", "set"): Op.timer_set("t1", 10),
            ("timer", "clear"): Op.timer_clear("t1"),
            ("http", "request"): Op.http_request("r1", "GET", "https://example.com"),
            ("log", "append"): Op.log_append("m"),
            ("sys", "noop"): Op.noop(),
        }
        for ns, name in case["ops"]:
            op = catalog[(ns, name)]
            d = op.to_dict()
            assert d["ns"] == ns and d["name"] == name, (ns, name, d)
            assert set(d.keys()) == {"ns", "name", "payload"}
            assert as_wire([op])[0] == d
        return

    if case.get("note") and "expect" not in case and "op" not in case:
        return

    raise AssertionError(f"unhandled vector case: {cid} ({family})")


def main() -> int:
    cases = load_cases()
    for c in cases:
        run_case(c)
        print(f"  vector ok: {c['id']}")
    print(f"vectors ok ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
