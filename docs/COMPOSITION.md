# Host composition + Peer perception

Peer logic stays on the Host. The Peer applies data and paints perception. It does not own control flow.

## Two clocks

| Clock | Where | What |
|-------|--------|------|
| **Authority** | Host `@action` → `list[Op]` | World changes under a Cap |
| **Perception** | Peer IR (`peer_ir.mjs`) | Instant UI while authority is in flight |

Perception must not write authority kv as truth. Shadows clear on the next `Result`.

## Compose Ops on the Host (control flow)

```python
from cek_surface import Surface, Op, plan, navigate_to, set_loading, Continuation

s = Surface()

@s.action("search.type")
def search_type(ctx):
    q = ctx.args.get("q") or ""
    ctx.continuations = [
        ctx.surface.mint_continuation(
            "timer.fired:search-debounce",
            "search.commit",
            args_from={"q": "store:search.pending"},
        )
    ]
    return plan(
        Op.kv_set("search.pending", q),
        *set_loading("results", True, "searching"),
    )

@s.action("go")
def go(ctx):
    return navigate_to("/home", title="Home")
```

- `plan(*ops)` concatenates lists of Ops.
- Macros (`navigate_to`, `signal_set`, `set_loading`, `form_errors`) expand to **declared-catalog pairs only**.
- `search_hits` / `search_clear` are **runtime** pairs. Call `load_bundled()` and `use_stdlibs(["baseline","ui","search"])` first; pass `stamp=ctx.surface.stamp`.
- `Surface.mint_continuation(...)` mints a continuation Cap. Peer fills slots; Host verifies again.

## Kill frontend jitter (Peer IR)

Implemented in `cek-surface/js/peer_ir.mjs`, wired in `peer.mjs` and `browser_peer.mjs`.

| Call | Effect |
|------|--------|
| `coalesceIntent(key, args, send)` | At most one Intent per key per `coalesceMs` (default 50) |
| `flush(key)` | Send now (Enter / blur) |
| `pending(target)` | Busy marker |
| `preview(target, patch)` | Optimistic paint, not authority |
| `filter(kvKey, q, out)` | Local filter over Host snapshot |
| `beforeAuthorityApply()` | Clear previews when Result lands |

From Host:

```python
s.mark_pending("search", True)
s.preview("hdr", {"text": "…"})
# later, submit() applies Result.ops and the peer clears previews
```

Browser search input uses the same IR: type → coalesce → Host action; Enter/blur → flush.
