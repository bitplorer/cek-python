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
| WS one-command | `scripts/run_ws_demo.sh` |

## Tests (`scripts/verify.sh`)

- `test_core.py`
- `test_roadmap.py`
- `test_carrier_ir.py`
- `test_host_kernel.py`
- `test_continuation_live.py`
- `test_http_host.py`
- `test_vectors.py`

## Invariants held

- refuse → `ops: []`
- Peer never mints Caps
- once / sealed-args fail closed
- wire shape = `Result.ops`
- Surface loads Host via `load_host_kernel()` → `CekHostPyKernel`
- no ux-channel dependency

## Timeline notes

See [TIMELINE.md](./TIMELINE.md) and [ROADMAP.md](./ROADMAP.md).

### 2026-08-15 — Real-world performance report

- Full shop journey, Cap security matrix, live continuation, HTTP Host: **PASS**
- Numbers: [PERFORMANCE.md](./PERFORMANCE.md) + `performance-report.json`
- Host-only p50 ~0.03 ms; Host→Peer p50 ~0.32 ms; lag RTT-bound
- Default policy rate-limit 50 intents/s documented as product guard

### 2026-08-15 — P2 vectors + WS demo

- `cek-surface/vectors/surface_core.json` v2 (14 cases, hot Op names aligned with cek-runtime)
- `tests/test_vectors.py` in `scripts/verify.sh`
- One-command WS: `sh scripts/run_ws_demo.sh`

### 2026-08-15 — P3 packaging / TestPyPI path

- `python -m build` sdist+wheel for both packages 0.1.0 — `twine check` PASS
- Wheel install smoke: Host refuse → `ops: []`
- Scripts: `build_release.sh`, `publish_testpypi.sh`
- CI: `publish-testpypi.yml` — split jobs:
  - `publish-host` → environment **`testpypi-host`**
  - `publish-surface` → environment **`testpypi-surface`**
- Setup guide: [TESTPYPI_SETUP.md](./TESTPYPI_SETUP.md)
- **Live on TestPyPI:** `cek-host==0.1.0`, `cek-surface==0.1.0` (publish-testpypi #1, all jobs green)
- Install smoke from test.pypi.org: Host refuse → `ops: []` **PASS**
