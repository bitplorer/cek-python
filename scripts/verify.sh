#!/bin/sh
# Clone-path verify: import smoke + test files.
# Usage (from repo root):
#   sh scripts/verify.sh

set -eu
cd "$(dirname "$0")/.."

if python3 -c "import cek_host, cek_surface" >/dev/null 2>&1; then
  :
else
  export PYTHONPATH="${PYTHONPATH:-}:cek-host/src:cek-surface/src"
fi

python3 -c "from cek_host import Host; from cek_surface import Surface, Op; print('import ok')"
python3 -c "from cek_host.cap import args_hash; assert args_hash({'sku':'abc-123','qty':2})=='96e4f83e3793b646323a67f314b51044'; print('oracle ok')"
python3 cek-surface/tests/test_core.py
python3 cek-surface/tests/test_catalog.py
python3 cek-surface/tests/test_composition.py
python3 cek-surface/tests/test_stamp.py
python3 cek-surface/tests/test_phase2_stdlibs.py
python3 cek-surface/tests/test_search_stdlib.py
python3 cek-surface/tests/test_async.py
python3 cek-surface/tests/test_phase3_wrap.py
python3 cek-surface/tests/test_roadmap.py
python3 cek-surface/tests/test_carrier_ir.py
python3 cek-surface/tests/test_host_kernel.py
python3 cek-surface/tests/test_continuation_live.py
python3 cek-surface/tests/test_http_host.py
python3 cek-surface/tests/test_vectors.py
python3 cek-surface/tests/test_host_parity.py
python3 cek-surface/tests/test_layer_honesty.py
python3 cek-surface/tests/test_hardening.py
python3 cek-surface/tests/test_contract_vectors.py
python3 cek-surface/tests/test_phase2.py
python3 cek-surface/tests/test_explain_doctor.py
echo "verify ok"
