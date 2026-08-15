# GitHub status (explicit)

Repo: **https://github.com/bitplorer/cek-python**

## On remote

- Docs knowledge base + ORGANIZATION
- `cek-host/` complete
- `cek-surface/` packaging stubs (README, pyproject, ARCHITECTURE)
- **Missing:** `cek-surface/src/**`, `js/**`, `demo/**`, `tests/**`, `vectors/**` until P0 push completes

## Local complete tree

`artifacts/cek-python/` has full implementation. Surface was never deleted — remote never received the blobs.

## Why surface looked empty

API batch publish prioritized org + host; HTTPS git push lacked credentials in the agent environment.
