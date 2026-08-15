# TESTING — green means

**Read [START.md](../START.md) first.**

| Command | Green means |
|---------|-------------|
| `sh scripts/verify.sh` | Import + oracle + 12 test files. Default fast gate. |
| `python -c "from cek_host.cap import args_hash; assert args_hash({'sku':'abc-123','qty':2})=='96e4f83e3793b646323a67f314b51044'"` | Dual-language sealed-args oracle. |
| `python cek-surface/tests/test_host_parity.py` | A (demo) ≡ B (adapt) on refuse / once / sealed-args / oracle. |
| `python cek-surface/tests/test_layer_honesty.py` | D3 + D4. EmbeddedHostKernel gone. `ux_channel` import graph is []. |
| `python cek-surface/tests/test_hardening.py` | production() refuses default secret + memory once. subject/scope/store-down/attenuate. |
| `python cek-surface/tests/test_contract_vectors.py` | Aligned refuse/once/sealed/subject/scope/digest family on published Host. |
| `python cek-surface/tests/test_vectors.py` | Surface shop pack v3 (20 cases). |
| `python -m cek_host doctor --fail` | **Expected FAIL** on a demo Host (default secret). PASS on `Host.production(...)`. |
| `python -m cek_host create-app /tmp/x && python /tmp/x/app.py` | Scaffold is a running app. |

`verify-sec` (chaos / soak / once replay under load) is **not** in the default fast gate. Run `python cek-surface/demo/bench_load_chaos.py` separately.

Rust (if you touched `cek-runtime` crates or vectors):

```bash
cargo test --workspace
cargo run -p cek-cli -- demo
./scripts/invariants.sh
```
