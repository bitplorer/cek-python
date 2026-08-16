"""Domain stdlibs — runtime-level domain expansion.

Core seeds: baseline + ui (S). Additional stdlibs load after structure
validation. Host and Peer agree on names+versions; Host stamps the union.
Via negativa: absent from stamp = illegal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from cek_host.legal import BASELINE_PAIRS, DOMAIN_PACKS, LEGAL_PAIRS, is_legal, name_is_token
from cek_host.structure import StructureError, validate_pair


@dataclass(frozen=True)
class DomainStdlib:
    name: str
    version: str
    seed_pairs: tuple[tuple[str, str], ...]
    driver_hint: str = ""
    core: bool = False

    def pairs(self) -> frozenset[tuple[str, str]]:
        return frozenset(self.seed_pairs)

    def major(self) -> str:
        return (self.version or "1").split(".")[0]


BASELINE = DomainStdlib(
    name="baseline",
    version="1",
    seed_pairs=tuple(sorted(BASELINE_PAIRS)),
    driver_hint="kv+log",
    core=True,
)

UI = DomainStdlib(
    name="ui",
    version="1",
    seed_pairs=tuple(DOMAIN_PACKS["ui.dom"]),
    driver_hint="ui.dom",
    core=True,
)


class Registry:
    """Mutable runtime registry. Core seeds are always present."""

    def __init__(self) -> None:
        self._items: dict[str, DomainStdlib] = {
            "baseline": BASELINE,
            "ui": UI,
        }

    def get(self, name: str) -> DomainStdlib | None:
        return self._items.get(name)

    def names(self) -> list[str]:
        return list(self._items)

    def all(self) -> list[DomainStdlib]:
        return list(self._items.values())

    def register(self, stdlib: DomainStdlib) -> None:
        if not stdlib.name or not stdlib.name.replace(".", "").isalnum():
            raise StructureError(f"invalid stdlib name: {stdlib.name!r}")
        if not stdlib.seed_pairs:
            raise StructureError(f"stdlib {stdlib.name} has no seed pairs")
        for ns, name in stdlib.seed_pairs:
            if not name_is_token(name):
                raise StructureError(f"{stdlib.name}: name must be a token: {name!r}")
            validate_pair(ns, name)
            if stdlib.core and not is_legal(ns, name):
                raise StructureError(f"core stdlib {stdlib.name} has undeclared pair {ns}.{name}")
        if stdlib.name in self._items and self._items[stdlib.name].core and not stdlib.core:
            raise StructureError(f"cannot overwrite core stdlib {stdlib.name}")
        self._items[stdlib.name] = stdlib


REGISTRY = Registry()


def register(stdlib: DomainStdlib) -> None:
    REGISTRY.register(stdlib)


def compatible(offered: DomainStdlib, accepted_version: str) -> bool:
    """Same major version = compatible."""
    return offered.major() == (accepted_version or "1").split(".")[0]


def agree(
    host_offers: Iterable[str],
    peer_accepts: Iterable[str],
    *,
    host_versions: dict[str, str] | None = None,
    peer_versions: dict[str, str] | None = None,
    registry: Registry | None = None,
) -> list[DomainStdlib]:
    """Intersect Host offers with Peer accepts. Order follows host_offers.

    Version: majors must match when both sides declare a version.
    Baseline is always included.
    """
    reg = registry or REGISTRY
    accepts = set(peer_accepts)
    hv = host_versions or {}
    pv = peer_versions or {}
    out: list[DomainStdlib] = []
    for name in host_offers:
        if name not in accepts:
            continue
        item = reg.get(name)
        if item is None:
            continue
        ov = hv.get(name, item.version)
        av = pv.get(name, item.version)
        if (ov or "1").split(".")[0] != (av or "1").split(".")[0]:
            continue
        out.append(item)
    if "baseline" not in {d.name for d in out}:
        base = reg.get("baseline")
        if base is not None:
            out.insert(0, base)
    return out


def stamp_from_agreement(agreed: Iterable[DomainStdlib]) -> frozenset[tuple[str, str]]:
    """Union seed pairs of agreed domain-stdlibs (core S ∪ extensions)."""
    out: set[tuple[str, str]] = set()
    for d in agreed:
        for ns, name in d.seed_pairs:
            if not name_is_token(name):
                continue
            try:
                validate_pair(ns, name)
            except StructureError:
                continue
            out.add((ns, name))
    return frozenset(out) if out else frozenset(BASELINE_PAIRS)


def default_agreement_stamp() -> frozenset[tuple[str, str]]:
    """Default agreement {baseline, ui} → core S."""
    return stamp_from_agreement(agree(["baseline", "ui"], ["baseline", "ui"]))


assert default_agreement_stamp() == LEGAL_PAIRS
