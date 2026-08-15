# cek-host

Python **Host kernel** for CEK: mint/verify Caps, package projected Ops into Results.

```bash
pip install cek-host
# or from monorepo: pip install -e ./cek-host
```

```python
from cek_host import Host

host = Host(secret=b"...")
cap = host.mint("Cart.add", once=True)
result = host.submit(action="Cart.add", args={...}, cap=cap, project_ops=[...])
# result.kind == "ok" | "authority_refusal"; refuse ⇒ ops=[]
```

Peers and browsers **never** mint. See [ORGANIZATION](../docs/ORGANIZATION.md).
