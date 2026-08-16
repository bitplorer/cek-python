"""Peer wrap — apply via the Rust peer-kernel (`cek apply`).

Does not reimplement apply. Requires the `cek` binary (cek-cli).
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

from cek_host.rust_wrap import find_cek_bin


def apply_via_kernel(
    result: dict[str, Any],
    *,
    profile: str = "ui",
    unknown_op_policy: str = "skip",
    bin_path: str | None = None,
) -> dict[str, Any]:
    """Call Rust peer-kernel. Raises if the wrap binary is missing."""
    exe = bin_path or find_cek_bin()
    if not exe:
        raise FileNotFoundError("cek binary not found (build cek-cli or set CEK_BIN)")
    req = {
        "result": result,
        "profile": profile,
        "unknown_op_policy": unknown_op_policy,
    }
    proc = subprocess.run(
        [exe, "apply"],
        input=json.dumps(req),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "cek apply failed")
    return json.loads(proc.stdout)


class KernelPeerCarrier:
    """Carrier that wraps the Rust Peer kernel. No mint."""

    name = "kernel"

    def __init__(self, *, profile: str = "ui", bin_path: str | None = None) -> None:
        self.profile = profile
        self.bin_path = bin_path
        self._last_stamp: list[dict[str, str]] = []

    def apply(self, result: dict[str, Any]) -> dict[str, Any]:
        resp = apply_via_kernel(result, profile=self.profile, bin_path=self.bin_path)
        receipt = resp.get("receipt") or {"landed": [], "failed": []}
        world = {
            "kv": resp.get("kv") or {},
            "ui": resp.get("ui") or {},
            "log": resp.get("log") or [],
        }
        return {"type": "applied", "receipt": receipt, "world": world}

    def stamp(self, pairs: list[dict[str, str]]) -> dict[str, Any]:
        # Recorded for Host/session honesty. The Rust kernel apply-set is
        # still the profile (Baseline or Baseline+UI). Extensions in this
        # stamp will be skipped by the kernel (no driver there).
        self._last_stamp = list(pairs)
        return {"type": "stamp_ack", "pairs": pairs, "kernel_apply": "profile"}

    def chrome(self, chrome: dict[str, Any]) -> dict[str, Any]:
        return {"type": "chrome_applied", "world": {}}

    def read_event(self, timeout: float | None = None) -> dict[str, Any] | None:
        return None

    def close(self) -> None:
        return None
