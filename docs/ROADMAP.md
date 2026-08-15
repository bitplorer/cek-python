# Roadmap

## Shipped

P0 full tree · P1 live continuations · P2 vectors+WS · **P3 TestPyPI 0.1.0** · **Production PyPI 0.1.0**

## Present

| Item | Status |
|------|--------|
| TestPyPI | `cek-host` / `cek-surface` 0.1.0 live |
| **PyPI** | `cek-host` / `cek-surface` **0.1.0** live (publish-pypi #1) |
| Vectors | v3 — **20 cases** in `verify.sh` |
| Consumer smoke | `scripts/consumer_smoke_testpypi.sh` PASS |
| Production publish | `publish-pypi.yml` + envs `pypi-host` / `pypi-surface` |

## Next (optional)

| Item | Do |
|------|----|
| More vectors | Further cek-runtime family parity as needed |
| Version bump | Only when shipping `0.1.1+` (0.1.0 locked on both indexes) |

## Anti-roadmap

Peer Cap mint · Peer plan IR · ux-channel dependency · Surface-owned Cap product

## Suggested next

```text
1) Use packages: pip install cek-host cek-surface
2) Keep refuse → ops:[] / Peer no mint / fail closed
3) Bump version only for intentional releases
```
