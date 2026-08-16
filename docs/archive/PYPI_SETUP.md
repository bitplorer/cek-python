# Production PyPI setup

**Status (2026-08-15):** `cek-host` and `cek-surface` **0.1.0** are on [pypi.org](https://pypi.org) (publish-pypi #1 green).

Related: [TESTPYPI_SETUP.md](./TESTPYPI_SETUP.md) · `.github/workflows/publish-pypi.yml`

```bash
pip install cek-host==0.1.0 cek-surface==0.1.0
```

---

## What was done

| Piece | Detail |
|-------|--------|
| GitHub Environments | `pypi-host`, `pypi-surface` |
| Trusted publishers | pypi.org → matching env names |
| Workflow | `publish-pypi.yml` (split host/surface jobs) |
| First upload | publish-pypi #1 — build + both publish jobs green |

## Re-publish (later versions only)

1. Bump `version` in both `cek-host/pyproject.toml` and `cek-surface/pyproject.toml`
2. Actions → **publish-pypi** → Run workflow  
   (or `git tag v0.1.1 && git push origin v0.1.1`)
3. Confirm: `pip index versions cek-host` / `cek-surface`

**Do not** re-upload `0.1.0` — version is unique per index.

## Checklist (historical)

- [x] GitHub Environments `pypi-host` + `pypi-surface`
- [x] Trusted publishers on pypi.org
- [x] First successful `workflow_dispatch`
- [x] `pip install cek-host cek-surface` smoke (refuse → `ops: []`)
