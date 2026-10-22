# Code map — `codemap/`

Map: [README.md](../../README.md#docs).

[`codemap/`](codemap/index.json) is a generated, machine-readable map of both
published packages, `cek-host/src/cek_host` and `cek-surface/src/cek_surface`,
with one JSON shard per module. It records layers, imports, symbols, each
package's public API, entry points, features and the domain charter. CI fails
when the map is stale or has a problem.

[`scripts/codemap.py`](../../scripts/codemap.py) is vendored byte-identical
from ux-dom, and `index.json` records its version and sha256. The full
reference (fields, config keys, checks) is ux-dom's
[CODEMAP.md](https://github.com/bitplorer/ux-dom/blob/main/docs/internals/CODEMAP.md).

## Rule

A PR updates the map in the same change as the code:

```bash
git add <new files>                      # consumers are read from tracked files
python scripts/codemap.py --write-changed
python scripts/codemap.py --check
```

## Two packages, one map

The `[tool.codemap]` table lives in the repo-root
[pyproject.toml](../../pyproject.toml). That file is dev tooling only. The
wheels and sdists are built from `cek-host/` and `cek-surface/`, so the table
never ships. Entry points come from each package's own `pyproject.toml`, and
`index.json` lists both under `projects`.

## What is curated here

| File | Content |
|------|---------|
| `[tool.codemap]` in [pyproject.toml](../../pyproject.toml) | Layers, layer rules, accepted exceptions |
| [features.toml](features.toml) | Features → modules, symbols, tests, docs |
| [domain.toml](domain.toml) | What the two packages own, their public API, non-goals, the foreign names they may use, and the cek-framework concepts they implement (`law`) |

The layer rules make the package boundary a checked fact. No `host-*` layer
may import a surface layer, so cek-host stays installable alone. The one
accepted crossing is `cek_host.doctor`, which probes lazily that
`EmbeddedHostKernel` is gone. Carriers (`surface-peer`) may reach only the
Rust wrap locator and never the Cap machine.
