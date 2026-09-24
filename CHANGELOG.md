# Changelog

## 0.2.0 — 2026-09-24

Breaking. `cek-host` and `cek-surface` publish together.

Versions before 0.2.0 (`0.1.0`, `0.1.2`, `0.1.3`) teach `cek_host.legal` and the noun "S".
They are not this law. Do not install them.
PyPI has no yank API. Mark `0.1.0`, `0.1.2`, and `0.1.3` yanked on each project's release page.
Until that mark is on the index, pip can still select those wheels when 0.2.0 does not match the specifier.
An exact pin (`==0.1.3`) installs that old law even after the yank. Do not use it.

### Removed

- Module `cek_host.legal`.
- Public names `is_legal`, `LEGAL_PAIRS`, `LEGAL_FQS`, `IllegalOp`, `DEMO_SECRET`.
- `Host.demo`, `mode="demo"`, `mode="production"`.

### Renamed

| 0.1.3 | 0.2.0 |
|---|---|
| `cek_host.legal` | `cek_host.catalog` |
| `is_legal` | `in_catalog` |
| `LEGAL_PAIRS` / `LEGAL_FQS` | `CATALOG_PAIRS` / `CATALOG_FQS` |
| `IllegalOp` | `UndeclaredPair` |
| `DEMO_SECRET` | `DEV_SECRET` |
| `Host.demo` / `mode="demo"` | `Host.dev` / `mode="dev"` |
| `mode="production"` | `Host.prod` / `mode="prod"` |
| `Surface.arm` | `Surface.mint_continuation` |

There is no law noun `S`.

### Behavior

- A shared-world op requires a verified Cap. `require_cap=False` refuses.
- A once-Cap is consumed before lineage or an idempotent record (CORE 08, CORE 26). Store down refuses and writes no second row.
- A refusal, a drain, or an idempotent replay does not arm or republish a new once-Cap.
- Missing session stamp: open mode projects the declared catalog. Strict mode projects Baseline only.
- `project_wire(..., stamp=)` is keyword-only.
