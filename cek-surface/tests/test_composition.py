"""Host composition macros + Surface perception helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_surface import (
    Continuation,
    Op,
    Surface,
    form_errors,
    navigate_to,
    plan,
    set_loading,
    signal_set,
)


def test_macros_expand_to_catalog():
    nav = navigate_to("/x", title="X")
    assert [o.fq for o in nav] == ["kv.set", "log.append"]
    assert nav[0].payload["key"] == "ui:nav"
    sig = signal_set("ui.theme", "dark")
    assert sig.fq == "kv.set" and sig.payload["key"] == "signal:ui.theme"
    load = set_loading("main", True, "wait")
    assert load[0].fq == "kv.set"
    assert load[1].fq == "ui.dom.morph"
    errs = form_errors("f", {"email": "required"})
    assert {o.ns for o in errs} <= {"kv", "ui.dom"}
    batch = plan(Op.log_append("a"), *nav)
    assert len(batch) == 3


def test_surface_perception_and_continuation():
    s = Surface(carrier_kind="memory")

    @s.action("boot")
    def boot(ctx):
        ctx.continuations = [
            ctx.surface.mint_continuation("timer.fired:x", "boot", args_from={"q": "store:q"})
        ]
        return [Op.log_append("boot")]

    s.submit("boot", {}, auto_mint=True, drain_async=False)
    ch = s.mark_pending("btn", True)
    assert ch["type"] == "perception_applied"
    sh = s.preview("hdr", {"text": "hi"})
    assert sh["type"] == "perception_applied"
    assert isinstance(s.last_continuations[0], Continuation) or s.last_continuations


if __name__ == "__main__":
    test_macros_expand_to_catalog()
    test_surface_perception_and_continuation()
    print("composition ok")
