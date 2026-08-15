#!/usr/bin/env sh
# Install cek-host + cek-surface from TestPyPI into a clean target and smoke.
# Usage: sh scripts/consumer_smoke_testpypi.sh
set -eu
cd "$(dirname "$0")/.."
TARGET="${TMPDIR:-/tmp}/cek-consumer-smoke-$$"
rm -rf "$TARGET"
mkdir -p "$TARGET"
python3 -m pip install -q \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  --target "$TARGET" \
  'cek-host==0.1.0' 'cek-surface==0.1.0'
PYTHONPATH="$TARGET" python3 - <<'PY'
from cek_host import Host
from cek_surface import Surface, Op

h = Host(secret=b"consumer-smoke-secret-32b!!!!!")
tok = h.mint("demo.ping", once=True)
ok = h.submit(
    action="demo.ping",
    args={},
    cap=tok,
    project_ops=[{"ns": "sys", "name": "noop", "payload": {}}],
)
assert ok.kind == "ok", ok
refuse = h.submit(action="demo.ping", args={}, cap=None, project_ops=[])
assert refuse.kind == "authority_refusal" and refuse.ops == [], refuse
op = Op(ns="kv", name="set", payload={"key": "x", "value": 1})
assert op.ns == "kv"
print("consumer smoke OK (TestPyPI packages)")
PY
rm -rf "$TARGET"
echo "consumer_smoke_testpypi ok"
