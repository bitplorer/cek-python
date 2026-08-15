# Never-regress invariants

1. Cap refuse → zero Ops
2. Verify Cap before projecting Ops (when require_cap)
3. Peer no mint
4. once jti burn on success path; replay refuses
5. Fail closed (unknown action, bad seal, expiry)
6. Wire = Result.ops only (no ambient code)
7. Perception ≠ authority (shadow must not be truth kv)
8. Law/implementation split (do not rewrite law into surface)
