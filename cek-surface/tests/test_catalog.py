"""S is closed. Pair identity. Host legal ≡ Surface catalog ≡ Rust decls."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import Host, IllegalOp, explain
from cek_host.legal import (
    BASELINE_PAIRS,
    DOMAIN_PACKS,
    LEGAL_FQS,
    LEGAL_PAIRS,
    is_legal,
    pack_is_scoped,
    project,
    project_wire,
)
from cek_surface import Op
from cek_surface.catalog import LEGAL_FQS as SURF_FQS
from cek_surface.catalog import LEGAL_PAIRS as SURF_PAIRS


S = frozenset(
    {
        ("kv", "set"),
        ("kv", "delete"),
        ("log", "append"),
        ("ui.dom", "morph"),
        ("ui.dom", "restore"),
    }
)

RUST_SRC = (
    ROOT.parent.parent / "cek-runtime" / "crates" / "cek-contract" / "src"
)


def rust_declared_pairs() -> set[tuple[str, str]]:
    baseline = (RUST_SRC / "baseline.rs").read_text(encoding="utf-8")
    domain = (RUST_SRC / "domain.rs").read_text(encoding="utf-8")
    pairs = set(re.findall(r'\("([a-z0-9.]+)", "([a-z0-9]+)"\)', baseline))
    pairs |= set(re.findall(r'ns:\s*"([^"]+)",\s*name:\s*"([^"]+)"', domain))
    return pairs


def test_s_is_exactly_five_pairs():
    assert LEGAL_PAIRS == S
    assert SURF_PAIRS == S
    assert LEGAL_FQS == SURF_FQS
    assert LEGAL_FQS == frozenset(f"{n}.{m}" for n, m in S)


def test_python_s_matches_rust_decls():
    rust = rust_declared_pairs()
    assert rust == set(S), (sorted(rust), sorted(S))


def test_packs_are_scoped():
    for pack, pairs in DOMAIN_PACKS.items():
        assert pack_is_scoped(pack), pack
        for ns, name in pairs:
            assert ns == pack
            assert "." not in name


def test_constructors_emit_s_only():
    assert Op.kv_set("k", 1).to_dict()["ns"] == "kv"
    assert Op.kv_delete("k").to_dict()["name"] == "delete"
    assert Op.log_append("m").to_dict()["ns"] == "log"
    assert Op.ui_morph("t", {}).to_dict()["ns"] == "ui.dom"
    assert Op.ui_restore("t", {}).to_dict()["name"] == "restore"
    assert Op.kv_set("k", 1).fq == "kv.set"


def test_illegal_constructors_raise():
    for ns, name in (
        ("nav", "push"),
        ("ui", "toast"),
        ("timer", "set"),
        ("sys", "noop"),
        ("http", "request"),
        ("signal", "set"),
        ("ui", "dom.morph"),
        ("ui.dom.morph", ""),
        ("kv", "merge"),
        ("ui.shell", "blur"),
    ):
        try:
            Op(ns, name, {})
            raise AssertionError(f"expected raise for {ns}.{name}")
        except ValueError as e:
            assert "illegal" in str(e)
        assert not is_legal(ns, name)


def test_split_alias_is_not_legal():
    assert is_legal("ui.dom", "morph")
    assert not is_legal("ui", "dom.morph")
    assert ("ui", "dom.morph") not in LEGAL_PAIRS


def test_project_strict_raises_on_unknown():
    legal = [{"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}}]
    bad = [{"ns": "nav", "name": "push", "payload": {"path": "/"}}]
    alias = [{"ns": "ui", "name": "dom.morph", "payload": {"target": "t", "patch": {}}}]
    assert project_wire(legal) == legal
    try:
        project_wire(legal + bad, unknown="strict")
        raise AssertionError("strict mixed batch must raise")
    except IllegalOp as e:
        assert e.ns == "nav" and e.name == "push"
    try:
        project_wire(legal + alias, unknown="strict")
        raise AssertionError("split-alias must raise")
    except IllegalOp:
        pass
    assert project_wire(legal + bad, unknown="tolerant") == legal
    assert project(legal + alias, packs=["ui.dom"], unknown="tolerant") == legal
    assert project_wire([], unknown="strict") == []


def test_host_illegal_project_ops_is_dispatch_error():
    h = Host(secret=b"library-polish-secret-32bytes!!")
    cap = h.mint("ping")
    mixed = h.submit(
        action="ping",
        args={},
        cap=cap,
        project_ops=[
            {"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}},
            {"ns": "nav", "name": "push", "payload": {"path": "/"}},
        ],
    )
    assert mixed.kind == "dispatch_error"
    assert mixed.ops == []
    assert "illegal" in (mixed.error or "")
    empty = h.submit(action="ping", args={}, cap=h.mint("ping"), project_ops=[])
    assert empty.kind == "ok" and empty.ops == []
    taught = explain(mixed.error)
    assert taught.code == "illegal_op"


def test_baseline_pairs_untouched():
    assert BASELINE_PAIRS == frozenset({("kv", "set"), ("kv", "delete"), ("log", "append")})


if __name__ == "__main__":
    test_s_is_exactly_five_pairs()
    test_python_s_matches_rust_decls()
    test_packs_are_scoped()
    test_constructors_emit_s_only()
    test_illegal_constructors_raise()
    test_split_alias_is_not_legal()
    test_project_strict_raises_on_unknown()
    test_host_illegal_project_ops_is_dispatch_error()
    test_baseline_pairs_untouched()
    print("catalog lock ok")
