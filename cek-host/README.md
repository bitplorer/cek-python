# cek-host

Python **Host runtime** — mint, verify, project. Peers never mint.

Not a wrap of the Rust kernel unless you use `RustHostKernel`.

```python
from cek_host import Host

host = Host(secret=b"dev-only-not-for-production-32!!")
cap = host.mint("hello", once=True)
r = host.submit(
    action="hello",
    args={},
    cap=cap,
    project_ops=[{"ns": "log", "name": "append", "payload": {"message": "hi"}}],
)
assert r.kind == "ok" and r.digest.startswith("cek1:")
```

Refuse → `r.ops == []`. Illegal pair → `dispatch_error`, never silent `ok`.

S (core) = `kv.set` `kv.delete` `log.append` `ui.dom.morph` `ui.dom.restore`.  
Pair = `(ns, name)`. Stamp = this session. FQ is display only.

`Host()` is demo. `Host.production(secret, FileOnceBackend(...))` refuses the demo secret and memory stores.

```bash
pip install cek-host
python -m cek_host explain "once cap already used"
```

Law: [cek-framework](https://github.com/bitplorer/cek-framework) · Kernels: [cek-runtime](https://github.com/bitplorer/cek-runtime) · Surface: `pip install cek-surface`
