# Shipped

**Read [START.md](../START.md) first.** What is in tree and verified (not aspirational).

## Packages

| Package | Role | Indexes |
|---------|------|---------|
| `cek-host` | Cap mint/verify, Result packaging, OnceBackend, doctor | TestPyPI + **PyPI** 0.1.0; tree is **0.1.1** Phase 1 |
| `cek-surface` | Compose, Peer IR, carriers, policy, continuations | TestPyPI + **PyPI** 0.1.0; tree is **0.1.1** |

```bash
pip install cek-host cek-surface
python -m cek_host create-app ./hello && python ./hello/app.py
```

## Phase 1 (this tree)

- One published Host (`cek_host.Host`). `EmbeddedHostKernel` gone.
- subject + scopes **enforced**. Result `digest` is `cek1:` + SHA-256.
- `OnceBackend`: memory (demo) + file. `production()` refuses default secret + memory once-store.
- `doctor` / `explain` / `create-app` CLI (`python -m cek_host`).
- A ≡ B (`test_host_parity`). D3 + D4 (`test_layer_honesty`).
- Aligned contract family (`test_contract_vectors`) + surface pack v3 (20).

## Demos

| Demo | Path |
|------|------|
| HTTP Host (browser Peer) | `cek-surface/demo/http_host.py` + `browser_shop.html` |
| Shop surface | `cek-surface/demo/shop_app.py` |
| Load / chaos bench | `cek-surface/demo/bench_load_chaos.py` |
| WS one-command | `scripts/run_ws_demo.sh` |

## Invariants held (named tests exist)

- refuse → `ops: []` · Peer never mints · once/sealed fail closed · subject/scope deny → `ops: []` · HMAC tamper → `ops: []` · digest `cek1:` · store-down fail closed · attenuate cannot widen · wire = `Result.ops` · no ux-channel · no EmbeddedHostKernel

Not claimed: BoundAsk, lineage reverse, Ed25519, idempotency (Phase 2).
