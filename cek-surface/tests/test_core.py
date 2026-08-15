"""Core unit tests — no Peer required."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import CapError, CapService
from cek_surface import Intent, Op
from cek_surface.host import Host


def test_op_wire():
    o = Op.kv_set("a", 1)
    d = o.to_dict()
    assert d == {"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}}


def test_cap_once():
    caps = CapService(secret=b"test-secret-key-32bytes-long!!!")
    tok = caps.mint("x", once=True)
    caps.verify(tok, "x")
    try:
        caps.verify(tok, "x")
        assert False, "should refuse second use"
    except CapError as e:
        assert "once" in str(e)


def test_cap_seal_args():
    caps = CapService(secret=b"test-secret-key-32bytes-long!!!")
    args = {"sku": "a", "qty": 2}
    tok = caps.mint("Cart.add", args=args, seal_args=True)
    caps.verify(tok, "Cart.add", args)
    try:
        caps.verify(tok, "Cart.add", {"sku": "a", "qty": 3})
        assert False
    except CapError as e:
        assert "sealed" in str(e)


def test_host_refuse_no_cap():
    h = Host(caps=CapService(secret=b"test-secret-key-32bytes-long!!!"), require_cap=True)

    @h.action("ping")
    def ping(ctx):
        return [Op.log_append("pong")]

    r = h.submit(Intent(action="ping", args={}))
    assert r.kind == "authority_refusal"
    assert r.ops == []


def test_host_ok():
    h = Host(caps=CapService(secret=b"test-secret-key-32bytes-long!!!"))

    @h.action("ping")
    def ping(ctx):
        return [Op.kv_set("x", 1), Op.ui_toast("hi")]

    tok = h.mint("ping")
    r = h.submit(Intent(action="ping", args={}, cap=tok))
    assert r.kind == "ok"
    assert len(r.ops) == 2
    assert r.ops[0]["ns"] == "kv"


if __name__ == "__main__":
    test_op_wire()
    test_cap_once()
    test_cap_seal_args()
    test_host_refuse_no_cap()
    test_host_ok()
    print("ok")
