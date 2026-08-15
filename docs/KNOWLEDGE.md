# CEK Python — complete knowledge base

**Audience:** maintainers and future agents.  
**Purpose:** nothing important stays only in chat. Past, present, and next work are explicit.

## Start here

| Priority | Doc | Contents |
|----------|-----|----------|
| 1 | [SHIPPED.md](./SHIPPED.md) | What exists and is verified |
| 2 | [ROADMAP.md](./ROADMAP.md) | Past → present → next → later |
| 3 | [INVARIANTS.md](./INVARIANTS.md) | Never-regress rules |
| 4 | [ARCHITECTURE.md](./ARCHITECTURE.md) | Layers, wire, Peer IR, carriers, Caps |
| 5 | [ORGANIZATION.md](./ORGANIZATION.md) | GitHub repos, pip install, what lives where |

## Reference

| Doc | Contents |
|-----|----------|
| [DECISIONS.md](./DECISIONS.md) | Non-obvious choices and rejected alternatives |
| [LATENCY.md](./LATENCY.md) | RTT model, human thresholds, Peer IR role |
| [PERFORMANCE.md](./PERFORMANCE.md) | Measured real-world + load numbers |
| [GITHUB_STATUS.md](./GITHUB_STATUS.md) | Remote inventory (honest) |
| [TIMELINE.md](./TIMELINE.md) | Narrative history |
| [PACKAGING.md](./PACKAGING.md) | setuptools today; uv/Poetry migration |
| [TESTPYPI_SETUP.md](./TESTPYPI_SETUP.md) | Trusted Publisher + TestPyPI checklist |
| [PYPI_SETUP.md](./PYPI_SETUP.md) | Production pypi.org Trusted Publisher checklist |

## External repos

| Repo | Role |
|------|------|
| [bitplorer/cek-framework](https://github.com/bitplorer/cek-framework) | **Law** — Cap, Intent, Op, lineage, reverse |
| [bitplorer/cek-runtime](https://github.com/bitplorer/cek-runtime) | **Rust** reference Host/Peer + contract vectors |
| [bitplorer/cek-python](https://github.com/bitplorer/cek-python) | **This monorepo** — `cek-host` + `cek-surface` |

## Doctrine

> Composition = Python + Caps; wire = `Result.ops`; Peer = closed drivers + perception IR; everything else is host policy or app sugar.

**Never regress:** refuse → `ops: []` · Peer no mint · once/sealed fail closed · no ux-channel dependency.
