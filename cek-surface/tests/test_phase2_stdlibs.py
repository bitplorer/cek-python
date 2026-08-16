"""Phase 2 — loadable domain-stdlibs + versioned agreement."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import Host, IllegalOp
from cek_host.legal import BASELINE_PAIRS, LEGAL_PAIRS, project_wire
from cek_host.structure import StructureError
from cek_surface import Op, Surface
from cek_surface.agreement import negotiate
from cek_surface.domain_loader import load_dir, parse_stdlib
from cek_surface.domain_stdlib import REGISTRY, DomainStdlib, agree, stamp_from_agreement
from cek_surface.ops import Op as OpCls


STDLIB_DIR = ROOT / "stdlibs"


def test_load_demo_echo():
    loaded = load_dir(STDLIB_DIR)
    names = {d.name for d in loaded}
    assert "demo.echo" in names
    echo = REGISTRY.get("demo.echo")
    assert echo is not None
    assert ("demo.echo", "ping") in echo.pairs()


def test_version_mismatch_not_agreed():
    REGISTRY.register(
        DomainStdlib(
            name="demo.echo",
            version="1.0.0",
            seed_pairs=(("demo.echo", "ping"),),
            driver_hint="echo",
        )
    )
    agr = negotiate([("demo.echo", "1.0.0"), "baseline"], [("demo.echo", "2.0.0"), "baseline"])
    assert all(a.name != "demo.echo" for a in agr.accepted)
    assert ("demo.echo", "ping") not in agr.stamp


def test_version_match_extends_stamp():
    REGISTRY.register(
        DomainStdlib(
            name="demo.echo",
            version="1.0.0",
            seed_pairs=(("demo.echo", "ping"),),
            driver_hint="echo",
        )
    )
    agr = negotiate(
        ["baseline", "ui", ("demo.echo", "1.0.0")],
        ["baseline", "ui", ("demo.echo", "1.2.0")],
    )
    assert {a.name for a in agr.accepted} >= {"baseline", "ui", "demo.echo"}
    assert ("demo.echo", "ping") in agr.stamp
    assert LEGAL_PAIRS <= agr.stamp


def test_host_projects_extension_only_on_stamp():
    h = Host(secret=b"library-polish-secret-32bytes!!")
    ext = [("demo.echo", "ping")]
    ping = [{"ns": "demo.echo", "name": "ping", "payload": {"value": "hi"}}]
    h.stamp = None
    r = h.submit(action="ping", args={}, cap=h.mint("ping"), project_ops=ping)
    assert r.kind == "dispatch_error"
    h.stamp = BASELINE_PAIRS | frozenset(ext)
    r2 = h.submit(action="ping", args={}, cap=h.mint("ping"), project_ops=ping)
    assert r2.kind == "ok"
    assert r2.ops[0]["ns"] == "demo.echo"


def test_op_stamped_constructor():
    stamp = LEGAL_PAIRS | {("demo.echo", "ping")}
    op = OpCls.stamped("demo.echo", "ping", {"value": 1}, stamp)
    assert op.ns == "demo.echo"
    try:
        OpCls.stamped("demo.echo", "ping", {}, LEGAL_PAIRS)
        raise AssertionError("unstamped extension must fail")
    except ValueError:
        pass


def test_reject_core_overwrite_and_bad_structure():
    try:
        REGISTRY.register(
            DomainStdlib(name="baseline", version="9", seed_pairs=(("kv", "set"),), core=False)
        )
        raise AssertionError("must not overwrite core")
    except StructureError:
        pass
    try:
        parse_stdlib(
            {
                "name": "bad.pack",
                "seed_pairs": [{"ns": "x", "name": "has.dot"}],
            }
        )
        # parse succeeds; register fails
        REGISTRY.register(
            DomainStdlib(name="bad.pack", version="1", seed_pairs=(("x", "has.dot"),))
        )
        raise AssertionError("dot in name")
    except StructureError:
        pass


def test_surface_use_stdlibs_default_still_s():
    s = Surface(carrier_kind="memory")
    assert s.stamp == LEGAL_PAIRS
    s.load_stdlib_dir(str(STDLIB_DIR))
    s.use_stdlibs(["baseline", "ui", "demo.echo"])
    assert ("demo.echo", "ping") in s.stamp
    assert ("kv", "set") in s.stamp


def test_project_wire_extension_tolerant():
    ops = [
        {"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}},
        {"ns": "demo.echo", "name": "ping", "payload": {}},
    ]
    stamp = LEGAL_PAIRS | {("demo.echo", "ping")}
    assert len(project_wire(ops, stamp=stamp)) == 2
    try:
        project_wire(ops, unknown="strict")
        raise AssertionError("no stamp → extension illegal")
    except IllegalOp:
        pass


if __name__ == "__main__":
    test_load_demo_echo()
    test_version_mismatch_not_agreed()
    test_version_match_extends_stamp()
    test_host_projects_extension_only_on_stamp()
    test_op_stamped_constructor()
    test_reject_core_overwrite_and_bad_structure()
    test_surface_use_stdlibs_default_still_s()
    test_project_wire_extension_tolerant()
    print("phase2 stdlibs ok")
