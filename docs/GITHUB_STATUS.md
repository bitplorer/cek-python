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

## TestPyPI index

| Package | Version | Notes |
|---------|---------|-------|
| `cek-host` | 0.1.0 | publish-testpypi #1 |
| `cek-surface` | 0.1.0 | publish-testpypi #1 |

```bash
pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  cek-host==0.1.0 cek-surface==0.1.0
```

## 2026-08-15 notes

- P0–P3 complete on `main` + TestPyPI
- Env names: `testpypi-host` / `testpypi-surface`
