/**
 * Browser Peer shell — apply Result.ops + Peer IR (coalesce/flush/shadow).
 * Carrier: postMessage or WebSocket JSON (same message shapes as peer.mjs).
 *
 * Usage (page):
 *   import { mountBrowserPeer } from './browser_peer.mjs';
 *   const peer = mountBrowserPeer({ send: (msg) => ws.send(JSON.stringify(msg)) });
 *   ws.onmessage = (e) => peer.onMessage(JSON.parse(e.data));
 *   peer.bindSearchInput(document.querySelector('#search-input'), {
 *     action: 'search.type',
 *     submitIntent: (args) => hostSubmit('search.type', args),
 *   });
 */

import { createPeerIR } from './peer_ir.mjs';

export function createBrowserWorld() {
  return {
    kv: new Map(),
    ui: new Map(),
    log: [],
    timers: new Map(),
    http: new Map(),
    nav: { stack: [{ path: '/', title: 'Home', state: null }], index: 0 },
    focus: null,
    scroll: null,
    toast: null,
    busy: new Map(),
    shadow: new Map(),
  };
}

export function mountBrowserPeer({ send, coalesceMs = 50, world = null } = {}) {
  const w = world || createBrowserWorld();
  const ir = createPeerIR({ coalesceMs });
  ir.bindWorld(w);

  function applyOp(op) {
    const p = op.payload || {};
    const fq = `${op.ns}.${op.name}`;
    switch (fq) {
      case 'kv.set':
        w.kv.set(p.key, p.value);
        return;
      case 'ui.dom.morph':
        w.ui.set(p.target, p.patch);
        if (typeof document !== 'undefined') {
          const el = document.getElementById(p.target);
          if (el && p.patch?.text != null) el.textContent = p.patch.text;
        }
        return;
      case 'ui.dom.set_text':
        if (typeof document !== 'undefined') {
          const el = document.getElementById(p.target);
          if (el) el.textContent = p.text;
        }
        return;
      case 'ui.toast':
        w.toast = { message: p.message, level: p.level || 'info', ms: p.ms ?? 3000 };
        ir.toastFade(p.ms ?? 3000);
        return;
      case 'ui.busy':
        w.busy.set(p.target, !!p.busy);
        return;
      case 'nav.push':
        w.nav.stack = w.nav.stack.slice(0, w.nav.index + 1);
        w.nav.stack.push({ path: p.path, title: p.title ?? null, state: p.state ?? null });
        w.nav.index = w.nav.stack.length - 1;
        return;
      case 'timer.set': {
        const prev = w.timers.get(p.id);
        if (prev) clearTimeout(prev);
        const id = p.id;
        w.timers.set(
          id,
          setTimeout(() => {
            w.timers.delete(id);
            send({ type: 'events', events: [{ type: 'timer.fired', id }] });
          }, Number(p.ms) || 0),
        );
        return;
      }
      case 'timer.clear': {
        const h = w.timers.get(p.id);
        if (h) clearTimeout(h);
        w.timers.delete(p.id);
        return;
      }
      case 'sys.noop':
        return;
      default:
        // keep fail-soft in browser for unknown chrome-adjacent ops
        w.log.push({ message: `op ${fq}`, level: 'debug' });
    }
  }

  function applyResult(result) {
    const receipt = { landed: [], failed: [] };
    if (!result || result.kind !== 'ok') return receipt;
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

  function onMessage(msg) {
    if (msg.type === 'apply') {
      const receipt = applyResult(msg.result);
      send({ type: 'applied', receipt, world: snapshot() });
    } else if (msg.type === 'chrome') {
      const c = msg.chrome || {};
      if (c.op === 'pending') ir.pending(c.target, c.on !== false);
      else if (c.op === 'shadowMorph') ir.shadowMorph(c.target, c.patch);
      else if (c.op === 'filterCached') ir.filterCached(c.kvKey, c.query, c.outTarget);
      else if (c.op === 'clearShadows') ir.clearShadows();
      send({ type: 'chrome_applied', world: snapshot() });
    }
  }

  function snapshot() {
    return {
      kv: Object.fromEntries(w.kv),
      ui: Object.fromEntries(w.ui),
      toast: w.toast,
      busy: Object.fromEntries(w.busy),
      chrome: ir.snapshotChrome(),
      nav: { path: w.nav.stack[w.nav.index]?.path, index: w.nav.index },
    };
  }

  /**
   * Wire an <input> to coalesce → Intent. Enter/blur flush immediately.
   */
  function bindSearchInput(el, { action = 'search.type', submitIntent, key = null } = {}) {
    if (!el || typeof submitIntent !== 'function') return () => {};
    const ckey = key || action;
    const onInput = () => {
      ir.pending('search', true);
      ir.coalesceIntent(ckey, { q: el.value, ms: 40 }, (args) => {
        submitIntent(action, args);
      });
    };
    const onFlush = () => {
      if (!ir.flush(ckey)) {
        submitIntent(action, { q: el.value, ms: 0 });
      }
    };
    el.addEventListener('input', onInput);
    el.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter') onFlush();
    });
    el.addEventListener('blur', onFlush);
    return () => {
      el.removeEventListener('input', onInput);
      ir.flush(ckey);
    };
  }

  return { onMessage, applyResult, ir, world: w, snapshot, bindSearchInput, send };
}
