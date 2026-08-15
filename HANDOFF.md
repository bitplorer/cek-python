# HANDOFF — next agent

**Read [START.md](./START.md) first.** Then [docs/S_TIER_SCORECARD.md](./docs/S_TIER_SCORECARD.md).

**Date:** 2026-08-15  
**Repo:** https://github.com/bitplorer/cek-python `@ ae2460f` (tree **0.1.2**)  
**Law:** https://github.com/bitplorer/cek-framework `@ 90d48fd`  
**Rust:** https://github.com/bitplorer/cek-runtime `@ cce98b6`

Phase 1 SHIP condition met (loop 4). Phase 2 is in this tree: BoundAsk, Idem/Lineage, Ed25519, law-generation, **29** aligned fixtures (includes `once-idempotent-retry`). Critic L5 **ALMOST** leftovers applied; clean-clone `sh scripts/verify.sh` → **verify ok** (2026-08-15). L5 close condition met. Phase 3 (Redis / crates.io) stays gated until an explicit Phase 3 plan — do not start it from this handoff.

```bash
export PYTHONPATH=cek-host/src:cek-surface/src
sh scripts/verify.sh
python -m cek_host doctor --fail     # demo Host is expected FAIL
python -m cek_host doctor --production-demo   # expected FAIL (memory + default secret)
```

NEVER REGRESS: refuse → `ops: []` · Peer no mint · once/sealed fail closed · no ux-channel · no EmbeddedHostKernel · no `cek_surface.host.Host` · subject/scope enforced · digest `cek1:` · submit without Cap refuses · BoundAsk() raises · empty idem key refuse · idem before once · landed-first reverse · Ed25519 missing/tamper refuse · blank/unknown law-gen refuse.
