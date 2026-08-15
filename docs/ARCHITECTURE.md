# Architecture (cek-python)

**Read [START.md](../START.md) first.**


## Layer diagram

```text
┌─────────────────────────────────────────────────────────────┐
│  App (Python)                                                 │
│  @action handlers → list[Op]                                  │
│  macros = Python functions (never on the wire)              │
└────────────────────────────┬────────────────────────────────┘
                             │ Intent + Cap
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  cek-host (authority)                                         │
│  mint / verify / once / sealed-args                           │
│  refuse → Result.ops = []                                     │
│  package projected ops into Result                            │
└────────────────────────────┬────────────────────────────────┘
                             │ Result (ops only)
                             │ optional continuation envelopes
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Carrier (transport only)                                     │
│  default: subprocess NDJSON                                   │
│  opt-in: memory | websocket                                   │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Peer (JS)                                                    │
│  apply Result.ops via closed drivers                          │
│  emit events (timer.fired, http.response)                     │
│  Peer IR: shadow / coalesce / flush / filter_cached           │
│  NEVER mint Caps                                              │
└─────────────────────────────────────────────────────────────┘
```

## Two clocks

| Clock | Owner | Allowed effects |
|-------|--------|-----------------|
| **Authority** | Host | World-changing Ops under Cap |
| **Perception** | Peer IR | pending, shadow morph, coalesce Intent, toast fade, filter over Host snapshot |

Rule: perception must not enlarge the set of states the next Cap would reject.

## Wire contract (carrier-agnostic)

Messages (JSON):

| type | Direction | Meaning |
|------|-----------|---------|
| `apply` | Host → Peer | `{ result: { kind, ops, error } }` |
| `applied` | Peer → Host | receipt + world snapshot |
| `chrome` | Host → Peer | perception-only (pending, shadow, …) |
| `chrome_applied` | Peer → Host | chrome ack |
| `events` | Peer → Host | timer/http/… |
| `done` | Host → Peer | shutdown |

## Op catalog (surface)

Namespaces used in practice: `kv.*`, `ui.dom.*`, `ui.*`, `nav.*`, `http.*`, `timer.*`, `signal.*`, `log.*`, `sys.noop`.

Host macros (`fetch_json`, `navigate_to`, `restart_timer`, …) expand to those Ops in Python — they never appear as Peer recipes.

## Continuations

Host may attach:

```text
event → action + pre-minted Cap + args_from slots
```

Peer fills slots and submits Intent; Host verifies again. Not Peer-side business logic.

## Dependency rule

```text
cek-surface → cek-host → (law is documentation in cek-framework)
cek-surface does NOT depend on ux-channel
Peers do NOT depend on cek-host for mint
```
