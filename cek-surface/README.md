# cek-surface

Compose `list[Op]`. Host authorizes. Peer applies. Peer IR is perception only.

**Read [START.md](../START.md) first.** Requires `cek-host`. `EmbeddedHostKernel` is gone (D3).

PyPI **0.1.0** is the last publish. Phase 2 lives in this tree (**0.1.2**). Clone path:

```bash
git clone https://github.com/bitplorer/cek-python && cd cek-python
pip install -e ./cek-host -e ./cek-surface
python cek-surface/demo/http_host.py   # browser shop
```

```python
from cek_host import Host
from cek_surface import Surface, Op

s = Surface(kernel=Host(secret=b"dev-only-not-for-production-32!!"), carrier_kind="memory")

@s.action("hello")
def hello(ctx):
    return [Op.ui_morph("shell", {"tag": "main", "text": "hi"})]

print(s.submit("hello", {}, auto_mint=True, drain_async=False)["result"])
```

Carriers: `subprocess` (default) · `memory` · `websocket` (opt-in). Continuations are Caps, not scripts (D9).

`sh scripts/verify.sh` from the monorepo root.
