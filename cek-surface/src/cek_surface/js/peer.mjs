/**
 * cek-surface Peer — apply Result.ops only.
 * No mint. No recipes. Fail closed on unknown ops.
 * Honors a session stamp sent by Host (`type: "stamp"`).
 */

import { createInterface } from "node:readline";
import { createPeerIR } from "./peer_ir.mjs";
import { applyResultS, createWorld, snapshotS, setStamp, getStamp } from "./apply_s.mjs";

const ir = createPeerIR({ coalesceMs: 50 });
const world = createWorld();
ir.bindWorld(world);

function snapshot() {
  return snapshotS(world, { chrome: ir.snapshotChrome() });
}

function applyResult(result) {
  return applyResultS(world, result, { before: () => ir.beforeAuthorityApply() });
}

function stampPairs() {
  const s = getStamp();
  if (!s) return null;
  return [...s].map((k) => {
    const i = k.indexOf("\0");
    return { ns: k.slice(0, i), name: k.slice(i + 1) };
  });
}

let emit = () => {};
const rl = createInterface({ input: process.stdin, crlfDelay: Infinity });
emit = (msg) => process.stdout.write(JSON.stringify(msg) + "\n");

for await (const line of rl) {
  const t = line.trim();
  if (!t) continue;
  let msg;
  try {
    msg = JSON.parse(t);
  } catch (e) {
    emit({ type: "events", events: [{ type: "peer.error", error: String(e) }] });
    continue;
  }
  if (msg.type === "stamp") {
    setStamp(msg.pairs || []);
    emit({ type: "stamp_ack", pairs: stampPairs() });
  } else if (msg.type === "apply") {
    emit({ type: "applied", receipt: applyResult(msg.result), world: snapshot() });
  } else if (msg.type === "chrome") {
    const c = msg.chrome || {};
    if (c.op === "pending") ir.pending(c.target, c.on !== false);
    else if (c.op === "shadowMorph") ir.shadowMorph(c.target, c.patch);
    else if (c.op === "filterCached") ir.filterCached(c.kvKey, c.query, c.outTarget);
    else if (c.op === "clearShadows") ir.clearShadows();
    emit({ type: "chrome_applied", world: snapshot() });
  } else if (msg.type === "done") {
    break;
  } else {
    emit({ type: "events", events: [{ type: "peer.error", error: `unknown ${msg.type}` }] });
  }
}
