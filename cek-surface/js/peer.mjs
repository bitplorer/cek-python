/**
 * cek-surface Peer — apply Result.ops only. Emit events for async.
 * No mint. No recipes. Fail closed on unknown ops.
 */

import { createInterface } from "node:readline";
import { createPeerIR } from "./peer_ir.mjs";

const ir = createPeerIR({ coalesceMs: 50 });

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
};

ir.bindWorld(world);

function snapshot() {
  return {
    kv: Object.fromEntries(world.kv),
    ui: Object.fromEntries(world.ui),
    log: [...world.log],
    nav: {
      path: world.nav.stack[world.nav.index]?.path,
      title: world.nav.stack[world.nav.index]?.title,
      stack: world.nav.stack.map((e) => e.path),
      index: world.nav.index,
    },
    focus: world.focus,
    scroll: world.scroll,
    toast: world.toast,
    busy: Object.fromEntries(world.busy),
    chrome: ir.snapshotChrome(),
  };
}

function ensureNode(target) {
  if (!world.ui.has(target)) {
    world.ui.set(target, { tag: "div", attrs: { id: target }, children: [], text: null });
  }
  return world.ui.get(target);
}

function applyOp(op) {
  const p = op.payload || {};
  const fq = `${op.ns}.${op.name}`;

  switch (fq) {
    case "kv.set":
      world.kv.set(p.key, p.value);
      return;
    case "kv.delete":
      world.kv.delete(p.key);
      return;
    case "kv.merge": {
      const cur = world.kv.get(p.key);
      const base = cur && typeof cur === "object" && !Array.isArray(cur) ? { ...cur } : {};
      world.kv.set(p.key, { ...base, ...(p.patch || {}) });
      return;
    }
    case "ui.dom.morph":
      world.ui.set(p.target, p.patch);
      return;
    case "ui.dom.restore":
      world.ui.set(p.target, p.snapshot);
      return;
    case "ui.dom.remove":
      world.ui.delete(p.target);
      return;
    case "ui.dom.set_text":
      ensureNode(p.target).text = p.text;
      return;
    case "ui.dom.set_attr": {
      const n = ensureNode(p.target);
      n.attrs = n.attrs || {};
      n.attrs[p.attr] = p.value;
      return;
    }
    case "ui.focus":
      world.focus = p.target;
      return;
    case "ui.scroll":
      world.scroll = { target: p.target, block: p.block || "start" };
      return;
    case "ui.toast":
      world.toast = { message: p.message, level: p.level || "info", ms: p.ms ?? 3000 };
      return;
    case "ui.busy":
      world.busy.set(p.target, !!p.busy);
      return;
    case "nav.push":
      world.nav.stack = world.nav.stack.slice(0, world.nav.index + 1);
      world.nav.stack.push({ path: p.path, title: p.title ?? null, state: p.state ?? null });
      world.nav.index = world.nav.stack.length - 1;
      return;
    case "nav.replace":
      world.nav.stack[world.nav.index] = {
        path: p.path,
        title: p.title ?? null,
        state: p.state ?? null,
      };
      return;
    case "nav.back":
      world.nav.index = Math.max(0, world.nav.index - Math.max(1, Number(p.steps) || 1));
      return;
    case "http.request": {
      const id = p.id;
      if (world.http.has(id)) {
        const prev = world.http.get(id);
        prev.abort?.();
        if (prev._timer) clearTimeout(prev._timer);
      }
      const ac = {
        aborted: false,
        abort() {
          this.aborted = true;
        },
      };
      world.http.set(id, ac);
      const delay = Math.min(40, Number(p.timeout_ms) || 40);
      ac._timer = setTimeout(() => {
        if (ac.aborted) return;
        world.http.delete(id);
        const url = String(p.url || "");
        if (url.includes("/fail")) {
          emit({
            type: "events",
            events: [{ type: "http.error", id, status: 500, message: "upstream failure" }],
          });
          return;
        }
        let items = [];
        try {
          const u = new URL(url, "https://api.local");
          const q = u.searchParams.get("q") || "";
          if (q) {
            items = [
              { id: "1", title: `${q} — overview`, price: 10 },
              { id: "2", title: `${q} — pro`, price: 25 },
            ];
          }
        } catch {
          /* ignore */
        }
        emit({
          type: "events",
          events: [
            {
              type: "http.response",
              id,
              status: 200,
              body: { ok: true, url, items, echo: p.body ?? null },
            },
          ],
        });
      }, delay);
      return;
    }
    case "http.cancel": {
      const ac = world.http.get(p.id);
      if (ac) {
        ac.abort();
        if (ac._timer) clearTimeout(ac._timer);
        world.http.delete(p.id);
      }
      return;
    }
    case "timer.clear": {
      const h = world.timers.get(p.id);
      if (h) clearTimeout(h);
      world.timers.delete(p.id);
      return;
    }
    case "timer.set": {
      const prev = world.timers.get(p.id);
      if (prev) clearTimeout(prev);
      const id = p.id;
      const h = setTimeout(() => {
        world.timers.delete(id);
        emit({ type: "events", events: [{ type: "timer.fired", id }] });
      }, Number(p.ms) || 0);
      world.timers.set(id, h);
      return;
    }
    case "log.append":
      world.log.push({
        message: p.message,
        level: p.level || "info",
        fields: p.fields || null,
        t: Date.now(),
      });
      return;
    case "signal.set":
      world.kv.set(`signal:${p.path}`, p.value);
      return;
    case "ui.dom.swap":
      world.ui.set(p.target, { tag: "html", mode: p.mode || "inner", html: p.html });
      return;
    case "nav.reload":
      world.nav.reload = true;
      return;
    case "sys.noop":
      return;
    default:
      throw new Error(`unknown op: ${fq}`);
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
      if (op.ns === "ui" && op.name === "toast") ir.toastFade(op.payload?.ms ?? 3000);
    } catch (e) {
      receipt.failed.push({ op, error: String(e) });
    }
  }
  return receipt;
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
  if (msg.type === "apply") {
    emit({ type: "applied", receipt: applyResult(msg.result), world: snapshot() });
  } else if (msg.type === "chrome") {
    const c = msg.chrome || {};
    if (c.op === "pending") ir.pending(c.target, c.on !== false);
    else if (c.op === "shadowMorph") ir.shadowMorph(c.target, c.patch);
    else if (c.op === "filterCached") ir.filterCached(c.kvKey, c.query, c.outTarget);
    else if (c.op === "clearShadows") ir.clearShadows();
    emit({ type: "chrome_applied", world: snapshot() });
  } else if (msg.type === "done") {
    for (const h of world.timers.values()) clearTimeout(h);
    for (const ac of world.http.values()) {
      ac.abort?.();
      if (ac._timer) clearTimeout(ac._timer);
    }
    break;
  } else {
    emit({ type: "events", events: [{ type: "peer.error", error: `unknown ${msg.type}` }] });
  }
}
