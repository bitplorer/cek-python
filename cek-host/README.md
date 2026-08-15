# cek-host

Python **Host kernel** — the published Cap machine. Peers never mint.

**Read [START.md](../START.md) first.** Tree is **0.1.1**. Indexes are still **0.1.0** (no `create-app` on PyPI yet).

```bash
git clone https://github.com/bitplorer/cek-python && cd cek-python
pip install -e ./cek-host -e ./cek-surface
python -m cek_host create-app ./hello && python ./hello/app.py
python -m cek_host doctor --fail
python -m cek_host explain "once cap already used"
```

```python
from cek_host import Host, FileOnceBackend
import secrets

host = Host.production(secrets.token_bytes(32), FileOnceBackend("once.json"))
cap = host.mint("Cart.add", once=True, args={"sku": "abc-123", "qty": 2}, seal_args=True)
r = host.submit(action="Cart.add", args={"sku": "abc-123", "qty": 2}, cap=cap, project_ops=[])
# refuse ⇒ r.ops == [] and r.digest.startswith("cek1:")
```

`Host()` is **demo** (memory once, default secret allowed). `Host.production()` refuses both.

Oracle: `args_hash({"sku":"abc-123","qty":2}) == 96e4f83e3793b646323a67f314b51044`
