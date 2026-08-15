"""Cap tokens — authority primitive for cek-host.

HMAC token format (published, keep): hex(canonical-json) + '.' + hmac-sha256
Oracle (keep): args_hash({'sku':'abc-123','qty':2}) == 96e4f83e3793b646323a67f314b51044

I13  Scope deny / blank token → zero Ops
I14  Attenuate cannot widen (K7)
I20  Cap HMAC missing/tamper → zero Ops
I21  Subject bind mismatch → zero Ops
"""

from __future__ import annotations

import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

from .digest import args_hash, canon
from .once import MemoryOnceBackend, OnceBackend, OnceUsed, StoreDown

# Re-export so `from cek_host.cap import args_hash` keeps working.
__all__ = ["CapService", "CapError", "args_hash", "resource_of", "scope_allows"]


def resource_of(action: str, args: dict[str, Any] | None) -> tuple[str, str]:
    """Same mapping as cek-runtime/ports/cek-host-py — do not invent a third."""
    args = args or {}
    if action in ("kv.write", "kv.delete"):
        return "kv", str(args.get("key") or "")
    if action in ("ui.morph", "ui.restore"):
        return "ui", str(args.get("target") or "")
    if action == "log.append":
        return "log", ""
    return "action", action


def scope_allows(scope: str, kind: str, name: str) -> bool:
    scope = scope.strip()
    if not scope:
        return False
    if scope == "*" or scope == kind or (name and scope == name):
        return True
    if ":" in scope:
        k, n = scope.split(":", 1)
        return k == kind and (n == "*" or (n and n == name))
    return False


class CapError(Exception):
    pass


@dataclass
class CapService:
    secret: bytes
    ttl_s: int = 3600
    now_fn: Any = field(default=time.time, repr=False)
    once: OnceBackend = field(default_factory=MemoryOnceBackend)

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
        law_generation: str | None = None,
        ed25519: str | None = None,
        ed25519_seed: bytes | None = None,
        args_hash_value: str | None = None,
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
        if args_hash_value is not None and "args_hash" not in payload:
            payload["args_hash"] = args_hash_value
        if scopes:
            payload["scopes"] = list(scopes)
        if subject is not None:
            payload["subject"] = subject
        if law_generation is not None:
            payload["law_generation"] = law_generation
        if ed25519 is not None:
            payload["ed25519"] = ed25519
        elif ed25519_seed is not None:
            from .ed25519 import sign as ed_sign

            payload["ed25519"] = ed_sign(ed25519_seed, canon(payload)).hex()
        body = canon(payload)
        sig = hmac.new(self.secret, body, "sha256").hexdigest()
        return body.hex() + "." + sig

    def decode(self, token: str) -> dict[str, Any]:
        """Verify HMAC and parse claims. Does not check action/expiry/once/scopes."""
        if not token or "." not in token:
            raise CapError("malformed cap")
        body_hex, sig = token.rsplit(".", 1)
        try:
            body = bytes.fromhex(body_hex)
        except ValueError as e:
            raise CapError("malformed cap body") from e
        expect = hmac.new(self.secret, body, "sha256").hexdigest()
        if not hmac.compare_digest(expect, sig):
            raise CapError("cap signature invalid")
        try:
            claims = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise CapError("cap payload invalid") from e
        if not isinstance(claims, dict):
            raise CapError("cap payload invalid")
        return claims

    def verify(
        self,
        token: str,
        action: str,
        args: dict[str, Any] | None = None,
        *,
        consume_once: bool = True,
        check_once: bool = True,
        subject: str | None = None,
    ) -> dict[str, Any]:
        claims = self.decode(token)
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
        self._check_subject(claims, args, subject)
        self._check_scopes(claims, action, args)
        if claims.get("once") and check_once:
            try:
                self.once.ensure_available(str(jti))
                if consume_once:
                    self.once.commit(str(jti))
            except OnceUsed as e:
                raise CapError("once cap already used") from e
            except StoreDown as e:
                raise CapError("once store down") from e
        return claims

    def commit_once(self, claims: dict[str, Any]) -> None:
        if not claims.get("once"):
            return
        jti = str(claims.get("jti") or "")
        try:
            self.once.commit(jti)
        except OnceUsed as e:
            raise CapError("once cap already used") from e
        except StoreDown as e:
            raise CapError("once store down") from e

    def attenuate(
        self,
        token: str,
        *,
        scopes: list[str] | None = None,
        not_after: float | None = None,
        once: bool | None = None,
        subject: str | None = None,
    ) -> str:
        """I14 / K7: attenuate cannot widen."""
        claims = self.decode(token)
        parent_scopes = [str(s) for s in (claims.get("scopes") or [])]
        if scopes is not None:
            if parent_scopes:
                extra = [s for s in scopes if s not in parent_scopes]
                if extra:
                    raise CapError("attenuate cannot widen scopes")
            # parent unrestricted → child may add limits
            new_scopes = list(scopes)
        else:
            new_scopes = parent_scopes
        parent_na = claims.get("not_after")
        if not_after is not None:
            if parent_na is not None and float(not_after) > float(parent_na):
                raise CapError("attenuate cannot extend not_after")
            new_na = float(not_after)
        else:
            new_na = parent_na
        parent_once = bool(claims.get("once"))
        if once is None:
            new_once = parent_once
        else:
            if parent_once and not once:
                raise CapError("attenuate cannot unset once")
            new_once = bool(once)
        parent_subj = claims.get("subject")
        if subject is not None:
            if parent_subj is not None and subject != parent_subj:
                raise CapError("attenuate cannot change subject")
            new_subj = subject
        else:
            new_subj = parent_subj
        return self.mint(
            str(claims.get("action") or ""),
            once=new_once,
            not_after=new_na,
            scopes=new_scopes or None,
            subject=new_subj,
            jti=None,  # new id; parent once-jti stays the parent's
            law_generation=claims.get("law_generation"),
            args_hash_value=claims.get("args_hash"),
        )

    def _check_subject(
        self,
        claims: dict[str, Any],
        args: dict[str, Any] | None,
        override: str | None,
    ) -> None:
        subj = claims.get("subject")
        if subj is None:
            return
        if not isinstance(subj, str) or not subj.strip():
            raise CapError("empty Cap subject is not allowed")
        got = override if override is not None else (args or {}).get("subject")
        if got != subj:
            raise CapError("subject bind mismatch")

    def _check_scopes(
        self,
        claims: dict[str, Any],
        action: str,
        args: dict[str, Any] | None,
    ) -> None:
        scopes = claims.get("scopes") or []
        if not scopes:
            return
        if any(not str(s).strip() for s in scopes):
            raise CapError("empty scope token is not allowed")
        kind, name = resource_of(action, args)
        if not any(scope_allows(str(s), kind, name) for s in scopes):
            raise CapError("scope does not allow resource")
