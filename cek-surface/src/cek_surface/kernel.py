"""Host-kernel boundary.

cek-surface does not reimplement the Cap state machine.
It calls cek-host. load_host_kernel fails closed if cek-host is missing.
EmbeddedHostKernel is gone (D3 / G4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from cek_host import Host as CekHost
from cek_host import KernelResult as HostKernelResult
from cek_host import CapError, CapService, explain
from .ops import Op, as_wire


@dataclass
class KernelResult:
    kind: str  # ok | authority_refusal | dispatch_error
    ops: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    digest: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"kind": self.kind, "ops": self.ops, "error": self.error}
        if self.digest is not None:
            d["digest"] = self.digest
        return d

    @property
    def ok(self) -> bool:
        return self.kind == "ok"

    def explain(self):
        return explain(self.error)


@runtime_checkable
class HostKernel(Protocol):
    """Minimal surface expected from cek-host."""

    def mint(
        self,
        action: str,
        *,
        once: bool = False,
        args: dict[str, Any] | None = None,
        seal_args: bool = False,
        **kw: Any,
    ) -> str: ...

    def check(
        self,
        action: str,
        args: dict[str, Any],
        cap: str | None,
        *,
        activity_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> KernelResult: ...

    def submit(
        self,
        action: str,
        args: dict[str, Any],
        cap: str | None,
        *,
        activity_id: str | None = None,
        project_ops: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
    ) -> KernelResult: ...


class CekHostPyKernel:
    """Thin adapter. One Cap machine: cek_host.Host."""

    def __init__(self, inner: CekHost | None = None) -> None:
        self._inner = inner if inner is not None else CekHost()
        self.name = getattr(self._inner, "name", "cek_host.Host")

    def mint(self, action: str, **kw: Any) -> str:
        return self._inner.mint(action, **kw)

    def check(
        self,
        action: str,
        args: dict[str, Any],
        cap: str | None,
        *,
        activity_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> KernelResult:
        r = self._inner.check(
            action, args, cap, activity_id=activity_id, idempotency_key=idempotency_key
        )
        return _as_kernel_result(r)

    def submit(
        self,
        action: str,
        args: dict[str, Any],
        cap: str | None,
        *,
        activity_id: str | None = None,
        project_ops: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
    ) -> KernelResult:
        r = self._inner.submit(
            action=action,
            args=args,
            cap=cap,
            activity_id=activity_id,
            project_ops=project_ops,
            idempotency_key=idempotency_key,
        )
        return _as_kernel_result(r)

    async def async_check(
        self,
        action: str,
        args: dict[str, Any],
        cap: str | None,
        *,
        activity_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> KernelResult:
        import asyncio

        inner = getattr(self._inner, "async_check", None)
        if inner is not None:
            r = await inner(
                action, args, cap, activity_id=activity_id, idempotency_key=idempotency_key
            )
        else:
            r = await asyncio.to_thread(
                self._inner.check,
                action,
                args,
                cap,
                activity_id=activity_id,
                idempotency_key=idempotency_key,
            )
        return _as_kernel_result(r)

    async def async_submit(
        self,
        action: str,
        args: dict[str, Any],
        cap: str | None,
        *,
        activity_id: str | None = None,
        project_ops: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
    ) -> KernelResult:
        import asyncio

        inner = getattr(self._inner, "async_submit", None)
        if inner is not None:
            r = await inner(
                action=action,
                args=args,
                cap=cap,
                activity_id=activity_id,
                project_ops=project_ops,
                idempotency_key=idempotency_key,
            )
        else:
            r = await asyncio.to_thread(
                self._inner.submit,
                action=action,
                args=args,
                cap=cap,
                activity_id=activity_id,
                project_ops=project_ops,
                idempotency_key=idempotency_key,
            )
        return _as_kernel_result(r)

    def report_receipt(self, activity_id: str, landed: list[dict[str, Any]] | None = None, **kw: Any):
        return self._inner.report_receipt(activity_id, landed, **kw)

    def end_activity(self, activity_id: str):
        return self._inner.end_activity(activity_id)

    def explain(self, error: str | None = None):
        return explain(error)

    def doctor(self, **kw: Any):
        return self._inner.doctor(**kw)


def _as_kernel_result(r: Any) -> KernelResult:
    if isinstance(r, dict):
        return KernelResult(
            kind=r.get("kind") or ("ok" if r.get("ok") else "authority_refusal"),
            ops=list(r.get("ops") or []),
            error=r.get("error"),
            digest=r.get("digest"),
        )
    return KernelResult(
        kind=getattr(r, "kind", "ok"),
        ops=list(getattr(r, "ops", []) or []),
        error=getattr(r, "error", None),
        digest=getattr(r, "digest", None),
    )


def load_host_kernel(host: CekHost | None = None) -> HostKernel:
    """Fail closed if cek-host is missing. No EmbeddedHostKernel."""
    try:
        inner = host if host is not None else CekHost()
    except Exception as e:  # constructor bugs are not a second Cap machine
        raise RuntimeError("cek-host Host() failed closed") from e
    return CekHostPyKernel(inner)


# Kept as a name so `from cek_surface.kernel import EmbeddedHostKernel` raises
# a clear error instead of succeeding with a shim.
def __getattr__(name: str):
    if name == "EmbeddedHostKernel":
        raise ImportError(
            "EmbeddedHostKernel is gone (D3). pip install cek-host and use load_host_kernel()."
        )
    raise AttributeError(name)
