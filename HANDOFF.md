# HANDOFF — next agent

**Read [START.md](./START.md) first.** Then [docs/S_TIER_SCORECARD.md](./docs/S_TIER_SCORECARD.md).

**Date:** 2026-08-15  
**Repo:** https://github.com/bitplorer/cek-python (tree **0.1.2**)  
**Law:** https://github.com/bitplorer/cek-framework `@ 90d48fd`  
**Rust:** https://github.com/bitplorer/cek-runtime `@ cce98b6`

**Phase 2 verdict: SHIP.** BoundAsk · Idem/Lineage · Ed25519 · law-generation · **29** aligned fixtures · clean-clone `verify ok`. Every plane ≥ 4. No kill. CHARTER/KILL/CORE untouched.

Phase 3 (Redis / crates.io / PyPI 0.1.2 publish) is **not** started — wait for an explicit Phase 3 plan.

```bash
export PYTHONPATH=cek-host/src:cek-surface/src
sh scripts/verify.sh
python -m cek_host doctor --fail     # demo Host is expected FAIL
python -m cek_host doctor --production-demo   # expected FAIL (memory + default secret)
```

NEVER REGRESS: refuse → `ops: []` · Peer no mint · once/sealed fail closed · no ux-channel · no EmbeddedHostKernel · no `cek_surface.host.Host` · subject/scope enforced · digest `cek1:` · submit without Cap refuses · BoundAsk() raises · empty idem key refuse · idem before once · landed-first reverse · Ed25519 missing/tamper refuse · blank/unknown law-gen refuse.
