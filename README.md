# cek-python

Python workspace for **CEK** (Cap-Effect Kernel).

| Package | PyPI | Role |
|---------|------|------|
| **[cek-host](./cek-host)** | `pip install cek-host` | Host kernel — Caps, refuse → empty ops |
| **[cek-surface](./cek-surface)** | `pip install cek-surface` | Compose Ops, Peer IR, carriers (depends on cek-host) |

**Law:** [cek-framework](https://github.com/bitplorer/cek-framework)  
**Rust reference:** [cek-runtime](https://github.com/bitplorer/cek-runtime)  

See **[docs/ORGANIZATION.md](./docs/ORGANIZATION.md)** for repo layout and install story.

## Quick start

```bash
pip install -e ./cek-host
pip install -e "./cek-surface[ws]"

python -c "from cek_host import Host; from cek_surface import Surface, Op; print('ok')"
```

```python
from cek_surface import Surface, Op

s = Surface()

@s.action("ping")
def ping(ctx):
    return [Op.ui_toast("pong")]

print(s.submit("ping", {}, auto_mint=True, drain_async=False)["result"]["kind"])
s.close()
```

## Layout

```text
cek-python/
  docs/ORGANIZATION.md
  cek-host/          # authority kernel (standalone install)
  cek-surface/       # surface + js peers + demos + tests
```

## Non-goals

- Peer does not mint Caps  
- Surface does not redefine law  
- Carriers are transport only (subprocess default; websocket opt-in)
