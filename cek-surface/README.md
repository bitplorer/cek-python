# cek-surface

CEK **surface** runtime: Python actions compose `list[Op]`; Host kernel authorizes; Peer applies; Peer IR handles perception (coalesce, shadow).

```bash
pip install cek-surface          # installs cek-host too
pip install "cek-surface[ws]"  # optional WebSocket carrier
```

Requires **cek-host** for Caps. See [ORGANIZATION](../docs/ORGANIZATION.md).

## Features

- Op catalog (kv, ui, nav, http, timer, signal, log)
- Portable carriers: `subprocess` (default), `memory`, `websocket`
- Peer IR: coalesce / flush / shadow / filter_cached
- Continuations, policy hooks, shop demo, benches

```python
from cek_surface import Surface, Op, open_carrier

s = Surface()  # Host via cek_host; Peer via subprocess peer.mjs
```

Source layout: `src/cek_surface/`, `js/`, `demo/`, `tests/`.
