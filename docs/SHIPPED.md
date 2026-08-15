# What was shipped (and why)

Status as of **2026-08-15**. Source of truth for “is this real?”.

---

## 1. Ecosystem context (pre-surface)

| Item | Why it exists |
|------|----------------|
| **cek-framework** | Locked conceptual law so runtimes don’t invent authority semantics |
| **cek-runtime (Rust)** | Reference Host/Peer, contract vectors, never-regress tests |

Python work began because apps (uidom / ux-channel class problems) needed **Host composition in Python** and **JS Peer apply**, without sending arbitrary JS on the wire.

---

## 2. Packages in this monorepo

### 2.1 `cek-host` (PyPI name: `cek-host`)

| Shipped | Why |
|---------|-----|
| `CapService` — HMAC mint/verify, once-jti, sealed-args, expiry | Authority must be a single place; Peer must never mint |
| `Host.submit` → `KernelResult(kind, ops, error)` | Refuse path packages **zero ops** |
| Standalone install | API workers can use Caps without UI surface |

**Not shipped in host:** durable lineage stores, Ed25519 product keys, multi-tenant policy (those are “next” or Rust parity).

### 2.2 `cek-surface` (PyPI name: `cek-surface`)

| Shipped | Why |
|---------|-----|
| `Surface` + `@action` / `@on` | App authors compose Ops in Python under Caps |
| `Op` catalog (kv, ui.dom, ui, nav, http, timer, signal, log, sys) | Closed effect algebra ↔ Peer drivers |
| `kernel.load_host_kernel()` → prefers `cek_host.Host` | Surface does not own Cap policy long-term |
| Portable **carriers** (`subprocess` default, `memory`, `websocket` opt-in) | Transport is not a kernel; demos zero-config |
| **Peer IR** (`js/peer_ir.mjs`) — coalesce, flush, shadow, pending, filter_cached, toast_fade | Human lag is RTT; perception must be local |
| Continuations (`continuation.py`) | Pre-minted next Intent templates; Host still verifies |
| Policy hooks (rate limit, action allow-list, nav prefixes) | Outer runtime guards, not Cap law |
| Node `peer.mjs`, browser `browser_peer.mjs`, shop demos, load/chaos/net benches | Prove path end-to-end |
| Tests: core, roadmap, carrier+IR, host kernel | Refuse/once/sealed/shadow/coalesce |

**Explicit non-ship:** ux-channel dependency, Peer recipes/eval, plan IR on the wire, Peer Cap mint.

---

## 3. Demos and benches (why they matter)

| Artifact | Proves |
|----------|--------|
| `demo/shop_app.py` + `demo/app.py` | Real flows: search debounce, cart, checkout, once-refuse |
| `demo/bench_load_chaos.py` | Host-only ~0.03 ms; full Peer ~0.5 ms; net sim RTT-bound |
| `demo/browser_shop.html` + `http_host.py` | Browser Peer IR + optional Host submit |
| `demo/ws_peer_server.mjs` | Opt-in WebSocket Peer (same JSON shapes) |

**Measured (order of magnitude, this machine):**

| Path | p50 |
|------|-----|
| Host compose + Cap | ~0.03 ms |
| Host → local Node Peer | ~0.4–0.6 ms |
| + simulated ~20 ms RTT | ~20 ms |
| + ~80 ms RTT | ~80 ms |
| Search + async @ ~20 ms RTT | ~120 ms (multi-round) |

Conclusion shipped with the benches: **mechanism is not the lag; RTT and round-trips are.**

---

## 4. GitHub publish status

| Component | On GitHub `bitplorer/cek-python` |
|-----------|----------------------------------|
| Docs ORGANIZATION + knowledge spine | **Yes** |
| cek-host package sources | **Yes** |
| cek-surface README / pyproject / ARCHITECTURE | **Yes** |
| cek-surface `src/`, `js/`, `demo/`, `tests/`, `vectors/` | **Yes (P0)** |
| `scripts/verify.sh` + GitHub Actions `test` | **Yes (P0)** |
| PyPI 0.1.0 | **No** (P3) |

---

## 5. What “done” means for this phase

- [x] Law/runtime split respected
- [x] Host authority separate package
- [x] Surface compose + closed Peer + perception IR
- [x] Carrier plug-and-play, default subprocess
- [x] Chaos: once, sealed-args, refuse
- [x] Org docs for install
- [x] Full surface tree on GitHub remote
- [x] Editable install smoke (`pip install -e ./cek-host -e ./cek-surface`)
- [ ] Browser E2E without `?mock=1` (P1)
- [ ] Continuation live path `timer.fired` → pre-minted Cap (P1)
- [ ] Production durable stores / Ed25519 parity with Rust
- [ ] PyPI publish of `cek-host` / `cek-surface`
