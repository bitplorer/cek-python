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

    def explain(self, error: str | None = None):
        from cek_host import explain as host_explain

        return host_explain(error)

    def submit(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        *,
        cap: str | None = None,
        activity_id: str | None = None,
        idempotency_key: str | None = None,
        auto_mint: bool = False,
        once: bool = False,
        seal_args: bool = False,
        drain_async: bool = True,
    ) -> dict[str, Any]:
        args = dict(args or {})
        if auto_mint and not cap:
            cap = self.mint(action, once=once, args=args, seal_args=seal_args)

        result, armed = self._compose_and_authorize(
            action, args, cap, activity_id=activity_id, idempotency_key=idempotency_key
        )
        return self._deliver(result, drain_async=drain_async, continuations=armed)

    def handle_event(self, event: dict[str, Any]) -> KernelResult | None:
        """Peer event → Host. Continuations (pre-minted Caps) win; else @on.

        Continuation path: fill slots, verify Cap, project. Fail closed.
        Bare @on handlers must not mint and should return None when a
        continuation was expected (timer.fired → search.commit).
        """
        et = event.get("type")
        if not et:
            return None

        cont = self._take_continuation(event)
        if cont is not None:
            args = resolve_args(cont, store=self.store, event=event)
            result, armed = self._compose_and_authorize(cont.action, args, cont.cap)
            if armed:
                self.last_continuations = list(armed)
            return result

        fn = self._events.get(str(et))
        if fn is None:
            return None
        ops = fn(event, self)
        if ops is None:
            return None
        # Un-capped @on is a compatibility path (http.response). Prefer continuations.
        return KernelResult("ok", as_wire(ops))

    def ensure_peer(self) -> PeerSession:
        if self.peer is None:
            self.peer = PeerSession(carrier_kind=self.carrier_kind, **self.carrier_opts)
        return self.peer

    def continuation_dicts(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for c in self.last_continuations:
            if isinstance(c, Continuation):
                out.append(c.to_dict())
            else:
                out.append(dict(c))
        return out

    def _compose_and_authorize(
        self,
        action: str,
        args: dict[str, Any],
        cap: str | None,
        *,
        activity_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[KernelResult, list | None]:
        pol = self.policy.check_action(action)
        if not pol.allow:
            return KernelResult("authority_refusal", [], pol.reason), None

        # Verify Cap BEFORE compose (store writes / continuation mint). I1 / I2-lite.
        if hasattr(self.kernel, "check"):
            pre = self.kernel.check(
                action, args, cap, activity_id=activity_id, idempotency_key=idempotency_key
            )
            if not getattr(pre, "ok", False):
                return pre, None

        handler = self._handlers.get(action)
        if handler is None:
            return KernelResult("dispatch_error", [], f"unknown action: {action}"), None

        ctx = Ctx(action=action, args=args, surface=self, store=self.store)
        try:
            ops = handler(ctx)
        except Exception as e:
            return KernelResult("dispatch_error", [], str(e)), None

        if not isinstance(ops, list):
            return KernelResult("dispatch_error", [], "handler must return list[Op]"), None

        wire = as_wire(ops)
        pol2 = self.policy.check_ops(wire)
        if not pol2.allow:
            return KernelResult("authority_refusal", [], pol2.reason), None

        result = self.kernel.submit(
            action,
            args,
            cap,
            activity_id=activity_id,
            project_ops=wire,
            idempotency_key=idempotency_key,
        )
        return result, getattr(ctx, "continuations", None)

    def _take_continuation(self, event: dict[str, Any]) -> Continuation | None:
        cont = match_continuation(self.last_continuations, event)
        if cont is None:
            return None
        remaining: list[Continuation] = []
        found = False
        for c in self.last_continuations:
            cur = c if isinstance(c, Continuation) else Continuation.from_dict(c)
            if not found and cur.event == cont.event and cur.cap == cont.cap:
                found = True
                continue
            remaining.append(cur)
        self.last_continuations = remaining
        return cont

    def _deliver(self, result: KernelResult, *, drain_async: bool, continuations=None) -> dict[str, Any]:
        if continuations:
            self.last_continuations = [
                c if isinstance(c, Continuation) else Continuation.from_dict(c)
                for c in continuations
            ]
        peer = self.ensure_peer()
        reply = peer.apply_result(result)
        self.last_world = reply.get("world") or {}
        payload = result.to_dict()
        # Refuse must not advertise leftover Caps (previous search debounce, etc.).
        conts = self.continuation_dicts() if result.ok else []
        if conts:
            payload["continuations"] = conts
        out: dict[str, Any] = {
            "result": payload,
            "receipt": reply.get("receipt"),
            "world": self.last_world,
            "continuations": conts,
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
                    payload = nxt.to_dict()
                    if nxt.ok:
                        conts = self.continuation_dicts()
                        if conts:
                            payload["continuations"] = conts
                    entry["result"] = payload
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
