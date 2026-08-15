# cek-python

Python workspace for **CEK** (Cap-Effect Kernel).

| Package | Install | Role |
|---------|---------|------|
| **[cek-host](./cek-host)** | `pip install cek-host` | Host kernel — Caps, refuse → empty ops |
| **[cek-surface](./cek-surface)** | `pip install cek-surface` | Compose Ops, Peer IR, carriers (depends on cek-host) |

**Law:** [cek-framework](https://github.com/bitplorer/cek-framework) · **Rust:** [cek-runtime](https://github.com/bitplorer/cek-runtime)

## Knowledge base

**→ [docs/KNOWLEDGE.md](./docs/KNOWLEDGE.md)** · Packaging: [docs/PACKAGING.md](./docs/PACKAGING.md)

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
python cek-surface/demo/app.py
python cek-surface/demo/http_host.py
sh scripts/run_ws_demo.sh
```

## Build / TestPyPI

Packaging backends and **uv / Poetry migration guide:** [docs/PACKAGING.md](./docs/PACKAGING.md).

```bash
sh scripts/build_release.sh
# Actions → publish-testpypi (Trusted Publishing) after TestPyPI setup
```

## Doctrine

> Composition = Python + Caps; wire = Result.ops; Peer = closed drivers + perception IR; carriers are transport only.
