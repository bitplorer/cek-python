"""D3 + D4 + one Cap machine. No Embedded. No sketch Host. No ux_channel.

W4 / G4 / G12. KILL: reverse import or second Cap machine.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT.parent / "cek-host" / "src"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HOST))


def _imports_of(tree_root: Path) -> list[str]:
    names: list[str] = []
    for p in tree_root.rglob("*.py"):
        src = p.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.extend(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module.split(".")[0])
    return names


def test_d4_no_ux_channel():
    for root in (ROOT / "src" / "cek_surface", HOST / "cek_host"):
        names = _imports_of(root)
        assert "ux_channel" not in names, root


def test_d3_surface_cap_reexports_host():
    import cek_surface.cap as scap
    import cek_host.cap as hcap

    assert scap.CapService is hcap.CapService
    assert scap.CapError is hcap.CapError


def test_one_published_host():
    from cek_host import Host
    from cek_surface.kernel import CekHostPyKernel, load_host_kernel

    k = load_host_kernel()
    assert isinstance(k, CekHostPyKernel)
    assert isinstance(k._inner, Host)


def test_embedded_not_in_all():
    import cek_surface

    assert "Host" not in cek_surface.__all__
    assert "EmbeddedHostKernel" not in cek_surface.__all__
    try:
        from cek_surface.kernel import EmbeddedHostKernel  # noqa: F401

        raise AssertionError("EmbeddedHostKernel importable")
    except ImportError:
        pass


def test_sketch_host_gone():
    import cek_surface.host as hmod

    assert not hasattr(hmod, "Host")
    try:
        from cek_surface.host import Host  # noqa: F401

        raise AssertionError("cek_surface.host.Host must not import")
    except ImportError:
        pass


def test_peer_modules_have_no_mint():
    js = (ROOT / "js").glob("*.mjs")
    for p in js:
        text = p.read_text(encoding="utf-8")
        assert "function mint" not in text
        assert ".mint(" not in text or "/* mint lives on Host" in text


if __name__ == "__main__":
    test_d4_no_ux_channel()
    test_d3_surface_cap_reexports_host()
    test_one_published_host()
    test_embedded_not_in_all()
    test_sketch_host_gone()
    test_peer_modules_have_no_mint()
    print("layer honesty ok")
