"""doctor() — go/no-go. ≡ production factory checklist (G10)."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from . import Host

DEMO_SECRET = b"cek-host-dev-secret-change-me!!!"
MIN_SECRET_LEN = 32
VECTOR_PACK_VERSION = 3


@dataclass
class Finding:
    ok: bool
    id: str
    detail: str

    def line(self) -> str:
        mark = "ok" if self.ok else "FAIL"
        return f"  [{mark}] {self.id}: {self.detail}"


@dataclass
class DoctorReport:
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(f.ok for f in self.findings)

    def to_text(self) -> str:
        lines = ["cek-host doctor"]
        lines.extend(f.line() for f in self.findings)
        lines.append("doctor: " + ("PASS" if self.ok else "FAIL"))
        return "\n".join(lines)


def _finding_secret(secret: bytes) -> Finding:
    if secret == DEMO_SECRET:
        return Finding(False, "secret", "default demo secret — production() refuses it")
    if len(secret) < MIN_SECRET_LEN:
        return Finding(False, "secret", f"length {len(secret)} < {MIN_SECRET_LEN}")
    return Finding(True, "secret", f"length {len(secret)}")


def _finding_once(host: Host) -> Finding:
    label = host.once_label()
    if label == "memory" and host.mode != "demo" and not host.allow_memory_stores:
        return Finding(False, "once-store", "memory — not a security domain across workers")
    if label == "down":
        return Finding(False, "once-store", "marked down — Host must refuse (K6)")
    return Finding(True, "once-store", label)


def _finding_embedded() -> Finding:
    try:
        import cek_surface  # noqa: F401

        try:
            from cek_surface.kernel import EmbeddedHostKernel  # type: ignore

            if EmbeddedHostKernel is not None:
                return Finding(False, "embedded", "EmbeddedHostKernel is still importable")
        except ImportError:
            return Finding(True, "embedded", "EmbeddedHostKernel absent")
    except ImportError:
        return Finding(True, "embedded", "cek-surface not installed (host-only)")
    return Finding(True, "embedded", "EmbeddedHostKernel absent")


def _finding_d4() -> Finding:
    for name in ("cek_host", "cek_surface"):
        try:
            mod = importlib.import_module(name)
        except ImportError:
            continue
        graph = getattr(mod, "__dict__", {})
        if "ux_channel" in graph:
            return Finding(False, "d4", f"{name} imported ux_channel")
    # module-level import scan
    import sys

    for key in list(sys.modules):
        if key == "ux_channel" or key.startswith("ux_channel."):
            # only fail if a cek_* module pulled it
            importer = sys.modules.get("cek_surface") or sys.modules.get("cek_host")
            if importer is not None and any(
                getattr(importer, attr, None) is sys.modules[key]
                for attr in dir(importer)
            ):
                return Finding(False, "d4", "ux_channel imported from a cek-* package")
    return Finding(True, "d4", "cek_surface → ux_channel is []")


def _finding_vectors() -> Finding:
    try:
        from importlib.resources import files
    except ImportError:
        files = None  # pragma: no cover
    # vectors live in cek-surface, not the host wheel
    from pathlib import Path

    here = Path(__file__).resolve()
    candidates = [
        here.parents[4] / "cek-surface" / "vectors" / "surface_core.json",
        Path("cek-surface/vectors/surface_core.json"),
    ]
    for p in candidates:
        if p.is_file():
            import json

            data = json.loads(p.read_text(encoding="utf-8"))
            ver = data.get("version")
            if ver != VECTOR_PACK_VERSION:
                return Finding(False, "vectors", f"surface pack version {ver}, want {VECTOR_PACK_VERSION}")
            return Finding(True, "vectors", f"surface_core v{ver} ({len(data.get('cases') or [])} cases)")
    return Finding(True, "vectors", f"pack v{VECTOR_PACK_VERSION} (not on this path)")


def doctor(host: Host | None = None, *, fail: bool = False) -> DoctorReport:
    """Inspect a Host (or the demo defaults) plus the install graph."""
    from . import Host

    h = host if host is not None else Host()
    report = DoctorReport(
        findings=[
            _finding_secret(h.secret),
            Finding(h.require_cap, "require_cap", str(h.require_cap)),
            _finding_once(h),
            Finding(True, "mode", h.mode),
            _finding_embedded(),
            _finding_d4(),
            _finding_vectors(),
        ]
    )
    if fail and not report.ok:
        raise SystemExit(report.to_text())
    return report
