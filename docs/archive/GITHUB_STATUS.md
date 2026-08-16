# GitHub status

Honest inventory of what is on **bitplorer/cek-python** `main`.

| Item | Status |
|------|--------|
| Repo | [bitplorer/cek-python](https://github.com/bitplorer/cek-python) |
| Packages | `cek-host/`, `cek-surface/` full trees |
| CI test | `.github/workflows/test.yml` |
| CI publish | `publish-testpypi.yml` + **`publish-pypi.yml`** |
| GH Environments | `testpypi-host`, `testpypi-surface`, `pypi-host`, `pypi-surface` |
| Install (dev) | `pip install -e ./cek-host -e ./cek-surface` |
| Install (release) | `pip install cek-host cek-surface` |

## Indexes

| Index | Packages | Version |
|-------|----------|---------|
| [TestPyPI](https://test.pypi.org) | cek-host, cek-surface | 0.1.0 |
| [PyPI](https://pypi.org) | cek-host, cek-surface | **0.1.0** |

```bash
pip install cek-host==0.1.0 cek-surface==0.1.0
```

## 2026-08-15 notes

- P0–P3 + **production PyPI** complete
- Env names: testpypi-* / pypi-*
