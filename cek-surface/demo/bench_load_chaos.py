#!/usr/bin/env python3
"""Load + chaos benchmarks for cek-surface shop.

Measures:
  - Host-only latency (compose + Cap + package, no Peer)
  - Full path latency (Host → JS Peer apply)
  - Throughput under sequential load
  - Chaos: refuse, once-replay, bad email, empty cart, rapid search, interleaved

Usage:
  python3 demo/bench_load_chaos.py
  python3 demo/bench_load_chaos.py --n 200 --peer
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_surface.kernel import KernelResult
from cek_surface.ops import as_wire
from shop_app import build_shop


def pct(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    i = min(len(s) - 1, max(0, int(round((p / 100) * (len(s) - 1)))))
    return s[i]


def summary(name: str, samples_ms: list[float]) -> dict:
    if not samples_ms:
        return {"name": name, "n": 0}
    return {
        "name": name,
        "n": len(samples_ms),
        "min_ms": round(min(samples_ms), 3),
        "p50_ms": round(pct(samples_ms, 50), 3),
        "p95_ms": round(pct(samples_ms, 95), 3),
        "p99_ms": round(pct(samples_ms, 99), 3),
        "max_ms": round(max(samples_ms), 3),
        "mean_ms": round(statistics.fmean(samples_ms), 3),
        "ops_per_s": round(1000.0 / statistics.fmean(samples_ms), 1) if samples_ms else 0,
    }


def host_only_submit(surface, action: str, args: dict, *, once: bool = False) -> tuple[KernelResult, float]:
    """Compose + kernel authorize without Peer (isolates Python path)."""
    t0 = time.perf_counter()
    handler = surface._handlers[action]
    from cek_surface.surface import Ctx

    ctx = Ctx(action=action, args=args, surface=surface, store=surface.store)
    ops = handler(ctx)
    cap = surface.mint(action, once=once, args=args, seal_args=once)
    result = surface.kernel.submit(action, args, cap, project_ops=as_wire(ops))
    dt = (time.perf_counter() - t0) * 1000
    return result, dt


def full_submit(surface, action: str, args: dict, **kw) -> tuple[dict, float]:
    t0 = time.perf_counter()
    out = surface.submit(action, args, auto_mint=True, **kw)
    dt = (time.perf_counter() - t0) * 1000
    return out, dt


def run_host_only_load(n: int) -> list[dict]:
    s = build_shop()
    # warm
    host_only_submit(s, "shop.boot", {})
    samples = []
    kinds = []
    for i in range(n):
        r, ms = host_only_submit(s, "cart.add", {"id": "sku-1", "qty": 1})
        samples.append(ms)
        kinds.append(r.kind)
    return [
        summary("host_only.cart.add", samples),
        {"ok_rate": kinds.count("ok") / len(kinds) if kinds else 0},
    ]


def run_full_load(n: int, with_peer: bool) -> list[dict]:
    s = build_shop()
    if not with_peer:
        # still use surface.submit but peer is started — always true for full
        pass
    out, boot_ms = full_submit(s, "shop.boot", {}, drain_async=False)
    assert out["result"]["kind"] == "ok", out

    cart_samples = []
    checkout_bad = []
    checkout_ok = []
    refuse_samples = []

    for i in range(n):
        _, ms = full_submit(s, "cart.add", {"id": "sku-2", "qty": 1}, drain_async=False)
        cart_samples.append(ms)

    # validation path
    full_submit(s, "checkout.start", {}, drain_async=False)
    for i in range(min(50, n)):
        o, ms = full_submit(s, "checkout.submit", {"email": "bad"}, drain_async=False)
        checkout_bad.append(ms)
        assert o["result"]["kind"] == "ok"  # validation is ops, not refuse

    # successful checkout once
    o, ms = full_submit(s, "checkout.submit", {"email": "load@test.example"}, drain_async=False)
    checkout_ok.append(ms)

    # refuse: no auto mint
    for i in range(min(50, n)):
        t0 = time.perf_counter()
        o = s.submit("cart.add", {"id": "sku-1"}, cap=None, drain_async=False)
        refuse_samples.append((time.perf_counter() - t0) * 1000)
        assert o["result"]["kind"] == "authority_refusal"
        assert o["result"]["ops"] == []

    s.close()
    return [
        summary("full.boot", [boot_ms]),
        summary("full.cart.add", cart_samples),
        summary("full.checkout.invalid_email", checkout_bad),
        summary("full.checkout.ok", checkout_ok),
        summary("full.refuse_no_cap", refuse_samples),
    ]


def run_async_search_load(n: int) -> list[dict]:
    """Each search pays timer + http event RTTs (demo peer uses ~40ms delays)."""
    s = build_shop()
    full_submit(s, "shop.boot", {}, drain_async=False)
    samples = []
    for i in range(n):
        t0 = time.perf_counter()
        out = s.submit("search.type", {"q": f"wid{i % 5}", "ms": 20}, auto_mint=True, drain_async=True)
        samples.append((time.perf_counter() - t0) * 1000)
        assert out["result"]["kind"] == "ok"
        # followups should include timer and maybe http
        assert out.get("followups"), "expected async followups"
    s.close()
    return [summary("full.search.type+async_drain", samples)]


def run_chaos(n: int) -> dict:
    s = build_shop()
    full_submit(s, "shop.boot", {}, drain_async=False)
    report = {
        "once_replay_refused": False,
        "sealed_args_refused": False,
        "empty_cart_checkout": False,
        "rapid_cart_ok": 0,
        "world_nav_sane": False,
        "errors": [],
    }

    # once replay
    args = {"id": "sku-3", "qty": 1}
    cap = s.mint("cart.add", once=True, args=args, seal_args=True)
    r1 = s.submit("cart.add", args, cap=cap, drain_async=False)
    r2 = s.submit("cart.add", args, cap=cap, drain_async=False)
    report["once_replay_refused"] = (
        r1["result"]["kind"] == "ok" and r2["result"]["kind"] == "authority_refusal"
    )
    if not report["once_replay_refused"]:
        report["errors"].append(f"once: {r1['result']} / {r2['result']}")

    # sealed args tamper
    args2 = {"id": "sku-1", "qty": 1}
    cap2 = s.mint("cart.add", once=False, args=args2, seal_args=True)
    r3 = s.submit("cart.add", {"id": "sku-1", "qty": 99}, cap=cap2, drain_async=False)
    report["sealed_args_refused"] = r3["result"]["kind"] == "authority_refusal"

    # empty cart checkout toast path
    s.store["cart"] = {}
    r4 = s.submit("checkout.start", {}, auto_mint=True, drain_async=False)
    report["empty_cart_checkout"] = r4["result"]["kind"] == "ok" and any(
        o.get("name") == "toast" for o in r4["result"]["ops"]
    )

    # rapid fire cart
    for i in range(n):
        o, _ = full_submit(s, "cart.add", {"id": "sku-1"}, drain_async=False)
        if o["result"]["kind"] == "ok":
            report["rapid_cart_ok"] += 1

    nav = (s.last_world or {}).get("nav") or {}
    report["world_nav_sane"] = isinstance(nav.get("path"), str)
    report["final_cart_lines"] = len(s.store.get("cart") or {})
    s.close()
    return report


def print_table(rows: list[dict]) -> None:
    print(f"{'name':<36} {'n':>5} {'p50':>8} {'p95':>8} {'p99':>8} {'max':>8} {'mean':>8} {'ops/s':>8}")
    print("-" * 100)
    for r in rows:
        if "p50_ms" not in r:
            continue
        print(
            f"{r['name']:<36} {r['n']:>5} {r['p50_ms']:>8} {r['p95_ms']:>8} "
            f"{r['p99_ms']:>8} {r['max_ms']:>8} {r['mean_ms']:>8} {r['ops_per_s']:>8}"
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100, help="iterations per load series")
    ap.add_argument("--search-n", type=int, default=20, help="async search iterations")
    ap.add_argument("--skip-async", action="store_true")
    ap.add_argument("--skip-net", action="store_true")
    ap.add_argument("--net-n", type=int, default=30, help="iters per network profile")
    args = ap.parse_args()

    print("=== cek-surface load + chaos ===\n")

    print("1) Host-only (no Peer) — compose + Cap + package")
    host_rows = run_host_only_load(args.n)
    print_table(host_rows)
    print("   ok_rate", host_rows[-1].get("ok_rate"))

    print("\n2) Full path (Host → JS Peer apply)")
    full_rows = run_full_load(args.n, with_peer=True)
    print_table(full_rows)

    if not args.skip_async:
        print("\n3) Search + async drain (timer + http events)")
        async_rows = run_async_search_load(args.search_n)
        print_table(async_rows)
        print("   note: demo Peer uses ~20–40ms artificial delay per timer/http")

    print("\n4) Chaos")
    chaos = run_chaos(args.n)
    for k, v in chaos.items():
        if k == "errors" and not v:
            continue
        print(f"   {k}: {v}")

    if not args.skip_net:
        print("\n5) Simulated network RTT (Intent uplink + Result downlink)")
        profiles = [
            ("lan_1ms", 0.5, 0.2),      # ~1ms RTT
            ("metro_20ms", 10.0, 2.0),  # ~20ms RTT
            ("wan_80ms", 40.0, 8.0),    # ~80ms RTT
            ("bad_200ms", 100.0, 30.0), # ~200ms RTT
        ]
        net_rows = run_network_sim(args.net_n, profiles)
        print_table(net_rows)
        print("\n6) Search+async under ~20ms RTT (extra RTT per followup)")
        print_table(run_network_search_sim(min(10, args.net_n), base=10.0, jitter=2.0))

    print("\n=== interpretation ===")
    host_p50 = next((r["p50_ms"] for r in host_rows if r.get("name") == "host_only.cart.add"), None)
    full_p50 = next((r["p50_ms"] for r in full_rows if r.get("name") == "full.cart.add"), None)
    if host_p50 is not None and full_p50 is not None:
        print(f"Host-only cart p50: {host_p50} ms")
        print(f"Full path cart p50:  {full_p50} ms")
        print(f"Peer/IPC overhead ≈  {round(full_p50 - host_p50, 3)} ms (subprocess NDJSON)")
        print("Under real network, add 1 RTT (~20–100ms+); apply stays local on Peer.")
    print("Net sim: each Intent/Result exchange sleeps 2*one_way (RTT).")
    print("Async search pays RTT per followup Result as well.")
    return 0


# ── network RTT simulation ──────────────────────────────────────────────────

import random


class NetSim:
    """Simulate client↔Host network: one RTT per Intent/Result exchange.

    model:
      one_way_ms ~ N(base_ms, jitter_ms) clamped to >= 0
      full Intent→Result path pays 2 * one_way (uplink + downlink)
      async event→Host→Result pays another 2 * one_way per round
    """

    def __init__(self, base_one_way_ms: float = 25.0, jitter_ms: float = 5.0, loss: float = 0.0):
        self.base = base_one_way_ms
        self.jitter = jitter_ms
        self.loss = loss

    def one_way(self) -> float:
        if self.loss > 0 and random.random() < self.loss:
            raise TimeoutError("simulated packet loss")
        d = random.gauss(self.base, self.jitter)
        return max(0.0, d)

    def rtt_sleep(self) -> float:
        """Block for one full RTT; return ms slept."""
        up = self.one_way()
        down = self.one_way()
        total_s = (up + down) / 1000.0
        time.sleep(total_s)
        return (up + down)


def full_submit_with_net(surface, action: str, args: dict, net: NetSim, **kw) -> tuple[dict, float]:
    """Measure wall time including simulated network RTT around Host+Peer path."""
    t0 = time.perf_counter()
    net.rtt_sleep()  # Intent uplink + Result downlink (before/after local work is fine as model)
    out = surface.submit(action, args, auto_mint=True, **kw)
    # If async followups, each Host round-trip pays another RTT
    for _ in out.get("followups") or []:
        if _.get("result") is not None:
            net.rtt_sleep()
    dt = (time.perf_counter() - t0) * 1000
    return out, dt


def run_network_sim(n: int, profiles: list[tuple[str, float, float]]) -> list[dict]:
    rows = []
    for name, base, jitter in profiles:
        s = build_shop()
        net = NetSim(base_one_way_ms=base, jitter_ms=jitter)
        # warm peer without counting net on boot peer spawn
        s.submit("shop.boot", {}, auto_mint=True, drain_async=False)
        samples = []
        for i in range(n):
            _, ms = full_submit_with_net(
                s, "cart.add", {"id": "sku-1", "qty": 1}, net, drain_async=False
            )
            samples.append(ms)
        s.close()
        rows.append(summary(f"net.{name}.cart.add", samples))
    return rows


def run_network_search_sim(n: int, base: float, jitter: float) -> list[dict]:
    """Search path: 1 RTT for search.type + 1 RTT per followup Result."""
    s = build_shop()
    net = NetSim(base_one_way_ms=base, jitter_ms=jitter)
    s.submit("shop.boot", {}, auto_mint=True, drain_async=False)
    samples = []
    for i in range(n):
        _, ms = full_submit_with_net(
            s, "search.type", {"q": f"w{i}", "ms": 15}, net, drain_async=True
        )
        samples.append(ms)
    s.close()
    return [summary(f"net.rtt{int(base*2)}ms.search+async", samples)]

if __name__ == "__main__":
    raise SystemExit(main())
