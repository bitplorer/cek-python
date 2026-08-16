"""Host wrap — decide via the Rust host-kernel (`cek host-json`).

Python Host remains the production language port. This adapter is the
opt-in wrap of the reference kernel.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def find_cek_bin() -> str | None:
    env = os.environ.get("CEK_BIN")
    if env and Path(env).is_file():
        return env
    which = shutil.which("cek")
    if which:
        return which
    here = Path(__file__).resolve()
    for root in (here.parents[4] / "cek-runtime", here.parents[3] / "cek-runtime"):
        for kind in ("debug", "release"):
            cand = root / "target" / kind / "cek"
            if cand.is_file():
                return str(cand)
    return None


def host_json(payload: dict[str, Any], *, bin_path: str | None = None) -> dict[str, Any]:
    exe = bin_path or find_cek_bin()
    if not exe:
        raise FileNotFoundError("cek binary not found (build cek-cli or set CEK_BIN)")
    proc = subprocess.run(
        [exe, "host-json"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "cek host-json failed")
    return json.loads(proc.stdout)


class RustHostKernel:
    """Thin wrap of cek-host-kernel. Caps are Rust Cap objects (JSON)."""

    name = "cek_host_kernel.wrap"

    def __init__(self, *, bin_path: str | None = None) -> None:
        self.bin_path = bin_path
        self.stamp = None

    def mint(self, action: str, *, once: bool = False, **kw: Any) -> dict[str, Any]:
        cid = str(kw.get("id") or f"cap-{action}")
        return host_json(
            {"cmd": "mint", "id": cid, "action": action, "once": once},
            bin_path=self.bin_path,
        )

    def submit_intent(self, intent: dict[str, Any]) -> dict[str, Any]:
        return host_json({"cmd": "submit", "intent": intent}, bin_path=self.bin_path)
