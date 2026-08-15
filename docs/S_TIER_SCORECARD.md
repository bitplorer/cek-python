# S-tier scorecard (W0)

**Trees read (not memory):**
- [cek-framework](https://github.com/bitplorer/cek-framework) `@ 90d48fd` — law freeze (`2a0d17a` INDEX pointer only)
- [cek-runtime](https://github.com/bitplorer/cek-runtime) `@ cce98b6` — reference + 57 vectors (docs after: START honesty)
- [cek-python](https://github.com/bitplorer/cek-python) `@ e3a129a` — workhorse; tree **0.1.1** Phase 1

**Doctrine (quote, not a new slogan):**
> Composition = Python + Caps · wire = `Result.ops` · Peer = closed drivers + perception IR · carriers = transport only · law = cek-framework · reference = cek-runtime

**Critic rule:** SHIP only if every plane ≥ 4, no kill-criteria, first-5 timed, `verify.sh` green.

---

## Layer map (from the trees)

```
cek-framework          LAW         Cap, Intent, Op, lineage, reverse
     ▲                             CHARTER · KILL-CRITERIA K1–K14 · CORE 00–27
cek-runtime            REFERENCE   BoundAsk, once, lineage, Ed25519, 57 vectors
     ▲                             ports/cek-host-py = historic sketch, not published
cek-host (PyPI)        AUTHORITY   HMAC hex-token · OnceBackend · subject/scope · digest
cek-surface            COMPOSE     Op catalog, Peer IR, carriers, shop
     ▲                             no EmbeddedHostKernel · no sketch Host
app / scaffold / demos CALLERS     create-app · doctor · explain · shop
ux-channel             PRODUCT     not imported (D4 held)
```

---

## REPLACE / ADAPT / KEEP (filled from the trees)

| Verdict | Object | Evidence |
|---------|--------|----------|
| **REPLACE** | `EmbeddedHostKernel` | **gone** — `kernel.py` `__getattr__` raises |
| **REPLACE** | `cek_surface.host.Host` | **gone** — Intent/Result/ActionContext only (D3) |
| **REPLACE** | `ports/cek-host-py` as “the port” | README is a pointer. Code stays for rust batteries. Not published. |
| **REPLACE** | Runtime `COMPLETENESS.md` “Shipping code is next” | Fixed |
| **REPLACE** | PERFORMANCE §6 “P3 when P2 green” | Fixed |
| **ADAPT** | `cek_host.Host` / `CapService` | HMAC + oracle kept; digest `cek1:`, OnceBackend, subject/scope enforced |
| **ADAPT** | Surface `load_host_kernel` | Fail closed if `cek-host` missing |
| **ADAPT** | Aligned contract family | Runner **loads** Rust JSON (vendored + sibling). One Cap-dict → hex-token adapter |
| **ADAPT** | Three READMEs | One screen + one START. PyPI 0.1.0 has no create-app — clone path is the command |
| **KEEP** | CHARTER / KILL-CRITERIA / CORE 00–27 | Frozen. INDEX pointer only |
| **KEEP** | Rust BoundAsk, lineage, Ed25519, File* stores, cek-cli | Phase 2 / stay in runtime |
| **KEEP** | Surface Op catalog, Peer IR, carriers, continuations, shop | D1, D5, D6, D9 |
| **KEEP** | D1–D10 | Especially D3 and D4 |
| **KEEP** | Oracle | `hash_args({"sku":"abc-123","qty":2}) == 96e4f83e3793b646323a67f314b51044` |
| **KEEP** | Channel | Never pull down |
| **KEEP IN FRAMEWORK** | Law encyclopedia | Point up; do not delete |

---

## Planes

| # | Plane | W0 | L1 | L2 | L3 (this loop) | Gap | Owner |
|---|-------|---:|---:|---:|---------------:|-----|-------|
| 1 | First 5 minutes | 2 | 3 | 4 | **4** | G0 | W1 |
| 2 | Doc pyramid | 2 | 3 | 4 | **4** | G1 | W1 |
| 3 | Explain / CLI | 1 | 4 | 4 | **4** | G6 | W2 |
| 4 | Scaffold | 1 | 4 | 4 | **4** | G7 | W2 |
| 5 | Security residuals | 2 | 3 | 4 | **4** | G8 | W3 |
| 6 | Kernel honesty | 2 | 3 | 4 | **4** | G2–G4 | W4 |
| 7 | Test honesty | 3 | 3 | 4 | **4** | G5 | W5/W9 |
| 8 | Flagship feel | 3 | 3 | 4 | **4** | G9 | W6 |
| 9 | Operability | 1 | 4 | 4 | **4** | G10 | W7 |
| 10 | Power preserved | 4 | 4 | 4 | **4** | — | W10 |
| 11 | Classic CEK | 4 | 4 | 4 | **4** | — | W10 |
| 12 | Layer honesty | 3 | 3 | 4 | **4** | G12 | W4/W11 |

Loop-2 self-score of “all 4s” was **rejected** by the independent critic (ALMOST): leftover sketch Host, four pages teaching PyPI `create-app`, translated vectors.

Loop 3 is the critic’s listed diffs only.

---

## Invariants claimed vs held (Python tree 0.1.1)

| # | Invariant | Status | Note |
|---|-----------|--------|------|
| 1 | Cap refuse → zero Ops | **held** | HMAC path, vectors, tests |
| 2 | BoundAsk only after verify+once | **unclaimed** | Phase 2. Surface `check()` before compose (I2-lite) |
| 3 | Peer has no mint | **held** | JS Peer + test |
| 4 | Once commit only after project | **held** | published Host commits after `project_ops` |
| 5 | Idempotency before once-ensure | **unclaimed** | Phase 2 |
| 6 | Same idem key + different body → refuse | **unclaimed** | Phase 2 |
| 7 | Landed-first reverse | **unclaimed** | Phase 2 |
| 8 | Digests `cek1:` + FIPS SHA-256 | **held** | Result.digest; args_hash oracle kept |
| 9 | Fail closed on store down | **held** | MemoryOnceBackend(down=True) |
| 10 | Trace is not permission | **held by absence** | Host ignores trace |
| 11 | Honest reverse | **unclaimed** | Phase 2 |
| 12 | Concurrent once: exactly one ok | **partial** | flock on FileOnce |
| 13 | Scope deny / blank token → zero Ops | **held** | |
| 14 | Attenuate cannot widen | **held** | |
| 15–16 | ui/kv reverse | **unclaimed** | Phase 2 |
| 17 | TS/JS/WASM/Python Peer no mint | **held** (JS) | |
| 18 | Empty idempotency key → refuse | **unclaimed** | Phase 2 |
| 19 | Action ≠ Op | **held** | |
| 20 | Cap HMAC missing/tamper → zero Ops | **held** | raw fixtures cap-sig-* |
| 21 | Subject bind mismatch → zero Ops | **held** | |
| 22 | Ed25519 missing/tamper | **unclaimed** | Phase 2 |
| 23 | Unknown/blank law generation | **unclaimed** | Phase 2 |
| 24 | Batteries: refuse never leaks Ops | **held** | shop + aligned family |

---

## Loop log

| Loop | Lowest plane | Diff | Proof | Critic |
|------|--------------|------|-------|--------|
| 0 | — | Scorecard only | trees @ frozen HEADs | — |
| 1 | 3,4,9 + 5,6 + 1,2 | Phase 1 Host + DX + pyramid + shop + aligned vectors | `verify ok`. FIRST5 **7.912 s**. A≡B | **ALMOST** |
| 2 | 1,2,5,6,8,12 | Honest START. Host unexported. flock. scaffold production()+FileOnce | `verify ok` | **ALMOST** — sketch Host still a machine; PyPI create-app lie; translated vectors |
| 3 | 2,6,7,12 | Delete `cek_surface.host.Host`. test_core → published Host+Surface. Four pages use clone path. Runner **loads** Rust JSON (14 aligned). `/cek/mint` + submit `auto_mint=False` | `sh scripts/verify.sh` → `verify ok`. FIRST5 **7.318 s**. 14 fixtures. missing cap → refuse | **ALMOST** — CLI `create-app` still printed `pip install cek-host cek-surface` |
| 4 | 3 | `cli.py` next-step is `python app.py` (no PyPI install). START timer **7.3 s** | `verify ok`. `create-app` stdout has no `pip install cek-host` | critic L3: SHIP if that line is gone and verify green — **condition met** |

## Critic pastes (loop 3 executed here)

```
FIRST5_WALL_S=7.318
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
test_layer_honesty.py → sketch Host gone; cek_surface → ux_channel is []
test_http_host.py → missing cap refuses; mint+submit shop + HTTP Host
test_contract_vectors.py → 14 Rust JSON fixtures (aligned family)
```

```
96e4f83e3793b646323a67f314b51044
```

## Remaining (honest, not Phase-1 blockers)

- `ports/cek-host-py` **code** kept because `scripts/batteries.sh` + `demo/host-peer` still run it. Not published.
- Phase 2 families (Ed25519, lineage, idempotency, law-generation) stay in runtime. Not claimed.
- Tree 0.1.1 is not on pypi.org yet. START says so.
- Phase 2 (BoundAsk, lineage, Ed25519) **does not start** until Phase 1 critic SHIP.

## Current critic verdict

Loop 2: **ALMOST** (independent critic, four planes at 3).
Loop 3: **ALMOST** (independent critic). Named leftover: `cli.py` create-app next-step still printed `pip install cek-host cek-surface`.
Loop 4: that line is `python {dest}/app.py`. `sh scripts/verify.sh` → `verify ok` on this machine.

Critic L3 close condition: “SHIP if that line is gone and `verify.sh` is green.” **Condition met.** Every plane ≥ 4. No kill. CHARTER / KILL-CRITERIA / CORE untouched. Phase 2 not started.

```
created …/app.py
next   : python …/app.py
doctor : python -m cek_host doctor --fail
```

