"""OnceBackend — durable-or-memory single-use store.

I4  Once commit only after successful project (K6)
I9  Fail closed on store down (K6)
I12 Concurrent once: exactly one ok (fcntl flock on file backend)

Memory is demo. production() refuses it unless allow_memory_stores=True.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Protocol, runtime_checkable


class StoreDown(Exception):
    """Required once-store is unavailable. Host must refuse (K6)."""


class OnceUsed(Exception):
    """jti already committed."""


@runtime_checkable
class OnceBackend(Protocol):
    def ensure_available(self, jti: str) -> None: ...
    def commit(self, jti: str) -> None: ...
    def label(self) -> str: ...


class MemoryOnceBackend:
    """In-process set. Demo only — multi-worker replay succeeds."""

    def __init__(self, *, down: bool = False) -> None:
        self._used: set[str] = set()
        self._down = down
        self._lock = threading.Lock()

    def mark_down(self, down: bool = True) -> None:
        self._down = down

    def ensure_available(self, jti: str) -> None:
        if self._down:
            raise StoreDown("once store down")
        with self._lock:
            if jti in self._used:
                raise OnceUsed("once cap already used")

    def commit(self, jti: str) -> None:
        if self._down:
            raise StoreDown("once store down")
        with self._lock:
            if jti in self._used:
                raise OnceUsed("once cap already used")
            self._used.add(jti)

    def label(self) -> str:
        return "down" if self._down else "memory"


class FileOnceBackend:
    """JSON set on disk. flock + temp+rename. Fail closed if unreadable/unwritable."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self._thread = threading.Lock()
        self._lock_fp = None

    def _flock(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        if self._lock_fp is None:
            self._lock_fp = open(lock_path, "a+", encoding="utf-8")
        try:
            import fcntl

            fcntl.flock(self._lock_fp.fileno(), fcntl.LOCK_EX)
        except ImportError:
            pass

    def _funlock(self) -> None:
        if self._lock_fp is None:
            return
        try:
            import fcntl

            fcntl.flock(self._lock_fp.fileno(), fcntl.LOCK_UN)
        except ImportError:
            pass

    def _load(self) -> set[str]:
        if not self.path.exists():
            return set()
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw or "[]")
        except (OSError, json.JSONDecodeError) as e:
            raise StoreDown(f"once store down: {e}") from e
        if not isinstance(data, list):
            raise StoreDown("once store down: corrupt")
        return {str(x) for x in data}

    def _save(self, used: set[str]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp.write_text(json.dumps(sorted(used)), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError as e:
            raise StoreDown(f"once store down: {e}") from e

    def ensure_available(self, jti: str) -> None:
        with self._thread:
            self._flock()
            try:
                if jti in self._load():
                    raise OnceUsed("once cap already used")
            finally:
                self._funlock()

    def commit(self, jti: str) -> None:
        with self._thread:
            self._flock()
            try:
                used = self._load()
                if jti in used:
                    raise OnceUsed("once cap already used")
                used.add(jti)
                self._save(used)
            finally:
                self._funlock()

    def label(self) -> str:
        return "file"
