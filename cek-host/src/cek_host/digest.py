"""Result digests — I8: `cek1:` + FIPS SHA-256.

Sealed-args oracle stays `args_hash` (32 hex) — do not replace it with cek1:.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

DIGEST_ALG = "cek1"


def canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def cek1_hex(data: bytes) -> str:
    return f"{DIGEST_ALG}:" + hashlib.sha256(data).hexdigest()


def result_digest(kind: str, ops: list[Any], error: str | None) -> str:
    return cek1_hex(canon({"error": error, "kind": kind, "ops": ops}))


def args_hash(args: dict[str, Any] | None) -> str:
    """Oracle: hash_args({'sku':'abc-123','qty':2}) == 96e4f83e3793b646323a67f314b51044"""
    return hashlib.sha256(canon(args or {})).hexdigest()[:32]
