"""W2 — explain catalog + doctor + create-app smoke."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST_SRC = ROOT.parent / "cek-host" / "src"
SURF_SRC = ROOT / "src"
sys.path.insert(0, str(SURF_SRC))
sys.path.insert(0, str(HOST_SRC))

from cek_host import Host, explain
from cek_host.cli import main as cli_main
from cek_host.scaffold import create_app


def test_explain_top_failures():
    cases = [
        ("cap required", "missing_cap"),
        ("once cap already used", "once_replay"),
        ("sealed-args mismatch", "sealed_args_tamper"),
        ("cap expired", "expired"),
        ("action mismatch", "action_mismatch"),
        ("subject bind mismatch", "subject_mismatch"),
        ("once store down", "store_down"),
        ("default secret", "short_secret"),
        ("EmbeddedHostKernel", "embedded_kernel"),
        ("require_cap", "require_cap_false"),
        ("memory once-store", "memory_once"),
        ("empty action", "empty_action"),
        ("cap signature invalid", "hmac_tamper"),
        ("illegal pair: nav.push", "illegal_op"),
    ]
    for err, code in cases:
        e = explain(err)
        assert e.code == code, (err, e.code)
        assert e.fix


def test_cli_explain_and_version():
    assert cli_main(["version"]) == 0
    assert cli_main(["explain", "once cap already used"]) == 0
    assert cli_main(["doctor", "--production-demo"]) == 0


def test_create_app_runs():
    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "demo-app"
        create_app(dest)
        assert (dest / "app.py").is_file()
        readme = (dest / "README.md").read_text()
        assert "doctor" in readme
        assert "require_cap" in readme
        env = dict(**{k: v for k, v in __import__("os").environ.items()})
        env["PYTHONPATH"] = f"{HOST_SRC}:{SURF_SRC}"
        # Generated app uses Surface(kernel=host). Host is a HostKernel via duck typing
        # (mint/check/submit). Memory carrier needs no Node.
        proc = subprocess.run(
            [sys.executable, str(dest / "app.py")],
            cwd=str(dest),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stdout + "\n" + proc.stderr)
        assert "once replay refused" in proc.stdout


if __name__ == "__main__":
    test_explain_top_failures()
    test_cli_explain_and_version()
    test_create_app_runs()
    print("explain/doctor/create-app ok")
