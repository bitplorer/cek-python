"""G8 / W3 — secret, memory once, subject, scopes, store-down, attenuate."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import (
    DEMO_SECRET,
    FileOnceBackend,
    Host,
    MemoryOnceBackend,
    doctor,
)

OPS = [{"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}}]
SECRET = b"hardening-secret-32-bytes-long!!"


def test_production_refuses_default_secret():
    try:
        Host.production(DEMO_SECRET, MemoryOnceBackend(), allow_memory_stores=True)
        raise AssertionError("default secret must fail")
    except ValueError as e:
        assert "secret" in str(e)


def test_production_refuses_memory_once():
    try:
        Host.production(SECRET, MemoryOnceBackend())
        raise AssertionError("memory once must fail")
    except ValueError as e:
        assert "memory" in str(e)


def test_production_file_once_ok():
    with tempfile.TemporaryDirectory() as td:
        h = Host.production(SECRET, FileOnceBackend(Path(td) / "once.json"))
        cap = h.mint("kv.write", once=True, args={"key": "a", "value": 1}, seal_args=True)
        r1 = h.submit(action="kv.write", args={"key": "a", "value": 1}, cap=cap, project_ops=OPS)
        r2 = h.submit(action="kv.write", args={"key": "a", "value": 1}, cap=cap, project_ops=OPS)
        assert r1.kind == "ok"
        assert r2.kind == "authority_refusal" and r2.ops == []


def test_subject_bind_enforced():
    h = Host(secret=SECRET)
    cap = h.mint("kv.write", subject="alice")
    bad = h.submit(
        action="kv.write",
        args={"key": "a", "value": 1, "subject": "bob"},
        cap=cap,
        project_ops=OPS,
    )
    good = h.submit(
        action="kv.write",
        args={"key": "a", "value": 1, "subject": "alice"},
        cap=cap,
        project_ops=OPS,
    )
    assert bad.kind == "authority_refusal" and bad.ops == []
    assert "subject" in (bad.error or "")
    assert good.kind == "ok"


def test_scope_deny_and_blank():
    h = Host(secret=SECRET)
    cap = h.mint("kv.write", scopes=["kv:other"])
    r = h.submit(
        action="kv.write",
        args={"key": "a", "value": 1},
        cap=cap,
        project_ops=OPS,
    )
    assert r.kind == "authority_refusal" and r.ops == []

    blank = h.mint("kv.write", scopes=["  "])
    r2 = h.submit(action="kv.write", args={"key": "a"}, cap=blank, project_ops=OPS)
    assert r2.kind == "authority_refusal" and r2.ops == []

    allow = h.mint("kv.write", scopes=["kv:a"])
    r3 = h.submit(action="kv.write", args={"key": "a", "value": 1}, cap=allow, project_ops=OPS)
    assert r3.kind == "ok"


def test_store_down_fail_closed():
    once = MemoryOnceBackend(down=True)
    h = Host.adapt(SECRET, once=once)
    cap = h.mint("ping", once=True)
    r = h.submit(action="ping", args={}, cap=cap, project_ops=OPS)
    assert r.kind == "authority_refusal" and r.ops == []
    assert "store down" in (r.error or "")


def test_attenuate_cannot_widen():
    h = Host(secret=SECRET)
    parent = h.mint("cart.add", scopes=["action:cart.add"], not_after=h.caps.now_fn() + 60)
    try:
        h.attenuate(parent, scopes=["action:cart.add", "action:cart.clear"])
        raise AssertionError("widen must fail")
    except Exception as e:
        assert "widen" in str(e)

    child = h.attenuate(parent, scopes=["action:cart.add"], once=True)
    claims = h.caps.decode(child)
    assert claims["once"] is True
    assert claims["scopes"] == ["action:cart.add"]


def test_hmac_tamper_zero_ops():
    h = Host(secret=SECRET)
    cap = h.mint("ping")
    body, sig = cap.rsplit(".", 1)
    tampered = body + "." + ("0" if sig[0] != "0" else "1") + sig[1:]
    r = h.submit(action="ping", args={}, cap=tampered, project_ops=OPS)
    assert r.kind == "authority_refusal" and r.ops == []


def test_doctor_flags_demo_secret():
    report = doctor(Host())
    ids = {f.id: f for f in report.findings}
    assert ids["secret"].ok is False
    assert ids["require_cap"].ok is True


def test_doctor_production_clean():
    with tempfile.TemporaryDirectory() as td:
        h = Host.production(SECRET, FileOnceBackend(Path(td) / "once.json"))
        report = h.doctor()
        ids = {f.id: f for f in report.findings}
        assert ids["secret"].ok
        assert ids["once-store"].ok
        assert ids["require_cap"].ok


if __name__ == "__main__":
    test_production_refuses_default_secret()
    test_production_refuses_memory_once()
    test_production_file_once_ok()
    test_subject_bind_enforced()
    test_scope_deny_and_blank()
    test_store_down_fail_closed()
    test_attenuate_cannot_widen()
    test_hmac_tamper_zero_ops()
    test_doctor_flags_demo_secret()
    test_doctor_production_clean()
    print("hardening ok")
