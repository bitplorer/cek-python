# S-tier scorecard (W0)

**Trees read (not memory):**
- [cek-framework](https://github.com/bitplorer/cek-framework) `@ 90d48fd` — law freeze
- [cek-runtime](https://github.com/bitplorer/cek-runtime) `@ cce98b6` — reference + 57 vectors
- [cek-python](https://github.com/bitplorer/cek-python) `@ e3a129a` — this workhorse, PyPI 0.1.0

**Doctrine (quote, not a new slogan):**
> Composition = Python + Caps · wire = `Result.ops` · Peer = closed drivers + perception IR · carriers = transport only · law = cek-framework · reference = cek-runtime

**Critic rule:** SHIP only if every plane ≥ 4, no kill-criteria, first-5 timed, `verify.sh` green. This file starts as the W0 snapshot, then records each loop.

---

## Layer map (from the trees)

```
cek-framework          LAW         Cap, Intent, Op, lineage, reverse
     ▲                             CHARTER · KILL-CRITERIA K1–K14 · CORE 00–27
cek-runtime            REFERENCE   BoundAsk, once, lineage, Ed25519, 57 vectors
     ▲                             ports/cek-host-py = rival in-tree Host
cek-host (PyPI)        AUTHORITY   HMAC hex-token + in-memory jti set
     ▲                             subject/scopes stored, not enforced
cek-surface            COMPOSE     Op catalog, Peer IR, carriers, shop
     ▲                             EmbeddedHostKernel residual + sketch Host
app / scaffold / demos CALLERS     no create-app, no doctor, two shops
ux-channel             PRODUCT     not imported (D4 held)
```

---

## REPLACE / ADAPT / KEEP (filled from the trees)

| Verdict | Object | Evidence |
|---------|--------|----------|
| **REPLACE** | `EmbeddedHostKernel` | `cek-surface/src/cek_surface/kernel.py:75`; `load_host_kernel` `except Exception` → shim (G4) |
| **REPLACE** | `ports/cek-host-py` as “the port” | Different token format (Cap dict + `cek1:` HMAC) vs published `hexbody.sig`; 51/57 vectors; not the PyPI Host (G2) |
| **REPLACE** | Runtime `COMPLETENESS.md` verdict | “Shipping code is next” next to 7 crates + 57 vectors + ports (G1, G10) |
| **REPLACE** | PERFORMANCE §6 “P3 when P2 green” | P2/P3 + pypi.org 0.1.0 already shipped same day (G1, G11) |
| **ADAPT** | `cek_host.Host` / `CapService` | Keep HMAC + `args_hash` oracle; add digest `cek1:`, OnceBackend, subject/scope enforce (G3, G8) |
| **ADAPT** | Surface `load_host_kernel` | Fail closed if `cek-host` missing; no shim (D3) |
| **ADAPT** | `cek_surface.host.Host` | Compose sketch; must use `cek_host.CapService`, not a second token format |
| **ADAPT** | 20 surface vectors | Keep shop-shaped pack; add aligned contract family runner (G5, W9) |
| **ADAPT** | Three READMEs | Glance → one screen + one START per repo (G0, G1) |
| **KEEP** | CHARTER / KILL-CRITERIA / CORE 00–27 | Frozen. W11 may add an INDEX pointer only |
| **KEEP** | Rust BoundAsk, lineage, Ed25519, File* stores, cek-cli | Phase 2 / stay in runtime (W8 gated) |
| **KEEP** | Surface Op catalog, Peer IR, carriers, continuations, shop | D1, D5, D6, D9 |
| **KEEP** | D1–D10 | Especially D3 (Host owns Cap) and D4 (no `ux_channel`) |
| **KEEP** | Oracle | `hash_args({"sku":"abc-123","qty":2}) == 96e4f83e3793b646323a67f314b51044` |
| **KEEP** | Channel (Region, @on, ASGI, SSE, CXB, workplace, MCP, WebRTC, Redis product) | Never pull down |
| **KEEP IN FRAMEWORK** | Law encyclopedia | Point up; do not delete |

---

## Planes (W0 scores — critic uses §7, not vibes)

| # | Plane | Score | Gap | Owner | Evidence |
|---|-------|------:|-----|-------|----------|
| 1 | First 5 minutes | **2** | G0 | W1 | cargo demo exists; pip path is clone+editable, not one-file morph. No START. |
| 2 | Doc pyramid | **2** | G1 | W1 | Three intros. Runtime COMPLETENESS lies. Python PERFORMANCE/HANDOFF stale vs SHIPPED. |
| 3 | Explain / CLI | **1** | G6 | W2 | No `explain()`, no `doctor()`, no console script. |
| 4 | Scaffold = running app | **1** | G7 | W2 | `create-app` does not exist. |
| 5 | Security residuals | **2** | G8 | W3 | Default secret hardcoded. Memory jti. subject/scopes write-only. HMAC/once/seal **held**. |
| 6 | Kernel honesty | **2** | G2–G4 | W4 | Two Python Hosts. Thin HMAC. No digest. Embedded residual. No BoundAsk (Phase 2). |
| 7 | Test honesty | **3** | G5 | W5/W9 | 20 shop vectors + 57 Rust vectors. No shared aligned-family runner on published Host. |
| 8 | Flagship product feel | **3** | G9 | W6 | `shop_app` has empty/error/pending/once. README points at legacy `app.py`. No once-used disable. |
| 9 | Operability | **1** | G10 | W7 | No `doctor()`. production factory absent. |
| 10 | Power preserved | **4** | — | W10 | D1–D2, D4–D10 held. Peer IR, carriers, continuations work. Surface composes **before** verify. |
| 11 | Classic CEK client | **4** | — | W10 | No Channel / hello / CXB required. HTTP demo `auto_mint` is a ding, not a kill. |
| 12 | Layer honesty | **3** | G12 | W4/W11 | D4 held. D3 partial (Embedded + sketch Host). Law unamended. ports/cek-host-py is a rival. |

**W0 floor:** 1. **W0 ceiling:** 4. **Any plane ≤ 2 ⇒ FAIL** if this were a SHIP review.

---

## Invariants claimed vs held (Python `@ e3a129a`)

From runtime INVARIANTS + framework K1–K14. Unclaimed = not SHIP on that plane.

| # | Invariant | Python 0.1.0 | Note |
|---|-----------|--------------|------|
| 1 | Cap refuse → zero Ops | **held** | HMAC path, vectors, tests |
| 2 | BoundAsk only after verify+once | **unclaimed** | No BoundAsk type (Phase 2). Surface composes before verify |
| 3 | Peer has no mint | **held** | JS Peer + test |
| 4 | Once commit only after project | **partial** | Burn inside `verify()`, in-memory set |
| 5 | Idempotency before once-ensure | **unclaimed** | Phase 2 |
| 6 | Same idem key + different body → refuse | **unclaimed** | Phase 2 |
| 7 | Landed-first reverse | **unclaimed** | Phase 2 |
| 8 | Digests `cek1:` + FIPS SHA-256 | **unclaimed** | `args_hash` is 32-hex (oracle, keep); Result has no digest |
| 9 | Fail closed on store down | **unclaimed** | There is no store (K6 residual) |
| 10 | Trace is not permission | **held by absence** | Host ignores trace |
| 11 | Honest reverse | **unclaimed** | Phase 2 |
| 12 | Concurrent once: exactly one ok | **unclaimed** | |
| 13 | Scope deny / blank token → zero Ops | **unclaimed** | scopes stored, not checked |
| 14 | Attenuate cannot widen | **unclaimed** | no `attenuate` |
| 15–16 | ui/kv reverse | **unclaimed** | Surface may project restore Ops; Host lineage is Phase 2 |
| 17 | TS/JS/WASM/Python Peer no mint | **held** (JS) | |
| 18 | Empty idempotency key → refuse | **unclaimed** | Phase 2 |
| 19 | Action ≠ Op | **held** | |
| 20 | Cap HMAC missing/tamper → zero Ops | **held** | |
| 21 | Subject bind mismatch → zero Ops | **unclaimed** | write-only |
| 22 | Ed25519 missing/tamper | **unclaimed** | Phase 2 Host policy |
| 23 | Unknown/blank law generation | **unclaimed** | Phase 2 |
| 24 | Batteries: refuse never leaks Ops | **partial** | shop chaos exists; not the 57-vector pack |

**Do not claim 2, 5–9, 11–16, 18, 21–23 in SHIPPED.md until a named test exists.**

---

## Two Python Hosts (G2) — measured

| | `cek-python/cek-host` (PyPI) | `cek-runtime/ports/cek-host-py` |
|--|------------------------------|----------------------------------|
| Token | `hex(json).hmac` | Cap dict + `sig: cek1:…` / `ed25519:…` |
| Digest | none | `cek1:` SHA-256 over `{error,kind,ops}` |
| Once | `set[str]` inside `CapService` | `set[str]` after project |
| Subject / scopes | minted, **not verified** | enforced (`_verify`) |
| Ed25519 | no | yes |
| Lineage / BoundAsk | no | lineage yes, BoundAsk **no** |
| Vectors | 20 shop-shaped | 51/57 contract |
| Published | **yes** (`cek-host` 0.1.0) | **must not** be a second Host |

Destination: **one** published Host (`cek-host`) runs the aligned family. `ports/cek-host-py` becomes a pointer.

---

## Loop log

| Loop | Lowest plane | Diff | Proof | Critic |
|------|--------------|------|-------|--------|
| 0 | — | Scorecard only | trees @ frozen HEADs | — |
| 1 | 3,4,9 + 5,6 + 1,2 | Phase 1 Host + DX + pyramid + shop + aligned vectors | `sh scripts/verify.sh` → `verify ok`. Oracle `96e4f83e3793b646323a67f314b51044`. FIRST5 editable-install **7.912 s**. A≡B. doctor --production-demo FAIL | **ALMOST** (7 planes at 3). Named: PyPI 0.1.1 lie, public `cek_surface.Host`, FileOnce no flock, bench imports Embedded, ARCHITECTURE stale, scaffold doctor-green on memory |
| 2 | 1,2,5,6,8,12 | Honest START (clone path). `Host` unexported. flock. bench+ARCHITECTURE fixed. scaffold uses `production()`+FileOnce. surface dep `cek-host>=0.1.0` | `verify ok` again | pending re-score |

## Critic pastes (loop 1 executed here; critic was read-only)

```
FIRST5_WALL_S=7.912
# clean venv → pip install -e ./cek-host -e ./cek-surface → create-app → first morph + once refuse
```

```
sh scripts/verify.sh
verify ok
```

```
python -m cek_host doctor --production-demo
cek-host doctor
  [FAIL] secret: default demo secret — production() refuses it
  [ok] require_cap: True
  [FAIL] once-store: memory — not a security domain across workers
  [ok] mode: adapt
  [ok] embedded: EmbeddedHostKernel absent
  [ok] d4: cek_surface → ux_channel is []
  [ok] vectors: surface_core v3 (20 cases)
doctor: FAIL
```

```
from cek_host.cap import args_hash
assert args_hash({"sku":"abc-123","qty":2})=="96e4f83e3793b646323a67f314b51044"
```

```
test_host_parity.py → host parity ok  A ≡ B
test_layer_honesty.py → cek_surface → ux_channel is []
test_http_host.py + test_vectors.py → two surface planes (shop + HTTP Host)
```

## Planes after loop 2

| # | Plane | W0 | L1 self | L1 critic | L2 |
|---|-------|---:|--------:|----------:|---:|
| 1 | First 5 minutes | 2 | 4 | 3 | **4** START is the clone path; 7.9 s timed |
| 2 | Doc pyramid | 2 | 4 | 3 | **4** PyPI 0.1.0 honesty; ARCHITECTURE/INVARIANTS fixed |
| 3 | Explain / CLI | 1 | 4 | 4 | 4 |
| 4 | Scaffold | 1 | 4 | 4 | **4** now `Host.production` + FileOnce |
| 5 | Security residuals | 2 | 4 | 3 | **4** flock on FileOnce |
| 6 | Kernel honesty | 2 | 4 | 3 | **4** `cek_surface.Host` not public. ports sketch stays for rust batteries, README-pointer |
| 7 | Test honesty | 3 | 4 | 3 | **4** verify executed. Aligned family translated (not raw 57 — noted) |
| 8 | Flagship feel | 3 | 4 | 3 | **4** bench no longer imports Embedded |
| 9 | Operability | 1 | 4 | 4 | 4 |
| 10 | Power preserved | 4 | 4 | 4 | 4 |
| 11 | Classic CEK | 4 | 4 | 4 | 4 |
| 12 | Layer honesty | 3 | 4 | 3 | **4** D3/D4 tests; law INDEX only |

## Remaining (not SHIP-blockers if critic agrees; still honest)

- `ports/cek-host-py` **code** kept because `scripts/batteries.sh` + `demo/host-peer` still run it. It is not published.
- Python does not execute the raw 57 JSON fixtures; it runs the aligned family on the published token format.
- Tree 0.1.1 is not on pypi.org yet.
- Phase 2 (BoundAsk, lineage, Ed25519) not started.

## Current critic verdict

Loop 1: **ALMOST**. Loop 2 addresses every named fix. Re-score required for SHIP — do not hallucinate SHIP.

Phase 2 (BoundAsk, IdemBackend, LineageBackend, Ed25519 Host policy, `require` cutover) **does not start** until Phase 1 critic SHIP.

