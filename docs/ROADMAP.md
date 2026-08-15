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

## Present (2026-08-15)

| State | Detail |
|-------|--------|
| **Local** | Full `cek-host` + `cek-surface` tree under `artifacts/cek-python` |
| **GitHub** | Org docs + full **cek-host** + surface **stubs**; surface **src/js/demo incomplete on remote** |
| **Kernel** | `load_host_kernel()` resolves `CekHostPyKernel` when `cek_host` on path |
| **Tests** | core / roadmap / carrier_ir / host_kernel — green when PYTHONPATH set |

**Happening now should be:** finish remote publish of surface sources; treat docs in `docs/` as the knowledge spine.

## Next (ship in order — do not skip)

| Priority | Item | Definition of done |
|----------|------|--------------------|
| **P0** | Push full `cek-surface` tree to GitHub | Remote tree matches local src/js/demo/tests/vectors |
| **P0** | Editable install works from clone | `pip install -e ./cek-host -e ./cek-surface` + smoke test |
| **P1** | Browser E2E without `?mock=1` | http_host + browser_shop against real Surface.submit |
| **P1** | Continuation live path | `timer.fired` uses pre-minted Cap path end-to-end |
| **P2** | Contract name alignment | Hot Ops match cek-runtime naming; golden vectors CI |
| **P2** | WS demo scripted | `ws_peer_server` + Surface(websocket) one-command doc |
| **P3** | PyPI test publish | `cek-host` 0.1.0, `cek-surface` 0.1.0 |

## Later (explicitly deferred)

| Item | Why deferred |
|------|----------------|
| Durable lineage / idem stores in Python | Prefer parity with Rust stores design |
| Ed25519 product Caps | HMAC sufficient for host-local |
| npm `@cek/peer` package | js/ under surface enough until demand |
| Diff/patch Ops as Baseline | Wait until morph size is a real problem |
| Multi-region Host | Policy/product, not surface core |
| Merging with ux-channel | Permanently out of scope as dependency |

## Anti-roadmap (will not do)

- Peer Cap mint
- Peer plan IR / recipes / eval
- Surface owning Cap as product
- Replacing cek-framework law with surface docs
- Arbitrary function projection as executable Peer code
