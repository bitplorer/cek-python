# CEK Python — complete knowledge base

**Audience:** maintainers and future agents.  
**Purpose:** nothing important stays only in chat. Past, present, and next work are explicit.

| Doc | Contents |
|-----|----------|
| [ORGANIZATION.md](./ORGANIZATION.md) | GitHub repos, pip install story, what lives where |
| [SHIPPED.md](./SHIPPED.md) | What exists, why it was built, verification status |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Runtime model, layers, Peer IR, carriers, Caps |
| [DECISIONS.md](./DECISIONS.md) | Non-obvious choices and rejected alternatives |
| [INVARIANTS.md](./INVARIANTS.md) | Never-regress rules (law ↔ implementation) |
| [ROADMAP.md](./ROADMAP.md) | Past → present → next → later |
| [LATENCY.md](./LATENCY.md) | Measured lag, human thresholds, Peer IR role |
| [GITHUB_STATUS.md](./GITHUB_STATUS.md) | What is on GitHub vs local-only (honest inventory) |
| [PACKAGING.md](./PACKAGING.md) | setuptools today; uv/Poetry migration recipes |

**Related external repos**

| Repo | Role |
|------|------|
| [bitplorer/cek-framework](https://github.com/bitplorer/cek-framework) | **Law** — Cap, Intent, Op, lineage, reverse |
| [bitplorer/cek-runtime](https://github.com/bitplorer/cek-runtime) | **Rust** reference Host/Peer + contract vectors |
| [bitplorer/cek-python](https://github.com/bitplorer/cek-python) | **This monorepo** — `cek-host` + `cek-surface` |

**One-line product doctrine**

> Composition = Python + Caps; wire = Result.ops; Peer = closed drivers + perception IR; everything else is host policy or app sugar.
