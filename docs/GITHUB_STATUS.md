# GitHub status

Honest inventory of what is on **bitplorer/cek-python** `main`.

| Item | Status |
|------|--------|
| Repo | [bitplorer/cek-python](https://github.com/bitplorer/cek-python) |
| Packages | `cek-host/`, `cek-surface/` full trees (not stubs) |
| CI test | `.github/workflows/test.yml` — editable install + `verify.sh` |
| CI publish | `.github/workflows/publish-testpypi.yml` — split host/surface |
| GH Environments | `testpypi-host`, `testpypi-surface` (created by maintainer) |
| Install | `pip install -e ./cek-host -e ./cek-surface` |
| Kernel | `CekHostPyKernel` when `cek_host` on path |
| Docs | Full knowledge set under `docs/` (see [KNOWLEDGE.md](./KNOWLEDGE.md)) |

## On tree

- Host + Surface source, JS Peer, demos, tests, vectors
- Scripts: `verify.sh`, `build_release.sh`, `publish_testpypi.sh`, `run_ws_demo.sh`
- Performance report + packaging + TestPyPI setup docs

## Not yet on TestPyPI index

Live `pip install` from test.pypi.org waits on:

1. Pending Trusted Publishers (`cek-host` → `testpypi-host`, `cek-surface` → `testpypi-surface`)
2. First successful Actions run

See [TESTPYPI_SETUP.md](./TESTPYPI_SETUP.md).

## 2026-08-15 notes

- P0–P2 content synced; P3 path (build + split workflow) on `main`
- Env names standardized to `testpypi-host` / `testpypi-surface` (not bare `testpypi`)
