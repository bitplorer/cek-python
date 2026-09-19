"""Peer wrap — apply via the in-process Rust peer-kernel (`cek_peer_pyo3`).

Taught path: `carrier_kind="kernel"` → PyO3 `PeerAbi`
construct → bind → apply → release. Same JSON as wasm / `cek apply`
(`{ result, profile, unknown_op_policy }` → `{ receipt, kv, ui, log }`).

Does not reimplement apply. No mint. Not a Python Peer kernel.

Leftover (untaught, until absence lock): subprocess `cek apply` via
`CEK_KERNEL_CARRIER=subprocess` or `backend="subprocess"`. Do not teach
that door as an equal default.

Install the taught module from cek-runtime (same crate; no second wheel
story). See `PYO3_INSTALL`.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Taught install — matches cek-runtime ports/cek-peer-pyo3 (SHA 5e58cca).
PYO3_INSTALL = """cek_peer_pyo3 is not installed (taught kernel carrier).

Install from bitplorer/cek-runtime (crates/cek-peer-pyo3 + ports/cek-peer-pyo3).
Do not invent a second packaging story — cargo build of that crate is the door:

  git clone https://github.com/bitplorer/cek-runtime && cd cek-runtime
  git checkout 5e58cca7ea1f59e2b73ebfc49222edc5eb81544a
  cargo build -p cek-peer-pyo3 --features extension-module --release

Needs python3-dev / libpython headers. Then either:

  export CEK_PEER_PYO3=$PWD/target/release/libcek_peer_pyo3.so

or put a copy named cek_peer_pyo3.so on PYTHONPATH and `import cek_peer_pyo3`.

See cek-runtime ports/cek-peer-pyo3/README.md.

Leftover (untaught): CEK_KERNEL_CARRIER=subprocess uses `cek apply`.
"""

_LOADED_MOD: Any | None = None

_CDYLIB_NAMES = (
    "cek_peer_pyo3.so",
    "libcek_peer_pyo3.so",
    "cek_peer_pyo3.dylib",
    "libcek_peer_pyo3.dylib",
    "cek_peer_pyo3.pyd",
    "cek_peer_pyo3.dll",
)


def reset_pyo3_cache() -> None:
    """Drop the cached extension (tests). Not a kernel door."""
    global _LOADED_MOD
    _LOADED_MOD = None


def _taught_backend(explicit: str | None) -> str:
    raw = (explicit or os.environ.get("CEK_KERNEL_CARRIER") or "pyo3").strip().lower()
    if raw in ("subprocess", "cek-apply", "cli"):
        return "subprocess"
    if raw in ("pyo3", "cek_peer_pyo3", "inproc", "taught", ""):
        return "pyo3"
    raise ValueError(
        f"unknown kernel carrier backend: {raw!r} (taught: pyo3; leftover: subprocess)"
    )


def _runtime_roots() -> list[Path]:
    here = Path(__file__).resolve()
    roots: list[Path] = []
    for idx in (3, 4):
        if idx < len(here.parents):
            roots.append(here.parents[idx] / "cek-runtime")
    roots.extend((Path.cwd() / "cek-runtime", Path.cwd().parent / "cek-runtime"))
    return roots


def find_cek_peer_pyo3() -> str | None:
    """Locate the taught cdylib. None if the module is not installed."""
    env = os.environ.get("CEK_PEER_PYO3")
    if env and Path(env).is_file():
        return env
    try:
        import cek_peer_pyo3  # type: ignore

        loc = getattr(cek_peer_pyo3, "__file__", None)
        if loc and Path(loc).is_file():
            return str(Path(loc))
    except ImportError:
        pass
    for root in _runtime_roots():
        for kind in ("release", "debug"):
            folder = root / "target" / kind
            for name in _CDYLIB_NAMES:
                cand = folder / name
                if cand.is_file():
                    return str(cand)
    return None


def _load_cdylib(path: str) -> Any:
    spec = importlib.util.spec_from_file_location("cek_peer_pyo3", path)
    if spec is None or spec.loader is None:
        raise ImportError(PYO3_INSTALL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "PeerAbi"):
        raise ImportError("cek_peer_pyo3 is missing PeerAbi — not the taught ABI")
    sys.modules.setdefault("cek_peer_pyo3", mod)
    return mod


def load_cek_peer_pyo3() -> Any:
    """Import the taught apply-only module. Fail closed with install text."""
    global _LOADED_MOD
    if _LOADED_MOD is not None:
        return _LOADED_MOD
    try:
        import cek_peer_pyo3  # type: ignore

        if hasattr(cek_peer_pyo3, "PeerAbi"):
            _LOADED_MOD = cek_peer_pyo3
            return _LOADED_MOD
    except ImportError:
        pass
    path = find_cek_peer_pyo3()
    if not path:
        raise ImportError(PYO3_INSTALL)
    _LOADED_MOD = _load_cdylib(path)
    return _LOADED_MOD


def _apply_request(
    result: dict[str, Any],
    *,
    profile: str,
    unknown_op_policy: str,
) -> dict[str, Any]:
    return {
        "result": result,
        "profile": profile,
        "unknown_op_policy": unknown_op_policy,
    }


def _apply_via_pyo3(
    result: dict[str, Any],
    *,
    profile: str,
    unknown_op_policy: str,
    abi: Any | None = None,
) -> dict[str, Any]:
    """One apply through a bound handle. Caller owns construct/bind/release."""
    if abi is None:
        raise RuntimeError("PeerAbi handle is not bound (released or never constructed)")
    req = _apply_request(result, profile=profile, unknown_op_policy=unknown_op_policy)
    resp = abi.apply(req)
    if isinstance(resp, str):
        resp = json.loads(resp)
    if not isinstance(resp, dict):
        raise RuntimeError("cek_peer_pyo3.apply did not return a receipt document")
    return resp


def _apply_via_subprocess_leftover(
    result: dict[str, Any],
    *,
    profile: str,
    unknown_op_policy: str,
    bin_path: str | None,
) -> dict[str, Any]:
    """Untaught leftover door. Named so it cannot be mistaken for the default."""
    from cek_host.rust_wrap import find_cek_bin

    exe = bin_path or find_cek_bin()
    if not exe:
        raise FileNotFoundError(
            "leftover kernel carrier needs the cek binary "
            "(build cek-cli or set CEK_BIN). Taught path is cek_peer_pyo3."
        )
    req = _apply_request(result, profile=profile, unknown_op_policy=unknown_op_policy)
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


def apply_via_kernel(
    result: dict[str, Any],
    *,
    profile: str = "ui",
    unknown_op_policy: str = "skip",
    bin_path: str | None = None,
    backend: str | None = None,
) -> dict[str, Any]:
    """Call the Rust peer-kernel. Taught: in-process PyO3. Raises if missing."""
    kind = _taught_backend(backend)
    if kind == "subprocess":
        return _apply_via_subprocess_leftover(
            result,
            profile=profile,
            unknown_op_policy=unknown_op_policy,
            bin_path=bin_path,
        )
    if bin_path:
        raise ValueError(
            "bin_path is leftover subprocess only; taught kernel uses cek_peer_pyo3. "
            "Pass backend='subprocess' to use the untaught cek apply door."
        )
    mod = load_cek_peer_pyo3()
    abi = mod.PeerAbi.construct()
    abi.bind()
    try:
        return _apply_via_pyo3(
            result, profile=profile, unknown_op_policy=unknown_op_policy, abi=abi
        )
    finally:
        abi.release()


class KernelPeerCarrier:
    """Carrier that wraps the Rust Peer kernel (taught: PyO3). No mint."""

    name = "kernel"

    def __init__(
        self,
        *,
        profile: str = "ui",
        bin_path: str | None = None,
        backend: str | None = None,
    ) -> None:
        self.profile = profile
        self.bin_path = bin_path
        self.backend = _taught_backend(backend)
        self._last_stamp: list[dict[str, str]] = []
        self._abi: Any | None = None
        if self.backend == "subprocess":
            return
        if bin_path:
            raise ValueError(
                "bin_path is leftover subprocess only; taught kernel uses cek_peer_pyo3. "
                "Pass backend='subprocess' to use the untaught cek apply door."
            )
        mod = load_cek_peer_pyo3()
        abi = mod.PeerAbi.construct()
        try:
            abi.bind()
        except Exception:
            abi.release()
            raise
        self._abi = abi

    def apply(self, result: dict[str, Any]) -> dict[str, Any]:
        if self.backend == "subprocess":
            resp = _apply_via_subprocess_leftover(
                result,
                profile=self.profile,
                unknown_op_policy="skip",
                bin_path=self.bin_path,
            )
        else:
            resp = _apply_via_pyo3(result, profile=self.profile, unknown_op_policy="skip", abi=self._abi)
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
        abi = self._abi
        self._abi = None
        if abi is not None:
            abi.release()
