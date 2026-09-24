# Catalog authority — locked model

**Status:** implemented. Default catalog mode is `open`.

## One sentence

> Core signs stable contracts, freezes Baseline, and enforces consistent domain+driver structure; domain growth lives in runtime domain stdlibs; Host and Peer agree on the domain stdlibs they share; Host stamps the closed pair set; both sides honor only that stamp.

The letter **S** was a nickname for the declared catalog. It was not "shared world".

**Shared world** (CORE 14) is any effect a Peer applies: `Result.ops`. That needs a verified Cap. It is not a list of five names.

**Declared catalog** is which `(ns, name)` pairs this build knows. **Session stamp** is which of those this session may project.

| Name | Meaning | Who owns it |
|------|---------|-------------|
| **pair** | `(ns, name)` — the membership key. `name` is one token (no dots). | wire + catalogs |
| **FQ** | `ns.name` display/serialization only. Never the identity key. | wire |
| **Baseline** | `("kv","set")` `("kv","delete")` `("log","append")`. Never grows. | core |
| **UI seed** | `("ui.dom","morph")` `("ui.dom","restore")`. Domain pack `ui.dom`. | core |
| **declared catalog** | Baseline ∪ UI seed. Five pairs. Python: `LEGAL_PAIRS`. JS frozen spelling: `S_PAIRS`. There is no law noun "S". | `cek-contract` + `cek_host.legal` |
| **domain stdlib** | Versioned runtime module with seed pairs. Core ones: `baseline`, `ui`. | runtime (`cek_surface`) |
| **session stamp** | Closed pair set for **one session**. Subset of the declared catalog, or that catalog plus an agreed extension. | Host builds, Peer honors |
| **Host runtime** | Language port of decide (Python `cek-host`). | not the Rust kernel unless wrap is used |
| **Host kernel** | Rust `cek-host-kernel` (reference decide). | `cek-runtime` |
| **Peer kernel** | Rust `cek-peer-kernel` (reference apply). | `cek-runtime` |
| **Peer runtime** | Language port / carrier that **wraps** apply (JS `apply_s`, or `cek_peer_pyo3`). | must not reimplement decide |

## Pair identity

`("ui.dom", "morph")` is legal. `("ui", "dom.morph")` is not — same FQ string, different pair.

Tokens: lowercase ASCII letters and digits only. Dots belong in `ns`, never in `name`.

## Two legality questions (do not mix)

1. **Is it in the declared catalog?** — `is_legal`. This is not "lawful for this session".
2. **Is it in this session's stamp?** — what Host may project and what a JS Peer may apply. `in_stamp`.

- No stamp + `open` → declared catalog (Baseline ∪ UI seed).
- No stamp + `strict` (`CEK_CATALOG_MODE=strict`) → Baseline only.
- Stamp present → **only** the stamp (via negativa). Runtime stdlib pairs (e.g. `search.hits`) may appear here without being in the declared catalog.

Bundled stdlibs in `cek-surface`: `search` (`hits`, `clear`). Load with `load_bundled()`, then `Surface.use_stdlibs(["baseline","ui","search"])`.

## Handshake

In-process agreement (`negotiate`) picks stdlibs. Then:

```text
Host → Peer  { "type": "stamp", "pairs": [{ "ns", "name" }, ...] }
Peer → Host  { "type": "stamp_ack", "pairs": [...] }
```

There is no on-the-wire `agree` message. Version intersection happens in the Host runtime before the stamp is sent.

## What each apply path will actually apply

| Path | Applies |
|------|---------|
| JS `apply_s.mjs` | Stamp ∩ (built-in catalog drivers ∪ `registerDriver`). Filename is a frozen spelling. |
| Rust `cek-peer-kernel` / `cek_peer_pyo3` / leftover `cek apply` | **Declared catalog only** (Baseline or Baseline+UI profile). Extensions are skipped. |
| Memory carrier | Echoes ops (tests). Not a kernel. |

So: Host can *project* a stamped extension; only a Peer **runtime with a driver** will *apply* it. The Peer **kernel** never grows drivers for day-to-day domains.

## Phase 3 wrap (honest)

Taught Python kernel carrier: `carrier_kind="kernel"` → in-process `cek_peer_pyo3` (`PeerAbi` construct → bind → apply → release; same JSON as wasm). Fail closed if the module is missing.

**Leftover (untaught):** `CEK_KERNEL_CARRIER=subprocess` / `backend="subprocess"` still shells `cek apply`. `cek host-json` / `RustHostKernel` remain the Host wrap. Dual implementations are **ports**, not a third kernel.

Default `Surface()` still uses the Python Host port + JS Peer port. That is deliberate: apps do not require a `cek` binary or `cek_peer_pyo3`.

## Catalog mode

- `CEK_CATALOG_MODE=open` (default) — missing stamp = declared catalog
- `CEK_CATALOG_MODE=strict` — missing stamp = Baseline
