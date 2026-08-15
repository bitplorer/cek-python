"""Host kernel smoke — prefers cek_host package."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_surface import Op, Surface, load_host_kernel
from cek_surface.kernel import EmbeddedHostKernel


def test_loads_cek_host():
    k = load_host_kernel()
    # With python/cek_host on path, should wrap real Host
    name = type(k).__name__
    assert name in ("CekHostPyKernel", "EmbeddedHostKernel"), name
    # mint/submit smoke
    tok = k.mint("ping")
    r = k.submit("ping", {}, tok, project_ops=[{"ns": "sys", "name": "noop", "payload": {}}])
    assert r.kind == "ok"
    assert len(r.ops) == 1


def test_surface_uses_kernel():
    s = Surface()
    print("surface kernel", type(s.kernel).__name__)

    @s.action("ping")
    def ping(ctx):
        return [Op.log_append("pong")]

    out = s.submit("ping", {}, auto_mint=True, drain_async=False)
    assert out["result"]["kind"] == "ok"
    s.close()


def test_contract_op_names():
    """Hot ops align with Baseline-ish names used in vectors."""
    assert Op.kv_set("a", 1).to_dict()["ns"] == "kv"
    assert Op.ui_morph("t", {}).to_dict()["name"] == "morph"
    assert Op.ui_toast("x").to_dict()["ns"] == "ui"


if __name__ == "__main__":
    test_loads_cek_host()
    test_surface_uses_kernel()
    test_contract_op_names()
    print("host kernel ok", type(load_host_kernel()).__name__)
