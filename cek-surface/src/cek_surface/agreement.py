"""Host↔Peer domain-stdlib agreement.

Offer / accept / stamp. Versions: major must match.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .domain_stdlib import REGISTRY, Registry, agree, stamp_from_agreement
from .stamp import pairs_as_wire


@dataclass
class StdlibOffer:
    name: str
    version: str


@dataclass
class Agreement:
    offered: list[StdlibOffer]
    accepted: list[StdlibOffer]
    stamp: frozenset = field(default_factory=frozenset)

    def to_dict(self) -> dict[str, Any]:
        return {
            "offered": [o.__dict__ for o in self.offered],
            "accepted": [a.__dict__ for a in self.accepted],
            "stamp": pairs_as_wire(self.stamp),
        }


def negotiate(
    host_offers: Iterable[tuple[str, str] | str],
    peer_accepts: Iterable[tuple[str, str] | str],
    *,
    registry: Registry | None = None,
) -> Agreement:
    """host_offers / peer_accepts: name or (name, version)."""
    reg = registry or REGISTRY

    def split(items: Iterable[tuple[str, str] | str]) -> tuple[list[str], dict[str, str]]:
        names: list[str] = []
        vers: dict[str, str] = {}
        for it in items:
            if isinstance(it, str):
                names.append(it)
            else:
                names.append(it[0])
                vers[it[0]] = it[1]
        return names, vers

    hn, hv = split(host_offers)
    pn, pv = split(peer_accepts)
    agreed = agree(hn, pn, host_versions=hv, peer_versions=pv, registry=reg)
    stamp = stamp_from_agreement(agreed)
    offered = [
        StdlibOffer(name=n, version=hv.get(n, (reg.get(n).version if reg.get(n) else "1")))
        for n in hn
    ]
    accepted = [StdlibOffer(name=d.name, version=d.version) for d in agreed]
    return Agreement(offered=offered, accepted=accepted, stamp=stamp)
