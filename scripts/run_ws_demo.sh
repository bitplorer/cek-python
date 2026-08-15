#!/usr/bin/env sh
# One-command WS Peer demo for cek-surface.
# From repo root:
#   sh scripts/run_ws_demo.sh
set -e
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT"
export PYTHONPATH="${ROOT}/cek-host/src:${ROOT}/cek-surface/src${PYTHONPATH:+:$PYTHONPATH}"

# ensure node ws module
if [ ! -d "$ROOT/cek-surface/node_modules/ws" ]; then
  (cd "$ROOT/cek-surface" && npm install ws --no-save)
fi

# ensure python websockets
python3 -c "import websockets" 2>/dev/null || pip3 install -q websockets

python3 "$ROOT/cek-surface/demo/ws_demo.py"
