# Catalog authority — locked model

**Status:** implemented. Default catalog mode is `open`.

## One sentence

> Core signs stable contracts, freezes Baseline, and enforces consistent domain+driver structure; domain growth lives in runtime domain stdlibs; Host and Peer agree on the domain stdlibs they share; Host stamps the closed pair set; both sides honor only that stamp.

## Glossary (use these names only)

| Name | Meaning | Who owns it |
|------|---------|-------------|
| **pair** | `(ns, name)` — the legality key. `name` is one token (no dots). | wire + catalogs |
| **FQ** | `ns.name` display/serialization only. Never the identity key. | wire |
| **S** | Frozen **core** set: Baseline ∪ UI seed. Five pairs. | `cek-contract` + `cek_host.legal` |
| **Baseline** | `("kv","set")` `("kv","delete")` `("log","append")` | core, never grows |
| **UI seed** | `("ui.dom","morph")` `("ui.dom","restore")` | core Domain pack `ui.dom` |
| **domain stdlib** | Versioned runtime module with seed pairs. Core ones: `baseline`, `ui`. | runtime (`cek_surface`) |
| **stamp** | Closed pair set for **one session**. Subset or extension of S after agreement. | Host builds, Peer honors |
| **Host runtime** | Language port of decide (Python `cek-host`). | not the Rust kernel unless wrap is used |
| **Host kernel** | Rust `cek-host-kernel` (reference decide). | `cek-runtime` |
| **Peer kernel** | Rust `cek-peer-kernel` (reference apply). | `cek-runtime` |
| **Peer runtime** | Language port / carrier that **wraps** apply (JS `apply_s`, or `cek apply`). | must not reimplement decide |

## Pair identity

`("ui.dom", "morph")` is legal. `("ui", "dom.morph")` is not — same FQ string, different pair.

Tokens: lowercase ASCII letters and digits only. Dots belong in `ns`, never in `name`.

## Two legality questions (do not mix)

1. **Is it in S?** — core declaration. `is_legal` / `is_legal_pair`.
2. **Is it in this session's stamp?** — what Host may project and what a JS Peer may apply.

- No stamp + `open` → treat as S.
- No stamp + `strict` (`CEK_CATALOG_MODE=strict`) → Baseline only.
- Stamp present → **only** the stamp (via negativa). Runtime stdlib pairs (e.g. `search.hits`) may appear here without being in S.

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
| JS `apply_s.mjs` | Stamp ∩ (built-in S drivers ∪ `registerDriver`) |
| Rust `cek-peer-kernel` / `cek apply` | **S only** (Baseline or Baseline+UI profile). Extensions are skipped. |
| Memory carrier | Echoes ops (tests). Not a kernel. |

So: Host can *project* a stamped extension; only a Peer **runtime with a driver** will *apply* it. The Peer **kernel** never grows drivers for day-to-day domains.

## Phase 3 wrap (honest)

`cek apply` and `cek host-json` wrap the Rust kernels. Python `carrier_kind="kernel"` and `RustHostKernel` call those binaries.

Default `Surface()` still uses the Python Host port + JS Peer port. That is deliberate: apps do not require a `cek` binary. Dual implementations are **ports**, not a third kernel.

## Catalog mode

- `CEK_CATALOG_MODE=open` (default) — missing stamp = S
- `CEK_CATALOG_MODE=strict` — missing stamp = Baseline
