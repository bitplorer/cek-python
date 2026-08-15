# GitHub status (explicit)

Repo: **https://github.com/bitplorer/cek-python**

## On remote (2026-08-15 P0)

- `README.md`, `HANDOFF.md`, `LICENSE`, `scripts/verify.sh`, `.github/workflows/test.yml`
- Full knowledge docs under `docs/`
- `cek-host/` complete (`pyproject`, README, `src/cek_host/{__init__,cap,py.typed}`)
- `cek-surface/` **complete**:
  - `src/cek_surface/*.py` (+ `py.typed`)
  - `js/{peer,peer_ir,browser_peer}.mjs`
  - `demo/` (shop, http host, browser page, benches, WS peer)
  - `tests/` (core, roadmap, carrier_ir, host_kernel)
  - `vectors/surface_core.json`
  - README / pyproject / ARCHITECTURE

## How to verify from a clean clone

```bash
git clone https://github.com/bitplorer/cek-python
cd cek-python
pip install -e ./cek-host -e ./cek-surface
sh scripts/verify.sh
```

## History (why this was incomplete)

1. Organization and host package were prioritized for the install story.
2. Surface implementation is large; early API push was batched; credentials blocked bulk `git push`.
3. Surface was **not** emptied — remote simply never received the blobs until this P0 commit.

## Remaining publish (not P0/P1)

| Item | Status |
|------|--------|
| PyPI `cek-host` / `cek-surface` 0.1.0 | P3 — after P2 green |
| npm `@cek/peer` | Deferred (js/ under surface is enough) |
| Contract/vector alignment | P2 |
| Scripted WS demo | P2 |

