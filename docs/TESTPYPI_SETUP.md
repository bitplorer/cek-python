# TestPyPI setup (one-time + publish)

**Purpose:** future reference for publishing `cek-host` / `cek-surface` to [TestPyPI](https://test.pypi.org).  
**Repo wiring is done.** Live upload still needs the one-time account steps below (OIDC or token).

Related: [ORGANIZATION.md](./ORGANIZATION.md) · [PACKAGING.md](./PACKAGING.md) · `.github/workflows/publish-testpypi.yml`

---

## What is already in the repo

| Piece | Location |
|-------|----------|
| Build both packages | `scripts/build_release.sh` |
| Token upload helper | `scripts/publish_testpypi.sh` |
| Trusted Publishing CI | `.github/workflows/publish-testpypi.yml` |
| Versions | `cek-host` / `cek-surface` **0.1.0** in each `pyproject.toml` |

Workflow builds both wheels, runs `twine check`, then publishes to `https://test.pypi.org/legacy/` via OIDC (`id-token: write`) under GitHub Environment **`testpypi`**.

---

## One-time: Trusted Publishing (preferred)

### 1. GitHub Environment

Repo **Settings → Environments → New environment**

- Name: `testpypi`  
- (Optional later) second env `testpypi-surface` if you split publishers — see § Two packages below.

### 2. Pending publisher for `cek-host`

On [test.pypi.org](https://test.pypi.org) → account **Publishing** → **Add a new pending publisher**:

| Field | Value |
|-------|--------|
| Project name | `cek-host` |
| Owner | `bitplorer` |
| Repository | `cek-python` |
| Workflow name | `publish-testpypi.yml` |
| Environment | `testpypi` |

### 3. Pending publisher for `cek-surface` (important)

**Do not** re-use the exact same `(owner, repo, workflow, environment)` tuple as a second *pending* publisher. TestPyPI rejects it:

> A pending trusted publisher matching this configuration has already been registered for a different project name.

**Options (pick one):**

| Option | What to do |
|--------|------------|
| **A — second environment (recommended)** | Pending publisher for `cek-surface` with Environment = `testpypi-surface`. Create matching GitHub Environment. Split workflow `publish` job (or add a second job) so surface uses `environment: testpypi-surface`. |
| **B — publish host first** | Run workflow once for `cek-host` (pending becomes normal). Create `cek-surface` project via token upload, then add a **project-scoped** trusted publisher on the existing project page. |
| **C — token only** | Skip pending publishers for the second package; use API token (§ Token path). |

### 4. First publish

GitHub → **Actions → publish-testpypi → Run workflow**  
(or push tag matching `v0.1.0*`)

After success:

```bash
pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  cek-host==0.1.0 cek-surface==0.1.0
```

`--extra-index-url` is required so dependencies (and any missing index entries) still resolve from real PyPI.

---

## Token path (no OIDC)

```bash
sh scripts/build_release.sh
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-...   # TestPyPI API token
sh scripts/publish_testpypi.sh
```

Create token: TestPyPI → Account settings → API tokens (scope to project once projects exist).

---

## Rules that bite later

1. **Version is unique per index** — `0.1.0` can only be uploaded once to TestPyPI; bump for retries.  
2. **TestPyPI ≠ PyPI** — production needs a separate publish + separate trusted publisher on pypi.org.  
3. **Pending publisher uniqueness** — one pending config tuple → one project name (§3 above).  
4. **Both packages in one workflow artifact** — current workflow uploads everything in `dist/`; if only one pending publisher is registered, the other package name may fail until option A/B/C is done.

---

## Status checklist

- [x] `pyproject.toml` + build scripts + workflow on `main`  
- [ ] GitHub Environment `testpypi` (and optional `testpypi-surface`)  
- [ ] Pending / trusted publisher for `cek-host`  
- [ ] Path for `cek-surface` (second env, token, or project-scoped publisher)  
- [ ] First successful `workflow_dispatch` (or token upload)  
- [ ] Install smoke from TestPyPI confirmed  

When the checklist is green, mark P3 complete in [ROADMAP.md](./ROADMAP.md) / [SHIPPED.md](./SHIPPED.md).
