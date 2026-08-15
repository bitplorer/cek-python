/**
 * Opt-in WebSocket Peer server — same JSON protocol as peer.mjs.
 *
 *   node demo/ws_peer_server.mjs
 *   Surface(carrier_kind="websocket", carrier_opts={"url": "ws://127.0.0.1:8766"})
 *
 * Requires: npm i ws   (or global) — falls back to print install hint.
 */

import { createServer } from "node:http";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");

let WebSocketServer;
try {
  const require = createRequire(import.meta.url);
  ({ WebSocketServer } = require("ws"));
} catch {
  console.error("Install ws: npm install ws");
  process.exit(1);
}

// Reuse apply logic by spawning protocol compatible with peer — inline minimal
const { createPeerIR } = await import(pathToFileURL(path.join(root, "js/peer_ir.mjs")).href);

const world = {
  kv: new Map(),
  ui: new Map(),
  log: [],
  timers: new Map(),
  http: new Map(),
  nav: { stack: [{ path: "/", title: "Home", state: null }], index: 0 },
  focus: null,
  scroll: null,
  toast: null,
  busy: new Map(),
  shadow: new Map(),
};
const ir = createPeerIR({ coalesceMs: 50 });
ir.bindWorld(world);

function snapshot() {
  return {
    kv: Object.fromEntries(world.kv),
    ui: Object.fromEntries(world.ui),
    toast: world.toast,
    busy: Object.fromEntries(world.busy),
    chrome: ir.snapshotChrome(),
    nav: {
      path: world.nav.stack[world.nav.index]?.path,
      index: world.nav.index,
    },
  };
}

function applyOp(op) {
  const p = op.payload || {};
  const fq = `${op.ns}.${op.name}`;
  switch (fq) {
    case "kv.set":
      world.kv.set(p.key, p.value);
      return;
    case "ui.dom.morph":
      world.ui.set(p.target, p.patch);
      return;
    case "ui.toast":
      world.toast = { message: p.message, level: p.level || "info", ms: p.ms ?? 3000 };
      ir.toastFade(p.ms ?? 3000);
      return;
    case "sys.noop":
      return;
    case "log.append":
      world.log.push(p);
      return;
    default:
      world.log.push({ skipped: fq });
  }
}

function applyResult(result) {
  const receipt = { landed: [], failed: [] };
  if (!result || result.kind !== "ok") return receipt;
  ir.beforeAuthorityApply();
  for (const op of result.ops || []) {
    try {
      applyOp(op);
      receipt.landed.push(op);
    } catch (e) {
      receipt.failed.push({ op, error: String(e) });
    }
  }
  return receipt;
}

const port = Number(process.env.PORT || 8766);
const wss = new WebSocketServer({ port });
console.log(`cek-surface WS Peer ws://127.0.0.1:${port}`);

wss.on("connection", (ws) => {
  ws.on("message", (raw) => {
    let msg;
    try {
      msg = JSON.parse(String(raw));
    } catch (e) {
      ws.send(JSON.stringify({ type: "events", events: [{ type: "peer.error", error: String(e) }] }));
      return;
    }
    if (msg.type === "apply") {
      ws.send(JSON.stringify({ type: "applied", receipt: applyResult(msg.result), world: snapshot() }));
    } else if (msg.type === "chrome") {
      const c = msg.chrome || {};
      if (c.op === "pending") ir.pending(c.target, c.on !== false);
      else if (c.op === "clearShadows") ir.clearShadows();
      ws.send(JSON.stringify({ type: "chrome_applied", world: snapshot() }));
    } else if (msg.type === "done") {
      ws.close();
    }
  });
});
