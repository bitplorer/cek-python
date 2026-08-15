# Narrative timeline (so “what happened” is not tribal knowledge)

## Phase A — Law and Rust

- CEK framed as Cap → Intent → Result.ops → apply → lineage/reverse  
- cek-framework = law; cek-runtime = Rust implementation + vectors  
- Hard rules: refuse → zero ops; Peer no mint; once; fail closed  

## Phase B — Python Host ↔ JS Peer need

- Goal: write logic in Python, effects on JS, without shipping code on the wire  
- Explored AST/N-API/FFI; concluded **Option 1**: plan-in-Python, execute-as-Ops-on-Peer  
- Rejected “arbitrary JS composition on the wire”  

## Phase C — Radical surface

- Doctrine locked: Composition = Python + Caps; wire = Result.ops; Peer = drivers + events  
- Built cek-surface Op catalog, Surface actions, embedded Cap then Host kernel split  
- Absorbed **ideas** from ux-channel without depending on it  

## Phase D — Latency and Peer IR

- Benches showed Host/Peer local path ≪ human threshold  
- Network RTT dominates; multi-round flows feel slow  
- Peer IR: coalesce, flush, shadow, pending — perception clock only  

## Phase E — Carriers and productization

- Carrier abstraction: subprocess default, memory tests, websocket opt-in  
- Shop demo, browser page, HTTP host, WS peer server  
- Package split: **cek-host** + **cek-surface**  

## Phase F — Organization

- Created **bitplorer/cek-python** monorepo  
- Documented install story; linked from cek-runtime PORTS.md  
- Partial GitHub upload → surface remote incomplete → documented in GITHUB_STATUS.md  

## Phase G — Knowledge capture (this docs set)

- SHIPPED / ARCHITECTURE / DECISIONS / INVARIANTS / ROADMAP / LATENCY / GITHUB_STATUS  
- Goal: next human or agent can continue without chat archaeology  

## Phase H — P0–P3 productization (2026-08-15)

- **P0:** Full surface tree on GitHub; editable install smoke; CI `test.yml`
- **P1:** Browser E2E + live continuation Cap path (timer.fired → pre-minted once Cap)
- **P2:** Golden vectors (`surface_core.json` v2, 14 cases) + `run_ws_demo.sh`
- **P3 path:** `build_release.sh`, split `publish-testpypi.yml`  
  Environments: `testpypi-host` / `testpypi-surface`  
  Live index upload still needs publisher registration (see TESTPYPI_SETUP.md)
- Knowledge base expanded: PERFORMANCE, PACKAGING, TESTPYPI_SETUP
