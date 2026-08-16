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

Tree **0.1.2** (Phase 2). Indexes still **0.1.0** until the next publish — do not `pip install cek-host==0.1.2` yet.

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

## Docs

| Doc | Role |
|-----|------|
| **[START.md](./START.md)** | First morph |
| [docs/CATALOG_AUTHORITY_TARGET.md](./docs/CATALOG_AUTHORITY_TARGET.md) | Glossary (pair / S / stamp) |
| [docs/COMPOSITION.md](./docs/COMPOSITION.md) | Host compose + Peer IR |
| [docs/INVARIANTS.md](./docs/INVARIANTS.md) | NEVER REGRESS |
| [docs/ORGANIZATION.md](./docs/ORGANIZATION.md) | Repos and packages |

History and publish runbooks: `docs/archive/`.
