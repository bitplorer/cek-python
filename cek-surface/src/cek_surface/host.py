"""Host kernel sketch — Intent + Cap → Result.ops.

Peer never mints. Refuse → ops=[].
Action handlers are pure Python composition returning list[Op].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .cap import CapError, CapService
from .ops import Op, as_wire


Handler = Callable[["ActionContext"], list[Op]]


@dataclass
class Intent:
    action: str
    args: dict[str, Any] = field(default_factory=dict)
    cap: str | None = None
    activity_id: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Intent:
        return cls(
            action=str(d.get("action") or ""),
            args=dict(d.get("args") or {}),
            cap=d.get("cap"),
            activity_id=d.get("activity_id"),
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
    host: "Host"
    claims: dict[str, Any] = field(default_factory=dict)


@dataclass
class Host:
    caps: CapService
    require_cap: bool = True
    store: dict[str, Any] = field(default_factory=dict)  # app session state
    _handlers: dict[str, Handler] = field(default_factory=dict)
    _event_handlers: dict[str, Callable[[dict[str, Any], "Host"], list[Op] | None]] = field(
        default_factory=dict
    )

    def action(self, name: str) -> Callable[[Handler], Handler]:
        def deco(fn: Handler) -> Handler:
            self._handlers[name] = fn
            return fn

        return deco

    def on(self, event_type: str) -> Callable:
        def deco(fn: Callable[[dict[str, Any], Host], list[Op] | None]):
            self._event_handlers[event_type] = fn
            return fn

        return deco

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

    def submit(self, intent: Intent | dict[str, Any]) -> Result:
        if isinstance(intent, dict):
            intent = Intent.from_dict(intent)
        action = (intent.action or "").strip()
        if not action:
            return Result("authority_refusal", [], "empty action")

        claims: dict[str, Any] = {}
        if self.require_cap or intent.cap:
            if not intent.cap:
                return Result("authority_refusal", [], "cap required")
            try:
                claims = self.caps.verify(intent.cap, action, intent.args)
            except CapError as e:
                return Result("authority_refusal", [], str(e))

        handler = self._handlers.get(action)
        if handler is None:
            return Result("dispatch_error", [], f"unknown action: {action}")

        ctx = ActionContext(action=action, args=intent.args, host=self, claims=claims)
        try:
            ops = handler(ctx)
        except Exception as e:
            return Result("dispatch_error", [], str(e))

        if not isinstance(ops, list):
            return Result("dispatch_error", [], "handler must return list[Op]")
        return Result("ok", as_wire(ops))

    def handle_event(self, event: dict[str, Any]) -> Result | None:
        et = event.get("type")
        if not et:
            return None
        fn = self._event_handlers.get(str(et))
        if fn is None:
            return None
        ops = fn(event, self)
        if ops is None:
            return None
        return Result("ok", as_wire(ops))
