# Decisions (non-obvious)

### D1 — Control flow stays in Python
Host composes list[Op]; Peer applies closed drivers; events return to Host. Rejected: plan IR, recipes, eval, executable AST on Peer.

### D2 — Discard cek-plan as product IR
Effect algebra = Op constructors ↔ Peer drivers; macros = Python only.

### D3 — Surface depends on Host kernel
Product Caps in cek-host; surface does not own Cap policy long-term.

### D4 — No ux-channel dependency
Adopt vocabulary/ideas; never import ux_channel as runtime.

### D5 — Peer IR is perception only
coalesce/flush/shadow/pending; clear shadows on authority Result. Rejected: optimistic authority kv.

### D6 — Carrier plug-and-play, default subprocess
subprocess | memory | websocket; same JSON shapes. Transport ≠ kernel.

### D7 — Python monorepo (cek-python)
cek-host + cek-surface together; law and Rust stay separate repos.

### D8 — PyPI names cek-host / cek-surface
Not cek-host-py.

### D9 — Continuations as Caps, not scripts
Pre-mint attenuated Cap + Intent template for timer.fired.

### D10 — Optimize round-trips, not Host CPU
Benches: Host ~0.03ms; lag is RTT × decisions.
