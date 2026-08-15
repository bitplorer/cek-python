"""Phase 2 — BoundAsk, idem, lineage, Ed25519, law-generation."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import (
    DEMO_SECRET,
    FileIdemBackend,
    FileLineageBackend,
    FileOnceBackend,
    Host,
    IdemConflict,
    MemoryIdemBackend,
    MemoryLineageBackend,
    MemoryOnceBackend,
    BoundAsk,
)

SECRET = b"phase2-secret-32-bytes-long!!!!!"
ED_SEED = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")


def test_boundask_no_public_ctor():
    try:
        BoundAsk()  # type: ignore[misc]
        raise AssertionError("BoundAsk() must raise")
    except TypeError as e:
        assert "public" in str(e).lower() or "I2" in str(e)
    try:
        BoundAsk("kv.write", {}, {}, 0.0)  # type: ignore[misc]
        raise AssertionError("BoundAsk positional must raise")
    except TypeError:
        pass


def test_empty_idempotency_key():
    h = Host(secret=SECRET)
    cap = h.mint("kv.write")
    r = h.submit(
        action="kv.write",
        args={"key": "a", "value": 1},
        cap=cap,
        idempotency_key="",
    )
    assert r.kind == "authority_refusal" and r.ops == []
    assert "idempotency" in (r.error or "")


def test_idem_replay_and_conflict():
    h = Host(secret=SECRET)
    cap = h.mint("kv.write")
    r1 = h.submit(
        action="kv.write",
        args={"key": "k", "value": 1},
        cap=cap,
        idempotency_key="same",
    )
    r2 = h.submit(
        action="kv.write",
        args={"key": "k", "value": 1},
        cap=cap,
        idempotency_key="same",
    )
    assert r1.kind == "ok" and r2.kind == "ok"
    assert r1.ops == r2.ops
    assert r1.digest == r2.digest
    r3 = h.submit(
        action="kv.write",
        args={"key": "k", "value": 9},
        cap=h.mint("kv.write"),
        idempotency_key="same",
    )
    assert r3.kind == "authority_refusal" and r3.ops == []
    assert "conflict" in (r3.error or "")


def test_idem_before_once():
    """Retry of a spent once-Cap with the same key returns the cached ok."""
    h = Host(secret=SECRET)
    cap = h.mint("kv.write", once=True)
    r1 = h.submit(
        action="kv.write",
        args={"key": "k", "value": 1},
        cap=cap,
        idempotency_key="once-retry",
    )
    r2 = h.submit(
        action="kv.write",
        args={"key": "k", "value": 1},
        cap=cap,
        idempotency_key="once-retry",
    )
    assert r1.kind == "ok" and r2.kind == "ok"
    assert r2.digest == r1.digest
    bare = h.submit(action="kv.write", args={"key": "k", "value": 1}, cap=cap)
    assert bare.kind == "authority_refusal" and bare.ops == []


def test_lineage_reverse_on_end():
    h = Host(secret=SECRET)
    cap = h.mint("kv.write")
    r = h.submit(
        action="kv.write",
        args={"key": "k", "value": 1},
        cap=cap,
        activity_id="act-rev",
    )
    assert r.kind == "ok"
    rev = h.end_activity("act-rev")
    assert rev.ops == [{"ns": "kv", "name": "delete", "payload": {"key": "k"}}]
    assert rev.used_landed is False


def test_receipt_landed_first():
    h = Host(secret=SECRET)
    cap = h.mint("kv.write")
    r = h.submit(
        action="kv.write",
        args={"key": "greet", "value": "hello"},
        cap=cap,
        activity_id="act-rcpt",
    )
    h.report_receipt("act-rcpt", r.ops)
    rev = h.end_activity("act-rcpt")
    assert rev.used_landed is True
    assert rev.ops == [{"ns": "kv", "name": "delete", "payload": {"key": "greet"}}]


def test_kv_delete_prior_and_no_prior():
    h = Host(secret=SECRET)
    r = h.submit(
        action="kv.delete",
        args={"key": "greeting", "prior": "hello"},
        cap=h.mint("kv.delete"),
        activity_id="act-del",
    )
    assert r.ops[0]["payload"]["prior"] == "hello"
    h.report_receipt("act-del", r.ops)
    rev = h.end_activity("act-del")
    assert rev.ops == [{"ns": "kv", "name": "set", "payload": {"key": "greeting", "value": "hello"}}]

    r2 = h.submit(
        action="kv.delete",
        args={"key": "greeting"},
        cap=h.mint("kv.delete"),
        activity_id="act-deln",
    )
    assert r2.kind == "ok"
    rev2 = h.end_activity("act-deln")
    assert rev2.ops == []
    assert rev2.non_reversible


def test_ui_morph_snapshot_reverse():
    h = Host(secret=SECRET)
    r = h.submit(
        action="ui.morph",
        args={"target": "hdr", "patch": {"t": "new"}, "snapshot": {"t": "old"}},
        cap=h.mint("ui.morph"),
        activity_id="act-ui",
    )
    assert r.ops[0]["ns"] == "ui.dom" and r.ops[0]["name"] == "morph"
    h.report_receipt("act-ui", r.ops)
    rev = h.end_activity("act-ui")
    assert rev.used_landed is True
    assert rev.ops == [
        {"ns": "ui.dom", "name": "restore", "payload": {"target": "hdr", "snapshot": {"t": "old"}}}
    ]


def test_ed25519_ok_missing_tamper():
    h = Host(secret=SECRET, ed25519_seed=ED_SEED)
    cap = h.mint("kv.write")
    claims = h.caps.decode(cap)
    assert claims.get("ed25519")
    assert h.submit(action="kv.write", args={"key": "a", "value": 1}, cap=cap).kind == "ok"

    unsigned = h.mint("kv.write", attach_ed25519=False)
    miss = h.submit(action="kv.write", args={"key": "a", "value": 1}, cap=unsigned)
    assert miss.kind == "authority_refusal" and miss.ops == []

    forged = h.caps.mint(
        "kv.write",
        jti=claims["jti"] + "-bad",
        law_generation=claims.get("law_generation"),
        ed25519="00" * 64,
    )
    bad = h.submit(action="kv.write", args={"key": "a", "value": 1}, cap=forged)
    assert bad.kind == "authority_refusal" and bad.ops == []


def test_law_generation_window():
    h = Host(secret=SECRET, accepted_generations=["cek-law-0"])
    blank = h.mint("kv.write", law_generation="  ")
    r = h.submit(action="kv.write", args={"key": "a", "value": 1}, cap=blank)
    assert r.kind == "authority_refusal" and r.ops == []

    unknown = h.mint("kv.write", law_generation="cek-law-99")
    r2 = h.submit(action="kv.write", args={"key": "a", "value": 1}, cap=unknown)
    assert r2.kind == "authority_refusal" and r2.ops == []

    ok = h.mint("kv.write", law_generation="cek-law-0")
    r3 = h.submit(action="kv.write", args={"key": "a", "value": 1}, cap=ok)
    assert r3.kind == "ok"
    unset = h.caps.mint("kv.write")  # no generation = legacy accept
    r4 = h.submit(action="kv.write", args={"key": "a", "value": 1}, cap=unset)
    assert r4.kind == "ok"


def test_production_refuses_memory_idem_and_lineage():
    try:
        Host.production(SECRET, MemoryOnceBackend(), allow_memory_stores=True)
        # allow_memory_stores=True permits memory once/idem/lineage
    except ValueError:
        raise AssertionError("allow_memory_stores should permit memory stores")
    try:
        Host.production(
            SECRET,
            MemoryOnceBackend(),
            idem=MemoryIdemBackend(),
            lineage=MemoryLineageBackend(),
        )
        raise AssertionError("memory stores must fail")
    except ValueError as e:
        assert "memory" in str(e)
    try:
        Host.production(DEMO_SECRET, MemoryOnceBackend(), allow_memory_stores=True)
        raise AssertionError("demo secret must fail")
    except ValueError as e:
        assert "secret" in str(e)


def test_file_backends_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        h = Host.production(
            SECRET,
            FileOnceBackend(root / "once.json"),
            idem=FileIdemBackend(root / "idem.json"),
            lineage=FileLineageBackend(root / "lin.json"),
        )
        cap = h.mint("kv.write", once=True)
        r = h.submit(
            action="kv.write",
            args={"key": "a", "value": 1},
            cap=cap,
            activity_id="act-f",
            idempotency_key="fk",
        )
        assert r.kind == "ok"
        replay = h.submit(
            action="kv.write",
            args={"key": "a", "value": 1},
            cap=cap,
            idempotency_key="fk",
        )
        assert replay.kind == "ok"
        rev = h.end_activity("act-f")
        assert rev.ops
        report = h.doctor()
        ids = {f.id: f for f in report.findings}
        assert ids["once-store"].ok and ids["idem-store"].ok and ids["lineage-store"].ok


def test_idem_store_down():
    idem = MemoryIdemBackend(down=True)
    h = Host(secret=SECRET, idem=idem)
    r = h.submit(
        action="kv.write",
        args={"key": "a", "value": 1},
        cap=h.mint("kv.write"),
        idempotency_key="x",
    )
    assert r.kind == "authority_refusal" and r.ops == []
    assert "store down" in (r.error or "")


if __name__ == "__main__":
    test_boundask_no_public_ctor()
    test_empty_idempotency_key()
    test_idem_replay_and_conflict()
    test_idem_before_once()
    test_lineage_reverse_on_end()
    test_receipt_landed_first()
    test_kv_delete_prior_and_no_prior()
    test_ui_morph_snapshot_reverse()
    test_ed25519_ok_missing_tamper()
    test_law_generation_window()
    test_production_refuses_memory_idem_and_lineage()
    test_file_backends_roundtrip()
    test_idem_store_down()
    print("phase2 ok")
