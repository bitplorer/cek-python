# cek-surface architecture

**Read [../START.md](../START.md) first.**


## Product boundary (frozen)

| Layer | Package | Owns |
|-------|---------|------|
| **Host kernel** | `cek-host` only | mint, verify, once, sealed-args, package Result |
| **Surface** | **cek-surface** | Op constructors bound to S, actions, events, Peer apply, chrome IR, coalesce, policy hooks |
| **Law / contract** | cek-framework + cek-contract | schemas, vectors, Baseline Ops |
| **ux-channel** | — | **not a dependency** |

```text
Composition  = Python actions → list[Op]
Authority    = Host kernel under Caps
Wire         = Result.ops (+ optional continuation envelopes)
Peer         = closed apply + perception IR (shadow, coalesce, reducers)
```

## Non-goals

- No Peer Cap mint
- No Peer recipe registry / eval
- No second plan IR on the wire
- No ux-channel import
- No product growth of surface `CapService` (D3 — `cek-host` owns Caps)

## Peer IR (perception only)

Safe: `pending`, `filter_cached`, `toast_fade`, shadow morph, Intent coalesce.
Banned: inventing entitlements, writing authority kv, policy `if`.

## Continuations

Host may attach pre-minted attenuated Caps + Intent templates to Results.
Peer fills declared slots and submits — Host still verifies and projects.

## Carrier (transport)

Plug-and-play, **opt-in**, not a kernel.

| kind | Module | When |
|------|--------|------|
| **subprocess** (default) | `SubprocessNdjsonCarrier` | demos, CI, zero deps |
| **memory** | `MemoryCarrier` | unit tests, same-process |
| **websocket** | `WebSocketCarrier` | production browser Peer (`pip install websockets`) |

```python
from cek_surface import Surface, open_carrier

s = Surface()  # default subprocess peer.mjs

s = Surface(carrier_kind="memory")
s = Surface(carrier_kind="websocket", carrier_opts={"url": "ws://127.0.0.1:8765"})
```

Message shapes are identical across carriers: `apply` / `chrome` / `events` / `done`.
