"""Op catalog — single source of truth for Host composition and Peer drivers.

Composition language = Python. Wire = list of Op.to_dict() only.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


class Op:
    __slots__ = ("ns", "name", "payload")

    def __init__(self, ns: str, name: str, payload: dict[str, Any] | None = None):
        self.ns = ns
        self.name = name
        self.payload = payload or {}

    def to_dict(self) -> dict[str, Any]:
        return {"ns": self.ns, "name": self.name, "payload": dict(self.payload)}

    def __repr__(self) -> str:
        return f"Op({self.ns}.{self.name}, {self.payload!r})"

    # ── kv ──────────────────────────────────────────────────────────────────

    @staticmethod
    def kv_set(key: str, value: Any) -> Op:
        _nonempty(key, "kv.set key")
        return Op("kv", "set", {"key": key, "value": value})

    @staticmethod
    def kv_delete(key: str, prior: Any | None = None) -> Op:
        _nonempty(key, "kv.delete key")
        p: dict[str, Any] = {"key": key}
        if prior is not None:
            p["prior"] = prior
        return Op("kv", "delete", p)

    @staticmethod
    def kv_merge(key: str, patch: Mapping[str, Any]) -> Op:
        _nonempty(key, "kv.merge key")
        if not isinstance(patch, Mapping):
            raise ValueError("kv.merge patch must be a mapping")
        return Op("kv", "merge", {"key": key, "patch": dict(patch)})

    # ── ui.dom ──────────────────────────────────────────────────────────────

    @staticmethod
    def ui_morph(target: str, patch: Any, snapshot: Any | None = None) -> Op:
        _nonempty(target, "ui.morph target")
        p: dict[str, Any] = {"target": target, "patch": patch}
        if snapshot is not None:
            p["snapshot"] = snapshot
        return Op("ui.dom", "morph", p)

    @staticmethod
    def ui_restore(target: str, snapshot: Any) -> Op:
        _nonempty(target, "ui.restore target")
        return Op("ui.dom", "restore", {"target": target, "snapshot": snapshot})

    @staticmethod
    def ui_remove(target: str) -> Op:
        _nonempty(target, "ui.remove target")
        return Op("ui.dom", "remove", {"target": target})

    @staticmethod
    def ui_set_text(target: str, text: str) -> Op:
        _nonempty(target, "ui.set_text target")
        return Op("ui.dom", "set_text", {"target": target, "text": text})

    @staticmethod
    def ui_set_attr(target: str, attr: str, value: Any) -> Op:
        _nonempty(target, "ui.set_attr target")
        _nonempty(attr, "ui.set_attr attr")
        return Op("ui.dom", "set_attr", {"target": target, "attr": attr, "value": value})

    # ── ui chrome ───────────────────────────────────────────────────────────

    @staticmethod
    def ui_focus(target: str) -> Op:
        _nonempty(target, "ui.focus target")
        return Op("ui", "focus", {"target": target})

    @staticmethod
    def ui_scroll(target: str, *, block: str = "start") -> Op:
        _nonempty(target, "ui.scroll target")
        return Op("ui", "scroll", {"target": target, "block": block})

    @staticmethod
    def ui_toast(message: str, *, level: str = "info", ms: int = 3000) -> Op:
        if not isinstance(message, str):
            raise ValueError("ui.toast message must be str")
        return Op("ui", "toast", {"message": message, "level": level, "ms": int(ms)})

    @staticmethod
    def ui_busy(target: str, busy: bool) -> Op:
        _nonempty(target, "ui.busy target")
        return Op("ui", "busy", {"target": target, "busy": bool(busy)})

    # ── nav ─────────────────────────────────────────────────────────────────

    @staticmethod
    def nav_push(path: str, *, state: Any | None = None, title: str | None = None) -> Op:
        _nonempty(path, "nav.push path")
        p: dict[str, Any] = {"path": path}
        if state is not None:
            p["state"] = state
        if title is not None:
            p["title"] = title
        return Op("nav", "push", p)

    @staticmethod
    def nav_replace(path: str, *, state: Any | None = None, title: str | None = None) -> Op:
        _nonempty(path, "nav.replace path")
        p: dict[str, Any] = {"path": path}
        if state is not None:
            p["state"] = state
        if title is not None:
            p["title"] = title
        return Op("nav", "replace", p)

    @staticmethod
    def nav_back(steps: int = 1) -> Op:
        if steps < 1:
            raise ValueError("nav.back steps >= 1")
        return Op("nav", "back", {"steps": int(steps)})

    # ── http (async → events) ───────────────────────────────────────────────

    @staticmethod
    def http_request(
        request_id: str,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        body: Any | None = None,
        timeout_ms: int = 30_000,
    ) -> Op:
        _nonempty(request_id, "http.request id")
        _nonempty(method, "http.request method")
        _nonempty(url, "http.request url")
        p: dict[str, Any] = {
            "id": request_id,
            "method": method.upper(),
            "url": url,
            "timeout_ms": int(timeout_ms),
        }
        if headers:
            p["headers"] = dict(headers)
        if body is not None:
            p["body"] = body
        return Op("http", "request", p)

    @staticmethod
    def http_cancel(request_id: str) -> Op:
        _nonempty(request_id, "http.cancel id")
        return Op("http", "cancel", {"id": request_id})

    # ── timer (async → events) ──────────────────────────────────────────────

    @staticmethod
    def timer_clear(timer_id: str) -> Op:
        _nonempty(timer_id, "timer.clear id")
        return Op("timer", "clear", {"id": timer_id})

    @staticmethod
    def timer_set(timer_id: str, ms: int) -> Op:
        _nonempty(timer_id, "timer.set id")
        if ms < 0:
            raise ValueError("timer.set ms < 0")
        return Op("timer", "set", {"id": timer_id, "ms": int(ms)})

    # ── log ─────────────────────────────────────────────────────────────────

    @staticmethod
    def log_append(
        message: str, *, level: str = "info", fields: Mapping[str, Any] | None = None
    ) -> Op:
        if not isinstance(message, str):
            raise ValueError("log.append message must be str")
        p: dict[str, Any] = {"message": message, "level": level}
        if fields:
            p["fields"] = dict(fields)
        return Op("log", "append", p)



    # ── signals / misc (ux-channel ideas, CEK-native) ───────────────────────

    @staticmethod
    def signal_set(path: str, value: Any) -> Op:
        _nonempty(path, "signal.set path")
        return Op("signal", "set", {"path": path, "value": value})

    @staticmethod
    def ui_swap(target: str, html: str, *, mode: str = "inner") -> Op:
        _nonempty(target, "ui.swap target")
        return Op("ui.dom", "swap", {"target": target, "html": html, "mode": mode})

    @staticmethod
    def nav_reload() -> Op:
        return Op("nav", "reload", {})

    @staticmethod
    def noop() -> Op:
        return Op("sys", "noop", {})


def plan(*ops: Op) -> list[Op]:
    return list(ops)


def as_wire(ops: Sequence[Op]) -> list[dict[str, Any]]:
    return [o.to_dict() for o in ops]


def _nonempty(v: Any, label: str) -> None:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{label} must be non-empty str")


# ── Host-only macros ────────────────────────────────────────────────────────

def restart_timer(timer_id: str, ms: int) -> list[Op]:
    return plan(Op.timer_clear(timer_id), Op.timer_set(timer_id, ms))


def set_loading(region: str, busy: bool, status: str | None = None) -> list[Op]:
    ops = [Op.ui_busy(region, busy)]
    if status is not None:
        ops.append(Op.ui_set_text(f"{region}-status", status))
    return ops


def form_errors(form_id: str, errors: Mapping[str, str]) -> list[Op]:
    ops: list[Op] = []
    for field, msg in errors.items():
        ops.append(Op.ui_set_text(f"{form_id}.{field}-error", msg))
        ops.append(Op.ui_set_attr(f"{form_id}.{field}", "aria-invalid", "true"))
    if errors:
        ops.append(Op.ui_focus(f"{form_id}.{next(iter(errors))}"))
    return ops


def clear_form_errors(form_id: str, fields: Sequence[str]) -> list[Op]:
    ops: list[Op] = []
    for field in fields:
        ops.append(Op.ui_set_text(f"{form_id}.{field}-error", ""))
        ops.append(Op.ui_set_attr(f"{form_id}.{field}", "aria-invalid", "false"))
    return ops


def navigate_to(path: str, *, title: str | None = None, replace: bool = False) -> list[Op]:
    op = Op.nav_replace(path, title=title) if replace else Op.nav_push(path, title=title)
    return plan(op, Op.log_append(f"nav {'replace' if replace else 'push'} {path}"))


def fetch_json(
    request_id: str,
    url: str,
    *,
    method: str = "GET",
    body: Any | None = None,
    headers: Mapping[str, str] | None = None,
    busy_region: str | None = None,
) -> list[Op]:
    ops: list[Op] = []
    if busy_region:
        ops.extend(set_loading(busy_region, True, "Loading…"))
    hdrs = {"accept": "application/json", **(dict(headers) if headers else {})}
    if body is not None and method.upper() != "GET":
        hdrs.setdefault("content-type", "application/json")
    ops.append(Op.http_request(request_id, method, url, headers=hdrs, body=body))
    ops.append(Op.log_append(f"http {method} {url}", fields={"id": request_id}))
    return ops
