"""A (demo) ≡ B (adapt) on refuse / once / sealed-args / oracle.

W4 / G2 / G3. Same Cap machine, two factory paths.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import Host, MemoryOnceBackend, args_hash

SECRET = b"parity-secret-32-bytes-long!!!!!"
ORACLE = "96e4f83e3793b646323a67f314b51044"
OPS = [{"ns": "log", "name": "append", "payload": {"message": "x"}}]


def _pair():
    a = Host.demo(secret=SECRET)
    b = Host.adapt(secret=SECRET, once=MemoryOnceBackend())
    return a, b


def _cmp(ra, rb) -> None:
    assert ra.kind == rb.kind, (ra, rb)
    assert ra.ops == rb.ops, (ra, rb)
    assert (ra.error or "") == (rb.error or ""), (ra, rb)


def test_oracle():
    assert args_hash({"sku": "abc-123", "qty": 2}) == ORACLE


def test_refuse_no_cap():
    a, b = _pair()
    _cmp(a.submit(action="cart.add", args={"id": "x"}), b.submit(action="cart.add", args={"id": "x"}))
    assert a.submit(action="cart.add", args={"id": "x"}).ops == []


def test_once_second_use():
    a, b = _pair()
    for h in (a, b):
        cap = h.mint("cart.add", once=True, args={"id": "sku-1"}, seal_args=True)
        r1 = h.submit(action="cart.add", args={"id": "sku-1"}, cap=cap, project_ops=OPS)
        r2 = h.submit(action="cart.add", args={"id": "sku-1"}, cap=cap, project_ops=OPS)
        assert r1.kind == "ok" and r1.ops == OPS
        assert r2.kind == "authority_refusal" and r2.ops == []


def test_sealed_args():
    a, b = _pair()
    for h in (a, b):
        cap = h.mint("cart.add", args={"id": "sku-1", "qty": 1}, seal_args=True)
        bad = h.submit(
            action="cart.add",
            args={"id": "sku-1", "qty": 99},
            cap=cap,
            project_ops=OPS,
        )
        good = h.submit(
            action="cart.add",
            args={"id": "sku-1", "qty": 1},
            cap=cap,
            project_ops=OPS,
        )
        assert bad.kind == "authority_refusal" and bad.ops == []
        assert good.kind == "ok"


def test_digest_present_adapt():
    _, b = _pair()
    cap = b.mint("ping")
    r = b.submit(action="ping", args={}, cap=cap, project_ops=OPS)
    assert r.digest and r.digest.startswith("cek1:")


if __name__ == "__main__":
    test_oracle()
    test_refuse_no_cap()
    test_once_second_use()
    test_sealed_args()
    test_digest_present_adapt()
    print("host parity ok  A ≡ B")
