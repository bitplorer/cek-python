# CEK Python — complete knowledge base

**Read [START.md](../START.md) first.** This page is the Layer-2 index, not a second intro.

**Audience:** maintainers and future agents.  
**Purpose:** nothing important stays only in chat.

## Start here

| Priority | Doc | Contents |
|----------|-----|----------|
| 0 | [../START.md](../START.md) | Zero → first morph, one command |
| 1 | [INVARIANTS.md](./INVARIANTS.md) | Never-regress rules (Layer 1) |
| 2 | [S_TIER_SCORECARD.md](./S_TIER_SCORECARD.md) | Planes, REPLACE/ADAPT/KEEP, critic |
| 3 | [SHIPPED.md](./SHIPPED.md) | What exists and is verified |
| 4 | [ARCHITECTURE.md](./ARCHITECTURE.md) | Layers, wire, Peer IR, carriers, Caps |
| 5 | [ORGANIZATION.md](./ORGANIZATION.md) | GitHub repos, pip install, what lives where |

## Reference

| Doc | Contents |
|-----|----------|
| [DECISIONS.md](./DECISIONS.md) | D1–D10 |
| [TESTING.md](./TESTING.md) | Green means |
| [LATENCY.md](./LATENCY.md) | RTT model |
| [PERFORMANCE.md](./PERFORMANCE.md) | Measured numbers (cite, don't invent) |
| [ROADMAP.md](./ROADMAP.md) | Phase 1 shipped; Phase 2 gated |
| [GITHUB_STATUS.md](./GITHUB_STATUS.md) | Remote inventory |
| [TIMELINE.md](./TIMELINE.md) | Narrative history |
| [PACKAGING.md](./PACKAGING.md) | setuptools today |
| [TESTPYPI_SETUP.md](./TESTPYPI_SETUP.md) | Trusted Publisher |
| [PYPI_SETUP.md](./PYPI_SETUP.md) | Production pypi.org |

## External repos

| Repo | Role |
|------|------|
| [bitplorer/cek-framework](https://github.com/bitplorer/cek-framework) | **Law** |
| [bitplorer/cek-runtime](https://github.com/bitplorer/cek-runtime) | **Rust** reference + contract vectors |
| [bitplorer/cek-python](https://github.com/bitplorer/cek-python) | **This monorepo** — `cek-host` + `cek-surface` |

## Doctrine

> Composition = Python + Caps; wire = `Result.ops`; Peer = closed drivers + perception IR; everything else is host policy or app sugar.

**Never regress:** refuse → `ops: []` · Peer no mint · once/sealed fail closed · no ux-channel dependency · no EmbeddedHostKernel.
