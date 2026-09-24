"""0.2.0 public surface. 0.1.3 legal names do not install."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

import cek_host
import cek_surface
from cek_host import Host


REMOVED = ("is_legal", "LEGAL_PAIRS", "LEGAL_FQS", "IllegalOp", "DEMO_SECRET")
PRESENT = (
    "in_catalog",
    "CATALOG_PAIRS",
    "CATALOG_FQS",
    "UndeclaredPair",
    "DEV_SECRET",
    "project_wire",
)


def test_version_is_020() -> None:
    assert cek_host.__version__ == "0.2.0"
    assert cek_surface.__version__ == "0.2.0"


def test_legal_module_is_gone() -> None:
    try:
        importlib.import_module("cek_host.legal")
    except ModuleNotFoundError:
        return
    raise AssertionError("cek_host.legal must not install on 0.2.0")


def test_public_names() -> None:
    for name in REMOVED:
        assert not hasattr(cek_host, name), name
        assert name not in cek_surface.__all__
    for name in PRESENT:
        assert hasattr(cek_host, name), name


def test_host_mode_is_dev_or_prod() -> None:
    host = Host.dev()
    assert host.mode == "dev"
    for bad in ("demo", "production", "adapt", ""):
        try:
            Host(mode=bad)
        except ValueError as exc:
            assert "dev|prod" in str(exc)
        else:
            raise AssertionError(f"mode {bad!r} must refuse")


if __name__ == "__main__":
    test_version_is_020()
    test_legal_module_is_gone()
    test_public_names()
    test_host_mode_is_dev_or_prod()
    print("public 0.2.0 ok")
