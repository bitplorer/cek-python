# Roadmap — past, present, next, later

## Past (done — do not re-litigate)

1. CEK law repo + Rust runtime baseline
2. Reject sending arbitrary JS / plan IR on the wire
3. Op constructor surface (`class Op`) practical catalog
4. Python Host compose + JS Peer apply demos
5. Cap once / sealed-args / refuse
6. Peer IR v0 (coalesce, flush, shadow)
7. Portable carriers (subprocess / memory / websocket opt-in)
8. Continuations module + shop search arming
9. Policy outer hooks
10. cek-python monorepo organization + cek-host package
11. Latency theory + benches (RTT-bound)
12. Explicit non-goals (no ux-channel, no Peer mint)
13. **P0:** full `cek-surface` tree on GitHub + editable-install smoke + CI

## Present (2026-08-15)

| State | Detail |
|-------|--------|
| **GitHub** | `bitplorer/cek-python` holds complete host + surface (src/js/demo/tests/vectors) |
| **Kernel** | `load_host_kernel()` resolves `CekHostPyKernel` when `cek_host` on path |
| **Tests** | core / roadmap / carrier_ir / host_kernel — green via `sh scripts/verify.sh` |
| **Install** | `pip install -e ./cek-host -e ./cek-surface` |

**Happening now should be:** P1 product path (browser E2E + live continuations).

## Next (ship in order — do not skip)

| Priority | Item | Definition of done |
|----------|------|--------------------|
| **P1** | Browser E2E without `?mock=1` | http_host + browser_shop against real Surface.submit |
| **P1** | Continuation live path | `timer.fired` uses pre-minted Cap path end-to-end |
| **P2** | Contract name alignment | Hot Ops match cek-runtime / framework naming; golden vectors CI |
| **P2** | WS demo scripted | `ws_peer_server` + Surface(websocket) one-command doc |
| **P3** | PyPI test publish | `cek-host` 0.1.0, `cek-surface` 0.1.0 (depends on host) |

## Later (explicitly deferred)

| Item | Why deferred |
|------|----------------|
| Durable lineage / idem stores in Python | Prefer parity with Rust stores design |
| Ed25519 product Caps | HMAC sufficient for host-local; product keys need key mgmt |
| npm `@cek/peer` package | js/ under surface is enough until consumers demand |
| Diff/patch Ops as Baseline | Wait until morph payload size is a real problem |
| Multi-region Host | Policy/product, not surface core |
| Merging with ux-channel | Permanently out of scope as dependency |

## Anti-roadmap (will not do)

- Peer Cap mint
- Peer plan IR / recipes / eval
- Surface owning Cap as product
- Replacing cek-framework law with surface docs
- “Arbitrary function projection” as executable Peer code

## Suggested next coding session (single slice)

```text
1) Browser E2E: http_host.py + browser_shop.html without ?mock=1
2) Live continuation: timer.fired → pre-minted Cap → search.commit
3) Keep refuse → ops:[] / Peer no mint / fail closed
```
