"""LineageBackend — Activity commit + honest reverse (I7, I11, I15, I16).

Reverse preference: landed Ops (receipt) first, else inverse recorded at commit.
NonReversible listed, never faked.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .once import StoreDown


class LineageError(Exception):
    """Lineage rule failure (already ended, empty id). Not a store-down."""

INVERSE = "inverse"
NON_REVERSIBLE = "non_reversible"


def inverse_ops(ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """kv.set → kv.delete; kv.delete+prior → kv.set; ui.dom.morph+snapshot → restore."""
    inv: list[dict[str, Any]] = []
    for op in reversed(ops):
        ns, name = op.get("ns"), op.get("name")
        payload = dict(op.get("payload") or {})
        if ns == "kv" and name == "set":
            key = payload.get("key")
            if key:
                inv.append({"ns": "kv", "name": "delete", "payload": {"key": key}})
        elif ns == "kv" and name == "delete" and "prior" in payload:
            key = payload.get("key")
            if key:
                inv.append(
                    {"ns": "kv", "name": "set", "payload": {"key": key, "value": payload["prior"]}}
                )
        elif ns == "ui.dom" and name == "morph" and "snapshot" in payload:
            target = payload.get("target")
            if target:
                inv.append(
                    {
                        "ns": "ui.dom",
                        "name": "restore",
                        "payload": {"target": target, "snapshot": payload["snapshot"]},
                    }
                )
    return inv


def reverse_class_for(ops: list[dict[str, Any]]) -> str:
    return INVERSE if inverse_ops(ops) else NON_REVERSIBLE


@dataclass
class ReverseOutcome:
    ops: list[dict[str, Any]] = field(default_factory=list)
    non_reversible: list[str] = field(default_factory=list)
    used_landed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ops": self.ops,
            "non_reversible": self.non_reversible,
            "used_landed": self.used_landed,
        }


@runtime_checkable
class LineageBackend(Protocol):
    def commit(
        self,
        cap_id: str,
        activity_id: str | None,
        action: str,
        authorized_ops: list[dict[str, Any]],
        reverse_class: str,
        inverse: list[dict[str, Any]],
    ) -> dict[str, Any]: ...

    def mark_ended(self, activity_id: str) -> None: ...
    def is_ended(self, activity_id: str) -> bool: ...
    def annotate_landed_latest(self, activity_id: str, landed: list[dict[str, Any]]) -> None: ...
    def for_activity(self, activity_id: str) -> list[dict[str, Any]]: ...
    def label(self) -> str: ...


class MemoryLineageBackend:
    def __init__(self, *, down: bool = False) -> None:
        self._seq = 1
        self._by_id: dict[str, dict[str, Any]] = {}
        self._by_act: dict[str, list[str]] = {}
        self._ended: set[str] = set()
        self._down = down
        self._lock = threading.Lock()

    def mark_down(self, down: bool = True) -> None:
        self._down = down

    def _chk(self) -> None:
        if self._down:
            raise StoreDown("lineage store down")

    def commit(
        self,
        cap_id: str,
        activity_id: str | None,
        action: str,
        authorized_ops: list[dict[str, Any]],
        reverse_class: str,
        inverse: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self._chk()
        with self._lock:
            if activity_id and activity_id in self._ended:
                raise LineageError(f"cannot commit to ended activity: {activity_id}")
            eid = f"lin-{self._seq}"
            self._seq += 1
            entry = {
                "id": eid,
                "cap_id": cap_id,
                "activity_id": activity_id,
                "action": action,
                "authorized_ops": list(authorized_ops),
                "reverse_class": reverse_class,
                "inverse_ops": list(inverse),
                "landed_ops": [],
            }
            self._by_id[eid] = entry
            if activity_id:
                self._by_act.setdefault(activity_id, []).append(eid)
            return dict(entry)

    def mark_ended(self, activity_id: str) -> None:
        self._chk()
        with self._lock:
            if activity_id in self._ended:
                raise LineageError(f"activity already ended: {activity_id}")
            self._ended.add(activity_id)

    def is_ended(self, activity_id: str) -> bool:
        with self._lock:
            return activity_id in self._ended

    def annotate_landed_latest(self, activity_id: str, landed: list[dict[str, Any]]) -> None:
        self._chk()
        with self._lock:
            ids = self._by_act.get(activity_id) or []
            if not ids:
                raise LineageError(f"no lineage for activity {activity_id}")
            self._by_id[ids[-1]]["landed_ops"] = list(landed)

    def for_activity(self, activity_id: str) -> list[dict[str, Any]]:
        self._chk()
        with self._lock:
            return [dict(self._by_id[i]) for i in self._by_act.get(activity_id, []) if i in self._by_id]

    def label(self) -> str:
        return "down" if self._down else "memory"


class FileLineageBackend:
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
            return {"seq": 1, "by_id": {}, "by_act": {}, "ended": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8") or "{}")
        except (OSError, json.JSONDecodeError) as e:
            raise StoreDown(f"lineage store down: {e}") from e
        if not isinstance(data, dict):
            raise StoreDown("lineage store down: corrupt")
        data.setdefault("seq", 1)
        data.setdefault("by_id", {})
        data.setdefault("by_act", {})
        data.setdefault("ended", [])
        return data

    def _save(self, data: dict[str, Any]) -> None:
        try:
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp.write_text(json.dumps(data), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError as e:
            raise StoreDown(f"lineage store down: {e}") from e

    def commit(
        self,
        cap_id: str,
        activity_id: str | None,
        action: str,
        authorized_ops: list[dict[str, Any]],
        reverse_class: str,
        inverse: list[dict[str, Any]],
    ) -> dict[str, Any]:
        with self._thread:
            self._flock()
            try:
                data = self._load()
                if activity_id and activity_id in data["ended"]:
                    raise LineageError(f"cannot commit to ended activity: {activity_id}")
                eid = f"lin-{data['seq']}"
                data["seq"] = int(data["seq"]) + 1
                entry = {
                    "id": eid,
                    "cap_id": cap_id,
                    "activity_id": activity_id,
                    "action": action,
                    "authorized_ops": list(authorized_ops),
                    "reverse_class": reverse_class,
                    "inverse_ops": list(inverse),
                    "landed_ops": [],
                }
                data["by_id"][eid] = entry
                if activity_id:
                    data["by_act"].setdefault(activity_id, []).append(eid)
                self._save(data)
                return dict(entry)
            finally:
                self._funlock()

    def mark_ended(self, activity_id: str) -> None:
        with self._thread:
            self._flock()
            try:
                data = self._load()
                if activity_id in data["ended"]:
                    raise LineageError(f"activity already ended: {activity_id}")
                data["ended"].append(activity_id)
                self._save(data)
            finally:
                self._funlock()

    def is_ended(self, activity_id: str) -> bool:
        with self._thread:
            self._flock()
            try:
                return activity_id in self._load()["ended"]
            finally:
                self._funlock()

    def annotate_landed_latest(self, activity_id: str, landed: list[dict[str, Any]]) -> None:
        with self._thread:
            self._flock()
            try:
                data = self._load()
                ids = data["by_act"].get(activity_id) or []
                if not ids:
                    raise LineageError(f"no lineage for activity {activity_id}")
                data["by_id"][ids[-1]]["landed_ops"] = list(landed)
                self._save(data)
            finally:
                self._funlock()

    def for_activity(self, activity_id: str) -> list[dict[str, Any]]:
        with self._thread:
            self._flock()
            try:
                data = self._load()
                return [dict(data["by_id"][i]) for i in data["by_act"].get(activity_id, []) if i in data["by_id"]]
            finally:
                self._funlock()

    def label(self) -> str:
        return "file"


def reverse_activity(store: LineageBackend, activity_id: str) -> ReverseOutcome:
    if not activity_id:
        raise LineageError("empty activity_id")
    store.mark_ended(activity_id)
    entries = store.for_activity(activity_id)
    ops: list[dict[str, Any]] = []
    non: list[str] = []
    used_landed = False
    for entry in reversed(entries):
        cls = entry.get("reverse_class") or NON_REVERSIBLE
        if cls == INVERSE:
            landed = list(entry.get("landed_ops") or [])
            if landed:
                used_landed = True
                ops.extend(inverse_ops(landed))
            else:
                ops.extend(list(entry.get("inverse_ops") or []))
        else:
            non.append(str(entry.get("id") or ""))
    return ReverseOutcome(ops=ops, non_reversible=non, used_landed=used_landed)
