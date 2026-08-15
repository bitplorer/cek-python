# Latency model and Peer IR

## Human thresholds (product acceptance)

| Delay click → useful feedback | Feel |
|-------------------------------|------|
| ≤ 100 ms | Instant |
| 100–300 ms | Acceptable |
| 300–1000 ms | Needs progress UI |
| > 1 s | Broken for “click” interactions |

Enterprise practical bar: **something visible &lt; 100 ms**; **authoritative morph p95 &lt; 300–500 ms** on networks you care about.

## Where CEK-surface spends time

| Segment | Typical | Notes |
|---------|---------|-------|
| Host compose + Cap | ~0.03 ms | Not the problem |
| Local Peer apply (NDJSON) | ~0.5 ms | Not the problem |
| Network RTT | 1–200+ ms | Dominates |
| Multi-round (timer → Host → http → Host) | N × RTT | Feels laggy without chrome |

## Where Peer IR steps in

| Use Peer IR | Keep on Host |
|-------------|--------------|
| pending / shadow | cart, money, checkout |
| coalesce / flush Intents | Cap verify, Op projection |
| filter_cached over Host snapshot | inventing new entitlements |
| toast fade | what toast message was authorized |

## Doctrine

> Lag ≈ RTT × (Host decisions). Apply is free once Result is local.
