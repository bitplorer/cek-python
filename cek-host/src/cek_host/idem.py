"""IdemBackend — same key + same digest replays; different body refuses (I5, I6, I18)."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .digest import result_digest
from .once import StoreDown


class IdemConflict(Exception):
    """Same idempotency key, different body."""


@runtime_checkable
class IdemBackend(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...
    def put_or_check(self, key: str, digest: str, result: dict[str, Any]) -> dict[str, Any] | None: ...
    def label(self) -> str: ...


class MemoryIdemBackend:
    def __init__(self, *, down: bool = False) -> None:
        self._data: dict[str, dict[str, Any]] = {}
        self._down = down
        self._lock = threading.Lock()

    def mark_down(self, down: bool = True) -> None:
        self._down = down

    def get(self, key: str) -> dict[str, Any] | None:
        if self._down:
            raise StoreDown("idempotency store down")
        with self._lock:
            rec = self._data.get(key)
            return dict(rec["result"]) if rec else None

    def put_or_check(self, key: str, digest: str, result: dict[str, Any]) -> dict[str, Any] | None:
        if self._down:
            raise StoreDown("idempotency store down")
        with self._lock:
            prev = self._data.get(key)
            if prev is None:
                self._data[key] = {"digest": digest, "result": dict(result)}
                return None
            if prev["digest"] == digest:
                return dict(prev["result"])
            raise IdemConflict(f"idempotency conflict for key `{key}`")

    def label(self) -> str:
        return "down" if self._down else "memory"


class FileIdemBackend:
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

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8") or "{}")
        except (OSError, json.JSONDecodeError) as e:
            raise StoreDown(f"idempotency store down: {e}") from e
        if not isinstance(data, dict):
            raise StoreDown("idempotency store down: corrupt")
        return data

    def _save(self, data: dict[str, Any]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp.write_text(json.dumps(data), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError as e:
            raise StoreDown(f"idempotency store down: {e}") from e

    def get(self, key: str) -> dict[str, Any] | None:
        with self._thread:
            self._flock()
            try:
                rec = self._load().get(key)
                return dict(rec["result"]) if rec else None
            finally:
                self._funlock()

    def put_or_check(self, key: str, digest: str, result: dict[str, Any]) -> dict[str, Any] | None:
        with self._thread:
            self._flock()
            try:
                data = self._load()
                prev = data.get(key)
                if prev is None:
                    data[key] = {"digest": digest, "result": dict(result)}
                    self._save(data)
                    return None
                if prev.get("digest") == digest:
                    return dict(prev["result"])
                raise IdemConflict(f"idempotency conflict for key `{key}`")
            finally:
                self._funlock()

    def label(self) -> str:
        return "file"


def digest_of_ok(ops: list[Any]) -> str:
    return result_digest("ok", ops, None)
