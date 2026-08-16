"""Portable Intent/Result carriers — opt-in, plug-and-play.

Default: subprocess NDJSON (zero config, demos/tests).
Opt-in: memory (in-process mock), websocket (when websockets installed).

Carriers are transport only — not kernels. They move:
  apply Result, chrome messages, async events, done.
"""

from __future__ import annotations

import json
import subprocess
import threading
import queue
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Carrier(Protocol):
    """Plug-and-play transport boundary."""

    name: str

    def apply(self, result: dict[str, Any]) -> dict[str, Any]:
        """Send Result for Peer apply; return receipt/world message."""
        ...

    def stamp(self, pairs: list[dict[str, str]]) -> dict[str, Any]:
        """Install session stamp on Peer. Optional on older carriers."""
        ...

    def chrome(self, chrome: dict[str, Any]) -> dict[str, Any]:
        """Perception-only chrome; not lineage."""
        ...

    def read_event(self, timeout: float | None = None) -> dict[str, Any] | None:
        """Block for Peer-emitted events. None on timeout/EOF. Phase-1 S has none."""
        ...

    def close(self) -> None: ...


# ── Memory (tests / same-process Peer mock) ─────────────────────────────────


class MemoryCarrier:
    """In-process queue pair. Host and a mock Peer share queues."""

    name = "memory"

    def __init__(self) -> None:
        self._to_peer: queue.Queue = queue.Queue()
        self._to_host: queue.Queue = queue.Queue()
        self._closed = False
        self.peer_handler: Any = None  # optional callable(msg)->list of replies

    def apply(self, result: dict[str, Any]) -> dict[str, Any]:
        return self._roundtrip({"type": "apply", "result": result})

    def stamp(self, pairs: list[dict[str, str]]) -> dict[str, Any]:
        return self._roundtrip({"type": "stamp", "pairs": pairs})

    def chrome(self, chrome: dict[str, Any]) -> dict[str, Any]:
        return self._roundtrip({"type": "chrome", "chrome": chrome})

    def read_event(self, timeout: float | None = None) -> dict[str, Any] | None:
        try:
            return self._to_host.get(timeout=timeout if timeout is not None else 30)
        except queue.Empty:
            return None

    def close(self) -> None:
        self._closed = True
        self._to_peer.put({"type": "done"})

    def peer_push(self, msg: dict[str, Any]) -> None:
        self._to_host.put(msg)

    def peer_poll(self, timeout: float = 0.05) -> dict[str, Any] | None:
        try:
            return self._to_peer.get(timeout=timeout)
        except queue.Empty:
            return None

    def _roundtrip(self, msg: dict[str, Any]) -> dict[str, Any]:
        if self.peer_handler:
            replies = self.peer_handler(msg)
            if not replies:
                return {"type": "applied", "receipt": {"landed": [], "failed": []}, "world": {}}
            for r in replies[:-1]:
                self._to_host.put(r)
            return replies[-1]
        # Default echo: no Node required. Tests that need a world set peer_handler.
        if msg.get("type") == "stamp":
            return {"type": "stamp_ack", "pairs": msg.get("pairs") or []}
        if msg.get("type") == "apply":
            ops = (msg.get("result") or {}).get("ops") or []
            return {
                "type": "applied",
                "receipt": {"landed": ops, "failed": []},
                "world": {},
            }
        return {"type": "chrome_applied", "world": {}}


# ── Subprocess NDJSON (default) ─────────────────────────────────────────────


class SubprocessNdjsonCarrier:
    """Default demo carrier: node peer.mjs over stdin/stdout NDJSON."""

    name = "subprocess_ndjson"

    def __init__(self, peer_js: Path | None = None):
        pkg = Path(__file__).resolve().parent
        bundled = pkg / "js" / "peer.mjs"
        repo = pkg.parents[1] / "js" / "peer.mjs"
        self.peer_js = peer_js or (bundled if bundled.is_file() else repo)
        self.proc = subprocess.Popen(
            ["node", str(self.peer_js)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._lock = threading.Lock()

    def apply(self, result: dict[str, Any]) -> dict[str, Any]:
        return self._rpc({"type": "apply", "result": result})

    def stamp(self, pairs: list[dict[str, str]]) -> dict[str, Any]:
        return self._rpc({"type": "stamp", "pairs": pairs})

    def chrome(self, chrome: dict[str, Any]) -> dict[str, Any]:
        return self._rpc({"type": "chrome", "chrome": chrome})

    def read_event(self, timeout: float | None = None) -> dict[str, Any] | None:
        # Blocking readline; timeout via non-portable select optional
        assert self.proc.stdout
        line = self.proc.stdout.readline()
        if not line:
            return None
        return json.loads(line)

    def close(self) -> None:
        if self.proc.stdin:
            try:
                self.proc.stdin.write(json.dumps({"type": "done"}) + "\n")
                self.proc.stdin.close()
            except BrokenPipeError:
                pass
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()

    def _rpc(self, msg: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            assert self.proc.stdin and self.proc.stdout
            self.proc.stdin.write(json.dumps(msg) + "\n")
            self.proc.stdin.flush()
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("peer died")
            return json.loads(line)


# ── WebSocket (opt-in) ──────────────────────────────────────────────────────


class WebSocketCarrier:
    """Opt-in carrier. Requires `websockets` and a peer that speaks same JSON frames.

    Server mode: Host listens; browser Peer connects.
    Client mode: Host connects to existing Peer endpoint.
    """

    name = "websocket"

    def __init__(
        self,
        *,
        url: str | None = None,
        host: str = "127.0.0.1",
        port: int = 8765,
        mode: str = "client",
    ):
        try:
            import websockets  # type: ignore
            import asyncio
        except ImportError as e:
            raise ImportError(
                "WebSocket carrier requires: pip install websockets\n"
                "Or use open_carrier('subprocess') / open_carrier('memory')."
            ) from e
        self._websockets = websockets
        self._asyncio = asyncio
        self.url = url or f"ws://{host}:{port}"
        self.mode = mode
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._ws = None
        self._inbox: queue.Queue = queue.Queue()
        fut = self._asyncio.run_coroutine_threadsafe(self._connect(), self._loop)
        fut.result(timeout=10)

    async def _connect(self):
        self._ws = await self._websockets.connect(self.url)
        self._asyncio.create_task(self._reader())

    async def _reader(self):
        assert self._ws
        async for raw in self._ws:
            self._inbox.put(json.loads(raw))

    def apply(self, result: dict[str, Any]) -> dict[str, Any]:
        return self._rpc({"type": "apply", "result": result})

    def stamp(self, pairs: list[dict[str, str]]) -> dict[str, Any]:
        return self._rpc({"type": "stamp", "pairs": pairs})

    def chrome(self, chrome: dict[str, Any]) -> dict[str, Any]:
        return self._rpc({"type": "chrome", "chrome": chrome})

    def read_event(self, timeout: float | None = None) -> dict[str, Any] | None:
        try:
            return self._inbox.get(timeout=timeout if timeout is not None else 30)
        except queue.Empty:
            return None

    def close(self) -> None:
        async def _close():
            if self._ws:
                await self._ws.send(json.dumps({"type": "done"}))
                await self._ws.close()

        try:
            self._asyncio.run_coroutine_threadsafe(_close(), self._loop).result(timeout=3)
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)

    def _rpc(self, msg: dict[str, Any]) -> dict[str, Any]:
        async def _send():
            assert self._ws
            await self._ws.send(json.dumps(msg))

        self._asyncio.run_coroutine_threadsafe(_send(), self._loop).result(timeout=5)
        # Wait for applied / chrome_applied (skip pure events)
        while True:
            reply = self._inbox.get(timeout=30)
            if reply.get("type") in ("applied", "chrome_applied"):
                return reply
            # push async events back for read_event consumers — keep simple: return only rpc
            self._inbox.put(reply)


def open_carrier(kind: str = "subprocess", **opts: Any) -> Carrier:
    """Factory — sensible default is subprocess NDJSON.

    kind:
      subprocess | ndjson  → SubprocessNdjsonCarrier (default)
      memory               → MemoryCarrier (tests)
      websocket | ws       → WebSocketCarrier (opt-in, needs websockets)
    """
    k = (kind or "subprocess").lower()
    if k in ("subprocess", "ndjson", "default"):
        return SubprocessNdjsonCarrier(**{k2: v for k2, v in opts.items() if k2 in ("peer_js",)})
    if k in ("memory", "mem", "inproc"):
        return MemoryCarrier()
    if k in ("websocket", "ws"):
        return WebSocketCarrier(**opts)
    if k in ("kernel", "peer-kernel", "rust-peer"):
        from .kernel_peer import KernelPeerCarrier

        return KernelPeerCarrier(
            **{kk: opts[kk] for kk in ("profile", "bin_path") if kk in opts}
        )
    raise ValueError(
        f"unknown carrier kind: {kind!r} (use subprocess|memory|websocket|kernel)"
    )
