#!/bin/sh
# Clone-path verify: import smoke + test files.
# Usage (from repo root):
#   sh scripts/verify.sh
#   # or after editable install, same command (PYTHONPATH not required)

set -eu
cd "$(dirname "$0")/.."

if python3 -c "import cek_host, cek_surface" >/dev/null 2>&1; then
  :
else
  export PYTHONPATH="${PYTHONPATH:-}:cek-host/src:cek-surface/src"
fi

python3 -c "from cek_host import Host; from cek_surface import Surface, Op; print('import ok')"
python3 cek-surface/tests/test_core.py
python3 cek-surface/tests/test_roadmap.py
python3 cek-surface/tests/test_carrier_ir.py
python3 cek-surface/tests/test_host_kernel.py
python3 cek-surface/tests/test_continuation_live.py
python3 cek-surface/tests/test_http_host.py
python3 cek-surface/tests/test_vectors.py
echo "verify ok"
