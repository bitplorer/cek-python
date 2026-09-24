# cek-surface

Compose `list[Op]`. Host authorizes. Peer applies. Peer IR is perception only.

```python
from cek_host import Host
from cek_surface import Surface, Op, search_hits
from cek_surface.domain_loader import load_bundled

load_bundled()
s = Surface(kernel=Host(secret=b"dev-only-not-for-production-32!!"), carrier_kind="memory")
s.use_stdlibs(["baseline", "ui", "search"])

@s.action("hello")
def hello(ctx):
    return [Op.ui_morph("shell", {"tag": "main", "text": "hi"})]

@s.action("find")
def find(ctx):
    return [search_hits("results", [{"title": "a"}], q="a", stamp=ctx.surface.stamp)]
```

S is frozen in core. `search.hits` is a **runtime** stdlib pair — legal only after Host↔Peer agree and the stamp includes it.

Carriers: `subprocess` (default Node Peer) · `memory` · `websocket` · `kernel` (taught: in-process `cek_peer_pyo3`).

**Taught kernel:** `Surface(carrier_kind="kernel")` → `cek_peer_pyo3.PeerAbi` construct → bind → apply → release. Install from [cek-runtime](https://github.com/bitplorer/cek-runtime) (`cargo build -p cek-peer-pyo3 --features extension-module --release`; `export CEK_PEER_PYO3=.../libcek_peer_pyo3.so`). Leftover (untaught): `CEK_KERNEL_CARRIER=subprocess` still shells `cek apply`.

Chrome (perception): `s.chrome_pending("btn")` · `s.arm("timer.fired:x", "find")`.

```bash
pip install cek-surface          # pulls cek-host>=0.1.3
```
