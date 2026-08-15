# Contract fixtures (aligned family)

**Source of truth:** [cek-runtime `crates/cek-contract/vectors`](https://github.com/bitplorer/cek-runtime/tree/main/crates/cek-contract/vectors).

These files are copies of the Rust JSON cases the published Host can run
(refuse / once / sealed-args / subject / scope / hmac / empty-action / expiry).
Do not hand-edit expected fields. Refresh from runtime when the pack moves.

Phase 2 families (Ed25519, lineage, idempotency including `once-idempotent-retry`, law-generation) are in this pack and run by `test_contract_vectors` (29 ids).
Do not hand-edit expected fields. Refresh from runtime when the pack moves.
