# CEK phases

## Phase 1 — closed catalog + stamp (SHIP)

Pair identity, session stamp, Host/Peer gates, domain-stdlib skeleton
(`baseline` + `ui`), structure validation, docs.

## Phase 2 — multi domain-stdlib + agreement (SHIP)

- Load `*.stdlib.json` at runtime (`cek_surface.domain_loader`)
- Versioned Host↔Peer agreement (major match)
- Stamp = union of agreed seed pairs (core S ∪ extensions)
- `Op.stamped` + `project_wire(..., stamp=)` accept extensions only on the stamp
- JS `registerDriver` applies stamped extensions (sample: `demo.echo.ping`)
- Core crates are **not** patched to add a domain

## Phase 3 — kernel wrap (SHIP)

- `cek apply` wraps **cek-peer-kernel** (via `cek-peer-wasm::apply_json`)
- `cek host-json` wraps **cek-host-kernel**
- Python `KernelPeerCarrier` (`carrier_kind="kernel"`) and `RustHostKernel`
  call those binaries — they do **not** reimplement decide/apply
- Language ports remain vector-aligned fallbacks when the binary is absent
- `cek-peer-wasm` remains the WASM wrap of the same Peer kernel (no second apply)
- Peer **kernel** apply-set is still S (Baseline / UI profile). Stamped extensions apply only in a Peer **runtime** that registered a driver

Dual implementations are **ports**, not second kernels. Default apps use the Python Host port. The wrap path is the reference kernel when `cek` is on PATH.

