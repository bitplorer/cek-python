"""BoundAsk — post-verify token (I2).

No public constructor. Only Host may bind after verify + idem + once-ensure.
"""

from __future__ import annotations

from typing import Any


class BoundAsk:
    """Proof that Cap verify + once/idempotency succeeded."""

    __slots__ = ("action", "args", "claims", "now")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("BoundAsk has no public constructor (I2)")

    @classmethod
    def _bind(
        cls,
        action: str,
        args: dict[str, Any],
        claims: dict[str, Any],
        now: float,
    ) -> BoundAsk:
        obj = object.__new__(cls)
        obj.action = action
        obj.args = dict(args)
        obj.claims = dict(claims)
        obj.now = now
        return obj
