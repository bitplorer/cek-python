#!/usr/bin/env sh
# Publish 0.1.0 artifacts to TestPyPI.
#
# Auth (one of):
#   1) Trusted Publishing from GitHub Actions (preferred) — see .github/workflows/publish-testpypi.yml
#   2) API token:
#        export TWINE_USERNAME=__token__
#        export TWINE_PASSWORD=pypi-...   # TestPyPI token
#
# Usage (repo root):
#   sh scripts/build_release.sh
#   sh scripts/publish_testpypi.sh
set -eu
cd "$(dirname "$0")/.."
export PATH="${HOME}/.local/bin:${PATH}"

if [ ! -d dist ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
  sh scripts/build_release.sh
fi

python3 -m twine upload --repository testpypi dist/*
echo "published to https://test.pypi.org/ — try:"
echo "  pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ cek-host==0.1.0 cek-surface==0.1.0"
