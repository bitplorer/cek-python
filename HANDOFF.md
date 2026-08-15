# HANDOFF — next agent

**Read [START.md](./START.md) first.** Then [docs/S_TIER_SCORECARD.md](./docs/S_TIER_SCORECARD.md).

**Date:** 2026-08-15  
**Repo:** https://github.com/bitplorer/cek-python  
**Law:** https://github.com/bitplorer/cek-framework `@ 90d48fd`  
**Rust:** https://github.com/bitplorer/cek-runtime `@ cce98b6`

Loop 3 applied the independent critic’s ALMOST diffs: sketch Host gone (D3), clone-path docs, Rust JSON fixtures, submit requires a Cap. `scripts/verify.sh` is the fast gate (12 files). Do not start Phase 2 (BoundAsk / lineage / Ed25519) until the scorecard critic says Phase 1 SHIP.

```bash
export PYTHONPATH=cek-host/src:cek-surface/src
sh scripts/verify.sh
python -m cek_host doctor --fail     # demo Host is expected FAIL
```

NEVER REGRESS: refuse → `ops: []` · Peer no mint · once/sealed fail closed · no ux-channel · no EmbeddedHostKernel · no `cek_surface.host.Host` · subject/scope enforced · digest `cek1:` · submit without Cap refuses.
