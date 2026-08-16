/**
 * Single apply of S + Phase 2 stamped extensions.
 * Pair identity: (ns, name), name is one token.
 * No mint. No recipes. Undeclared / unstamped pair throws.
 *
 * Session stamp: if set, only those pairs apply. Stamp may include
 * structure-valid extension pairs; those need a registered driver.
 */

export const S_PAIRS = [
  ["kv", "set"],
  ["kv", "delete"],
  ["log", "append"],
  ["ui.dom", "morph"],
  ["ui.dom", "restore"],
];

export const BASELINE_PAIRS = [
  ["kv", "set"],
  ["kv", "delete"],
  ["log", "append"],
];

function keyOf(ns, name) {
  return ns + "\0" + name;
}

function pairSet(list) {
  const s = new Set();
  for (const p of list) {
    const ns = Array.isArray(p) ? p[0] : p.ns;
    const name = Array.isArray(p) ? p[1] : p.name;
    s.add(keyOf(String(ns), String(name)));
  }
  return s;
}

function nameIsToken(name) {
  return !!name && name === name.toLowerCase() && !name.includes(".") && /^[a-z0-9]+$/.test(name);
}

const S_SET = pairSet(S_PAIRS);
let sessionStamp = null;
const drivers = new Map();

// Phase 2 sample driver — not core S. Only fires if stamp contains the pair.
registerDriver("demo.echo", "ping", (world, p) => {
  world.kv.set("echo:last", p.value ?? p.message ?? true);
  world.log.push({ message: `echo:${p.value ?? p.message ?? "ping"}`, level: "info", t: Date.now() });
});

registerDriver("search", "hits", (world, p) => {
  const items = Array.isArray(p.items) ? p.items : [];
  world.kv.set("search:q", p.q ?? "");
  world.kv.set("search:hits", items);
  if (p.target) {
    world.ui.set(p.target, {
      tag: "ul",
      attrs: { id: p.target },
      children: items.map((r, i) => ({
        tag: "li",
        attrs: { id: `hit-${i}` },
        text: (r && (r.title || r.name)) || String(r ?? i),
      })),
    });
  }
});

registerDriver("search", "clear", (world, p) => {
  world.kv.delete("search:q");
  world.kv.delete("search:hits");
  if (p.target) world.ui.delete(p.target);
});

export function registerDriver(ns, name, fn) {
  drivers.set(keyOf(ns, name), fn);
}

export function getStamp() {
  return sessionStamp;
}

export function setStamp(pairs) {
  if (!pairs || !pairs.length) {
    sessionStamp = null;
    return null;
  }
  const next = new Set();
  for (const p of pairs) {
    const ns = String(Array.isArray(p) ? p[0] : p.ns);
    const name = String(Array.isArray(p) ? p[1] : p.name);
    if (S_SET.has(keyOf(ns, name))) {
      next.add(keyOf(ns, name));
      continue;
    }
    // Phase 2 extension: token name, no empty ns
    if (!nameIsToken(name) || !ns) continue;
    next.add(keyOf(ns, name));
  }
  sessionStamp = next.size ? next : pairSet(BASELINE_PAIRS);
  return sessionStamp;
}

export function clearStamp() {
  sessionStamp = null;
}

export function stampAllows(ns, name) {
  const table = sessionStamp || S_SET;
  return table.has(keyOf(ns, name));
}

export function createWorld() {
  return {
    kv: new Map(),
    ui: new Map(),
    log: [],
    busy: new Map(),
    shadow: new Map(),
  };
}

function applyBuiltin(world, ns, name, p) {
  if (ns === "kv" && name === "set") {
    world.kv.set(p.key, p.value);
    return true;
  }
  if (ns === "kv" && name === "delete") {
    world.kv.delete(p.key);
    return true;
  }
  if (ns === "ui.dom" && name === "morph") {
    world.ui.set(p.target, p.patch);
    return true;
  }
  if (ns === "ui.dom" && name === "restore") {
    world.ui.set(p.target, p.snapshot);
    return true;
  }
  if (ns === "log" && name === "append") {
    world.log.push({
      message: p.message,
      level: p.level || "info",
      fields: p.fields || null,
      t: Date.now(),
    });
    return true;
  }
  return false;
}

export function applyS(world, op) {
  const p = op.payload || {};
  const ns = String(op.ns || "");
  const name = String(op.name || "");
  if (!name || name.includes(".")) {
    throw new Error(`illegal pair: ${ns}.${name}`);
  }
  if (!stampAllows(ns, name)) {
    throw new Error(`illegal pair: ${ns}.${name} — absent from session stamp`);
  }
  if (applyBuiltin(world, ns, name, p)) return;
  const drv = drivers.get(keyOf(ns, name));
  if (drv) {
    drv(world, p, op);
    return;
  }
  throw new Error(`illegal pair: ${ns}.${name} — no driver`);
}

export function applyResultS(world, result, { before } = {}) {
  const receipt = { landed: [], failed: [] };
  if (!result || result.kind !== "ok") return receipt;
  if (typeof before === "function") before();
  for (const op of result.ops || []) {
    try {
      applyS(world, op);
      receipt.landed.push(op);
    } catch (e) {
      receipt.failed.push({ op, error: String(e) });
    }
  }
  return receipt;
}

export function snapshotS(world, extra = {}) {
  return {
    kv: Object.fromEntries(world.kv),
    ui: Object.fromEntries(world.ui),
    log: [...world.log],
    nav: world.kv.get("ui:nav") || { path: "/", title: "Home" },
    busy: world.busy ? Object.fromEntries(world.busy) : {},
    ...extra,
  };
}
