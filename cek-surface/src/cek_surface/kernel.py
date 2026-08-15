"""Host-kernel boundary.

cek-surface does **not** reimplement the Cap state machine long-term.
It calls a Host kernel (cek-host / CEK Host) for authority.

Until cek-host is installed, EmbeddedHostKernel is a local shim so demos run.
Replace with CekHostPyKernel when available.
"""


from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

try:
    from cek_host import CapError, CapService, KernelResult as HostKernelResult
except ImportError:
    from .cap import CapError, CapService  # type: ignore
    HostKernelResult = None
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


@runtime_checkable
class HostKernel(Protocol):
    """Minimal surface expected from cek-host (or embedded shim)."""

    def mint(
        self,
        action: str,
        *,
        once: bool = False,
        args: dict[str, Any] | None = None,
        seal_args: bool = False,
        **kw: Any,
    ) -> str: ...

    def submit(
        self,
        action: str,
        args: dict[str, Any],
        cap: str | None,
        *,
        activity_id: str | None = None,
        project_ops: list[dict[str, Any]] | None = None,
    ) -> KernelResult:
        """
        Verify Cap for action+args, then either:
          - project_ops is provided (surface already composed) → accept under Cap, or
          - kernel dispatches internally (if it owns handlers).

        cek-surface prefers: app composes list[Op], kernel only authorizes + packages Result.
        """
        ...


class EmbeddedHostKernel:
    """Shim: Cap verify + package ops. Not a full CEK Host (no lineage/idem/BoundAsk).

    Swap for cek-host when packaging for production.
    """

    def __init__(self, secret: bytes = b"cek-surface-dev-secret-change-me", require_cap: bool = True):
        self.caps = CapService(secret=secret)
        self.require_cap = require_cap

    def mint(
        self,
        action: str,
        *,
        once: bool = False,
        args: dict[str, Any] | None = None,
        seal_args: bool = False,
        **kw: Any,
    ) -> str:
        return self.caps.mint(action, once=once, args=args, seal_args=seal_args, **kw)

    def submit(
        self,
        action: str,
        args: dict[str, Any],
        cap: str | None,
        *,
        activity_id: str | None = None,
        project_ops: list[dict[str, Any]] | None = None,
    ) -> KernelResult:
        action = (action or "").strip()
        if not action:
            return KernelResult("authority_refusal", [], "empty action")
        if self.require_cap or cap:
            if not cap:
                return KernelResult("authority_refusal", [], "cap required")
            try:
                self.caps.verify(cap, action, args)
            except CapError as e:
                return KernelResult("authority_refusal", [], str(e))
        ops = project_ops if project_ops is not None else []
        return KernelResult("ok", list(ops))


def load_host_kernel() -> HostKernel:
    """Prefer cek-host; fall back to embedded shim."""
    try:
        from cek_host import Host as CekHost  # type: ignore

        # Adapter shape may differ — normalize when cek-host API is fixed.
        class CekHostPyKernel:
            def __init__(self) -> None:
                self._inner = CekHost()

            def mint(self, action: str, **kw: Any) -> str:
                return self._inner.mint(action, **kw)

            def submit(
                self,
                action: str,
                args: dict[str, Any],
                cap: str | None,
                *,
                activity_id: str | None = None,
                project_ops: list[dict[str, Any]] | None = None,
            ) -> KernelResult:
                # Prefer explicit ops projection from surface
                if project_ops is not None and hasattr(self._inner, "submit_ops"):
                    r = self._inner.submit_ops(project_ops, cap=cap, action=action, args=args)
                else:
                    r = self._inner.submit(
                        {"action": action, "args": args, "cap": cap, "activity_id": activity_id}
                    )
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

        return CekHostPyKernel()
    except Exception:
        return EmbeddedHostKernel()
