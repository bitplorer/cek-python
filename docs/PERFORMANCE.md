# CEK Python — Real-World Test & Performance Report

**Read [START.md](../START.md) first.**

**Date:** 2026-08-15  
**Repo:** [bitplorer/cek-python](https://github.com/bitplorer/cek-python)  
**Machine:** Linux container, Python 3.12.3, Node v24.15.0  
**Packages:** `cek-host` 0.1.0 (numbers below) · Phase 1 kernel (`0.1.1`) must not regress Host-only p95 > 10%  
**Kernel under test:** `CekHostPyKernel` → `cek_host.Host`

---

## 1. Executive summary

| Gate | Result |
|------|--------|
| Unit / integration suite (`scripts/verify.sh`) | **PASS** |
| Shop end-to-end journey (boot → search → cart → checkout) | **PASS** |
| Cap security (once / sealed-args / refuse / wrong action) | **PASS** |
| Live continuation (`timer.fired` → pre-minted Cap → `search.commit`) | **PASS** |
| HTTP Host `/cek/submit` (browser-as-Peer, no `?mock=1`) | **PASS** |
| Invariants (refuse → `ops:[]`, Peer no mint, fail closed) | **PASS** |

**Performance takeaway:** Host compose + Cap is ~**0.03 ms** (p50). Full Host → local JS Peer is ~**0.3–0.5 ms**. End-user lag is **RTT-bound**, not mechanism-bound. Default policy rate-limits at **50 intents/s** (product guard, intentional).

No CXB / p95 claim without a checked-in number. Numbers below are the checked-in numbers.

---

## 2. Real-world scenarios

### A. Shop journey (subprocess Peer)

| Step | kind | ops | latency |
|------|------|-----|---------|
| `shop.boot` | ok | 7 | ~43 ms (cold Peer spawn) |
| `search.type` + async drain | ok | 4 | ~17 ms (timer 15 ms + commit) |
| `cart.add` sku-1 | ok | 4 | ~0.8 ms |
| `cart.add` sku-2 ×2 | ok | 4 | ~0.7 ms |
| `checkout.start` | ok | 5 | ~0.6 ms |
| `checkout.submit` bad email | ok | 3 | ~0.5 ms (validation via Ops, not refuse) |
| `checkout.submit` valid | ok | 8 | ~1.2 ms |

Order placed; `last_order.id` present. **PASS**.

### B. Cap security

| Case | Expected | Observed |
|------|----------|----------|
| once Cap first use | ok | ok |
| once Cap replay | `authority_refusal`, `ops: []` | **PASS** |
| sealed-args tamper (qty 1 → 99) | refuse, empty ops | **PASS** |
| missing Cap | refuse, empty ops | **PASS** |
| Cap for wrong action | refuse, empty ops | **PASS** |

### C. Live continuation

`search.type` arms `timer.fired:search-debounce` with a **once** Cap for `search.commit`.  
Drain produced 1 followup `kind=ok`, catalog hit `sku-3` for query `Gadget`.  
Wall time ~**11.5 ms** (dominated by 10 ms timer). **PASS**.

### D. HTTP Host (browser is Peer)

| Call | Result | latency |
|------|--------|---------|
| `shop.boot` | ok | ~1.8 ms |
| `search.type` | ok + continuation Cap | ~1.1 ms |
| `search.commit` under Cap | ok | ~1.0 ms |
| same Cap replay | `authority_refusal`, `ops: []` | — |
| `cart.add` | ok | ~1.0 ms |

Compose-only Host path (memory Peer echo); browser applies `Result.ops`. **PASS**.

---

## 3. Performance numbers

All times in **milliseconds**. Rate limit raised to ∞ for pure load series (default 50/s is a separate product guard).

### 3.1 Mechanism (no network)

| Path | n | p50 | p95 | p99 | max | mean | ops/s |
|------|---|-----|-----|-----|-----|------|-------|
| **Cap mint** | 500 | 0.009 | 0.014 | 0.030 | 0.078 | 0.010 | ~101k |
| **Cap verify** | 500 | 0.006 | 0.008 | 0.014 | 0.040 | 0.006 | ~164k |
| **Host-only** compose+Cap+package (`cart.add`) | 200 | **0.026** | 0.048 | 0.072 | 0.193 | 0.030 | ~33k |
| **Memory carrier** full submit | 200 | **0.041** | 0.139 | 0.526 | 1.814 | 0.072 | ~14k |
| **Full path** Host → Node Peer apply | 100 | **0.321** | 0.535 | 0.901 | 0.914 | 0.350 | ~2.9k |
| **Refuse** (no Cap) full path | 100 | 0.321 | 0.959 | 1.866 | 3.168 | 0.436 | ~2.3k |

Kernel-parity budget: Host-only p95 must not regress **> 10%** vs 0.048 ms (ceiling **0.053 ms**).

### 3.2 Multi-round / async

| Path | n | p50 | p95 | mean | notes |
|------|---|-----|-----|------|-------|
| `search.type` + continuation drain | 15 | **11.4** | 16.3 | 12.1 | timer `ms=10` dominates |

### 3.3 Simulated network RTT (uplink + downlink sleep around local Host→Peer)

| Profile | n | p50 | p95 | mean |
|---------|---|-----|-----|------|
| LAN ~1 ms RTT | 30 | 1.6 | 2.1 | 1.6 |
| Metro ~20 ms RTT | 30 | **22.1** | 25.1 | 22.3 |
| WAN ~80 ms RTT | 30 | **78.8** | 102.1 | 82.3 |

### 3.4 Product rate limit (default policy)

80 sequential `cart.add` with default `max_intents_per_sec=50`:

- **50** ok  
- **30** `authority_refusal` (rate limited)

This is intentional outer policy, not Cap law.

---

## 4. Interpretation vs human thresholds

| Human bar | Mechanism status |
|-----------|------------------|
| ≤ 100 ms “instant” feedback | Host+local Peer ≪ 1 ms; Peer IR coalesce/shadow for interim chrome |
| Authoritative morph p95 300–500 ms | Budget is almost entirely **network RTT × round-trips** |
| Multi-hop search | Continuation Cap removes a “what next?” policy hop; timer still costs its `ms` |

**Doctrine confirmed by measurement:**  
> Lag ≈ RTT × (Host decisions). Apply is free once Result is local.

---

## 5. How Caps should be used in production

`cek-host` is the **authority** package. PyPI/import name is `cek-host` / `cek_host` — not `cek-host-py`.

```python
from cek_host import Host, FileOnceBackend
import secrets

host = Host.production(secrets.token_bytes(32), FileOnceBackend("once.json"))
cap = host.mint("Cart.add", once=True, args={...}, seal_args=True)
result = host.submit(action="Cart.add", args={...}, cap=cap, project_ops=[...])
# refuse ⇒ result.ops == []
```

| Rule | Behavior |
|------|----------|
| Mint | Host only (Peer never) |
| once | `jti` burned after successful project (`OnceBackend`) |
| seal_args | args hash must match (oracle 32-hex) |
| refuse | always empty `ops` + `cek1:` digest |
| Continuations | pre-mint next Intent Cap; Peer fills slots only |
| subject / scopes | **enforced** (Phase 1) |

---

## 6. Known limits / next work

| Item | Notes |
|------|--------|
| Default rate limit 50/s | Breaks naive tight load loops; raise in benches, keep in prod |
| Cold subprocess Peer | First `boot` ~40 ms (Node spawn); steady-state ~0.3 ms |
| Phase 2 | BoundAsk · IdemBackend · LineageBackend · Ed25519 Host policy — **gated** on Phase 1 critic SHIP |
| Memory OnceBackend | Demo only. `production()` refuses it unless `allow_memory_stores=True` |

P0–P3 (vectors v3, WS demo, TestPyPI + pypi.org 0.1.0) **already shipped** 2026-08-15. This section no longer pretends they are future work.

---

## 7. Reproduce

```bash
git clone https://github.com/bitplorer/cek-python
cd cek-python
pip install -e ./cek-host -e ./cek-surface
sh scripts/verify.sh
PYTHONPATH=cek-host/src:cek-surface/src python3 cek-surface/demo/http_host.py
```

Machine JSON dump: `docs/performance-report.json`.

---

## 8. Verdict

CEK Python is **demo- and CI-ready** for Host Caps + Surface compose + closed Peer apply + live continuations. Mechanism latency is noise vs RTT. Security fail-closed paths (once, sealed-args, refuse → empty ops) hold under real shop, HTTP Host, and load series. Phase 1 adds one Host, subject/scope, digest, OnceBackend, doctor. Do not spend cycles on Host micro-optimization under the p95 budget above.
