"""Session stamp + domain-stdlib agreement. Pair identity. Via negativa."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import Host, IllegalOp
from cek_host.legal import (
    BASELINE_PAIRS,
    LEGAL_PAIRS,
    default_stamp_pairs,
    in_stamp,
    normalize_stamp,
    project_wire,
)
from cek_host.structure import StructureError, validate_domain_name, validate_op_name, validate_pair
from cek_surface import Op, Surface
from cek_surface.domain_stdlib import (
    REGISTRY,
    agree,
    default_agreement_stamp,
    stamp_from_agreement,
)
from cek_surface.stamp import pairs_as_wire


def test_default_agreement_is_s():
    assert default_agreement_stamp() == LEGAL_PAIRS
    assert len(default_agreement_stamp()) == 5


def test_agree_intersection():
    both = agree(["baseline", "ui"], ["baseline", "ui"])
    assert {d.name for d in both} == {"baseline", "ui"}
    only_base = agree(["baseline", "ui"], ["baseline"])
    assert [d.name for d in only_base] == ["baseline"]
    stamp = stamp_from_agreement(only_base)
    assert stamp == BASELINE_PAIRS
    assert not in_stamp(stamp, "ui.dom", "morph")
    assert in_stamp(stamp, "kv", "set")


def test_concatenation_hole_not_in_stamp():
    stamp = default_agreement_stamp()
    assert in_stamp(stamp, "ui.dom", "morph")
    assert not in_stamp(stamp, "ui", "dom.morph")
    # split-alias is not a legal pair, so it never enters a stamp
    alias = normalize_stamp([("ui", "dom.morph")])
    assert not in_stamp(alias, "ui", "dom.morph")



def test_malformed_stamp_falls_back():
    # empty / split-alias / uppercase → not a valid pair; only-invalid → default
    fb = normalize_stamp([("ui", "dom.morph"), ("NAV", "PUSH")])
    assert fb == default_stamp_pairs()
    # Phase 2: structure-valid extension is kept
    ext = normalize_stamp([("demo.echo", "ping")])
    assert ("demo.echo", "ping") in ext



def test_project_wire_stamp_rejects():
    legal = [{"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}}]
    ui = [{"ns": "ui.dom", "name": "morph", "payload": {"target": "t", "patch": {}}}]
    baseline = BASELINE_PAIRS
    assert project_wire(legal, stamp=baseline) == legal
    try:
        project_wire(ui, unknown="strict", stamp=baseline)
        raise AssertionError("ui.dom.morph must be absent from baseline stamp")
    except IllegalOp as e:
        assert e.ns == "ui.dom" and e.name == "morph"


def test_host_stamp_rejects_unstamped_pair():
    h = Host(secret=b"library-polish-secret-32bytes!!")
    h.stamp = BASELINE_PAIRS
    cap = h.mint("ping")
    r = h.submit(
        action="ping",
        args={},
        cap=cap,
        project_ops=[
            {"ns": "ui.dom", "name": "morph", "payload": {"target": "t", "patch": {}}},
        ],
    )
    assert r.kind == "dispatch_error"
    assert r.ops == []
    assert "illegal" in (r.error or "")
    cap2 = h.mint("ping")
    ok = h.submit(
        action="ping",
        args={},
        cap=cap2,
        project_ops=[{"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}}],
    )
    assert ok.kind == "ok"
    assert ok.ops[0]["ns"] == "kv"


def test_host_baseline_pairs_still_succeed():
    h = Host(secret=b"library-polish-secret-32bytes!!")
    h.stamp = BASELINE_PAIRS
    for ns, name, payload in (
        ("kv", "set", {"key": "k", "value": 1}),
        ("kv", "delete", {"key": "k"}),
        ("log", "append", {"message": "m"}),
    ):
        r = h.submit(
            action="ping",
            args={},
            cap=h.mint("ping"),
            project_ops=[{"ns": ns, "name": name, "payload": payload}],
        )
        assert r.kind == "ok", r.error
        assert r.ops[0]["name"] == name


def test_surface_stamp_handshake_memory():
    s = Surface(carrier_kind="memory")
    s.stamp = BASELINE_PAIRS
    peer = s.ensure_peer()
    ack = peer.install_stamp(pairs_as_wire(s.stamp))
    assert ack["type"] == "stamp_ack"
    assert { (p["ns"], p["name"]) for p in ack["pairs"] } == set(BASELINE_PAIRS)


def test_structure_gate():
    validate_pair("ui.dom", "morph")
    validate_domain_name("nav")
    try:
        validate_domain_name("cek.secret")
        raise AssertionError("forbidden prefix")
    except StructureError:
        pass
    try:
        validate_op_name("dom.morph")
        raise AssertionError("dot in name")
    except StructureError:
        pass
    try:
        validate_domain_name("kv")
        raise AssertionError("reserved baseline")
    except StructureError:
        pass


def test_seed_registry_names():
    assert set(REGISTRY.names()) >= {"baseline", "ui"}


def test_strict_mode_default_stamp_is_baseline():
    prev = os.environ.get("CEK_CATALOG_MODE")
    os.environ["CEK_CATALOG_MODE"] = "strict"
    try:
        # re-import path uses live env
        from cek_host.catalog_mode import get_catalog_mode
        from importlib import reload
        import cek_host.catalog_mode as cm
        import cek_host.legal as legal

        reload(cm)
        reload(legal)
        assert cm.get_catalog_mode() == "strict"
        assert legal.default_stamp_pairs() == BASELINE_PAIRS
    finally:
        if prev is None:
            os.environ.pop("CEK_CATALOG_MODE", None)
        else:
            os.environ["CEK_CATALOG_MODE"] = prev
        from importlib import reload
        import cek_host.catalog_mode as cm
        import cek_host.legal as legal

        reload(cm)
        reload(legal)


if __name__ == "__main__":
    test_default_agreement_is_s()
    test_agree_intersection()
    test_concatenation_hole_not_in_stamp()
    test_malformed_stamp_falls_back()
    test_project_wire_stamp_rejects()
    test_host_stamp_rejects_unstamped_pair()
    test_host_baseline_pairs_still_succeed()
    test_surface_stamp_handshake_memory()
    test_structure_gate()
    test_seed_registry_names()
    test_strict_mode_default_stamp_is_baseline()
    print("stamp lock ok")
