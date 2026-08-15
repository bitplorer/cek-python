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

- `test_core.py` … `test_vectors.py` (20 golden cases)

## Invariants held

- refuse → `ops: []` · Peer never mints · once/sealed fail closed · wire = `Result.ops` · no ux-channel

### 2026-08-15 — P3 TestPyPI live

- `cek-host==0.1.0`, `cek-surface==0.1.0` on test.pypi.org (publish-testpypi #1)

### 2026-08-15 — A/B/C follow-on

- Production PyPI workflow: `.github/workflows/publish-pypi.yml` + [PYPI_SETUP.md](./PYPI_SETUP.md)
- Vectors **v3**: 20 cases (expired Cap, action mismatch, dispatch_error, more Op shapes)
- Consumer smoke: `sh scripts/consumer_smoke_testpypi.sh`
