"""search domain stdlib — runtime expansion, not core S."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import Host, IllegalOp
from cek_host.legal import LEGAL_PAIRS, is_legal
from cek_surface import Op, Surface, search_clear, search_hits
from cek_surface.domain_loader import load_bundled
from cek_surface.domain_stdlib import REGISTRY, agree, stamp_from_agreement


def test_search_not_in_s():
    assert not is_legal("search", "hits")
    assert ("search", "hits") not in LEGAL_PAIRS


def test_load_bundled_search():
    load_bundled()
    s = REGISTRY.get("search")
    assert s is not None
    assert ("search", "hits") in s.pairs()
    assert ("search", "clear") in s.pairs()


def test_stamp_and_project():
    load_bundled()
    stamp = stamp_from_agreement(agree(["baseline", "ui", "search"], ["baseline", "ui", "search"]))
    assert ("search", "hits") in stamp
    h = Host(secret=b"library-polish-secret-32bytes!!")
    h.stamp = stamp
    op = search_hits("results", [{"title": "a"}], q="a", stamp=stamp)
    r = h.submit(action="q", args={}, cap=h.mint("q"), project_ops=[op.to_dict()])
    assert r.kind == "ok"
    assert r.ops[0]["ns"] == "search"
    h.stamp = LEGAL_PAIRS
    r2 = h.submit(action="q", args={}, cap=h.mint("q"), project_ops=[op.to_dict()])
    assert r2.kind == "dispatch_error"


def test_surface_use_search():
    load_bundled()
    s = Surface(carrier_kind="memory")
    s.use_stdlibs(["baseline", "ui", "search"])
    assert ("search", "hits") in s.stamp
    op = search_hits("results", [], q="", stamp=s.stamp)
    assert op.ns == "search"
    clr = search_clear("results", stamp=s.stamp)
    assert clr.name == "clear"
    try:
        Op("search", "hits", {})
        raise AssertionError("Op() without stamp must not invent S")
    except ValueError:
        pass


if __name__ == "__main__":
    test_search_not_in_s()
    test_load_bundled_search()
    test_stamp_and_project()
    test_surface_use_search()
    print("search stdlib ok")
