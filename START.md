# START — zero → first morph in one file

**Read this first.** Encyclopedia lives under `docs/`. Law is [cek-framework](https://github.com/bitplorer/cek-framework). Rust reference is [cek-runtime](https://github.com/bitplorer/cek-runtime).

```text
mint Cap → submit Intent {action, args, cap} → verify → project Ops → Result {kind, ops[]}
```

## One command (from this tree — this is the working path today)

PyPI still has `0.1.0` (no `create-app`). Phase 2 lives in this repo as **tree 0.1.2** until the next publish.

```bash
git clone https://github.com/bitplorer/cek-python
cd cek-python
pip install -e ./cek-host -e ./cek-surface
python -m cek_host create-app ./hello-cek && python ./hello-cek/app.py
```

Timed (clean venv, editable install → first morph): **7.3 s**. Budget is 5 minutes.

That prints a `ui.dom.morph` Result, then a once-replay refuse with `ops: []`.

## One file (no scaffold)

```python
from cek_host import Host
from cek_surface import Op, Surface

host = Host(secret=b"dev-only-not-for-production-32!!")
s = Surface(kernel=host, carrier_kind="memory")

@s.action("hello")
def hello(ctx):
    return [Op.ui_morph("shell", {"tag": "main", "text": "hello, cek"})]

cap = host.mint("hello", once=True)
print(s.submit("hello", {}, cap=cap, drain_async=False)["result"])
```

## Go / no-go

```bash
python -m cek_host doctor --production-demo --fail   # expect FAIL (default secret + memory)
python -m cek_host explain "cap required"
sh scripts/verify.sh
```

Production: `Host.production(secret=secrets.token_bytes(32), once=FileOnceBackend("once.json"))` — also stands up FileIdem + FileLineage beside the once file. BoundAsk is not constructible. `end_activity` reverses landed-first.

Shop (browser is the Peer): `python cek-surface/demo/http_host.py`

Next: [docs/INVARIANTS.md](docs/INVARIANTS.md) · [docs/DECISIONS.md](docs/DECISIONS.md) · [docs/S_TIER_SCORECARD.md](docs/S_TIER_SCORECARD.md)
