"""cek-host — Python Host kernel (authority).

Mint/verify Caps, package projected Ops into Results.
Surface and apps depend on this; Peers never import it for mint.

mode:
  demo   — today's path. In-memory once. Hardcoded secret allowed. CI default.
  adapt  — OnceBackend + digest + subject/scope live.
  require — Phase 2 (BoundAsk + durable once). production() is the factory.

I1  Cap refuse → zero Ops
I4  Once commit only after successful project
I8  Digests are cek1: + FIPS SHA-256
I9  Fail closed on store down
I20 HMAC tamper → zero Ops
I21 Subject bind mismatch → zero Ops
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .cap import CapError, CapService, args_hash, resource_of, scope_allows
from .digest import result_digest
from .doctor import DEMO_SECRET, MIN_SECRET_LEN, DoctorReport, doctor
from .explain import Explanation, explain
from .once import FileOnceBackend, MemoryOnceBackend, OnceBackend, OnceUsed, StoreDown

__version__ = "0.1.1"


@dataclass
class KernelResult:
    kind: str
    ops: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    digest: str | None = None

    def __post_init__(self) -> None:
        if self.digest is None:
            self.digest = result_digest(self.kind, self.ops, self.error)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "ops": self.ops,
            "error": self.error,
            "digest": self.digest,
        }

    @property
    def ok(self) -> bool:
        return self.kind == "ok"

    def explain(self) -> Explanation:
        return explain(self.error)


def _refuse(error: str) -> KernelResult:
    return KernelResult("authority_refusal", [], error)


class Host:
    """Authority kernel: Cap machine + Result packaging.

    Does not compose handlers (that is Surface). Does not apply Ops (that is Peer).
    """

    def __init__(
        self,
        secret: bytes = DEMO_SECRET,
        require_cap: bool = True,
        *,
        once: OnceBackend | None = None,
        mode: str = "demo",
        allow_memory_stores: bool = False,
        ttl_s: int = 3600,
    ) -> None:
        if mode not in ("demo", "adapt", "require"):
            raise ValueError("Host.mode must be demo|adapt|require")
        self.secret = secret
        self.require_cap = require_cap
        self.mode = mode
        self.allow_memory_stores = allow_memory_stores
        self._once: OnceBackend = once if once is not None else MemoryOnceBackend()
        self.caps = CapService(secret=secret, ttl_s=ttl_s, once=self._once)
        self.name = "cek_host.Host"

    @classmethod
    def demo(cls, **kw: Any) -> Host:
        kw.setdefault("mode", "demo")
        return cls(**kw)

    @classmethod
    def adapt(
        cls,
        secret: bytes,
        once: OnceBackend | None = None,
        **kw: Any,
    ) -> Host:
        kw.setdefault("mode", "adapt")
        return cls(secret=secret, once=once or MemoryOnceBackend(), **kw)

    @classmethod
    def production(
        cls,
        secret: bytes,
        once: OnceBackend,
        *,
        allow_memory_stores: bool = False,
        require_cap: bool = True,
        ttl_s: int = 3600,
    ) -> Host:
        """W3 / G8: refuses default secret and memory once-store."""
        if not require_cap:
            raise ValueError("production requires require_cap=True")
        if secret == DEMO_SECRET:
            raise ValueError("production refuses the default demo secret")
        if len(secret) < MIN_SECRET_LEN:
            raise ValueError(f"production secret must be ≥ {MIN_SECRET_LEN} bytes")
        if isinstance(once, MemoryOnceBackend) and not allow_memory_stores:
            raise ValueError(
                "production refuses memory once-store unless allow_memory_stores=True"
            )
        return cls(
            secret=secret,
            once=once,
            mode="adapt",
            allow_memory_stores=allow_memory_stores,
            require_cap=True,
            ttl_s=ttl_s,
        )

    def once_label(self) -> str:
        return self._once.label()

    def mint(
        self,
        action: str,
        *,
        once: bool = False,
        args: dict[str, Any] | None = None,
        seal_args: bool = False,
        **kw: Any,
    ) -> str:
        return self.caps.mint(action, once=once, args=args, seal_args=seal_args, **kw)

    def attenuate(self, token: str, **kw: Any) -> str:
        return self.caps.attenuate(token, **kw)

    def check(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        cap: str | None = None,
        **_kw: Any,
    ) -> KernelResult:
        """Verify without burning once (Surface pre-compose gate)."""
        return self._verify(action, args or {}, cap, consume_once=False)

    def submit(
        self,
        intent: dict[str, Any] | str | None = None,
        args: dict[str, Any] | None = None,
        cap: str | None = None,
        *,
        action: str | None = None,
        activity_id: str | None = None,
        project_ops: list[dict[str, Any]] | None = None,
        **_kw: Any,
    ) -> KernelResult:
        # HostKernel protocol: submit(action, args, cap, *, project_ops=...)
        if isinstance(intent, str):
            action = intent
        elif intent is not None:
            action = intent.get("action") or action
            args = intent.get("args") if args is None else args
            cap = intent.get("cap") if cap is None else cap
            activity_id = intent.get("activity_id") if activity_id is None else activity_id
        action = (action or "").strip()
        args = dict(args or {})
        pre = self._verify(action, args, cap, consume_once=False)
        if not pre.ok:
            return pre
        ops = list(project_ops or [])
        claims = getattr(pre, "_claims", None) or {}
        if claims.get("once"):
            try:
                self.caps.commit_once(claims)
            except CapError as e:
                return _refuse(str(e))
        return KernelResult("ok", ops, None)

    def submit_ops(
        self,
        project_ops: list[dict[str, Any]],
        *,
        cap: str | None = None,
        action: str = "",
        args: dict[str, Any] | None = None,
    ) -> KernelResult:
        return self.submit(action=action, args=args or {}, cap=cap, project_ops=project_ops)

    def explain(self, error: str | None = None) -> Explanation:
        return explain(error)

    def doctor(self, *, fail: bool = False) -> DoctorReport:
        return doctor(self, fail=fail)

    def _verify(
        self,
        action: str,
        args: dict[str, Any],
        cap: str | None,
        *,
        consume_once: bool,
    ) -> KernelResult:
        if not action:
            return _refuse("empty action")
        if self.require_cap or cap:
            if not cap:
                return _refuse("cap required")
            try:
                claims = self.caps.verify(cap, action, args, consume_once=consume_once)
            except CapError as e:
                return _refuse(str(e))
        else:
            claims = {}
        r = KernelResult("ok", [], None)
        r._claims = claims  # type: ignore[attr-defined]
        return r


__all__ = [
    "Host",
    "KernelResult",
    "CapService",
    "CapError",
    "OnceBackend",
    "MemoryOnceBackend",
    "FileOnceBackend",
    "StoreDown",
    "OnceUsed",
    "args_hash",
    "resource_of",
    "scope_allows",
    "result_digest",
    "explain",
    "Explanation",
    "doctor",
    "DoctorReport",
    "DEMO_SECRET",
    "MIN_SECRET_LEN",
    "__version__",
]
