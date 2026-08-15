# cek-python

Python workspace for **CEK** (Cap-Effect Kernel).

| Package | Install | Role |
|---------|---------|------|
| **[cek-host](./cek-host)** | `pip install cek-host` | Host kernel — Cap mint/verify, refuse → `ops: []` |
| **[cek-surface](./cek-surface)** | `pip install cek-surface` | Compose Ops, Peer IR, carriers (depends on `cek-host`) |

**Law:** [cek-framework](https://github.com/bitplorer/cek-framework) · **Rust:** [cek-runtime](https://github.com/bitplorer/cek-runtime)

> Composition = Python + Caps · wire = `Result.ops` · Peer = closed drivers + perception IR

## Quick start

```bash
git clone https://github.com/bitplorer/cek-python
cd cek-python
pip install -e ./cek-host -e ./cek-surface
python -c "from cek_host import Host; from cek_surface import Surface, Op; print('ok')"
sh scripts/verify.sh
```

## Demos

```bash
python cek-surface/demo/app.py              # shop, subprocess Peer
python cek-surface/demo/http_host.py        # browser shop (real Host)
sh scripts/run_ws_demo.sh                   # WebSocket carrier one-command
```

## Build / publish

```bash
sh scripts/build_release.sh
# TestPyPI: docs/TESTPYPI_SETUP.md · Production: docs/PYPI_SETUP.md
```

`pip install cek-host==0.1.0 cek-surface==0.1.0`

## Docs (start here)

| Doc | Purpose |
|-----|---------|
| **[docs/KNOWLEDGE.md](./docs/KNOWLEDGE.md)** | Index of all knowledge |
| [docs/SHIPPED.md](./docs/SHIPPED.md) | What exists and is verified |
| [docs/ROADMAP.md](./docs/ROADMAP.md) | Past / present / next / later |
| [docs/INVARIANTS.md](./docs/INVARIANTS.md) | Never-regress rules |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Layers, wire, Peer IR |
| [docs/ORGANIZATION.md](./docs/ORGANIZATION.md) | Repos and install story |
| [docs/TESTPYPI_SETUP.md](./docs/TESTPYPI_SETUP.md) | TestPyPI Trusted Publisher checklist |
| [docs/PACKAGING.md](./docs/PACKAGING.md) | setuptools today; uv/Poetry migration |
| [docs/PERFORMANCE.md](./docs/PERFORMANCE.md) | Measured real-world latency |

## Status (2026-08-15)

- **P0–P3 + production PyPI shipped** — TestPyPI and **pypi.org** `0.1.0`
- Install: `pip install cek-host==0.1.0 cek-surface==0.1.0`
- CI: [test.yml](./.github/workflows/test.yml) · [publish-testpypi.yml](./.github/workflows/publish-testpypi.yml) · [publish-pypi.yml](./.github/workflows/publish-pypi.yml)
