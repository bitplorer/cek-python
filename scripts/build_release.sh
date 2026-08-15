#!/usr/bin/env sh
# Build sdist + wheel for cek-host and cek-surface into dist/
# Usage (repo root): sh scripts/build_release.sh
set -eu
cd "$(dirname "$0")/.."
ROOT=$(pwd)
OUT="$ROOT/dist"
rm -rf "$OUT"
mkdir -p "$OUT"

python3 -m pip install -q build twine 2>/dev/null || true
export PATH="${HOME}/.local/bin:${PATH}"

python3 -m build --outdir "$OUT" cek-host
python3 -m build --outdir "$OUT" cek-surface
python3 -m twine check "$OUT"/*
ls -la "$OUT"
echo "build_release ok → $OUT"
