# Roadmap

## Shipped

P0 full tree · P1 live continuations · P2 vectors+WS · **P3 TestPyPI 0.1.0**

## Present

| Item | Status |
|------|--------|
| TestPyPI | `cek-host` / `cek-surface` 0.1.0 live |
| Vectors | v3 — **20 cases** in `verify.sh` |
| Consumer smoke | `scripts/consumer_smoke_testpypi.sh` PASS |
| Production PyPI path | `publish-pypi.yml` + [PYPI_SETUP.md](./PYPI_SETUP.md) ready |

## Next

| Item | Do |
|------|----|
| Production PyPI | Create `pypi-host` / `pypi-surface` envs + publishers → Run `publish-pypi` |
| More vectors | Optional further cek-runtime family parity |

## Anti-roadmap

Peer Cap mint · Peer plan IR · ux-channel dependency · Surface-owned Cap product

## Suggested next

```text
1) Production PyPI: PYPI_SETUP.md → Run publish-pypi
2) Keep refuse → ops:[] / Peer no mint / fail closed
```
