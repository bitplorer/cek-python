# Packaging & future migration (setuptools → uv / Poetry)

**Status:** current production path is **setuptools** + `python -m build` + `twine` / Trusted Publishing.  
**Purpose of this doc:** when you *choose* to migrate build tooling, follow these steps without rediscovering layout, TestPyPI rules, or monorepo pitfalls.

Related:

| Doc | Role |
|-----|------|
| [ORGANIZATION.md](./ORGANIZATION.md) | Install story, TestPyPI one-liner |
| [SHIPPED.md](./SHIPPED.md) | What is already verified |
| [INVARIANTS.md](./INVARIANTS.md) | Never-regress (unrelated to backend; do not weaken) |
| Scripts | `scripts/build_release.sh`, `scripts/publish_testpypi.sh` |
| CI | `.github/workflows/publish-testpypi.yml`, `.github/workflows/test.yml` |

---

## 1. Current layout (source of truth)

```text
cek-python/
  cek-host/
    pyproject.toml          # name = cek-host, setuptools backend
    src/cek_host/
  cek-surface/
    pyproject.toml          # name = cek-surface, depends on cek-host>=0.1.0
    src/cek_surface/
  scripts/build_release.sh
  scripts/publish_testpypi.sh
  .github/workflows/publish-testpypi.yml
```

### Current `[build-system]` (both packages)

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

### Current build / publish commands

```bash
# from repo root
sh scripts/build_release.sh
# → dist/cek_host-0.1.0-*.whl + .tar.gz
# → dist/cek_surface-0.1.0-*.whl + .tar.gz

# TestPyPI (token)
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-... sh scripts/publish_testpypi.sh

# or: Actions → publish-testpypi (Trusted Publishing; env testpypi / per-package envs)
```

### Non-negotiables when migrating

1. **Two packages stay two distributions:** `cek-host` and `cek-surface` (not one mega-wheel).
2. **Import names stay** `cek_host` / `cek_surface`.
3. **`cek-surface` depends on `cek-host>=0.1.0`** (or later floor).
4. **src layout** (`src/cek_host`, `src/cek_surface`) preferred — keep it.
5. **`py.typed`** must ship in both wheels.
6. **Version uniqueness per index:** you cannot re-upload the same version to TestPyPI or PyPI.
7. **TestPyPI ≠ PyPI:** separate publish; separate Trusted Publishers.
8. **Invariants** (refuse → `ops: []`, Peer no mint, etc.) are independent of packaging backend.

---

## 2. Using uv *without* changing the backend (recommended first step)

uv can build and publish **while setuptools remains the backend**. No `pyproject.toml` rewrite required.

```bash
# install uv: https://docs.astral.sh/uv/
cd /path/to/cek-python

uv build --directory cek-host --out-dir dist
uv build --directory cek-surface --out-dir dist

# TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/ --token "$TEST_PYPI_TOKEN" dist/cek_host-*
uv publish --publish-url https://test.pypi.org/legacy/ --token "$TEST_PYPI_TOKEN" dist/cek_surface-*

# Production PyPI (only when intentional)
uv publish --token "$PYPI_TOKEN" dist/cek_host-*
uv publish --token "$PYPI_TOKEN" dist/cek_surface-*
```

Editable / verify:

```bash
uv pip install -e ./cek-host -e "./cek-surface[ws]"
sh scripts/verify.sh
```

**When this is enough:** you want faster CLI, lockfiles for *apps* that consume CEK, or scripted publish — not a backend change.

---

## 3. Migration A — hatchling backend (uv-native libraries)

Prefer this over Poetry for **libraries** in a path-based monorepo.

### 3.1 `cek-host/pyproject.toml` (target shape)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "cek-host"
version = "0.1.0"   # or switch to dynamic version later
description = "CEK Python Host kernel — Cap mint/verify, Result packaging (authority only)"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [{ name = "bitplorer" }]
dependencies = []

[project.urls]
Homepage = "https://github.com/bitplorer/cek-python"
Law = "https://github.com/bitplorer/cek-framework"
Rust = "https://github.com/bitplorer/cek-runtime"

[tool.hatch.build.targets.wheel]
packages = ["src/cek_host"]

[tool.hatch.build.targets.sdist]
include = ["src/cek_host", "README.md"]
```

If hatchling does not pick up `src/` automatically, map sources explicitly (exact keys vary by hatchling version — verify with `uv build` and inspect the wheel).

Ship `py.typed` via force-include if needed:

```toml
[tool.hatch.build.targets.wheel.force-include]
"src/cek_host/py.typed" = "cek_host/py.typed"
```

### 3.2 `cek-surface/pyproject.toml` (target shape)

Same pattern; keep:

```toml
dependencies = [
  "cek-host>=0.1.0",
]

[project.optional-dependencies]
ws = ["websockets>=12.0"]
dev = ["websockets>=12.0"]
```

### 3.3 Checklist after hatchling switch

```bash
rm -rf dist cek-host/dist cek-surface/dist
uv build --directory cek-host --out-dir dist
uv build --directory cek-surface --out-dir dist

python -m twine check dist/*
unzip -l dist/cek_host-*.whl | grep py.typed
unzip -l dist/cek_surface-*.whl | grep py.typed

pip install --force-reinstall dist/cek_host-*.whl dist/cek_surface-*.whl
python -c "from cek_host import Host; from cek_surface import Surface, Op; print('ok')"
sh scripts/verify.sh
```

### 3.4 CI updates

In `scripts/build_release.sh` and `.github/workflows/publish-testpypi.yml`:

- Keep `python -m build` **or** replace with `uv build` (install uv in the job).
- Trusted Publishing (`pypa/gh-action-pypi-publish`) is **backend-agnostic**.
- Pending publisher uniqueness: one `(repo, workflow, environment)` per pending project name — use `testpypi` vs `testpypi-surface` if needed.

### 3.5 Rollback

Restore the setuptools `[build-system]` and `[tool.setuptools.*]` blocks from git history. No code changes required.

---

## 4. Migration B — Poetry as build backend

Poetry is heavier for **two library packages** in one git repo. Use only if you deliberately want Poetry workspaces / Poetry-only publish.

### 4.1 Constraints

- Each of `cek-host` and `cek-surface` becomes its own Poetry project.
- Root may use a Poetry **workspace** (optional) or two independent Poetry projects.
- `poetry.lock` is optional for pure libs.
- Editable: `poetry install` inside each package dir, or path deps.

### 4.2 Convert metadata (conceptual)

Toward Poetry:

```toml
[tool.poetry]
name = "cek-host"
version = "0.1.0"
description = "..."
authors = ["bitplorer"]
readme = "README.md"
packages = [{ include = "cek_host", from = "src" }]

[tool.poetry.dependencies]
python = ">=3.10"

[build-system]
requires = ["poetry-core>=1.9.0"]
build-backend = "poetry.core.masonry.api"
```

`cek-surface`:

```toml
[tool.poetry.dependencies]
python = ">=3.10"
cek-host = ">=0.1.0"

[tool.poetry.extras]
ws = ["websockets"]
```

Path development without publishing:

```toml
cek-host = { path = "../cek-host", develop = true }
```

### 4.3 Build & publish with Poetry

```bash
cd cek-host
poetry build
poetry publish -r testpypi

cd ../cek-surface
poetry build
poetry publish -r testpypi
```

Configure TestPyPI once:

```bash
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.testpypi pypi-...
```

### 4.4 Checklist after Poetry switch

- [ ] `poetry build` produces wheel + sdist for both packages
- [ ] Wheel contains `py.typed`
- [ ] `pip install dist/*.whl` import smoke
- [ ] `sh scripts/verify.sh` green
- [ ] Update `scripts/build_release.sh` or document Poetry-only path
- [ ] CI installs poetry or keeps `python -m build` (PEP 517)

### 4.5 Rollback

Revert `pyproject.toml` files to setuptools PEP 621 form from git. Delete `poetry.lock` if present.

---

## 5. uv workspaces (optional monorepo tool)

```toml
# repo root pyproject.toml (workspace only — do not publish the root)
[tool.uv.workspace]
members = ["cek-host", "cek-surface"]
```

- Members keep their own package `pyproject.toml`.
- Publish **member** packages, never the workspace root as `cek-python` unless intentional.

---

## 6. TestPyPI / PyPI rules (any backend)

| Rule | Detail |
|------|--------|
| Version unique per index | `0.1.0` once on TestPyPI; bump for retries |
| Trusted pending publisher | One `(owner, repo, workflow, environment)` → one pending **project name** |
| Two packages, one workflow | Two GitHub Environments (`testpypi`, `testpypi-surface`) or two workflow files |
| Token vs OIDC | Both fine; OIDC is Actions-only |
| Install from TestPyPI | Always `--extra-index-url https://pypi.org/simple/` |
| Production | Separate publish to pypi.org; separate trusted publisher |

```bash
pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  cek-host==0.1.0 cek-surface==0.1.0
```

---

## 7. Decision guide (when to migrate)

| Goal | Action |
|------|--------|
| Publish 0.1.0 now | **Stay on setuptools**; use existing scripts / Actions |
| Prefer `uv` CLI only | §2 — no backend change |
| Align with uv/hatch ecosystem long-term | §3 hatchling |
| Org standard is Poetry for everything | §4 Poetry (accept monorepo friction) |
| App elsewhere uses Poetry/uv | No migration — depend on published package |

**Default:** remain on setuptools until there is a concrete tooling requirement; use §2 for uv ergonomics.

---

## 8. Verification matrix (run after any packaging change)

```bash
sh scripts/build_release.sh   # or uv/poetry equivalent
python -m twine check dist/*
unzip -l dist/cek_host-*.whl | grep -E 'cek_host/.+|py.typed'
unzip -l dist/cek_surface-*.whl | grep -E 'cek_surface/.+|py.typed'

pip install --force-reinstall --no-deps dist/cek_host-*.whl
pip install --force-reinstall dist/cek_surface-*.whl
python -c "from cek_host import Host; from cek_surface import Surface, Op; \
 h=Host(secret=b't'*32); t=h.mint('x'); \
 r=h.submit(action='x',args={},cap=t,project_ops=[{'ns':'sys','name':'noop','payload':{}}]); \
 assert r.kind=='ok'; \
 r2=h.submit(action='x',args={},cap=None,project_ops=[]); \
 assert r2.kind=='authority_refusal' and r2.ops==[]; print('packaging smoke ok')"

pip install -e ./cek-host -e ./cek-surface
sh scripts/verify.sh
```

---

## 9. Files to touch during a real migration

| File | setuptools → hatchling | setuptools → Poetry |
|------|------------------------|---------------------|
| `cek-host/pyproject.toml` | Yes | Yes (schema rewrite) |
| `cek-surface/pyproject.toml` | Yes | Yes |
| `scripts/build_release.sh` | Optional (`uv build`) | Yes |
| `scripts/publish_testpypi.sh` | Optional | Adjust or keep twine |
| `.github/workflows/publish-testpypi.yml` | Optional | Optional |
| `.github/workflows/test.yml` | Usually unchanged | May install poetry |
| `docs/ORGANIZATION.md` | Note new commands | Note new commands |
| Root `poetry.lock` / `uv.lock` | Only if workspace | If you commit locks |

Do **not** move Cap logic, Peer drivers, or tests as part of a packaging migration.

---

## 10. One-page “migrate tomorrow” recipe

**uv/hatchling (preferred if leaving setuptools):**

1. Edit both `pyproject.toml` → hatchling backend + package map (§3).
2. `uv build --directory cek-host --out-dir dist` (and surface).
3. `twine check dist/*` + verify matrix (§8).
4. Bump version if `0.1.0` already on TestPyPI.
5. Publish via Trusted Publishing or `uv publish`.
6. Commit; ensure CI green.

**Poetry:**

1. Rewrite both `pyproject.toml` to `[tool.poetry]` (§4).
2. `poetry build` in each package directory.
3. Same verify matrix.
4. `poetry publish -r testpypi` or twine on `dist/`.
5. Update scripts/docs; CI green.

Until then: **do nothing** — setuptools path remains valid and supported.
