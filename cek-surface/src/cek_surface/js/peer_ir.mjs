/**
 * Peer IR v0 — perception only.
 * Shadow chrome, coalesce, closed reducers.
 * No mint. No authority kv writes. No recipes.
 */

export function createPeerIR({ coalesceMs = 50 } = {}) {
  const shadows = new Map(); // target -> shadow node
  const coalesce = new Map(); // key -> { timer, lastArgs, send }
  let worldRef = null;

  function bindWorld(world) {
    worldRef = world;
    if (!world.shadow) world.shadow = new Map();
  }

  /** Immediate chrome — not Result.ops, not lineage. */
  function pending(target, on = true) {
    if (!worldRef) return;
    worldRef.busy.set(target, !!on);
    worldRef.shadow.set(`pending:${target}`, { on: !!on, t: Date.now() });
  }

  function shadowMorph(target, patch) {
    if (!worldRef) return;
    shadows.set(target, patch);
    worldRef.shadow.set(target, { patch, t: Date.now() });
    // do not write world.ui authority tree as final truth
  }

  function clearShadows() {
    shadows.clear();
    if (worldRef?.shadow) worldRef.shadow.clear();
    if (worldRef?.busy) worldRef.busy.clear();
  }

  /** Call before applying authority Result. */
  function beforeAuthorityApply() {
    clearShadows();
  }

  function toastFade(ms = 3000) {
    if (!worldRef?.toast) return;
    const t = worldRef.toast;
    setTimeout(() => {
      if (worldRef.toast === t) worldRef.toast = null;
    }, ms);
  }

  /** Filter cached list in kv — display only. */
  function filterCached(kvKey, query, outTarget) {
    if (!worldRef) return;
    const raw = worldRef.kv.get(kvKey);
    const q = String(query || "").toLowerCase();
    let rows = Array.isArray(raw) ? raw : raw && typeof raw === "object" ? Object.values(raw) : [];
    if (q) {
      rows = rows.filter((r) => JSON.stringify(r).toLowerCase().includes(q));
    }
    worldRef.ui.set(outTarget, {
      tag: "ul",
      attrs: { id: outTarget, "data-cek-chrome": "1" },
      children: rows.map((r, i) => ({
        tag: "li",
        attrs: { id: `chrome-hit-${i}` },
        text: r.title || r.name || String(r.id || i),
      })),
    });
  }

  /**
   * Coalesce Intents: at most one send per key per coalesceMs.
   * send(args) should post Intent to Host.
   */
  function coalesceIntent(key, args, send) {
    const prev = coalesce.get(key);
    if (prev?.timer) clearTimeout(prev.timer);
    const entry = {
      lastArgs: args,
      send,
      timer: setTimeout(() => {
        const e = coalesce.get(key);
        coalesce.delete(key);
        if (e) e.send(e.lastArgs);
      }, coalesceMs),
    };
    coalesce.set(key, entry);
  }

  /** Flush pending Intent immediately (Enter / blur / submit). */
  function flush(key) {
    const e = coalesce.get(key);
    if (!e) return false;
    if (e.timer) clearTimeout(e.timer);
    coalesce.delete(key);
    e.send(e.lastArgs);
    return true;
  }

  function flushAll() {
    for (const key of [...coalesce.keys()]) flush(key);
  }

  function pendingKeys() {
    return [...coalesce.keys()];
  }

  function snapshotChrome() {
    return {
      shadows: Object.fromEntries(worldRef?.shadow || []),
      busy: worldRef ? Object.fromEntries(worldRef.busy) : {},
    };
  }

  return {
    bindWorld,
    pending,
    shadowMorph,
    clearShadows,
    beforeAuthorityApply,
    toastFade,
    filterCached,
    coalesceIntent,
    flush,
    flushAll,
    pendingKeys,
    snapshotChrome,
  };
}
