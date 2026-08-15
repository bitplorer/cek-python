# Latency model (CEK surface)

## Doctrine

**Lag ≈ RTT × (Host decisions).** Apply is free once `Result` is local.

Mechanism (compose + Cap + package + local Peer apply) is noise vs network. Optimize round-trips and interim chrome — not Host CPU.

## Human thresholds (guidance)

| Bar | Target |
|-----|--------|
| Instant feedback | ≤ 100 ms (Peer IR chrome / shadows) |
| Authoritative morph p95 | 300–500 ms |
| Multi-hop search | Continuation Cap removes a policy hop; timer still costs its `ms` |

## Peer IR role

coalesce / flush / shadow / pending / filter_cached on Peer give interim feedback while authority waits one RTT. Shadows clear on authoritative Result.

## Measured (2026-08-15)

Full real-world + load numbers live in **[PERFORMANCE.md](./PERFORMANCE.md)** (and `performance-report.json`).

Headline on this machine:

| Path | p50 |
|------|-----|
| Cap mint / verify | ~0.01 / ~0.006 ms |
| Host-only compose+Cap+package | **~0.026 ms** |
| Host → Node Peer apply | **~0.32 ms** |
| Simulated metro ~20 ms RTT | ~22 ms |
| Simulated WAN ~80 ms RTT | ~79 ms |

Doctrine holds: lag ≈ RTT × Host decisions; apply is free once Result is local.
