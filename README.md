# cek-python

**Composition = Python + Caps.** Wire = `Result.ops`. Peer = closed drivers + perception IR.

| Package | Install | Role |
|---------|---------|------|
| **cek-host** | `pip install cek-host` | Authority — mint / verify / once / sealed-args. Refuse → `ops: []` |
| **cek-surface** | `pip install cek-surface` | Compose Ops, Peer IR, carriers. Depends on Host. |

**Law:** [cek-framework](https://github.com/bitplorer/cek-framework) · **Rust:** [cek-runtime](https://github.com/bitplorer/cek-runtime)

## First morph (≤ 5 minutes)

```bash
git clone https://github.com/bitplorer/cek-python && cd cek-python
pip install -e ./cek-host -e ./cek-surface
python -m cek_host create-app ./hello-cek && python ./hello-cek/app.py
```

**Start here:** [START.md](./START.md)

Tree **0.1.1** (Phase 1). Indexes still **0.1.0** until the next publish — do not `pip install cek-host==0.1.1` yet.

## Shop

```bash
python cek-surface/demo/http_host.py          # browser shop, real Host
python cek-surface/demo/shop_app.py           # importable shop surface
sh scripts/run_ws_demo.sh                     # WebSocket carrier
```

```bash
sh scripts/verify.sh
python -m cek_host doctor --fail
```

## Docs (pyramid)

| Layer | Doc |
|-------|-----|
| 0 | **This README** + **[START.md](./START.md)** |
| 1 | [docs/INVARIANTS.md](./docs/INVARIANTS.md) · [docs/S_TIER_SCORECARD.md](./docs/S_TIER_SCORECARD.md) |
| 2 | [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) · [docs/DECISIONS.md](./docs/DECISIONS.md) · [docs/PERFORMANCE.md](./docs/PERFORMANCE.md) — each says “read START first” |

Status: tree **0.1.1** Phase 1 (one Host, subject/scope, digest, OnceBackend, doctor). PyPI indexes still **0.1.0** until publish. Phase 2 (BoundAsk / lineage / Ed25519) is gated.
