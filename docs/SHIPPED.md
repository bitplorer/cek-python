# Shipped

What is in tree and verified (not aspirational).

## Packages

| Package | Role |
|---------|------|
| `cek-host` | Cap mint/verify, Result packaging |
| `cek-surface` | Compose, Peer IR, carriers, policy, continuations |

## Demos

| Demo | Path |
|------|------|
| Shop (subprocess Peer) | `cek-surface/demo/app.py` |
| HTTP Host (browser Peer) | `cek-surface/demo/http_host.py` + `browser_shop.html` |
| Load / chaos bench | `cek-surface/demo/bench_load_chaos.py` |
| WS peer server | `cek-surface/demo/ws_peer_server.mjs` |

## Tests (verify.sh)

- `test_core.py`
- `test_roadmap.py`
- `test_carrier_ir.py`
- `test_host_kernel.py`
- `test_continuation_live.py`
- `test_http_host.py`

## Invariants held

- refuse → `ops: []`
- Peer never mints Caps
- once / sealed-args fail closed
- wire shape = `Result.ops`
- Surface loads Host via `load_host_kernel()` → `CekHostPyKernel`

## Timeline notes

See [TIMELINE.md](./TIMELINE.md) and [ROADMAP.md](./ROADMAP.md).

### 2026-08-15 — Real-world performance report

- Full shop journey, Cap security matrix, live continuation, HTTP Host: **PASS**
- Numbers published: `docs/PERFORMANCE.md` + `docs/performance-report.json`
- Host-only p50 ~0.03 ms; Host→Peer p50 ~0.32 ms; lag RTT-bound
- Default policy rate-limit 50 intents/s documented as product guard
