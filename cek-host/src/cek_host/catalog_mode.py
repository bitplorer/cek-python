"""Catalog mode — which pairs a missing session stamp stands for.

CEK_CATALOG_MODE=open|strict  (default: open)

The law noun is Baseline or profile, never "S".
The declared catalog is Baseline ∪ the UI seed (five pairs). It is what this
Host and the bundled document Peer both ship.

open:   no stamp yet → declared catalog, so ui.dom morph works before a handshake.
strict: no stamp yet → Baseline only. Use this for a peer that has not been identified.
A stamp that was actually received is the only legal set for that session.
"""

from __future__ import annotations

import os
from typing import Literal

CatalogMode = Literal["open", "strict"]

_DEFAULT: CatalogMode = "open"


def get_catalog_mode() -> CatalogMode:
    raw = (os.environ.get("CEK_CATALOG_MODE") or _DEFAULT).strip().lower()
    if raw in ("open", "strict"):
        return raw  # type: ignore[return-value]
    return _DEFAULT


def is_strict() -> bool:
    return get_catalog_mode() == "strict"
