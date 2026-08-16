"""Op constructors — emit only legal S (catalog.py).

Composition language = Python. Wire = list of Op.to_dict() only.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .catalog import LEGAL_FQS, fq_of, is_legal, project
from cek_host.legal import name_is_token
from cek_host.structure import StructureError, validate_pair


class Op:
    __slots__ = ("ns", "name", "payload")

    def __init__(
        self,
        ns: str,
        name: str,
        payload: dict[str, Any] | None = None,
        *,
        stamp: frozenset | None = None,
    ):
        if stamp is not None:
            if (ns, name) not in stamp:
                raise ValueError(f"illegal pair: {fq_of(ns, name)} — absent from session stamp")
        elif not is_legal(ns, name):
            raise ValueError(f"illegal pair: {fq_of(ns, name)}")
        self.ns = ns
        self.name = name
        self.payload = payload or {}

    @staticmethod
    def stamped(ns: str, name: str, payload: dict[str, Any] | None, stamp: frozenset) -> "Op":
        """Compose an extension pair that is present on the session stamp."""
        if not name_is_token(name):
            raise ValueError(f"illegal pair: {fq_of(ns, name)}")
        try:
            validate_pair(ns, name)
        except StructureError as e:
            raise ValueError(str(e)) from e
        return Op(ns, name, payload, stamp=stamp)

    def to_dict(self) -> dict[str, Any]:
        return {"ns": self.ns, "name": self.name, "payload": dict(self.payload)}

    @property
    def fq(self) -> str:
        return fq_of(self.ns, self.name)

    def __repr__(self) -> str:
        return f"Op({self.fq}, {self.payload!r})"

    @staticmethod
    def kv_set(key: str, value: Any) -> Op:
        _nonempty(key, "kv.set key")
        return Op("kv", "set", {"key": key, "value": value})

    @staticmethod
    def kv_delete(key: str, prior: Any | None = None) -> Op:
        _nonempty(key, "kv.delete key")
        p: dict[str, Any] = {"key": key}
        if prior is not None:
            p["prior"] = prior
        return Op("kv", "delete", p)

    @staticmethod
    def ui_morph(target: str, patch: Any, snapshot: Any | None = None) -> Op:
        _nonempty(target, "ui.dom.morph target")
        p: dict[str, Any] = {"target": target, "patch": patch}
        if snapshot is not None:
            p["snapshot"] = snapshot
        return Op("ui.dom", "morph", p)

    @staticmethod
    def ui_restore(target: str, snapshot: Any) -> Op:
        _nonempty(target, "ui.dom.restore target")
        return Op("ui.dom", "restore", {"target": target, "snapshot": snapshot})

    @staticmethod
    def log_append(
        message: str, *, level: str = "info", fields: Mapping[str, Any] | None = None
    ) -> Op:
        if not isinstance(message, str):
            raise ValueError("log.append message must be str")
        p: dict[str, Any] = {"message": message, "level": level}
        if fields:
            p["fields"] = dict(fields)
        return Op("log", "append", p)


def plan(*ops: Op) -> list[Op]:
    return list(ops)


def as_wire(ops: Sequence[Op]) -> list[dict[str, Any]]:
    return [o.to_dict() for o in ops]


def _nonempty(v: Any, label: str) -> None:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{label} must be non-empty str")


# ── Host-only macros (expand to S only) ─────────────────────────────────────

def signal_set(path: str, value: Any) -> Op:
    """Not a Domain pack. Macro → kv.set(\"signal:{path}\")."""
    _nonempty(path, "signal path")
    return Op.kv_set(f"signal:{path}", value)


def navigate_to(path: str, *, title: str | None = None, replace: bool = False) -> list[Op]:
    """Not nav.*. Store location in kv + log."""
    _nonempty(path, "navigate path")
    loc = {"path": path, "title": title, "replace": replace}
    return plan(Op.kv_set("ui:nav", loc), Op.log_append(f"nav {path}", fields=loc))


def set_loading(region: str, busy: bool, status: str | None = None) -> list[Op]:
    ops = [Op.kv_set(f"ui:busy:{region}", busy)]
    if status is not None:
        ops.append(Op.ui_morph(f"{region}-status", {"tag": "span", "text": status}))
    return ops


def form_errors(form_id: str, errors: Mapping[str, str]) -> list[Op]:
    ops: list[Op] = []
    for field, msg in errors.items():
        ops.append(Op.ui_morph(f"{form_id}.{field}-error", {"tag": "span", "text": msg}))
        ops.append(Op.kv_set(f"ui:invalid:{form_id}.{field}", True))
    if errors:
        first = next(iter(errors))
        ops.append(Op.kv_set("ui:focus", f"{form_id}.{first}"))
    return ops


def clear_form_errors(form_id: str, fields: Sequence[str]) -> list[Op]:
    ops: list[Op] = []
    for field in fields:
        ops.append(Op.ui_morph(f"{form_id}.{field}-error", {"tag": "span", "text": ""}))
        ops.append(Op.kv_set(f"ui:invalid:{form_id}.{field}", False))
    return ops


def search_hits(
    target: str,
    items: Sequence[Any],
    q: str = "",
    *,
    stamp: frozenset,
) -> Op:
    """search.hits — runtime stdlib pair. Requires search on the session stamp."""
    _nonempty(target, "search target")
    return Op.stamped(
        "search",
        "hits",
        {"target": target, "items": list(items), "q": q},
        stamp,
    )


def search_clear(target: str, *, stamp: frozenset) -> Op:
    """search.clear — runtime stdlib pair."""
    _nonempty(target, "search target")
    return Op.stamped("search", "clear", {"target": target}, stamp)


def project_ops(
    ops: Sequence[Op] | Sequence[dict[str, Any]],
    *,
    packs: Sequence[str] | None = None,
    unknown: str = "strict",
) -> list[dict[str, Any]]:
    wire = [o.to_dict() if isinstance(o, Op) else o for o in ops]
    return project(wire, packs=packs, unknown=unknown)  # type: ignore[arg-type]


__all__ = [
    "Op",
    "plan",
    "as_wire",
    "LEGAL_FQS",
    "signal_set",
    "navigate_to",
    "set_loading",
    "form_errors",
    "clear_form_errors",
    "search_hits",
    "search_clear",
    "project_ops",
]
