"""`cek` on PATH: the Rust cek-cli wins over cek-host's own `cek` script.

Both are on PATH in either order. find_cek_bin must pick the Rust binary,
and RustHostKernel must reach it. CEK_BIN still overrides.
"""

from __future__ import annotations

import contextlib
import io
import os
import stat
import sys
import sysconfig
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host.cli import deprecated_main, main
from cek_host.rust_wrap import RustHostKernel, find_cek_bin

FAKE_RUST = """#!/bin/sh
[ "$1" = host-json ] || exit 2
cat >/dev/null
echo '{"action": "buy", "fake": "rust"}'
"""

# What pip writes for `cek = "cek_host.cli:deprecated_main"`.
PIP_SCRIPT = f"""#!{sys.executable}
import sys
from cek_host.cli import deprecated_main
if __name__ == "__main__":
    sys.exit(deprecated_main())
"""


def _write_exe(path: Path, text: str) -> None:
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _python_cek_dir(tmp: Path) -> Path:
    """The installed `cek` script's directory, or a pip-style copy."""
    installed = Path(sysconfig.get_path("scripts")) / "cek"
    if installed.is_file():
        return installed.parent
    d = tmp / "py"
    d.mkdir()
    _write_exe(d / "cek", PIP_SCRIPT)
    return d


@contextlib.contextmanager
def _env(path: str, cek_bin: str | None = None):
    old = {k: os.environ.get(k) for k in ("PATH", "CEK_BIN")}
    os.environ["PATH"] = path
    os.environ.pop("CEK_BIN", None)
    if cek_bin:
        os.environ["CEK_BIN"] = cek_bin
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_rust_cek_wins_both_orders():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        rust_dir = tmp / "rust"
        rust_dir.mkdir()
        rust = rust_dir / "cek"
        _write_exe(rust, FAKE_RUST)
        py_dir = _python_cek_dir(tmp)
        for order in ((py_dir, rust_dir), (rust_dir, py_dir)):
            with _env(os.pathsep.join(map(str, order))):
                assert find_cek_bin() == str(rust), (order, find_cek_bin())
                assert RustHostKernel().mint("buy")["fake"] == "rust"
        with _env(str(py_dir)):
            assert find_cek_bin() != str(py_dir / "cek")
        with _env(str(py_dir), cek_bin=str(py_dir / "cek")):
            assert find_cek_bin() == str(py_dir / "cek")


def test_cek_script_warns_deprecated():
    err = io.StringIO()
    old_argv = sys.argv
    sys.argv = ["cek", "version"]
    try:
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            assert deprecated_main() == 0
    finally:
        sys.argv = old_argv
    line = err.getvalue()
    assert line.count("\n") == 1 and "0.3.0" in line and "cek-host" in line, line


def test_help_names_invoked_script():
    old_argv = sys.argv
    try:
        for argv0, entry, prog in (
            ("/venv/bin/cek", deprecated_main, "cek"),
            ("/venv/bin/cek-host", main, "cek-host"),
            ("/src/cek_host/__main__.py", main, "cek-host"),
        ):
            sys.argv = [argv0, "--help"]
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                try:
                    entry()
                except SystemExit as e:
                    assert e.code == 0
            assert out.getvalue().startswith(f"usage: {prog} "), (argv0, out.getvalue())
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    test_rust_cek_wins_both_orders()
    test_cek_script_warns_deprecated()
    test_help_names_invoked_script()
    print("cek bin ok")
