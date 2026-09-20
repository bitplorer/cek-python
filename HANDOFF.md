# HANDOFF — next agent

**Read [START.md](./START.md) first.** Glossary: [docs/CATALOG_AUTHORITY_TARGET.md](docs/CATALOG_AUTHORITY_TARGET.md). Compose: [docs/COMPOSITION.md](docs/COMPOSITION.md). Invariants: [docs/INVARIANTS.md](docs/INVARIANTS.md).

**Date:** 2026-09-19  
**Repo:** https://github.com/bitplorer/cek-python (tree **0.1.3**)  
**Law:** https://github.com/bitplorer/cek-framework  
**Rust:** https://github.com/bitplorer/cek-runtime

S = frozen core (5 pairs). Stamp = session set. FQ is display only. Peer kernel applies S; extensions need a runtime driver.

```bash
export PYTHONPATH=cek-host/src:cek-surface/src
sh scripts/verify.sh
# taught kernel carrier (in-process PyO3 — not a second Peer kernel)
cargo build -p cek-peer-pyo3 --features extension-module --release \
  --manifest-path ../cek-runtime/Cargo.toml
export CEK_PEER_PYO3=../cek-runtime/target/release/libcek_peer_pyo3.so
python3 cek-surface/tests/test_kernel_peer.py
# leftover Host wrap + untaught `cek apply` door
cargo build -p cek-cli --manifest-path ../cek-runtime/Cargo.toml
CEK_BIN=../cek-runtime/target/debug/cek python3 cek-surface/tests/test_phase3_wrap.py
```

NEVER REGRESS: refuse → `ops: []` · Peer no mint · once/sealed fail closed · no EmbeddedHostKernel · digest `cek1:` · undeclared pair → `IllegalOp` · stamp membership is pair identity · loaded stdlibs cannot claim `core=true` · wrap path does not reimplement apply/decide · taught kernel carrier is `cek_peer_pyo3` (not subprocess `cek apply`).
