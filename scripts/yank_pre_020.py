#!/usr/bin/env python3
"""Yank cek-host and cek-surface releases before 0.2.0.

Those wheels teach cek_host.legal. A yanked release is ignored by pip
unless the specifier is an exact pin.

Auth: PYPI_API_TOKEN, an owner token. The publish workflow uses Trusted
Publishing and cannot yank.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request

VERSIONS = ("0.1.0", "0.1.2", "0.1.3")
PROJECTS = ("cek-host", "cek-surface")
REASON = (
    "Teaches cek_host.legal and the noun S. Use 0.2.0 (cek_host.catalog). "
    "An exact pin still installs this old law; do not use it."
)


def _yank(project: str, version: str, token: str) -> tuple[int, str]:
    url = f"https://pypi.org/api/projects/{project}/{version}"
    body = json.dumps({"yanked": True, "yanked_reason": REASON}).encode()
    req = urllib.request.Request(url, data=body, method="PATCH")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    raw = base64.b64encode(f"__token__:{token}".encode()).decode()
    req.add_header("Authorization", f"Basic {raw}")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def main() -> int:
    token = os.environ.get("PYPI_API_TOKEN", "").strip()
    if not token:
        print("PYPI_API_TOKEN is required (project owner token)", file=sys.stderr)
        return 2
    failed = False
    for project in PROJECTS:
        for version in VERSIONS:
            status, body = _yank(project, version, token)
            print(f"{project} {version} -> {status}")
            if status not in (200, 204):
                print(body[:500], file=sys.stderr)
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
