"""Host wrap — decide via the Rust host-kernel (`cek host-json`).

Python Host remains the production language port. This adapter is the
opt-in wrap of the reference kernel.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from importlib import metadata
from pathlib import Path
from typing import Any


def _own_scripts() -> set[Path]:
    """Console scripts that cek-host installed.

    Every match is read: a source-tree egg-info found first on sys.path has
    no RECORD, while the installed dist-info does.
    """
    scripts: set[Path] = set()
    for dist in metadata.distributions(name="cek-host"):
        names = {ep.name for ep in dist.entry_points if ep.group == "console_scripts"}
        scripts.update(
            Path(dist.locate_file(f)).resolve()
            for f in dist.files or ()
            if Path(f).stem in names and Path(f).parent.name in ("bin", "Scripts")
        )
    return scripts


def _is_python_cli(path: str) -> bool:
    """True for cek-host's own `cek` script, never the Rust cek-cli.

    The RECORD check covers this environment; the text check covers a
    cek-host script installed by another environment (pipx, a second venv).
    """
    resolved = Path(path).resolve()
    if resolved in _own_scripts():
        return True
    try:
        with open(resolved, "rb") as f:
            return b"cek_host.cli" in f.read(4096)
    except OSError:
        return False


def find_cek_bin() -> str | None:
    env = os.environ.get("CEK_BIN")
    if env and Path(env).is_file():
        return env
    for d in os.environ.get("PATH", os.defpath).split(os.pathsep):
        which = shutil.which("cek", path=d)
        if which and not _is_python_cli(which):
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
