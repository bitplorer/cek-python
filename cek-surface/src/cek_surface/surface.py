"""Surface runtime — composition, events, Peer session.

Depends on HostKernel for Caps (cek-host preferred).
Does not depend on ux-channel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .continuation import Continuation, match_continuation, resolve_args
from .kernel import HostKernel, KernelResult, load_host_kernel
from .ops import Op, as_wire
from .policy import SurfacePolicy
from .session import PeerSession


Handler = Callable[["Ctx"], list[Op]]
EventHandler = Callable[[dict[str, Any], "Surface"], list[Op] | None]


@dataclass
class Ctx:
    action: str
    args: dict[str, Any]
    surface: "Surface"
    store: dict[str, Any]
    continuations: list | None = None


@dataclass
class Surface:
    """App-facing Host: actions compose Ops; kernel authorizes; Peer applies."""

    kernel: HostKernel = field(default_factory=load_host_kernel)
    store: dict[str, Any] = field(default_factory=dict)
    policy: SurfacePolicy = field(default_factory=SurfacePolicy)
    _handlers: dict[str, Handler] = field(default_factory=dict)
    _events: dict[str, EventHandler] = field(default_factory=dict)
    peer: PeerSession | None = None
    carrier_kind: str = "subprocess"
    carrier_opts: dict = field(default_factory=dict)
    last_world: dict[str, Any] = field(default_factory=dict)
    last_continuations: list[Continuation] = field(default_factory=list)

    def action(self, name: str) -> Callable[[Handler], Handler]:
        def deco(fn: Handler) -> Handler:
            self._handlers[name] = fn
            return fn

        return deco

    def on(self, event_type: str) -> Callable[[EventHandler], EventHandler]:
        def deco(fn: EventHandler) -> EventHandler:
            self._events[event_type] = fn
            return fn

        return deco

    def mint(self, action: str, **kw: Any) -> str:
        return self.kernel.mint(action, **kw)

    def submit(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        *,
        cap: str | None = None,
        activity_id: str | None = None,
        auto_mint: bool = False,
        once: bool = False,
        seal_args: bool = False,
        drain_async: bool = True,
    ) -> dict[str, Any]:
        args = dict(args or {})
        if auto_mint and not cap:
            cap = self.mint(action, once=once, args=args, seal_args=seal_args)

        pol = self.policy.check_action(action)
        if not pol.allow:
            result = KernelResult("authority_refusal", [], pol.reason)
            return self._deliver(result, drain_async=False)

        handler = self._handlers.get(action)
        if handler is None:
            result = KernelResult("dispatch_error", [], f"unknown action: {action}")
            return self._deliver(result, drain_async=False)

        ctx = Ctx(action=action, args=args, surface=self, store=self.store)
        try:
            ops = handler(ctx)
        except Exception as e:
            result = KernelResult("dispatch_error", [], str(e))
            return self._deliver(result, drain_async=False)

        if not isinstance(ops, list):
            result = KernelResult("dispatch_error", [], "handler must return list[Op]")
            return self._deliver(result, drain_async=False)

        wire = as_wire(ops)
        pol2 = self.policy.check_ops(wire)
        if not pol2.allow:
            result = KernelResult("authority_refusal", [], pol2.reason)
            return self._deliver(result, drain_async=False)

        # Kernel: Cap check + package (does not re-compose)
        result = self.kernel.submit(
            action,
            args,
            cap,
            activity_id=activity_id,
            project_ops=wire,
        )
        return self._deliver(result, drain_async=drain_async, continuations=getattr(ctx, "continuations", None))

    def handle_event(self, event: dict[str, Any]) -> KernelResult | None:
        et = event.get("type")
        if not et:
            return None
        fn = self._events.get(str(et))
        if fn is None:
            return None
        ops = fn(event, self)
        if ops is None:
            return None
        # Events are already authorized by the activity that armed them;
        # still package as ok Result. Production: re-Cap or activity-scoped.
        return KernelResult("ok", as_wire(ops))

    def ensure_peer(self) -> PeerSession:
        if self.peer is None:
            self.peer = PeerSession(carrier_kind=self.carrier_kind, **self.carrier_opts)
        return self.peer

    def _deliver(self, result: KernelResult, *, drain_async: bool, continuations=None) -> dict[str, Any]:
        if continuations:
            self.last_continuations = list(continuations)
        peer = self.ensure_peer()
        reply = peer.apply_result(result)
        self.last_world = reply.get("world") or {}
        out: dict[str, Any] = {
            "result": result.to_dict(),
            "receipt": reply.get("receipt"),
            "world": self.last_world,
        }
        if drain_async and result.ok and _has_async(result.ops):
            out["followups"] = self.drain_events()
        return out

    def drain_events(self, max_rounds: int = 12) -> list[dict[str, Any]]:
        peer = self.ensure_peer()
        followups: list[dict[str, Any]] = []
        for _ in range(max_rounds):
            msg = peer.read()
            events = msg.get("events") or []
            if msg.get("type") in ("timer.fired", "http.response", "http.error"):
                events = [msg]
            if not events:
                break
            chained = False
            for ev in events:
                nxt = self.handle_event(ev)
                entry: dict[str, Any] = {"event": ev, "result": None}
                if nxt is not None:
                    reply = peer.apply_result(nxt)
                    self.last_world = reply.get("world") or {}
                    entry["result"] = nxt.to_dict()
                    entry["receipt"] = reply.get("receipt")
                    entry["world"] = self.last_world
                    if nxt.ok and _has_async(nxt.ops):
                        chained = True
                followups.append(entry)
            if not chained:
                # wait for possible further async from last apply
                if any(
                    _has_async((f.get("result") or {}).get("ops") or [])
                    for f in followups[-len(events) :]
                ):
                    continue
                break
        return followups

    def close(self) -> None:
        if self.peer:
            self.peer.close()
            self.peer = None


def _has_async(ops: list[dict[str, Any]]) -> bool:
    return any(o.get("ns") in ("timer", "http") for o in ops)
