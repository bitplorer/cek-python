# Never-regress invariants

Aligned with cek-framework law and cek-runtime hardening. **Do not “soft fail.”**

| # | Invariant | Surface/host implication |
|---|-----------|---------------------------|
| 1 | **Cap refuse → zero Ops** | `authority_refusal` results must carry `ops: []` |
| 2 | **BoundAsk / verify before project** | No Ops emitted without successful Cap verify (when require_cap) |
| 3 | **Peer no mint** | No CapService in Peer; browser never signs Caps |
| 4 | **once commit only after success path** | jti burn on successful verify/use; replay refuses |
| 5 | **Fail closed** | Unknown action, bad seal, expiry → refuse, not best-effort Ops |
| 6 | **Wire = Result.ops** | No ambient code, no Peer-executable plan IR |
| 7 | **Perception ≠ authority** | Shadow/pending must not write authority kv as truth |
| 8 | **Law/implementation split** | Do not rewrite law text into surface; implement against it |

**Chaos gates already used:** once replay, sealed-args tamper, refuse without cap, rapid cart under load.
