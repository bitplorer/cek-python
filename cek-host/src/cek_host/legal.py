"""Declared catalog — pair identity, not concatenated FQ.

The law has no noun "S". This module has three sets:

- Baseline: kv set/delete, log append. Never grows.
- UI seed: ui.dom morph/restore. The document pack this Host and Peer ship.
- Declared catalog: Baseline ∪ UI seed. Python name: LEGAL_PAIRS.

A session stamp is a different set: only those pairs, for this session.
Undeclared pair is not in the catalog. `ui` + `dom.morph` is not `ui.dom.morph`.

Host `project_wire(..., unknown="strict")` **raises** `IllegalOp`.
A non-empty illegal batch must never become `kind=ok` with empty ops.
"""

from __future__ import annotations

from typing import Any, Iterable, Literal

from .catalog_mode import get_catalog_mode, is_strict
from .structure import StructureError, validate_pair

# (ns, name) — name is a single token. Domain ns is the pack.
BASELINE_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {("kv", "set"), ("kv", "delete"), ("log", "append")}
)

# pack → pairs
DOMAIN_PACKS: dict[str, tuple[tuple[str, str], ...]] = {
    "ui.dom": (("ui.dom", "morph"), ("ui.dom", "restore")),
}

DOMAIN_PAIRS: frozenset[tuple[str, str]] = frozenset(
    p for pairs in DOMAIN_PACKS.values() for p in pairs
)
LEGAL_PAIRS: frozenset[tuple[str, str]] = BASELINE_PAIRS | DOMAIN_PAIRS
"""Declared catalog. Not a session stamp. Not the letter S."""


class IllegalOp(ValueError):
    """Undeclared `(ns, name)`. Host maps this to `dispatch_error`."""

    def __init__(self, ns: str, name: str, detail: str = ""):
        self.ns = ns
        self.name = name
        msg = f"illegal pair: {ns}.{name}"
        if detail:
            msg = f"{msg} — {detail}"
        super().__init__(msg)


def fq_of(ns: str, name: str) -> str:
    return f"{ns}.{name}"


BASELINE_FQS: frozenset[str] = frozenset(fq_of(*p) for p in BASELINE_PAIRS)
DOMAIN_FQS: frozenset[str] = frozenset(fq_of(*p) for p in DOMAIN_PAIRS)
LEGAL_FQS: frozenset[str] = BASELINE_FQS | DOMAIN_FQS

_PAIR_TO_PACK: dict[tuple[str, str], str] = {
    pair: pack for pack, pairs in DOMAIN_PACKS.items() for pair in pairs
}


def name_is_token(name: str) -> bool:
    return bool(name) and name.isalnum() and name == name.lower() and "." not in name


def is_baseline(ns: str, name: str) -> bool:
    return (ns, name) in BASELINE_PAIRS


def is_domain_pair(ns: str, name: str) -> bool:
    return name_is_token(name) and (ns, name) in DOMAIN_PAIRS


def is_legal(ns: str, name: str) -> bool:
    """True when the pair is in the declared catalog. Not "lawful for this session"."""
    return name_is_token(name) and (ns, name) in LEGAL_PAIRS


def pack_of_pair(ns: str, name: str) -> str | None:
    return _PAIR_TO_PACK.get((ns, name))


def pack_of(fq: str) -> str | None:
    for pack, pairs in DOMAIN_PACKS.items():
        for ns, name in pairs:
            if fq_of(ns, name) == fq:
                return pack
    return None


def pack_is_scoped(pack: str) -> bool:
    parts = pack.split(".")
    if len(parts) < 2:
        return False
    return all(p and p.isalnum() and p == p.lower() for p in parts)


UnknownMode = Literal["strict", "tolerant"]


def pair_from_fq(fq: str) -> tuple[str, str] | None:
    """Last-dot split. Prefer (ns, name) directly. Display/legacy only."""
    idx = fq.rfind(".")
    if idx <= 0 or idx + 1 >= len(fq):
        return None
    return fq[:idx], fq[idx + 1 :]


def default_stamp_pairs() -> frozenset[tuple[str, str]]:
    """Stamp installed when nobody agreed one yet.

    open  → declared catalog (Baseline ∪ UI seed). Bundled document peer.
    strict → Baseline only. Unknown peer.
    """
    if is_strict():
        return BASELINE_PAIRS
    return LEGAL_PAIRS


def normalize_stamp(
    pairs: Iterable[tuple[str, str] | dict[str, Any]] | None,
    *,
    allow_extension: bool = True,
) -> frozenset[tuple[str, str]]:
    """Close a stamp.

    Core catalog pairs always allowed. Structure-valid extension pairs
    may enter the stamp after Host↔Peer agreement (`allow_extension=True`).
    If nothing valid remains, fall back to default_stamp_pairs().
    """
    if pairs is None:
        return default_stamp_pairs()
    out: set[tuple[str, str]] = set()
    for item in pairs:
        if isinstance(item, dict):
            ns, name = str(item.get("ns") or ""), str(item.get("name") or "")
        else:
            ns, name = item[0], item[1]
        if is_legal(ns, name):
            out.add((ns, name))
            continue
        if not allow_extension:
            continue
        if not name_is_token(name):
            continue
        try:
            validate_pair(ns, name)
        except StructureError:
            continue
        out.add((ns, name))
    if not out:
        return default_stamp_pairs()
    return frozenset(out)


def in_stamp(stamp: frozenset[tuple[str, str]], ns: str, name: str) -> bool:
    """Pair identity membership. Concatenation is never the key."""
    return (ns, name) in stamp


def session_legal(ns: str, name: str, stamp: frozenset[tuple[str, str]] | None) -> bool:
    """Stamp membership when this session has a stamp.

    No stamp: catalog mode. open → declared catalog. strict → Baseline only.
    """
    if stamp is not None:
        return in_stamp(stamp, ns, name)
    return (ns, name) in default_stamp_pairs()


def project_wire(
    ops: Iterable[dict[str, Any]],
    *,
    unknown: str = "strict",
    stamp: Iterable[tuple[str, str] | dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Keep session-legal pairs. Strict unknown raises `IllegalOp` (never silent ok+[]).

    With a stamp: membership in the stamp is the only legality.
    Without a stamp: default_stamp_pairs() (declared catalog, or Baseline in strict).
    """
    closed = normalize_stamp(stamp) if stamp is not None else None
    out: list[dict[str, Any]] = []
    for op in ops:
        ns = str(op.get("ns") or "")
        name = str(op.get("name") or "")
        if session_legal(ns, name, closed):
            out.append(op)
        elif unknown == "strict":
            raise IllegalOp(ns, name, "absent from session stamp" if closed is not None else "")
    return out


def project(
    ops: Iterable[dict[str, Any]],
    *,
    packs: Iterable[str] | None = None,
    unknown: UnknownMode = "strict",
    stamp: Iterable[tuple[str, str] | dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Declared catalog ∩ profile packs. Declared-but-not-in-profile is skipped. Undeclared: raise or skip."""
    allowed = set(packs) if packs is not None else set(DOMAIN_PACKS)
    closed = normalize_stamp(stamp) if stamp is not None else None
    out: list[dict[str, Any]] = []
    for op in ops:
        ns = str(op.get("ns") or "")
        name = str(op.get("name") or "")
        if is_baseline(ns, name):
            if closed is None or in_stamp(closed, ns, name):
                out.append(op)
            elif unknown == "strict":
                raise IllegalOp(ns, name, "absent from session stamp")
            continue
        pack = pack_of_pair(ns, name)
        if pack is not None and pack in allowed:
            if closed is None or in_stamp(closed, ns, name):
                out.append(op)
            elif unknown == "strict":
                raise IllegalOp(ns, name, "absent from session stamp")
            continue
        if pack is not None:
            continue
        # Stamped extension (not in the declared catalog)
        if closed is not None and in_stamp(closed, ns, name):
            out.append(op)
            continue
        if unknown == "strict":
            raise IllegalOp(ns, name)
    return out
