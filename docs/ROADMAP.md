# Roadmap

## Shipped (do not re-open as “missing”)

1. Intent / Result / Op vocabulary
2. Surface action handlers compose `list[Op]`
3. Host Cap mint/verify + refuse → empty ops
4. Subprocess / memory / websocket carriers + JS Peer apply demos
5. Cap once / sealed-args / refuse
6. Peer IR v0 (coalesce, flush, shadow)
7. Portable carriers (subprocess / memory / websocket opt-in)
8. Continuations module + shop search arming
9. Policy outer hooks
10. cek-python monorepo organization + cek-host package
11. Latency theory + benches (RTT-bound)
12. Explicit non-goals (no ux-channel, no Peer mint)
13. **P0:** full `cek-surface` tree on GitHub + editable-install smoke + CI
14. **P1:** browser E2E against real Surface.submit; live continuation Cap path
15. **P2:** golden vectors + WS one-command demo
16. **P3:** build + TestPyPI publish path (wheels green; Trusted Publishing workflow)

## Present (2026-08-15)

| State | Detail |
|-------|--------|
| **GitHub** | `bitplorer/cek-python` holds complete host + surface |
| **Kernel** | `CekHostPyKernel` when `cek_host` on path |
| **Tests** | core / roadmap / carrier_ir / host_kernel / continuation_live / http_host / vectors |
| **Install** | `pip install -e ./cek-host -e ./cek-surface` |
| **WS** | `sh scripts/run_ws_demo.sh` |
| **Packaging** | `sh scripts/build_release.sh` → dist/ 0.1.0 |

**Measured:** see [PERFORMANCE.md](./PERFORMANCE.md).

**Happening now should be:** complete TestPyPI Trusted Publisher registration + first `workflow_dispatch` upload; optional deeper vector parity.

## Next (ship in order — do not skip)

| Priority | Item | Definition of done |
|----------|------|--------------------|
| **P2** | Contract name alignment | **SHIPPED** |
| **P2** | WS demo scripted | **SHIPPED** |
| **P3** | PyPI test publish | **READY** — build scripts + `publish-testpypi.yml`; needs TestPyPI Trusted Publisher once |

## Later (explicitly deferred)

| Item | Why deferred |
|------|----------------|
| Durable lineage / idem stores in Python | Prefer parity with Rust stores design |
| Ed25519 product Caps | HMAC sufficient for host-local |
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

## Suggested next coding session

```text
1) Register TestPyPI Trusted Publisher for cek-host + cek-surface (see publish-testpypi.yml)
2) workflow_dispatch → confirm pip install from test.pypi.org
3) Optional: promote same artifacts to production PyPI when stable
```
