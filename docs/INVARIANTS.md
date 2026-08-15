# Never-regress invariants

**Read [START.md](../START.md) first.**

Aligned with cek-framework law and cek-runtime hardening. **Do not “soft fail.”**

| # | Invariant | Surface/host implication | Named test |
|---|-----------|---------------------------|------------|
| 1 | **Cap refuse → zero Ops** | `authority_refusal` results must carry `ops: []` | `test_vectors` / `test_contract_vectors` |
| 2 | **verify before compose** | Surface `check()` before handler; BoundAsk only after verify + idem + once-ensure | `test_host_kernel` + `test_phase2` |
| 3 | **Peer no mint** | No CapService in Peer; browser never signs Caps | `test_continuation_live` / `test_layer_honesty` |
| 4 | **once commit only after success path** | `OnceBackend.commit` after project; replay refuses | `test_host_parity` / `test_hardening` |
| 5 | **Fail closed** | Unknown action, bad seal, expiry, store down → refuse | `test_hardening` / contract family |
| 6 | **Wire = Result.ops** | No ambient code, no Peer-executable plan IR | architecture + D1/D2 |
| 7 | **Perception ≠ authority** | Shadow/pending must not write authority kv as truth | `test_carrier_ir` |
| 8 | **Result digest `cek1:`** | FIPS SHA-256 over `{error,kind,ops}` | `test_contract_vectors` |
| 9 | **Law/implementation split** | Do not rewrite law text into surface | D7 |
| 10 | **Idempotency before once-ensure** | Lookup then ensure; once+same key replays | `test_phase2` / contract `idempotency-*` |
| 11 | **Empty idempotency key refuse** | Unclear bind is not a global key | `empty-idempotency-key` |
| 12 | **Honest reverse** | Landed-first; NonReversible listed, never faked | `lineage-reverse-on-end` / `receipt-landed-first-reverse` |
| 13 | **Ed25519 policy** | Missing/tamper → zero Ops when Host has a seed | `ed25519-*` |
| 14 | **Law generation window** | Blank/unknown refuse; unset = legacy | `law-gen-*` |

Unclaimed (Phase 3 — do not list in SHIPPED as held): Redis backends, crates.io publish.


**Chaos gates already used:** once replay, sealed-args tamper, refuse without cap, rapid cart under load.
