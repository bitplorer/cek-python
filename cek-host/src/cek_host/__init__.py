"""cek-host — Python Host kernel (authority).

Mint/verify Caps, package projected Ops into Results.
Surface and apps depend on this; Peers never import it for mint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .cap import CapError, CapService

__version__ = "0.1.0"


@dataclass
class KernelResult:
    kind: str
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


class Host:
    """Authority kernel: Cap machine + Result packaging."""

    def __init__(self, secret: bytes = b"cek-host-dev-secret-change-me!!!", require_cap: bool = True):
        self.caps = CapService(secret=secret)
        self.require_cap = require_cap
        self.name = "cek_host.Host"

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
        intent: dict[str, Any] | None = None,
        *,
        action: str | None = None,
        args: dict[str, Any] | None = None,
        cap: str | None = None,
        activity_id: str | None = None,
        project_ops: list[dict[str, Any]] | None = None,
        **_kw: Any,
    ) -> KernelResult:
        if intent is not None:
            action = intent.get("action") or action
            args = intent.get("args") if args is None else args
            cap = intent.get("cap") if cap is None else cap
            activity_id = intent.get("activity_id") if activity_id is None else activity_id
        action = (action or "").strip()
        args = dict(args or {})
        if not action:
            return KernelResult("authority_refusal", [], "empty action")
        if self.require_cap or cap:
            if not cap:
                return KernelResult("authority_refusal", [], "cap required")
            try:
                self.caps.verify(cap, action, args)
            except CapError as e:
                return KernelResult("authority_refusal", [], str(e))
        return KernelResult("ok", list(project_ops or []))

    def submit_ops(
        self,
        project_ops: list[dict[str, Any]],
        *,
        cap: str | None = None,
        action: str = "",
        args: dict[str, Any] | None = None,
    ) -> KernelResult:
        return self.submit(action=action, args=args or {}, cap=cap, project_ops=project_ops)


__all__ = ["Host", "KernelResult", "CapService", "CapError", "__version__"]
