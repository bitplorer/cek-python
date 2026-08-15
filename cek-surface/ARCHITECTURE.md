# cek-surface architecture

## Product boundary (frozen)

| Layer | Package | Owns |
|-------|---------|------|
| **Host kernel** | **cek-host** | mint, verify, once, sealed-args, package Result |
| **Surface** | **cek-surface** | Op catalog, actions, events, Peer drivers, chrome IR, coalesce, policy, carriers |
| **Law / contract** | cek-framework + cek-runtime contract | schemas, vectors |
| **ux-channel** | — | **not a dependency** |

```text
Composition  = Python actions → list[Op]
Authority    = Host kernel under Caps
Wire         = Result.ops (+ optional continuation envelopes)
Peer         = closed apply + perception IR (shadow, coalesce, reducers)
```

## Carriers (opt-in transport)

| kind | Default | Deps |
|------|---------|------|
| subprocess | yes | Node peer.mjs |
| memory | tests | none |
| websocket | opt-in | websockets |

## Non-goals

- No Peer Cap mint
- No Peer recipe registry / eval
- No second plan IR on the wire
- No ux-channel import
