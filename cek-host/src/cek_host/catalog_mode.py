"""Catalog mode — open (transitional) vs strict (fail-closed destination).

CEK_CATALOG_MODE=open|strict  (default: open)

Under strict mode a missing/malformed session stamp falls back to Baseline-only.
Under open mode a missing stamp uses the full declared S (Baseline ∪ Domain seed).
A received stamp is always the only legal pair set for the session.
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
