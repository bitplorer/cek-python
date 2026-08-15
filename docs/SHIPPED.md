# Shipped

**Read [START.md](../START.md) first.** What is in tree and verified (not aspirational).

## Packages

| Package | Role | Indexes |
|---------|------|---------|
| `cek-host` | Cap mint/verify, BoundAsk, Once/Idem/Lineage, doctor | TestPyPI + **PyPI** 0.1.0; tree is **0.1.2** Phase 2 |
| `cek-surface` | Compose, Peer IR, carriers, policy, continuations | TestPyPI + **PyPI** 0.1.0; tree is **0.1.2** |

PyPI **0.1.0** has no `create-app`. Use the tree:

```bash
git clone https://github.com/bitplorer/cek-python && cd cek-python
pip install -e ./cek-host -e ./cek-surface
python -m cek_host create-app ./hello && python ./hello/app.py
```

## Phase 1 (held)

- One published Host (`cek_host.Host`). `EmbeddedHostKernel` gone. `cek_surface.host.Host` gone.
- subject + scopes **enforced**. Result `digest` is `cek1:` + SHA-256.
- `OnceBackend`: memory (demo) + file. `production()` refuses default secret + memory once-store.
- `doctor` / `explain` / `create-app` CLI (`python -m cek_host`).
- A ≡ B (`test_host_parity`). D3 + D4 (`test_layer_honesty`).

## Phase 2 (this tree)

- `BoundAsk` — no public constructor. Host binds only after verify + idem + once-ensure.
- `IdemBackend` (memory + file/flock). Empty key refuse. Same digest replay. Different body refuse. Lookup **before** once-ensure.
- `LineageBackend` (memory + file/flock). `end_activity` reverse, receipts landed-first.
- Inverse: `kv.set`→`kv.delete`; `kv.delete`+prior→`kv.set`; `ui.dom.morph`+snapshot→`ui.dom.restore`. No-prior delete is NonReversible.
- Ed25519 Host policy (opt-in seed/trust). Unsigned or tampered refuse, zero Ops.
- Law-generation window: blank/unknown refuse; unset = legacy accept; `accepted_generations` dual-speak.
- `production()` refuses memory idem/lineage unless `allow_memory_stores`. FileOnce auto-creates FileIdem + FileLineage beside it.
- Aligned contract family: 28 Rust JSON fixtures (`test_contract_vectors`) + `test_phase2`.

## Demos

| Demo | Path |
|------|------|
| HTTP Host (browser Peer) | `cek-surface/demo/http_host.py` + `browser_shop.html` |
| Shop surface | `cek-surface/demo/shop_app.py` |
| Load / chaos bench | `cek-surface/demo/bench_load_chaos.py` |
| WS one-command | `scripts/run_ws_demo.sh` |

## Invariants held (named tests exist)

- refuse → `ops: []` · Peer never mints · once/sealed fail closed · subject/scope deny → `ops: []` · HMAC tamper → `ops: []` · digest `cek1:` · store-down fail closed · attenuate cannot widen · wire = `Result.ops` · no ux-channel · no EmbeddedHostKernel · no sketch Host
- BoundAsk no public ctor · empty idem key refuse · idem replay / conflict · idem before once · lineage reverse · landed-first · kv/ui reverse · Ed25519 missing/tamper/ok · blank/unknown law-gen refuse

Not claimed: Redis / crates.io (Phase 3).
