"""Aligned contract family on the published Host.

Source of truth: cek-runtime/crates/cek-contract/vectors
This runner translates the hot fixtures onto cek_host.Host (HMAC hex-token).
Does not invent a third refuse reason.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import Host, args_hash, result_digest

SECRET = b"contract-vector-secret-32b!!!!!!"
OPS = [{"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}}]
ORACLE = "96e4f83e3793b646323a67f314b51044"


def _host() -> Host:
    return Host(secret=SECRET)


def _refuse(h: Host, **kw) -> None:
    r = h.submit(project_ops=OPS, **kw)
    assert r.kind == "authority_refusal", r
    assert r.ops == [], r
    assert r.digest and r.digest.startswith("cek1:")


def test_oracle():
    assert args_hash({"sku": "abc-123", "qty": 2}) == ORACLE


def test_refuse_no_cap():
    _refuse(_host(), action="kv.write", args={"key": "a", "value": 1})


def test_empty_action():
    h = _host()
    cap = h.mint("kv.write")
    _refuse(h, action="", args={}, cap=cap)


def test_action_mismatch():
    h = _host()
    cap = h.mint("kv.write")
    _refuse(h, action="kv.delete", args={"key": "a"}, cap=cap)


def test_expired():
    h = _host()
    cap = h.mint("kv.write", not_after=time.time() - 10)
    _refuse(h, action="kv.write", args={"key": "a"}, cap=cap)


def test_once_second_use():
    h = _host()
    cap = h.mint("kv.write", once=True, args={"key": "x", "value": 1}, seal_args=True)
    r1 = h.submit(action="kv.write", args={"key": "x", "value": 1}, cap=cap, project_ops=OPS)
    r2 = h.submit(action="kv.write", args={"key": "x", "value": 1}, cap=cap, project_ops=OPS)
    assert r1.kind == "ok"
    assert r2.kind == "authority_refusal" and r2.ops == []


def test_sealed_args_mismatch():
    h = _host()
    cap = h.mint("kv.write", args={"key": "fixed", "value": 1}, seal_args=True)
    _refuse(h, action="kv.write", args={"key": "fixed", "value": 999}, cap=cap)


def test_sealed_args_match():
    h = _host()
    args = {"key": "fixed", "value": 1}
    cap = h.mint("kv.write", args=args, seal_args=True)
    r = h.submit(action="kv.write", args=args, cap=cap, project_ops=OPS)
    assert r.kind == "ok"


def test_subject_bind_mismatch():
    h = _host()
    cap = h.mint("kv.write", subject="alice")
    _refuse(h, action="kv.write", args={"key": "a", "value": 1, "subject": "bob"}, cap=cap)


def test_subject_bind_ok():
    h = _host()
    cap = h.mint("kv.write", subject="alice")
    r = h.submit(
        action="kv.write",
        args={"key": "a", "value": 1, "subject": "alice"},
        cap=cap,
        project_ops=OPS,
    )
    assert r.kind == "ok"


def test_scope_denies_key():
    h = _host()
    cap = h.mint("kv.write", scopes=["kv:other"])
    _refuse(h, action="kv.write", args={"key": "a", "value": 1}, cap=cap)


def test_scope_allows_key():
    h = _host()
    cap = h.mint("kv.write", scopes=["kv:a"])
    r = h.submit(action="kv.write", args={"key": "a", "value": 1}, cap=cap, project_ops=OPS)
    assert r.kind == "ok"


def test_hmac_tamper():
    h = _host()
    cap = h.mint("kv.write")
    body, sig = cap.rsplit(".", 1)
    flip = ("0" if sig[0] != "0" else "1") + sig[1:]
    _refuse(h, action="kv.write", args={"key": "a"}, cap=flip)


def test_digest_cek1():
    h = _host()
    cap = h.mint("kv.write")
    r = h.submit(action="kv.write", args={"key": "a"}, cap=cap, project_ops=OPS)
    assert r.digest == result_digest(r.kind, r.ops, r.error)
    assert r.digest.startswith("cek1:")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  contract ok: {name}")
    print("contract family ok")
