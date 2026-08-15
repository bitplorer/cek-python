# Shipped

What is in tree and verified (not aspirational).

## Packages

| Package | Role | Indexes |
|---------|------|---------|
| `cek-host` | Cap mint/verify, Result packaging | TestPyPI + **PyPI** 0.1.0 |
| `cek-surface` | Compose, Peer IR, carriers, policy, continuations | TestPyPI + **PyPI** 0.1.0 |

```bash
pip install cek-host==0.1.0 cek-surface==0.1.0
```

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

### 2026-08-15 — Production PyPI live

- `cek-host==0.1.0`, `cek-surface==0.1.0` on **pypi.org** (publish-pypi #1)
- Install smoke: refuse → `ops: []` **PASS**
- https://pypi.org/project/cek-host/ · https://pypi.org/project/cek-surface/

### 2026-08-15 — A/B/C follow-on

- Production workflow: `.github/workflows/publish-pypi.yml` + [PYPI_SETUP.md](./PYPI_SETUP.md)
- Vectors **v3**: 20 cases
- Consumer smoke: `sh scripts/consumer_smoke_testpypi.sh`
