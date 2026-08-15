"""Cap tokens - authority primitive for cek-host."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Any


def _canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def args_hash(args: dict[str, Any] | None) -> str:
    return hashlib.sha256(_canon(args or {})).hexdigest()[:32]


@dataclass
class CapService:
    secret: bytes
    ttl_s: int = 3600
    now_fn: Any = field(default=time.time, repr=False)
    _used_jti: set[str] = field(default_factory=set, repr=False)

    def mint(
        self,
        action: str,
        *,
        once: bool = False,
        args: dict[str, Any] | None = None,
        seal_args: bool = False,
        not_after: float | None = None,
        scopes: list[str] | None = None,
        subject: str | None = None,
        jti: str | None = None,
    ) -> str:
        if not action or not action.strip():
            raise ValueError("empty action")
        payload: dict[str, Any] = {
            "action": action,
            "jti": jti or secrets.token_urlsafe(16),
            "once": bool(once),
            "iat": float(self.now_fn()),
        }
        if not_after is not None:
            payload["not_after"] = float(not_after)
        else:
            payload["not_after"] = float(self.now_fn()) + self.ttl_s
        if seal_args:
            payload["args_hash"] = args_hash(args)
        if scopes:
            payload["scopes"] = list(scopes)
        if subject is not None:
            payload["subject"] = subject
        body = _canon(payload)
        sig = hmac.new(self.secret, body, hashlib.sha256).hexdigest()
        return body.hex() + "." + sig

    def verify(
        self,
        token: str,
        action: str,
        args: dict[str, Any] | None = None,
        *,
        consume_once: bool = True,
        subject: str | None = None,
    ) -> dict[str, Any]:
        if not token or "." not in token:
            raise CapError("malformed cap")
        body_hex, sig = token.rsplit(".", 1)
        try:
            body = bytes.fromhex(body_hex)
        except ValueError as e:
            raise CapError("malformed cap body") from e
        expect = hmac.new(self.secret, body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expect, sig):
            raise CapError("cap signature invalid")
        try:
            claims = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise CapError("cap payload invalid") from e
        if (claims.get("action") or "") != action:
            raise CapError("action mismatch")
        na = claims.get("not_after")
        if na is not None and float(self.now_fn()) >= float(na):
            raise CapError("cap expired")
        if "args_hash" in claims:
            if args_hash(args) != claims["args_hash"]:
                raise CapError("sealed-args mismatch")
        jti = claims.get("jti") or ""
        if not str(jti).strip():
            raise CapError("empty jti")
        if claims.get("once"):
            if jti in self._used_jti:
                raise CapError("once cap already used")
            if consume_once:
                self._used_jti.add(jti)
        return claims


class CapError(Exception):
    pass
