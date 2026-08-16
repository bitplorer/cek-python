"""Session stamp helpers — closed pair set for one Host↔Peer session."""

from __future__ import annotations

from typing import Any, Iterable

from cek_host.legal import (
    BASELINE_PAIRS,
    default_stamp_pairs,
    in_stamp,
    normalize_stamp,
)

__all__ = [
    "BASELINE_PAIRS",
    "default_stamp_pairs",
    "in_stamp",
    "normalize_stamp",
    "pairs_as_wire",
]


def pairs_as_wire(pairs: Iterable[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"ns": ns, "name": name} for ns, name in sorted(pairs)]


def pairs_from_wire(items: Iterable[dict[str, Any]]) -> frozenset[tuple[str, str]]:
    return normalize_stamp(items)
