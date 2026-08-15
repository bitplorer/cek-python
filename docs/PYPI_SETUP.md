# Production PyPI setup

**TestPyPI is done** (0.1.0 live). This doc is for **pypi.org** when you promote.

Related: [TESTPYPI_SETUP.md](./TESTPYPI_SETUP.md) · `.github/workflows/publish-pypi.yml`

---

## One-time

### 1. GitHub Environments

https://github.com/bitplorer/cek-python/settings/environments/new

| Environment | Package |
|-------------|---------| 
| `pypi-host` | `cek-host` |
| `pypi-surface` | `cek-surface` |

No secrets needed (OIDC). Optional: require reviewers for production.

### 2. Trusted publishers on pypi.org

For each project on [pypi.org](https://pypi.org):

| Project | Owner | Repo | Workflow | Environment |
|---------|-------|------|----------|-------------|
| `cek-host` | `bitplorer` | `cek-python` | `publish-pypi.yml` | `pypi-host` |
| `cek-surface` | `bitplorer` | `cek-python` | `publish-pypi.yml` | `pypi-surface` |

### 3. Version

TestPyPI and PyPI are **separate**. You can publish `0.1.0` to production once.

If a version is already on PyPI, bump both `pyproject.toml` files first.

### 4. Publish

https://github.com/bitplorer/cek-python/actions/workflows/publish-pypi.yml → **Run workflow**

Or: `git tag v0.1.0 && git push origin v0.1.0`

### 5. Install (production)

```bash
pip install cek-host==0.1.0 cek-surface==0.1.0
```

---

## Checklist

- [ ] GitHub Environments `pypi-host` + `pypi-surface`
- [ ] Trusted publishers on pypi.org (matching env names)
- [ ] Version in both `pyproject.toml` files
- [ ] `workflow_dispatch` or tag green
- [ ] `pip install cek-host cek-surface` smoke (refuse → `ops: []`)
