"""Python Host runtime — language port of decide.

Not a wrap of cek-host-kernel unless RustHostKernel is used.
Does not compose handlers (Surface). Does not apply Ops (Peer).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .bound import BoundAsk
from .cap import CapError, CapService
from .digest import result_digest
from .host_project import resolve_ops
from .host_verify import check_ed25519, check_generation
from .doctor import DEMO_SECRET, MIN_SECRET_LEN, DoctorReport, doctor
from .explain import Explanation, explain
from .idem import FileIdemBackend, IdemConflict, IdemBackend, MemoryIdemBackend
from .lineage import (
    FileLineageBackend,
    LineageBackend,
    LineageError,
    MemoryLineageBackend,
    ReverseOutcome,
    inverse_ops,
    reverse_activity,
    reverse_class_for,
)
from .once import FileOnceBackend, MemoryOnceBackend, OnceBackend, OnceUsed, StoreDown

LAW_GENERATION = "cek-law-1"


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
        idem: IdemBackend | None = None,
        lineage: LineageBackend | None = None,
        mode: str = "demo",
        allow_memory_stores: bool = False,
        ttl_s: int = 3600,
        ed25519_seed: bytes | None = None,
        ed25519_trust: list[bytes] | None = None,
        accepted_generations: list[str] | None = None,
    ) -> None:
        if mode not in ("demo", "adapt", "require"):
            raise ValueError("Host.mode must be demo|adapt|require")
        self.secret = secret
        self.require_cap = require_cap
        self.mode = mode
        self.allow_memory_stores = allow_memory_stores
        self._once: OnceBackend = once if once is not None else MemoryOnceBackend()
        self._idem: IdemBackend = idem if idem is not None else MemoryIdemBackend()
        self._lineage: LineageBackend = lineage if lineage is not None else MemoryLineageBackend()
        self.caps = CapService(secret=secret, ttl_s=ttl_s, once=self._once)
        self.name = "cek_host.Host"
        self._ed_seed = ed25519_seed
        self._ed_trust = list(ed25519_trust or [])
        if ed25519_seed is not None:
            from .ed25519 import public_key

            pk = public_key(ed25519_seed)
            if pk not in self._ed_trust:
                self._ed_trust.append(pk)
        self.accepted_generations = list(accepted_generations or [LAW_GENERATION])
        if LAW_GENERATION not in self.accepted_generations:
            self.accepted_generations.insert(0, LAW_GENERATION)
        # Session stamp: None = use default_stamp_pairs() at project time.
        self.stamp: frozenset[tuple[str, str]] | None = None

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
        idem: IdemBackend | None = None,
        lineage: LineageBackend | None = None,
        allow_memory_stores: bool = False,
        require_cap: bool = True,
        ttl_s: int = 3600,
        ed25519_seed: bytes | None = None,
    ) -> Host:
        """Refuses default secret and memory stores unless allow_memory_stores."""
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
        if idem is None and isinstance(once, FileOnceBackend):
            idem = FileIdemBackend(str(once.path) + ".idem")
        if lineage is None and isinstance(once, FileOnceBackend):
            lineage = FileLineageBackend(str(once.path) + ".lineage")
        if idem is None:
            idem = MemoryIdemBackend()
        if lineage is None:
            lineage = MemoryLineageBackend()
        if not allow_memory_stores:
            if isinstance(idem, MemoryIdemBackend):
                raise ValueError(
                    "production refuses memory idem-store unless allow_memory_stores=True"
                )
            if isinstance(lineage, MemoryLineageBackend):
                raise ValueError(
                    "production refuses memory lineage-store unless allow_memory_stores=True"
                )
        return cls(
            secret=secret,
            once=once,
            idem=idem,
            lineage=lineage,
            mode="require",
            allow_memory_stores=allow_memory_stores,
            require_cap=True,
            ttl_s=ttl_s,
            ed25519_seed=ed25519_seed,
        )

    def once_label(self) -> str:
        return self._once.label()

    def idem_label(self) -> str:
        return self._idem.label()

    def lineage_label(self) -> str:
        return self._lineage.label()

    def mint(
        self,
        action: str,
        *,
        once: bool = False,
        args: dict[str, Any] | None = None,
        seal_args: bool = False,
        law_generation: str | None = ...,  # type: ignore[assignment]
        attach_ed25519: bool = True,
        **kw: Any,
    ) -> str:
        if law_generation is ...:  # type: ignore[comparison-overlap]
            law_generation = LAW_GENERATION
        kw.pop("ed25519_seed", None)
        ed_seed = self._ed_seed if attach_ed25519 else None
        return self.caps.mint(
            action,
            once=once,
            args=args,
            seal_args=seal_args,
            law_generation=law_generation,
            ed25519_seed=ed_seed,
            **kw,
        )

    def attenuate(self, token: str, **kw: Any) -> str:
        tok = self.caps.attenuate(token, **kw)
        if self._ed_seed is None:
            return tok
        claims = self.caps.decode(tok)
        return self.caps.mint(
            str(claims.get("action") or ""),
            once=bool(claims.get("once")),
            not_after=claims.get("not_after"),
            scopes=list(claims["scopes"]) if claims.get("scopes") else None,
            subject=claims.get("subject"),
            jti=claims.get("jti"),
            law_generation=claims.get("law_generation"),
            args_hash_value=claims.get("args_hash"),
            ed25519_seed=self._ed_seed,
        )

    def check(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        cap: str | None = None,
        **kw: Any,
    ) -> KernelResult:
        """Verify without burning once (Surface pre-compose gate).

        Once-availability is skipped when an idempotency key is present so a
        retry of a spent once-Cap can still replay (I5).
        """
        idem_key = kw.get("idempotency_key")
        check_once = not (isinstance(idem_key, str) and idem_key.strip())
        return self._verify(
            action, args or {}, cap, consume_once=False, check_once=check_once
        )

    def submit(
        self,
        intent: dict[str, Any] | str | None = None,
        args: dict[str, Any] | None = None,
        cap: str | None = None,
        *,
        action: str | None = None,
        activity_id: str | None = None,
        project_ops: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
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
            if idempotency_key is None:
                idempotency_key = intent.get("idempotency_key")
        action = (action or "").strip()
        args = dict(args or {})

        # 1. Cap verify (no once). Law-gen + Ed25519 are Host policy.
        pre = self._verify(action, args, cap, consume_once=False, check_once=False)
        if not pre.ok:
            return pre
        claims = getattr(pre, "_claims", None) or {}

        # 2. Idempotency lookup BEFORE once-ensure (I5 / I18).
        if idempotency_key is not None:
            if not str(idempotency_key).strip():
                return _refuse("empty idempotency key is not allowed")
            try:
                planned = resolve_ops(action, args, project_ops, self.stamp)
            except ValueError:
                planned = None
            try:
                prior = self._idem.get(str(idempotency_key))
            except StoreDown:
                return _refuse("idempotency store down")
            if prior is not None:
                if planned is None:
                    return _refuse(f"idempotency conflict for key `{idempotency_key}`")
                digest = result_digest("ok", planned, None)
                if prior.get("digest") == digest:
                    return KernelResult(
                        str(prior.get("kind") or "ok"),
                        list(prior.get("ops") or []),
                        prior.get("error"),
                    )
                return _refuse(f"idempotency conflict for key `{idempotency_key}`")

        # 3. Once-ensure, then BoundAsk (I2).
        if claims.get("once"):
            jti = str(claims.get("jti") or "")
            try:
                self._once.ensure_available(jti)
            except OnceUsed:
                return _refuse("once cap already used")
            except StoreDown:
                return _refuse("once store down")

        bound = BoundAsk._bind(action, args, claims, self.caps.now_fn())
        return self._finish(bound, project_ops, activity_id, idempotency_key)

    async def async_check(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        cap: str | None = None,
        **kw: Any,
    ) -> KernelResult:
        """Awaitable check. Same law as check; does not occupy the event loop."""
        import asyncio

        return await asyncio.to_thread(self.check, action, args, cap, **kw)

    async def async_submit(
        self,
        intent: dict[str, Any] | str | None = None,
        args: dict[str, Any] | None = None,
        cap: str | None = None,
        *,
        action: str | None = None,
        activity_id: str | None = None,
        project_ops: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
        **_kw: Any,
    ) -> KernelResult:
        """Awaitable submit. Same law as submit; store I/O runs in a worker."""
        import asyncio

        return await asyncio.to_thread(
            self.submit,
            intent,
            args,
            cap,
            action=action,
            activity_id=activity_id,
            project_ops=project_ops,
            idempotency_key=idempotency_key,
            **_kw,
        )

    async def async_submit_ops(
        self,
        project_ops: list[dict[str, Any]],
        *,
        cap: str | None = None,
        action: str = "",
        args: dict[str, Any] | None = None,
        activity_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> KernelResult:
        return await self.async_submit(
            action=action,
            args=args or {},
            cap=cap,
            project_ops=project_ops,
            activity_id=activity_id,
            idempotency_key=idempotency_key,
        )

    def submit_ops(
        self,
        project_ops: list[dict[str, Any]],
        *,
        cap: str | None = None,
        action: str = "",
        args: dict[str, Any] | None = None,
        activity_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> KernelResult:
        return self.submit(
            action=action,
            args=args or {},
            cap=cap,
            project_ops=project_ops,
            activity_id=activity_id,
            idempotency_key=idempotency_key,
        )

    def report_receipt(
        self,
        activity_id: str,
        landed: list[dict[str, Any]] | None = None,
        *,
        receipt: dict[str, Any] | None = None,
    ) -> None:
        ops = (
            list(landed)
            if landed is not None
            else list((receipt or {}).get("landed") or (receipt or {}).get("ops") or [])
        )
        self._lineage.annotate_landed_latest(activity_id, ops)

    def end_activity(self, activity_id: str) -> ReverseOutcome:
        return reverse_activity(self._lineage, activity_id)

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
        check_once: bool = True,
    ) -> KernelResult:
        if not action:
            return _refuse("empty action")
        if self.require_cap or cap:
            if not cap:
                return _refuse("cap required")
            try:
                claims = self.caps.verify(
                    cap, action, args, consume_once=consume_once, check_once=check_once
                )
                check_generation(claims, self.accepted_generations)
                check_ed25519(claims, seed=self._ed_seed, trust=self._ed_trust)
            except CapError as e:
                return _refuse(str(e))
        else:
            claims = {}
        r = KernelResult("ok", [], None)
        r._claims = claims  # type: ignore[attr-defined]
        return r

    def _finish(
        self,
        bound: BoundAsk,
        project_ops: list[dict[str, Any]] | None,
        activity_id: str | None,
        idempotency_key: str | None,
    ) -> KernelResult:
        try:
            ops = resolve_ops(bound.action, bound.args, project_ops, self.stamp)
        except ValueError as e:
            # Dispatch miss: once-Cap is NOT committed.
            return KernelResult("dispatch_error", [], str(e))

        digest = result_digest("ok", ops, None)
        result = KernelResult("ok", ops, None)

        if idempotency_key is not None:
            try:
                replay = self._idem.put_or_check(
                    str(idempotency_key), digest, result.to_dict()
                )
            except IdemConflict as e:
                return _refuse(str(e))
            except StoreDown:
                return _refuse("idempotency store down")
            if replay is not None:
                return KernelResult(
                    str(replay.get("kind") or "ok"),
                    list(replay.get("ops") or []),
                    replay.get("error"),
                )

        if bound.claims.get("once"):
            try:
                self.caps.commit_once(bound.claims)
            except CapError as e:
                return _refuse(str(e))

        if activity_id is not None:
            if not str(activity_id).strip():
                return KernelResult("dispatch_error", [], "empty activity_id")
            inverse = inverse_ops(ops)
            rclass = reverse_class_for(ops)
            try:
                self._lineage.commit(
                    str(bound.claims.get("jti") or ""),
                    activity_id,
                    bound.action,
                    ops,
                    rclass,
                    inverse,
                )
            except LineageError as e:
                return KernelResult("dispatch_error", [], str(e))
            except StoreDown as e:
                return KernelResult("dispatch_error", [], str(e))

        return result
