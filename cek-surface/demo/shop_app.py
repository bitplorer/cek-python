#!/usr/bin/env python3
"""Real-world shop surface: catalog, cart, checkout, search debounce."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_surface import Continuation, Op, Surface
from cek_surface.ops import (
    clear_form_errors,
    form_errors,
    navigate_to,
    plan,
    restart_timer,
    set_loading,
)

CATALOG = {
    "sku-1": {"id": "sku-1", "title": "Widget Basic", "price": 9.99},
    "sku-2": {"id": "sku-2", "title": "Widget Pro", "price": 29.99},
    "sku-3": {"id": "sku-3", "title": "Gadget X", "price": 49.0},
}


def _hits_for(q: str) -> list[dict]:
    needle = q.lower().strip()
    if not needle:
        return []
    return [it for it in CATALOG.values() if needle in it["title"].lower()]


def _results_ops(q: str, items: list[dict]) -> list[Op]:
    children = [
        {
            "tag": "li",
            "attrs": {"id": f"hit-{it['id']}"},
            "text": f"{it['title']} — ${it['price']}",
        }
        for it in items
    ]
    return plan(
        Op.kv_set("search.results", items),
        Op.ui_morph(
            "results",
            {"tag": "ul", "attrs": {"id": "results"}, "children": children},
        ),
        Op.ui_toast(f"Found {len(children)}", level="success", ms=1500),
        Op.log_append("search.commit", fields={"q": q, "n": len(children)}),
    )


def build_shop(*, carrier_kind: str = "subprocess", **carrier_opts) -> Surface:
    s = Surface(carrier_kind=carrier_kind, carrier_opts=dict(carrier_opts))
    s.store["catalog"] = CATALOG
    s.store["cart"] = {}

    @s.action("shop.boot")
    def boot(ctx):
        cards = [
            {
                "tag": "article",
                "attrs": {"id": f"card-{it['id']}"},
                "text": f"{it['title']} — ${it['price']}",
            }
            for it in CATALOG.values()
        ]
        return plan(
            *navigate_to("/shop", title="Shop"),
            Op.ui_morph(
                "catalog",
                {
                    "tag": "div",
                    "attrs": {"id": "catalog"},
                    "children": cards,
                },
            ),
            Op.kv_set("catalog", CATALOG),
            Op.ui_set_text("cart", "Cart: 0"),
            Op.signal_set("ui.theme", "light"),
            Op.log_append("shop.boot"),
        )

    @s.action("search.type")
    def search_type(ctx):
        q = str(ctx.args.get("q") or "")
        ctx.store["search.pending"] = q
        ms = int(ctx.args.get("ms") or 40)
        # Pre-authorize next hop: timer.fired → search.commit under once Cap
        cap = ctx.surface.mint(
            "search.commit",
            once=True,
            args={"q": q},
            seal_args=False,
        )
        ctx.continuations = [
            Continuation(
                event="timer.fired:search-debounce",
                action="search.commit",
                cap=cap,
                args_from={"q": "store:search.pending"},
                static_args={"ms": 0},
            )
        ]
        return plan(
            Op.kv_set("search.pending", q),
            Op.ui_set_text("search-input", q),
            *restart_timer("search-debounce", ms),
        )

    @s.action("search.commit")
    def search_commit(ctx):
        q = str(ctx.args.get("q") or ctx.store.get("search.pending") or "")
        items = _hits_for(q)
        ctx.store["search.results"] = items
        if not q.strip():
            return plan(
                Op.ui_morph(
                    "results",
                    {"tag": "ul", "attrs": {"id": "results"}, "children": []},
                )
            )
        return _results_ops(q, items)

    @s.action("cart.add")
    def cart_add(ctx):
        sku = str(ctx.args.get("id") or "")
        item = CATALOG.get(sku) or {
            "id": sku,
            "title": str(ctx.args.get("title") or sku),
            "price": float(ctx.args.get("price") or 0),
        }
        if not sku:
            return plan(Op.ui_toast("Missing sku", level="error"))
        cart = dict(ctx.store.get("cart") or {})
        line = dict(cart.get(sku) or {**item, "qty": 0})
        line["qty"] = int(line["qty"]) + int(ctx.args.get("qty") or 1)
        cart[sku] = line
        ctx.store["cart"] = cart
        n = sum(int(x["qty"]) for x in cart.values())
        total = sum(int(x["qty"]) * float(x["price"]) for x in cart.values())
        return plan(
            Op.kv_set("cart", cart),
            Op.ui_set_text("cart", f"Cart: {n} · ${total:.2f}"),
            Op.ui_toast(f"Added {line['title']}", level="success", ms=1500),
            Op.log_append("cart.add", fields={"sku": sku, "qty": line["qty"]}),
        )

    @s.action("cart.clear")
    def cart_clear(ctx):
        ctx.store["cart"] = {}
        return plan(
            Op.kv_set("cart", {}),
            Op.ui_set_text("cart", "Cart: 0"),
            Op.ui_toast("Cart cleared"),
        )

    @s.action("checkout.start")
    def checkout_start(ctx):
        if not (ctx.store.get("cart") or {}):
            return plan(Op.ui_toast("Cart empty", level="error"))
        return plan(
            *navigate_to("/checkout", title="Checkout"),
            *clear_form_errors("checkout", ["email"]),
            Op.ui_focus("checkout.email"),
        )

    @s.action("checkout.submit")
    def checkout_submit(ctx):
        email = str(ctx.args.get("email") or "").strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            return plan(*form_errors("checkout", {"email": "Valid email required"}))
        cart = ctx.store.get("cart") or {}
        if not cart:
            return plan(Op.ui_toast("Cart empty", level="error"))
        order_id = "ord-" + str(abs(hash(email + str(sorted(cart))) ) % 10_000_000)
        order = {"id": order_id, "email": email, "cart": cart}
        ctx.store["last_order"] = order
        ctx.store["cart"] = {}
        return plan(
            Op.kv_set("cart", {}),
            Op.kv_set("last_order", order),
            Op.ui_set_text("cart", "Cart: 0"),
            *navigate_to("/thanks", title="Thanks", replace=True),
            Op.ui_morph(
                "shell",
                {"tag": "main", "attrs": {"id": "shell"}, "text": f"Order {order_id} for {email}"},
            ),
            Op.ui_toast("Order placed", level="success"),
            Op.log_append("checkout.ok", fields={"order": order_id}),
        )

    @s.on("timer.fired")
    def on_timer(ev, surface: Surface):
        # Live path is the pre-minted continuation (Surface.handle_event).
        # No un-capped compose — fail closed if nothing was armed.
        return None

    @s.on("http.response")
    def on_http(ev, surface: Surface):
        if ev.get("id") != "search-1":
            return None
        items = (ev.get("body") or {}).get("items") or []
        q = str(surface.store.get("search.pending") or "").lower()
        local = [it for it in CATALOG.values() if q in it["title"].lower()]
        merged = local or items
        surface.store["search.results"] = merged
        children = [
            {
                "tag": "li",
                "attrs": {"id": f"hit-{it.get('id')}"},
                "text": f"{it.get('title')} — ${it.get('price')}",
            }
            for it in merged
            if isinstance(it, dict)
        ]
        return plan(
            *set_loading("search", False, f"{len(children)} hits"),
            Op.ui_morph("results", {"tag": "ul", "attrs": {"id": "results"}, "children": children}),
            Op.ui_toast(f"Found {len(children)}", level="success"),
        )

    @s.on("http.error")
    def on_err(ev, surface: Surface):
        return plan(
            *set_loading("search", False, "Error"),
            Op.ui_toast(ev.get("message") or "error", level="error"),
        )

    return s
