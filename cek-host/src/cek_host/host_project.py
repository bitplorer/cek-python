"""Project kernel actions → wire Ops. Surface always passes project_ops."""

from __future__ import annotations

from typing import Any

from .catalog import project_wire


def project_action(action: str, args: dict[str, Any]) -> list[dict[str, Any]]:
    """Kernel actions only."""
    if action == "kv.write":
        key = args.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError("kv.write requires string args.key")
        return [{"ns": "kv", "name": "set", "payload": {"key": key, "value": args.get("value")}}]
    if action == "kv.delete":
        key = args.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError("kv.delete requires string args.key")
        payload: dict[str, Any] = {"key": key}
        if "prior" in args:
            payload["prior"] = args["prior"]
        return [{"ns": "kv", "name": "delete", "payload": payload}]
    if action == "log.append":
        msg = args.get("message")
        if not isinstance(msg, str):
            raise ValueError("log.append requires string args.message")
        return [{"ns": "log", "name": "append", "payload": {"message": msg}}]
    if action == "ui.morph":
        target = args.get("target")
        if not isinstance(target, str) or not target:
            raise ValueError("ui.morph requires string args.target")
        if "patch" not in args:
            raise ValueError("ui.morph requires args.patch")
        payload = {"target": target, "patch": args["patch"]}
        if "snapshot" in args:
            payload["snapshot"] = args["snapshot"]
        return [{"ns": "ui.dom", "name": "morph", "payload": payload}]
    if action == "ui.restore":
        target = args.get("target")
        if not isinstance(target, str) or not target:
            raise ValueError("ui.restore requires string args.target")
        if "snapshot" not in args:
            raise ValueError("ui.restore requires args.snapshot")
        return [
            {
                "ns": "ui.dom",
                "name": "restore",
                "payload": {"target": target, "snapshot": args["snapshot"]},
            }
        ]
    raise ValueError(f"unknown action: {action}")


def resolve_ops(
    action: str,
    args: dict[str, Any],
    project_ops: list[dict[str, Any]] | None,
    stamp: frozenset[tuple[str, str]] | None,
) -> list[dict[str, Any]]:
    if project_ops is not None:
        planned = list(project_ops)
    else:
        planned = project_action(action, args)
    # Stamp membership is the session. No stamp → default_stamp_pairs().
    # Never return a planned list that skipped the legal table.
    return project_wire(planned, unknown="strict", stamp=stamp)
