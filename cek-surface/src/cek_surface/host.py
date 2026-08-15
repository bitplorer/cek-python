"""Intent / Result types. Authority is cek_host.Host (D3).

This module is not a Cap machine. Mint / verify / once live on cek_host.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Intent:
    action: str
    args: dict[str, Any] = field(default_factory=dict)
    cap: str | None = None
    activity_id: str | None = None
    idempotency_key: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Intent:
        return cls(
            action=str(d.get("action") or ""),
            args=dict(d.get("args") or {}),
            cap=d.get("cap"),
            activity_id=d.get("activity_id"),
            idempotency_key=d.get("idempotency_key"),
        )


@dataclass
class Result:
    kind: str  # ok | authority_refusal | dispatch_error
    ops: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "ops": self.ops, "error": self.error}

    @property
    def ok(self) -> bool:
        return self.kind == "ok"


@dataclass
class ActionContext:
    action: str
    args: dict[str, Any]
    host: Any = None
    claims: dict[str, Any] = field(default_factory=dict)


__all__ = ["Intent", "Result", "ActionContext"]
