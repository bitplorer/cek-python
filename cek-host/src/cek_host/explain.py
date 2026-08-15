"""Errors that teach — G6.

Every first-week failure names the fix. Silent failures are a P0.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Explanation:
    code: str
    error: str
    meaning: str
    fix: str
    invariant: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "error": self.error,
            "meaning": self.meaning,
            "fix": self.fix,
            "invariant": self.invariant,
        }

    def render(self) -> str:
        return (
            f"[{self.code}] {self.error}\n"
            f"  meaning : {self.meaning}\n"
            f"  fix     : {self.fix}\n"
            f"  holds   : {self.invariant}"
        )


# Matched in order; first needle-in-error wins.
_CATALOG: tuple[tuple[tuple[str, ...], Explanation], ...] = (
    (
        ("cap required", "missing cap", "no cap"),
        Explanation(
            "missing_cap",
            "cap required",
            "Shared-world change needs a verified Cap (K1).",
            "Mint a Cap for this action: host.mint(action, once=True, args=args, seal_args=True).",
            "K1 / I1",
        ),
    ),
    (
        ("once cap already used", "once Cap already used", "already used"),
        Explanation(
            "once_replay",
            "once cap already used",
            "A once-Cap may land exactly one successful project.",
            "Mint a new Cap. Do not retry the same token. Buttons that spent a once-Cap must disable.",
            "K6 / I4",
        ),
    ),
    (
        ("sealed-args mismatch", "sealed args", "args_hash"),
        Explanation(
            "sealed_args_tamper",
            "sealed-args mismatch",
            "The Cap was bound to different args than the Intent.",
            "Submit the same args you sealed, or mint again with the new args.",
            "CORE/22 / I1",
        ),
    ),
    (
        ("cap expired", "expired"),
        Explanation(
            "expired",
            "cap expired",
            "not_after is in the past. Host clock is the clock.",
            "Mint a fresh Cap. Do not extend not_after past the parent (attenuate cannot widen).",
            "I1",
        ),
    ),
    (
        ("action mismatch",),
        Explanation(
            "action_mismatch",
            "action mismatch",
            "Cap.action and Intent.action are different. Action ≠ Op.",
            "Mint for the action you will submit. Do not reuse a Cap across actions.",
            "I19",
        ),
    ),
    (
        ("subject bind mismatch", "empty Cap subject"),
        Explanation(
            "subject_mismatch",
            "subject bind mismatch",
            "Cap.subject must equal args.subject. Claims are no longer write-only.",
            "Pass args={'subject': <same string minted on the Cap>}.",
            "I21",
        ),
    ),
    (
        ("scope does not allow", "empty scope"),
        Explanation(
            "scope_deny",
            "scope does not allow resource",
            "Cap.scopes is a allow-list. Blank tokens refuse. Attenuate cannot widen.",
            "Mint with a scope that matches the resource (action:<name> or kv:<key>).",
            "I13 / I14 / K7",
        ),
    ),
    (
        ("once store down", "store down"),
        Explanation(
            "store_down",
            "once store down",
            "Required once-store is down. Skipping the check would be K6.",
            "Restore the OnceBackend (file path writable, or stop marking memory down).",
            "K6 / I9",
        ),
    ),
    (
        ("short secret", "secret too short", "default secret", "demo secret"),
        Explanation(
            "short_secret",
            "default or short secret",
            "The hardcoded demo secret is not a security domain.",
            "Host.production(secret=secrets.token_bytes(32), once=FileOnceBackend(path)).",
            "G8",
        ),
    ),
    (
        ("embeddedhostkernel", "embedded host"),
        Explanation(
            "embedded_kernel",
            "EmbeddedHostKernel in prod",
            "Surface must not own Cap state. The shim was deleted.",
            "pip install cek-host. load_host_kernel() fails closed if it is missing.",
            "D3 / G4",
        ),
    ),
    (
        ("require_cap",),
        Explanation(
            "require_cap_false",
            "require_cap=False",
            "Production templates never ship require_cap=False.",
            "Construct Host(require_cap=True) or Host.production(...).",
            "K1",
        ),
    ),
    (
        ("memory once", "memory once-store", "multi-worker"),
        Explanation(
            "memory_once",
            "memory once-store in multi-worker",
            "In-process set is not a security domain across workers.",
            "Use FileOnceBackend (or later Redis). production() refuses memory unless allow_memory_stores=True.",
            "K6 / G8",
        ),
    ),
    (
        ("empty action",),
        Explanation(
            "empty_action",
            "empty action",
            "An Intent without an action is not a Cap-bound ask.",
            "Submit a non-empty action string.",
            "I19",
        ),
    ),
    (
        ("malformed cap", "cap body", "cap payload", "cap signature"),
        Explanation(
            "hmac_tamper",
            "cap signature invalid",
            "Missing or tampered HMAC → refuse, zero Ops. Browser is hostile.",
            "Do not edit tokens. Mint from Host. Present the exact string.",
            "I20",
        ),
    ),
    (
        ("empty jti",),
        Explanation(
            "empty_jti",
            "empty jti",
            "A Cap without an id cannot be once-tracked.",
            "Let Host.mint assign jti (default). Do not mint with jti=''.",
            "I4",
        ),
    ),
    (
        ("unknown action",),
        Explanation(
            "unknown_action",
            "unknown action",
            "Surface has no handler. This is dispatch_error, not an authority grant.",
            "Register @surface.action(name) before submit.",
            "I19",
        ),
    ),
    (
        ("rate", "intents_per_sec"),
        Explanation(
            "rate_limited",
            "rate limited",
            "Product policy (not Cap law). Default 50 intents/s.",
            "Back off, or raise SurfacePolicy.max_intents_per_sec in benches only.",
            "D10",
        ),
    ),
)


_FALLBACK = Explanation(
    "unknown",
    "unrecognized error",
    "Host refused or Surface failed, but this string is not in the top-20 catalog.",
    "Read result.error. If refuse, ops is []. File a vector if this is a new kernel reason.",
    "I1",
)


def explain(error: str | None) -> Explanation:
    text = (error or "").strip().lower()
    if not text:
        return Explanation(
            "missing_cap",
            "cap required",
            "No error string — treat as a missing Cap.",
            "Mint a Cap and pass it on the Intent.",
            "K1 / I1",
        )
    for needles, item in _CATALOG:
        if any(n in text for n in needles):
            return item
    return Explanation(
        _FALLBACK.code,
        error or _FALLBACK.error,
        _FALLBACK.meaning,
        _FALLBACK.fix,
        _FALLBACK.invariant,
    )


def catalog() -> list[Explanation]:
    return [item for _, item in _CATALOG]
