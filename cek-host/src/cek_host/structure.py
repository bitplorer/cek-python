"""Domain + driver structure validation (core signing / acceptance gate).

Does not own domain content — only naming structure so runtimes stay consistent.
"""

from __future__ import annotations

FORBIDDEN_PREFIXES = ("cek.", "sys.", "_")
RESERVED_BASELINE_DOMAINS = ("kv", "log")
KNOWN_SEED_DOMAINS = frozenset({"kv", "log", "ui.dom"})
MAX_NS_DOTS = 2


class StructureError(ValueError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"structure: {reason}")


def validate_domain_name(domain: str, *, allow_reserved: bool = False) -> None:
    if not domain:
        raise StructureError("domain name is empty")
    if domain.startswith(".") or domain.endswith("."):
        raise StructureError(f"domain '{domain}' has leading/trailing dot")
    if ".." in domain:
        raise StructureError(f"domain '{domain}' contains empty segment")
    if domain.count(".") > MAX_NS_DOTS:
        raise StructureError(f"domain '{domain}' has too many dots (max {MAX_NS_DOTS})")
    for prefix in FORBIDDEN_PREFIXES:
        if domain.startswith(prefix):
            raise StructureError(f"domain '{domain}' uses forbidden prefix '{prefix}'")
    if not allow_reserved and domain in RESERVED_BASELINE_DOMAINS:
        raise StructureError(f"domain '{domain}' is reserved Baseline")
    if not all(c.islower() or c.isdigit() or c == "." for c in domain):
        raise StructureError(f"domain '{domain}' has invalid characters")


def validate_op_name(name: str) -> None:
    if not name:
        raise StructureError("op name is empty")
    if "." in name:
        raise StructureError(f"op name '{name}' must not contain dots (dots belong in ns)")
    if not all(c.islower() or c.isdigit() for c in name):
        raise StructureError(f"op name '{name}' has invalid characters")


def validate_pair(ns: str, name: str) -> None:
    allow = ns in KNOWN_SEED_DOMAINS
    validate_domain_name(ns, allow_reserved=allow)
    validate_op_name(name)
