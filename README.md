# cek-python

Python workspace for **CEK** (Cap-Effect Kernel).

| Package | Install | Role |
|---------|---------|------|
| **[cek-host](./cek-host)** | `pip install cek-host` | Host kernel — Caps, refuse → empty ops |
| **[cek-surface](./cek-surface)** | `pip install cek-surface` | Compose Ops, Peer IR, carriers (depends on cek-host) |

**Law:** [cek-framework](https://github.com/bitplorer/cek-framework) · **Rust:** [cek-runtime](https://github.com/bitplorer/cek-runtime)

## Knowledge base (start here)

Everything that was shipped, why, architecture, decisions, invariants, and roadmap:

**→ [docs/KNOWLEDGE.md](./docs/KNOWLEDGE.md)**

| Doc | Purpose |
|-----|---------|
| [SHIPPED.md](./docs/SHIPPED.md) | What exists and why |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Layers, wire, Peer IR |
| [DECISIONS.md](./docs/DECISIONS.md) | Non-obvious choices |
| [INVARIANTS.md](./docs/INVARIANTS.md) | Never-regress rules |
| [ROADMAP.md](./docs/ROADMAP.md) | Past / present / next / later |
| [LATENCY.md](./docs/LATENCY.md) | RTT model and Peer IR |
| [GITHUB_STATUS.md](./docs/GITHUB_STATUS.md) | Remote vs local honesty |
| [ORGANIZATION.md](./docs/ORGANIZATION.md) | Repos and install |
| [TIMELINE.md](./docs/TIMELINE.md) | Narrative history |

## Quick start (local monorepo)

```bash
git clone https://github.com/bitplorer/cek-python
cd cek-python
pip install -e ./cek-host
pip install -e "./cek-surface[ws]"
python -c "from cek_host import Host; from cek_surface import Surface, Op; print('ok')"
```

Without install, set `PYTHONPATH`:

```bash
export PYTHONPATH=cek-host/src:cek-surface/src
python -c "from cek_host import Host; from cek_surface import Surface, Op; print('ok')"
```

## Verify (clone path)

Requires Python 3.10+ and Node (subprocess Peer).

```bash
sh scripts/verify.sh
```

That runs the import smoke plus:

- `cek-surface/tests/test_core.py`
- `cek-surface/tests/test_roadmap.py`
- `cek-surface/tests/test_carrier_ir.py`
- `cek-surface/tests/test_host_kernel.py`

Never-regress gates: Cap refuse → `ops: []`; Peer no mint; once / sealed-args fail closed; wire = `Result.ops`.

## Demos

```bash
# Shop via default subprocess Peer
python cek-surface/demo/app.py

# Browser shop + Host HTTP (real Surface.submit, not ?mock=1)
python cek-surface/demo/http_host.py
# then open the printed URL
```

## Doctrine

> Composition = Python + Caps; wire = Result.ops; Peer = closed drivers + perception IR; carriers are transport only.
