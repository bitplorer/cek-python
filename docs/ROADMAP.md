# Roadmap

**Read [START.md](../START.md) first.**

## Shipped

P0 full tree · P1 live continuations · P2 vectors+WS · **P3 TestPyPI + PyPI 0.1.0** · **Phase 1 Host** · **Phase 2 BoundAsk / Idem / Lineage / Ed25519**

## Present

| Item | Status |
|------|--------|
| Published Host | `cek-host` is the only Cap machine. `EmbeddedHostKernel` gone. |
| production() | Refuses default secret + memory once/idem/lineage |
| BoundAsk | No public constructor. Bind after verify + idem + once-ensure |
| Idem / Lineage | File+memory backends. `end_activity` landed-first reverse |
| Ed25519 / law-gen | Opt-in Host policy. Blank/unknown generation refuse |
| Vectors | surface v3 (20) + 28 aligned Rust JSON fixtures |
| doctor / explain / create-app | `python -m cek_host` |

## Next (Phase 3 — gated on Phase 2 critic SHIP)

| Item | Do |
|------|----|
| Redis backends | Once / Idem / Lineage |
| crates.io | Rust reference publish |
| Next PyPI | 0.1.2 Host + Surface |

## Anti-roadmap

Peer Cap mint · Peer plan IR · ux-channel dependency · Surface-owned Cap product · publishing `ports/cek-host-py` as a second Host · `require_cap=False` in templates
