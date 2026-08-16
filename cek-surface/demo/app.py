#!/usr/bin/env python3
"""Shop demo: Surface + Host kernel (independent of ux-channel)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_surface import Op, Surface
from cek_surface.ops import (
    clear_form_errors,
    form_errors,
    navigate_to,
    plan,
    set_loading,
    signal_set,
)


def build() -> Surface:
    s = Surface()

    @s.action("app.boot")
    def boot(ctx):
        return plan(
            *navigate_to("/shop", title="Shop"),
            Op.ui_morph(
                "shell",
                {
                    "tag": "main",
                    "attrs": {"id": "shell"},
                    "children": [
                        {"tag": "input", "attrs": {"id": "search-input"}},
                        {"tag": "ul", "attrs": {"id": "results"}, "children": []},
                        {"tag": "div", "attrs": {"id": "cart"}, "text": "Cart: 0"},
                    ],
                },
            ),
            signal_set("ui.theme", "light"),
            Op.log_append("boot"),
        )

    @s.action("search.type")
    def search_type(ctx):
        q = str(ctx.args.get("q") or "")
        ctx.store["search.pending"] = q
        return plan(
            Op.kv_set("search.pending", q),
            Op.ui_morph("search-input", {"tag": "input", "attrs": {"id": "search-input"}, "text": q}),
            Op.log_append("search.type", fields={"q": q}),
        )

    @s.action("cart.add")
    def cart_add(ctx):
        item_id = str(ctx.args.get("id") or "")
        title = str(ctx.args.get("title") or item_id)
        price = float(ctx.args.get("price") or 0)
        if not item_id:
            return plan(Op.log_append("Missing item", level="error"))
        cart = dict(ctx.store.get("cart") or {})
        line = dict(cart.get(item_id) or {"id": item_id, "title": title, "price": price, "qty": 0})
        line["qty"] = int(line["qty"]) + 1
        cart[item_id] = line
        ctx.store["cart"] = cart
        n = sum(int(x["qty"]) for x in cart.values())
        total = sum(int(x["qty"]) * float(x["price"]) for x in cart.values())
        return plan(
            Op.kv_set("cart", cart),
            Op.ui_morph("cart", {"tag": "div", "attrs": {"id": "cart"}, "text": f"Cart: {n} · ${total:.2f}"}),
            Op.log_append(f"Added {title}"),
        )

    @s.action("checkout.start")
    def checkout_start(ctx):
        if not (ctx.store.get("cart") or {}):
            return plan(Op.log_append("Cart empty", level="error"))
        return plan(
            *navigate_to("/checkout", title="Checkout"),
            *clear_form_errors("checkout", ["email"]),
            Op.kv_set("ui:focus", "checkout.email"),
        )

    @s.action("checkout.submit")
    def checkout_submit(ctx):
        email = str(ctx.args.get("email") or "").strip()
        if "@" not in email:
            return plan(*form_errors("checkout", {"email": "Valid email required"}))
        cart = ctx.store.get("cart") or {}
        order_id = "ord-" + str(abs(hash(email + str(cart))) % 10_000_000)
        ctx.store["last_order"] = {"id": order_id, "email": email, "cart": cart}
        ctx.store["cart"] = {}
        return plan(
            Op.kv_set("cart", {}),
            Op.kv_set("last_order", ctx.store["last_order"]),
            Op.ui_morph("cart", {"tag": "div", "attrs": {"id": "cart"}, "text": "Cart: 0"}),
            *navigate_to("/thanks", title="Thanks", replace=True),
            Op.log_append("Order placed"),
        )

    @s.on("timer.fired")
    def on_timer(ev, surface: Surface):
        if ev.get("id") != "search-debounce":
            return None
        q = surface.store.get("search.pending") or ""
        if not str(q).strip():
            return plan(Op.ui_morph("results", {"tag": "ul", "children": []}))
        return plan(Op.log_append("search.debounce", fields={"q": q}))

    @s.on("http.response")
    def on_http(ev, surface: Surface):
        if ev.get("id") != "search-1":
            return None
        items = (ev.get("body") or {}).get("items") or []
        surface.store["search.results"] = items
        children = [
            {"tag": "li", "attrs": {"id": f"hit-{it['id']}"}, "text": it.get("title")}
            for it in items
            if isinstance(it, dict)
        ]
        return plan(
            *set_loading("search", False, f"{len(children)} results"),
            Op.ui_morph("results", {"tag": "ul", "attrs": {"id": "results"}, "children": children}),
            Op.log_append(f"Found {len(children)}"),
        )

    @s.on("http.error")
    def on_err(ev, surface: Surface):
        return plan(
            *set_loading("search", False, "Error"),
            Op.log_append(ev.get("message") or "error", level="error"),
        )

    return s


def main() -> int:
    s = build()
    try:
        def go(action, args=None, **kw):
            out = s.submit(action, args or {}, auto_mint=True, **kw)
            print(f"\n=== {action} ===")
            print("kind:", out["result"]["kind"], "ops:", len(out["result"]["ops"]))
            if out["result"].get("error"):
                print("error:", out["result"]["error"])
            print("nav:", (out.get("world") or {}).get("nav"))
            for fu in out.get("followups") or []:
                print("  event", (fu.get("event") or {}).get("type"), (fu.get("event") or {}).get("id"))
            return out

        go("app.boot")
        go("search.type", {"q": "widget", "ms": 40})
        results = s.store.get("search.results") or []
        if results:
            it = results[0]
            go(
                "cart.add",
                {"id": it["id"], "title": it["title"], "price": it.get("price", 10)},
                once=True,
            )
            args = {"id": "x", "title": "X", "price": 1}
            cap = s.mint("cart.add", once=True, args=args, seal_args=True)
            r1 = s.submit("cart.add", args, cap=cap, drain_async=False)
            r2 = s.submit("cart.add", args, cap=cap, drain_async=False)
            print("\nonce replay:", r1["result"]["kind"], "→", r2["result"]["kind"], r2["result"].get("error"))

        go("checkout.start")
        go("checkout.submit", {"email": "bad"})
        go("checkout.submit", {"email": "a@b.co"})
        print("\norder", (s.store.get("last_order") or {}).get("id"))
        print("kernel", type(s.kernel).__name__)
    finally:
        s.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
