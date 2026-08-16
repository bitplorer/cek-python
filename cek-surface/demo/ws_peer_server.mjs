/**
 * Opt-in WebSocket Peer server — same JSON protocol as peer.mjs.
 *
 *   node demo/ws_peer_server.mjs
 *   Surface(carrier_kind="websocket", carrier_opts={"url": "ws://127.0.0.1:8766"})
 */

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

const { createPeerIR } = await import(pathToFileURL(path.join(root, "js/peer_ir.mjs")).href);
const { applyResultS, createWorld, snapshotS } = await import(
  pathToFileURL(path.join(root, "js/apply_s.mjs")).href
);

const world = createWorld();
const ir = createPeerIR({ coalesceMs: 50 });
ir.bindWorld(world);

function snapshot() {
  return snapshotS(world, { chrome: ir.snapshotChrome() });
}

function applyResult(result) {
  return applyResultS(world, result, { before: () => ir.beforeAuthorityApply() });
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
