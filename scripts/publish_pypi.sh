#!/usr/bin/env sh
# Publish cek-host then cek-surface to PyPI (or TestPyPI).
#   REPO=testpypi sh scripts/publish_pypi.sh     # default
#   REPO=pypi     sh scripts/publish_pypi.sh     # needs TWINE_PASSWORD
set -eu
cd "$(dirname "$0")/.."
export PATH="${HOME}/.local/bin:${PATH}"
REPO="${REPO:-testpypi}"

if [ ! -d dist ] || [ -z "$(ls -A dist 2>/dev/null || true)" ]; then
  sh scripts/build_release.sh
fi

if [ -z "${TWINE_PASSWORD:-}" ] && [ -z "${TWINE_USERNAME:-}" ]; then
  echo "No twine credentials. Built dist/ only. Set TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-..." >&2
  ls -l dist
  exit 2
fi

python3 -m twine upload --repository "$REPO" dist/*
echo "published $REPO"
