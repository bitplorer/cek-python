"""Phase 3 — wrap Rust kernels. Skip (exit 0) if `cek` binary is not built."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host.rust_wrap import RustHostKernel, find_cek_bin
from cek_surface.kernel_peer import KernelPeerCarrier, apply_via_kernel


def test_find_or_skip():
    exe = find_cek_bin()
    if not exe:
        print("phase3 wrap skip (no cek binary)")
        return
    # Peer wrap: kv.set lands
    resp = apply_via_kernel(
        {
            "kind": "ok",
            "ops": [{"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}}],
        },
        profile="baseline",
        bin_path=exe,
    )
    assert resp["receipt"]["landed"]
    assert resp["kv"]["a"] == 1
    # refuse is noop
    refuse = apply_via_kernel(
        {"kind": "authority_refusal", "ops": [], "error": "no"},
        profile="baseline",
        bin_path=exe,
    )
    assert refuse["kv"] == {} or "a" not in refuse.get("kv", {})
    # Host wrap: mint + submit kv.write
    wrap = RustHostKernel(bin_path=exe)
    cap = wrap.mint("kv.write", id="wrap-1")
    assert cap.get("action") == "kv.write"
    result = wrap.submit_intent(
        {
            "action": "kv.write",
            "args": {"key": "g", "value": "hi"},
            "cap": cap,
        }
    )
    assert result.get("kind") in ("ok", "authority_refusal")
    if result.get("kind") == "ok":
        assert result["ops"]
        assert result["ops"][0]["ns"] == "kv"
    # Carrier façade
    c = KernelPeerCarrier(profile="baseline", bin_path=exe)
    applied = c.apply(
        {"kind": "ok", "ops": [{"ns": "kv", "name": "set", "payload": {"key": "z", "value": 9}}]}
    )
    assert applied["type"] == "applied"
    assert applied["world"]["kv"]["z"] == 9
    print("phase3 wrap ok")


if __name__ == "__main__":
    test_find_or_skip()
