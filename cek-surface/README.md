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

## Verify from this monorepo

```bash
# from repo root
pip install -e ../cek-host -e ".[ws]"   # or: pip install -e ./cek-host -e ./cek-surface
python -c "from cek_host import Host; from cek_surface import Surface, Op; print('ok')"
python tests/test_core.py
python tests/test_roadmap.py
python tests/test_carrier_ir.py
python tests/test_host_kernel.py
```

From repo root the one-liner is `sh scripts/verify.sh` (includes live continuation + HTTP Host tests).

Browser shop (real Host, no `?mock=1`):

```bash
python demo/http_host.py
# Peer IR coalesces search; timer.fired submits the pre-minted search.commit Cap
```

