"""Host-runtime policy hooks (outer layer — not Cap law).

Rate limits, action allow-lists, navigate allow-lists.
Refuse produces zero ops via Surface/kernel still owning Cap checks.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PolicyDecision:
    allow: bool
    reason: str | None = None


@dataclass
class SurfacePolicy:
    """Optional guards before compose + kernel submit."""

    allowed_actions: set[str] | None = None
    navigate_prefixes: tuple[str, ...] = ("/",)
    max_intents_per_sec: float = 50.0
    max_ops_per_result: int = 64
    _hits: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def check_action(self, action: str, subject: str = "default") -> PolicyDecision:
        action = (action or "").strip()
        if not action:
            return PolicyDecision(False, "empty action")
        if self.allowed_actions is not None and action not in self.allowed_actions:
            return PolicyDecision(False, f"action not allowed: {action}")
        now = time.monotonic()
        window = self._hits[subject]
        window[:] = [t for t in window if now - t < 1.0]
        if len(window) >= self.max_intents_per_sec:
            return PolicyDecision(False, "rate limited")
        window.append(now)
        return PolicyDecision(True)

    def check_ops(self, ops: list[dict[str, Any]]) -> PolicyDecision:
        if len(ops) > self.max_ops_per_result:
            return PolicyDecision(False, f"too many ops: {len(ops)}")
        for o in ops:
            if o.get("ns") == "kv" and o.get("name") == "set":
                key = str((o.get("payload") or {}).get("key") or "")
                if key == "ui:nav":
                    val = (o.get("payload") or {}).get("value") or {}
                    path = str(val.get("path") if isinstance(val, dict) else "")
                    if not any(path.startswith(p) for p in self.navigate_prefixes):
                        return PolicyDecision(False, f"nav path denied: {path}")
        return PolicyDecision(True)
