"""Core unit tests — published Host + Surface. No sketch Cap machine."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import CapError, CapService, Host
from cek_surface import Intent, Op, Surface

SECRET = b"test-secret-key-32bytes-long!!!"


def test_op_wire():
    o = Op.kv_set("a", 1)
    d = o.to_dict()
    assert d == {"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}}


def test_cap_once():
    caps = CapService(secret=SECRET)
    tok = caps.mint("x", once=True)
    caps.verify(tok, "x")
    try:
        caps.verify(tok, "x")
        assert False, "should refuse second use"
    except CapError as e:
        assert "once" in str(e)


def test_cap_seal_args():
    caps = CapService(secret=SECRET)
    args = {"sku": "a", "qty": 2}
    tok = caps.mint("Cart.add", args=args, seal_args=True)
    caps.verify(tok, "Cart.add", args)
    try:
        caps.verify(tok, "Cart.add", {"sku": "a", "qty": 3})
        assert False
    except CapError as e:
        assert "sealed" in str(e)


def test_host_refuse_no_cap():
    host = Host(secret=SECRET)
    s = Surface(kernel=host, carrier_kind="memory")

    @s.action("ping")
    def ping(ctx):
        return [Op.log_append("pong")]

    out = s.submit("ping", {}, drain_async=False)
    assert out["result"]["kind"] == "authority_refusal"
    assert out["result"]["ops"] == []
    s.close()


def test_host_ok():
    host = Host(secret=SECRET)
    s = Surface(kernel=host, carrier_kind="memory")

    @s.action("ping")
    def ping(ctx):
        return [Op.kv_set("x", 1), Op.ui_toast("hi")]

    tok = host.mint("ping")
    out = s.submit("ping", {}, cap=tok, drain_async=False)
    assert out["result"]["kind"] == "ok"
    assert len(out["result"]["ops"]) == 2
    assert out["result"]["ops"][0]["ns"] == "kv"
    s.close()


def test_intent_type_still_exported():
    i = Intent(action="ping", args={}, cap=None)
    assert i.action == "ping"
    try:
        from cek_surface.host import Host as Sketch  # noqa: F401

        raise AssertionError("cek_surface.host.Host must be gone")
    except ImportError:
        pass


if __name__ == "__main__":
    test_op_wire()
    test_cap_once()
    test_cap_seal_args()
    test_host_refuse_no_cap()
    test_host_ok()
    test_intent_type_still_exported()
    print("ok")
