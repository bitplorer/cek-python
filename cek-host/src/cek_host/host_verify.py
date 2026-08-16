"""Cap verify — generation + Ed25519. No once. No project."""

from __future__ import annotations

from typing import Any

from .cap import CapError
from .digest import canon


def check_generation(claims: dict[str, Any], accepted: list[str]) -> None:
    g = claims.get("law_generation")
    if g is None:
        return
    if not str(g).strip():
        raise CapError("empty law generation is not allowed")
    if g not in accepted:
        raise CapError(f"law generation `{g}` not in {accepted}")


def check_ed25519(
    claims: dict[str, Any],
    *,
    seed: bytes | None,
    trust: list[bytes],
) -> None:
    if seed is None and not trust:
        return
    raw = claims.get("ed25519")
    if not raw:
        raise CapError("Cap signature required")
    sig_hex = str(raw)
    if sig_hex.startswith("ed25519:"):
        sig_hex = sig_hex.split(":", 1)[1]
    try:
        sig = bytes.fromhex(sig_hex)
    except ValueError as e:
        raise CapError("Cap signature invalid") from e
    body = {k: v for k, v in claims.items() if k != "ed25519"}
    msg = canon(body)
    from .ed25519 import verify as ed_verify

    for pk in trust:
        if ed_verify(pk, msg, sig):
            return
    raise CapError("Cap signature invalid")
