# CEK organization on GitHub & install

## Repos (bitplorer)

| Repo | Role | Install |
|------|------|---------|
| **[cek-framework](https://github.com/bitplorer/cek-framework)** | **Law** only — Caps, Intent, Ops, lineage, reverse | docs / charter (not a runtime pip package) |
| **[cek-runtime](https://github.com/bitplorer/cek-runtime)** | **Rust** reference Host/Peer + contract vectors | `cargo` workspace |
| **[cek-python](https://github.com/bitplorer/cek-python)** | **Python** Host kernel + surface + JS Peer assets | `pip install cek-host` / `cek-surface` |

Do **not** put law into runtime repos. Do **not** put Cap mint into Peer packages.

```text
                    cek-framework (law)
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
     cek-runtime      cek-python      (future: cek-js npm
     (Rust kernels)   (this monorepo)   if Peer grows large)
           │               │
           │         ┌─────┴─────┐
           │         ▼           ▼
           │     cek-host    cek-surface
           │    (authority)  (compose + Peer IR + carriers)
           └─────────┬───────────┘
                     ▼
              contract / vectors (align over time)
```

## Why one Python monorepo (not N repos)

- One CI, one version story for Host ↔ Surface API  
- `cek-host` stays installable alone (servers, workers)  
- `cek-surface` depends on `cek-host` — apps don’t invent Caps  
- JS Peer files live under `cek-surface/js` until an npm package is justified  

Separate repos later only if package teams diverge.

## How someone installs

```bash
# Application / full stack
pip install cek-surface          # pulls cek-host

# Authority only (API worker, no Peer)
pip install cek-host

# From monorepo (dev)
git clone https://github.com/bitplorer/cek-python
cd cek-python
pip install -e ./cek-host
pip install -e "./cek-surface[ws]"
```

```python
from cek_host import Host
from cek_surface import Surface, Op, open_carrier

host = Host(secret=b"...")
surface = Surface()  # uses load_host_kernel() → cek_host.Host
```

Optional carriers:

```python
Surface()  # default subprocess NDJSON peer
Surface(carrier_kind="memory")
Surface(carrier_kind="websocket", carrier_opts={"url": "ws://..."})  # pip install cek-surface[ws]
```

## What goes where

| Concern | Package |
|---------|---------|
| Cap mint / verify / once | **cek-host** |
| Action handlers, Op catalog | **cek-surface** |
| Peer apply drivers, Peer IR | **cek-surface/js** |
| Carrier transport | **cek-surface** (`open_carrier`) |
| Durable lineage stores (full) | cek-runtime Rust / future cek-host backends |
| Law text | **cek-framework** |

## Naming

| Name | Meaning |
|------|---------|
| `cek-host` | PyPI + import `cek_host` |
| `cek-surface` | PyPI + import `cek_surface` |
| Not `cek-host-py` on PyPI | Prefer short `cek-host`; “py” is implied by the ecosystem repo |

## Peer languages

| Peer | Location |
|------|----------|
| Node NDJSON / WS | `cek-surface/js/` |
| Browser | `cek-surface/js/browser_peer.mjs` |
| Rust Peer | `cek-runtime` crates |

New language Peers: same **contract messages** (`apply` / `chrome` / `events`), not a new Cap authority.

## Publish (TestPyPI)

**One-time Trusted Publisher + checklist:** [TESTPYPI_SETUP.md](./TESTPYPI_SETUP.md)

```bash
sh scripts/build_release.sh
# Trusted Publishing: Actions → publish-testpypi → Run workflow
# or token: TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-... sh scripts/publish_testpypi.sh
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ cek-host==0.1.0 cek-surface==0.1.0
```

## Packaging backends (current + future)

**Current:** setuptools (`python -m build`, `scripts/build_release.sh`).

**Later migrations (uv without backend change, hatchling, Poetry):** see **[PACKAGING.md](./PACKAGING.md)** — complete step-by-step, verify matrix, TestPyPI rules, rollback.
