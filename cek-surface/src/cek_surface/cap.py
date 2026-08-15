"""Re-export Caps from cek-host. Surface does not own Cap policy."""
from __future__ import annotations

try:
    from cek_host.cap import CapError, CapService
except ImportError:  # pragma: no cover
    # fallback only if installed without cek-host (not recommended)
    raise ImportError("cek-surface requires cek-host: pip install cek-host") from None

__all__ = ["CapError", "CapService"]
