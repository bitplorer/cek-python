"""Continuation envelopes — pre-authorized next Intent templates.

Peer does not interpret business logic. It:
  1) observes event (e.g. timer.fired)
  2) builds Intent from declared slots
  3) attaches pre-minted attenuated Cap
  4) submits to Host

Host still verifies + projects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Continuation:
    """Attached to Result metadata (not an Op)."""

    event: str  # e.g. "timer.fired:search-debounce"
    action: str
    cap: str
    args_from: dict[str, str] | None = None  # intent arg <- slot source
    static_args: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "event": self.event,
            "action": self.action,
            "cap": self.cap,
        }
        if self.args_from:
            d["args_from"] = dict(self.args_from)
        if self.static_args:
            d["static_args"] = dict(self.static_args)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Continuation:
        return cls(
            event=str(d["event"]),
            action=str(d["action"]),
            cap=str(d["cap"]),
            args_from=dict(d["args_from"]) if d.get("args_from") else None,
            static_args=dict(d["static_args"]) if d.get("static_args") else None,
        )


def resolve_args(
    cont: Continuation,
    *,
    store: dict[str, Any],
    event: dict[str, Any],
) -> dict[str, Any]:
    """Fill Intent args from slots. Sources: store:KEY, event:KEY, literal via static_args."""
    args = dict(cont.static_args or {})
    for arg_name, src in (cont.args_from or {}).items():
        if src.startswith("store:"):
            args[arg_name] = store.get(src[6:])
        elif src.startswith("event:"):
            args[arg_name] = event.get(src[6:])
        else:
            args[arg_name] = src
    return args


def match_continuation(
    continuations: list[Continuation] | list[dict[str, Any]],
    event: dict[str, Any],
) -> Continuation | None:
    et = str(event.get("type") or "")
    eid = event.get("id")
    key = f"{et}:{eid}" if eid is not None else et
    for c in continuations:
        cont = c if isinstance(c, Continuation) else Continuation.from_dict(c)
        if cont.event == key or cont.event == et:
            return cont
    return None
