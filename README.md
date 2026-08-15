# cek-python

Python workspace for **CEK** (Cap-Effect Kernel).

| Package | Install | Role |
|---------|---------|------|
| **[cek-host](./cek-host)** | `pip install cek-host` | Host kernel — Caps, refuse → empty ops |
| **[cek-surface](./cek-surface)** | `pip install cek-surface` | Compose Ops, Peer IR, carriers (depends on cek-host) |

**Law:** [cek-framework](https://github.com/bitplorer/cek-framework) · **Rust:** [cek-runtime](https://github.com/bitplorer/cek-runtime)

## Knowledge base (start here)

**→ [docs/KNOWLEDGE.md](./docs/KNOWLEDGE.md)**

| Doc | Purpose |
|-----|---------|
| [SHIPPED.md](./docs/SHIPPED.md) | What exists and why |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Layers, wire, Peer IR |
| [DECISIONS.md](./docs/DECISIONS.md) | Non-obvious choices |
| [INVARIANTS.md](./docs/INVARIANTS.md) | Never-regress rules |
| [ROADMAP.md](./docs/ROADMAP.md) | Past / present / next / later |
| [LATENCY.md](./docs/LATENCY.md) | RTT model and Peer IR |
| [PERFORMANCE.md](./docs/PERFORMANCE.md) | Measured real-world + load |
| [GITHUB_STATUS.md](./docs/GITHUB_STATUS.md) | Remote vs local honesty |
| [ORGANIZATION.md](./docs/ORGANIZATION.md) | Repos and install |
| [TIMELINE.md](./docs/TIMELINE.md) | Narrative history |

## Quick start

```bash
git clone https://github.com/bitplorer/cek-python
cd cek-python
pip install -e ./cek-host -e ./cek-surface
python -c "from cek_host import Host; from cek_surface import Surface, Op; print('ok')"
```

Without install:

```bash
export PYTHONPATH=cek-host/src:cek-surface/src
```

## Verify

```bash
sh scripts/verify.sh
```

Includes golden vectors (`test_vectors.py`) aligned with cek-runtime hot Op `ns.name`.

Never-regress: Cap refuse → `ops: []`; Peer no mint; once / sealed-args fail closed; wire = `Result.ops`.

## Demos

```bash
python cek-surface/demo/app.py
python cek-surface/demo/http_host.py
sh scripts/run_ws_demo.sh   # WebSocket Peer (needs node ws + pip websockets)
```

## Doctrine

> Composition = Python + Caps; wire = Result.ops; Peer = closed drivers + perception IR; carriers are transport only.
