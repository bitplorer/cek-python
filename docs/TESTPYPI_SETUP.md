# TestPyPI setup (one-time + publish)

**Purpose:** future reference for publishing `cek-host` / `cek-surface` to [TestPyPI](https://test.pypi.org).  
**Repo wiring is done.** Live upload still needs Trusted Publishers on TestPyPI (OIDC) or a token.

Related: [ORGANIZATION.md](./ORGANIZATION.md) · [PACKAGING.md](./PACKAGING.md) · `.github/workflows/publish-testpypi.yml`

---

## What is already in the repo

| Piece | Location |
|-------|----------|
| Build both packages | `scripts/build_release.sh` |
| Token upload helper | `scripts/publish_testpypi.sh` |
| Trusted Publishing CI | `.github/workflows/publish-testpypi.yml` |
| Versions | `cek-host` / `cek-surface` **0.1.0** |

Workflow:

1. Builds both wheels + `twine check`
2. **`publish-host`** → GitHub Environment **`testpypi-host`** → uploads only `cek_host-*`
3. **`publish-surface`** → GitHub Environment **`testpypi-surface`** → uploads only `cek_surface-*`

---

## GitHub Environments (done)

| Environment | Package |
|-------------|---------| 
| `testpypi-host` | `cek-host` |
| `testpypi-surface` | `cek-surface` |

https://github.com/bitplorer/cek-python/settings/environments

No secrets required on these envs (OIDC). Protection rules optional.

---

## TestPyPI pending / trusted publishers

On [test.pypi.org](https://test.pypi.org) → **Publishing** → pending publisher (or project Trusted Publisher after first upload).

### `cek-host`

| Field | Value |
|-------|--------|
| Project name | `cek-host` |
| Owner | `bitplorer` |
| Repository | `cek-python` |
| Workflow name | `publish-testpypi.yml` |
| Environment | **`testpypi-host`** |

### `cek-surface`

| Field | Value |
|-------|--------|
| Project name | `cek-surface` |
| Owner | `bitplorer` |
| Repository | `cek-python` |
| Workflow name | `publish-testpypi.yml` |
| Environment | **`testpypi-surface`** |

Different environment names avoid the pending-publisher clash.

If you previously registered env `testpypi` for host, **edit or remove** it and re-register with **`testpypi-host`** so it matches the workflow.

---

## First publish

https://github.com/bitplorer/cek-python/actions/workflows/publish-testpypi.yml  
→ **Run workflow**

After success:

```bash
pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  cek-host==0.1.0 cek-surface==0.1.0
```

---

## Token path (fallback)

```bash
sh scripts/build_release.sh
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-...   # TestPyPI API token
sh scripts/publish_testpypi.sh
```

---

## Rules

1. **Version unique per index** — `0.1.0` once on TestPyPI; bump for retries.  
2. **TestPyPI ≠ PyPI** — production is a separate publish.  
3. **Env names in workflow must match** pending publisher Environment fields exactly.

---

## Status checklist

- [x] Build scripts + split workflow on `main`  
- [x] GitHub Environments `testpypi-host` + `testpypi-surface`  
- [ ] Pending publisher `cek-host` → env `testpypi-host`  
- [ ] Pending publisher `cek-surface` → env `testpypi-surface`  
- [ ] First successful `workflow_dispatch`  
- [ ] Install smoke from TestPyPI confirmed  
