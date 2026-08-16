# Decisions (non-obvious)

**Read [START.md](../START.md) first.** Each entry: **Context → Decision → Why → Rejected**.


---

### D1 — Control flow stays in Python

**Context:** Desire to “compose JS functions from Python” / send if-else on the wire.  
**Decision:** Host composes `list[Op]`; Peer only applies closed drivers; callbacks return as **events** → Host → new Ops.  
**Why:** Arbitrary Peer logic hollows Caps; ambient power returns.  
**Rejected:** cek-plan IR, Peer recipe registry, `eval`, AST-as-executable on Peer.

---

### D2 — Discard cek-plan as a product IR

**Context:** Plan IR felt brittle.  
**Decision:** Effect algebra = Op constructors ↔ Peer drivers; macros = Python only.  
**Why:** One catalog, one wire shape (`Result.ops`).  
**Rejected:** Second schema for seq/if/call on the wire.

---

### D3 — Surface depends on Host kernel, not the reverse

**Context:** Cap mint briefly lived in surface `cap.py`.  
**Decision:** Product Caps in **cek-host**; surface re-exports or loads Host; surface `cap.py` is not the long-term owner.  
**Why:** Authority is one place; apps don’t fork Cap semantics.  
**Rejected:** Surface-owned Cap as production truth.

---

### D4 — No ux-channel dependency

**Context:** Adopt good ideas from ux-channel without coupling.  
**Decision:** Keep Intent/Result/Op vocabulary and Cap idea; implement natively in cek-surface.  
**Why:** Channel-as-kernel and Peer recipes conflict with CEK.  
**Rejected:** `import ux_channel` as runtime.

---

### D5 — Peer IR is perception only

**Context:** RTT makes pure Host-round-trip UI feel laggy.  
**Decision:** coalesce/flush/shadow/pending/filter_cached on Peer; clear shadows on authority Result.  
**Why:** Humans need &lt;100 ms feedback; authority can wait one RTT.  
**Rejected:** Optimistic authority kv writes; Peer-side checkout/policy.

---

### D6 — Carrier is plug-and-play, default subprocess

**Context:** Need tests, demos, and eventual browser without three kernels.  
**Decision:** `open_carrier("subprocess"|"memory"|"websocket")`; same message shapes.  
**Why:** Transport ≠ authority; zero-config demos.  
**Rejected:** Hard-wiring WebSocket as required dep.

---

### D7 — Python monorepo, not N repos

**Context:** Confusion about where host/peer/surface live.  
**Decision:** `cek-python` holds `cek-host` + `cek-surface`; law and Rust stay separate repos.  
**Why:** Shared version/API; clear pip story.  
**Rejected:** Putting Python inside cek-runtime; one repo for law+all runtimes.

---

### D8 — PyPI names `cek-host` / `cek-surface` (not `cek-host-py`)

**Context:** Naming clutter.  
**Decision:** Short names; “Python” implied by ecosystem.  
**Why:** Install ergonomics.  

---

### D9 — Continuations as Caps, not scripts

**Context:** Debounce/search multi-RTT.  
**Decision:** Pre-mint attenuated Cap + Intent template for `timer.fired`.  
**Why:** Saves a “what next?” hop without Peer policy.  
**Rejected:** Named Peer recipes for search commit.

---

### D10 — Enterprise lag targets inform Peer IR, not Host rewrite

**Context:** Host path already ≪ 1 ms.  
**Decision:** Optimize round-trips and interim chrome; do not put policy on Peer.  
**Why:** Benches proved CPU is noise vs RTT.  
