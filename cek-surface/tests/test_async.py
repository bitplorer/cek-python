"""Sync and async are first-class. Sync submit does not nest an event loop."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import Host
from cek_surface import Op, Surface


def _surface() -> Surface:
    return Surface(
        kernel=Host(secret=b"async-first-class-secret-32b!!"),
        carrier_kind="memory",
    )


def test_sync_handler_sync_submit():
    s = _surface()

    @s.action("hello")
    def hello(ctx):
        return [Op.log_append("hi")]

    cap = s.mint("hello")
    r = s.submit("hello", {}, cap=cap, drain_async=False)
    assert r["result"]["kind"] == "ok"
    assert r["result"]["ops"][0]["name"] == "append"


def test_async_handler_async_submit():
    s = _surface()

    @s.action("hello")
    async def hello(ctx):
        await asyncio.sleep(0)
        return [Op.log_append("hi-async")]

    cap = s.mint("hello")
    r = asyncio.run(s.async_submit("hello", {}, cap=cap, drain_async=False))
    assert r["result"]["kind"] == "ok"
    assert r["result"]["ops"][0]["payload"]["message"] == "hi-async"


def test_sync_submit_refuses_async_handler():
    s = _surface()

    @s.action("hello")
    async def hello(ctx):
        return [Op.log_append("no")]

    cap = s.mint("hello")
    try:
        s.submit("hello", {}, cap=cap, drain_async=False)
        raise AssertionError("sync submit must not run async handlers")
    except TypeError as e:
        assert "async_submit" in str(e)


def test_async_submit_runs_sync_handler():
    s = _surface()

    @s.action("hello")
    def hello(ctx):
        return [Op.log_append("either")]

    cap = s.mint("hello")
    r = asyncio.run(s.async_submit("hello", {}, cap=cap, drain_async=False))
    assert r["result"]["kind"] == "ok"


def test_host_async_submit_same_law():
    h = Host(secret=b"async-first-class-secret-32b!!")
    cap = h.mint("x", once=True)
    r = asyncio.run(
        h.async_submit(
            action="x",
            args={},
            cap=cap,
            project_ops=[{"ns": "log", "name": "append", "payload": {"message": "a"}}],
        )
    )
    assert r.kind == "ok"
    r2 = asyncio.run(
        h.async_submit(
            action="x",
            args={},
            cap=cap,
            project_ops=[{"ns": "log", "name": "append", "payload": {"message": "a"}}],
        )
    )
    assert r2.kind == "authority_refusal"
    assert r2.ops == []


def test_async_on_event():
    s = _surface()

    @s.on("tick")
    async def tick(event, surface):
        await asyncio.sleep(0)
        return [Op.log_append("tock")]

    r = asyncio.run(s.async_handle_event({"type": "tick"}))
    assert r is not None and r.ok
    try:
        s.handle_event({"type": "tick"})
        raise AssertionError("sync handle_event must refuse async @on")
    except TypeError as e:
        assert "async_handle_event" in str(e)


if __name__ == "__main__":
    test_sync_handler_sync_submit()
    test_async_handler_async_submit()
    test_sync_submit_refuses_async_handler()
    test_async_submit_runs_sync_handler()
    test_host_async_submit_same_law()
    test_async_on_event()
    print("async ok")
