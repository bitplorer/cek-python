# HANDOFF — Grok build / next agent

**Date:** 2026-08-15  
**Repo (target):** https://github.com/bitplorer/cek-python  
**Law:** https://github.com/bitplorer/cek-framework  
**Rust:** https://github.com/bitplorer/cek-runtime  

This zip is the **complete local monorepo**. GitHub may still lack `cek-surface/src|js|demo|tests` until you push. **Read `docs/KNOWLEDGE.md` first.**

---

## Prompt for Grok (copy-paste)

```text
You are continuing CEK Python work from the uploaded cek-python monorepo (bitplorer/cek-python).

BEFORE changing code:
1. Read docs/KNOWLEDGE.md, docs/SHIPPED.md, docs/ROADMAP.md, docs/INVARIANTS.md, docs/GITHUB_STATUS.md, docs/DECISIONS.md
2. Confirm local tree has cek-host/src and cek-surface/src (not empty stubs)
3. Run:
   export PYTHONPATH=cek-host/src:cek-surface/src
   python -c "from cek_host import Host; from cek_surface import Surface, Op; print('import ok')"
   python cek-surface/tests/test_core.py
   python cek-surface/tests/test_roadmap.py
   python cek-surface/tests/test_carrier_ir.py
   python cek-surface/tests/test_host_kernel.py

NEVER REGRESS:
- Cap refuse → ops: []
- Peer no mint
- once / sealed-args fail closed
- Wire = Result.ops only (no Peer plan IR / recipes / eval)
- No ux-channel dependency
- Composition stays in Python + Caps

PRIORITY (do in order):
P0. Ensure full cek-surface tree is on GitHub (src, js, demo, tests, vectors) if remote is incomplete
P0. Document and verify: pip install -e ./cek-host && pip install -e ./cek-surface smoke test
P1. Browser E2E: demo/http_host.py + browser_shop.html without relying only on ?mock=1
P1. Live continuation path: timer.fired → pre-minted Cap → search.commit
P2. Align hot Op names with cek-runtime/contract; expand golden vectors
P2. One-command WebSocket carrier demo (ws_peer_server.mjs + Surface websocket)
P3. Prepare PyPI 0.1.0 metadata only when P0 green

Doctrine: Composition = Python + Caps; wire = Result.ops; Peer = closed drivers + perception IR; carriers are transport only (subprocess default).

After each change: run the test suite above; update docs/SHIPPED.md and docs/GITHUB_STATUS.md if publish state changes.
```

---

## Next steps checklist (human + agent)

### Immediately after unzip / clone

- [ ] Open `docs/KNOWLEDGE.md`
- [ ] `export PYTHONPATH=cek-host/src:cek-surface/src`
- [ ] Run all four test files under `cek-surface/tests/`
- [ ] Compare GitHub tree to local; push any missing `cek-surface/**` files

### P0 — Publish completeness

- [ ] Remote contains `cek-surface/src/cek_surface/*.py`
- [ ] Remote contains `cek-surface/js/{peer,peer_ir,browser_peer}.mjs`
- [ ] Remote contains `demo/`, `tests/`, `vectors/`
- [ ] `pip install -e ./cek-host -e ./cek-surface` works from a clean clone

### P1 — Product path

- [ ] `python demo/http_host.py` serves shop; Host submit path works
- [ ] Coalesce + flush documented in browser peer
- [ ] Continuation Cap path exercised in a test

### P2 / P3

- [ ] Contract/vector alignment notes in docs
- [ ] WS demo in README
- [ ] Version tags only after tests green

---

## Layout of this zip

```text
cek-python/
  HANDOFF.md          ← this file
  README.md
  docs/               ← full knowledge base
  cek-host/           ← Cap + Host kernel (complete)
  cek-surface/        ← surface + js + demos + tests (complete locally)
```

## Doctrine (do not dilute)

> Composition = Python + Caps; wire = Result.ops; Peer = closed drivers + perception IR; carriers are transport only.
