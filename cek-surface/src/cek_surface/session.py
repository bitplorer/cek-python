"""Host ↔ Peer session via portable Carrier (default: subprocess NDJSON)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from .carrier import Carrier, open_carrier


class _ResultLike(Protocol):
    def to_dict(self) -> dict[str, Any]: ...


class PeerSession:
    """Thin façade over a Carrier. Default transport is zero-config subprocess."""

    def __init__(
        self,
        peer_js: Path | None = None,
        *,
        carrier: Carrier | None = None,
        carrier_kind: str = "subprocess",
        **carrier_opts: Any,
    ):
        if carrier is not None:
            self.carrier = carrier
        else:
            opts = dict(carrier_opts)
            if peer_js is not None:
                opts["peer_js"] = peer_js
            self.carrier = open_carrier(carrier_kind, **opts)

    @property
    def carrier_name(self) -> str:
        return getattr(self.carrier, "name", type(self.carrier).__name__)

    def apply_result(self, result: _ResultLike | dict[str, Any]) -> dict[str, Any]:
        payload = result.to_dict() if hasattr(result, "to_dict") else result
        return self.carrier.apply(payload)

    def apply(self, result: _ResultLike | dict[str, Any]) -> dict[str, Any]:
        return self.apply_result(result)

    def install_stamp(self, pairs: list[dict[str, str]]) -> dict[str, Any]:
        stamp = getattr(self.carrier, "stamp", None)
        if stamp is None:
            return {"type": "stamp_ack", "pairs": pairs}
        return stamp(pairs)

    def chrome(self, chrome: dict[str, Any]) -> dict[str, Any]:
        return self.carrier.chrome(chrome)

    def read(self) -> dict[str, Any]:
        msg = self.carrier.read_event()
        if msg is None:
            raise RuntimeError("peer died or timeout")
        return msg

    def close(self) -> None:
        self.carrier.close()
