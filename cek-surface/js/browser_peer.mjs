/**
 * Browser Peer shell — apply Result.ops + Peer IR (coalesce/flush/shadow).
 * Carrier: postMessage or WebSocket JSON (same message shapes as peer.mjs).
 *
 * Continuations: Peer never mints. On timer.fired it fills declared slots
 * and submits the pre-minted Cap back to Host.
 *
 * Usage (page):
 *   import { mountBrowserPeer } from './browser_peer.mjs';
 *   const peer = mountBrowserPeer({
 *     send: (msg) => ws.send(JSON.stringify(msg)),
 *     submitIntent: (action, args, cap) => hostSubmit(action, args, cap),
 *   });
 *   ws.onmessage = (e) => peer.onMessage(JSON.parse(e.data));
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

export function matchContinuation(conts, event) {
  const et = String(event?.type || '');
  const key = event?.id != null ? `${et}:${event.id}` : et;
  return (conts || []).find((c) => c.event === key || c.event === et) || null;
}

export function resolveContinuationArgs(cont, { store = {}, event = {} } = {}) {
  const args = { ...(cont.static_args || {}) };
  for (const [name, src] of Object.entries(cont.args_from || {})) {
    if (String(src).startsWith('store:')) args[name] = store[src.slice(6)];
    else if (String(src).startsWith('event:')) args[name] = event[src.slice(6)];
    else args[name] = src;
  }
  return args;
}

function renderPatch(el, patch) {
  if (!el || patch == null) return;
  if (typeof patch !== 'object') {
    el.textContent = String(patch);
    return;
  }
  if (patch.attrs && typeof patch.attrs === 'object') {
    for (const [k, v] of Object.entries(patch.attrs)) {
      if (k === 'id') continue;
      if (v == null) el.removeAttribute(k);
      else el.setAttribute(k, String(v));
    }
  }
  if (Array.isArray(patch.children)) {
    el.replaceChildren();
    if (patch.text) el.appendChild(document.createTextNode(String(patch.text)));
    for (const child of patch.children) {
      const node = document.createElement((child && child.tag) || 'div');
      if (child && child.attrs) {
        for (const [k, v] of Object.entries(child.attrs)) {
          if (v != null) node.setAttribute(k, String(v));
        }
      }
      if (child && Array.isArray(child.children)) renderPatch(node, child);
      else if (child && child.text != null) node.textContent = String(child.text);
      el.appendChild(node);
    }
    return;
  }
  if (patch.text != null) el.textContent = String(patch.text);
}

export function mountBrowserPeer({ send, submitIntent, coalesceMs = 50, world = null } = {}) {
  const w = world || createBrowserWorld();
  const ir = createPeerIR({ coalesceMs });
  ir.bindWorld(w);
  let lastContinuations = [];

  function showToast(msg, ms = 2000) {
    if (typeof document === 'undefined') return;
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.style.display = 'block';
    setTimeout(() => {
      if (t.textContent === msg) t.style.display = 'none';
    }, ms);
  }

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
          if (el) renderPatch(el, p.patch);
        }
        return;
      case 'ui.dom.set_text':
        if (typeof document !== 'undefined') {
          const el = document.getElementById(p.target);
          if (el) el.textContent = p.text;
        }
        return;
      case 'ui.dom.swap':
        if (typeof document !== 'undefined') {
          const el = document.getElementById(p.target);
          if (el) {
            if (p.mode === 'outer') el.outerHTML = p.html || '';
            else el.innerHTML = p.html || '';
          }
        }
        return;
      case 'ui.toast':
        w.toast = { message: p.message, level: p.level || 'info', ms: p.ms ?? 3000 };
        ir.toastFade(p.ms ?? 3000);
        showToast(p.message, p.ms ?? 3000);
        return;
      case 'ui.busy':
        w.busy.set(p.target, !!p.busy);
        if (typeof document !== 'undefined') {
          const el = document.getElementById(p.target);
          if (el) el.classList.toggle('pending', !!p.busy);
        }
        return;
      case 'nav.push':
        w.nav.stack = w.nav.stack.slice(0, w.nav.index + 1);
        w.nav.stack.push({ path: p.path, title: p.title ?? null, state: p.state ?? null });
        w.nav.index = w.nav.stack.length - 1;
        return;
      case 'nav.replace':
        w.nav.stack[w.nav.index] = { path: p.path, title: p.title ?? null, state: p.state ?? null };
        return;
      case 'timer.set': {
        const prev = w.timers.get(p.id);
        if (prev) clearTimeout(prev);
        const id = p.id;
        w.timers.set(
          id,
          setTimeout(() => {
            w.timers.delete(id);
            const ev = { type: 'timer.fired', id };
            const cont = matchContinuation(lastContinuations, ev);
            if (cont && typeof submitIntent === 'function') {
              const args = resolveContinuationArgs(cont, {
                store: Object.fromEntries(w.kv),
                event: ev,
              });
              submitIntent(cont.action, args, cont.cap);
              lastContinuations = lastContinuations.filter((c) => c !== cont);
              return;
            }
            if (typeof send === 'function') {
              send({ type: 'events', events: [ev] });
            }
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
      case 'log.append':
        w.log.push({ message: p.message, level: p.level || 'info' });
        return;
      case 'sys.noop':
        return;
      default:
        w.log.push({ message: `op ${fq}`, level: 'debug' });
    }
  }

  function applyResult(result) {
    const receipt = { landed: [], failed: [] };
    if (result?.continuations) lastContinuations = result.continuations;
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
    if (msg.continuations) lastContinuations = msg.continuations;
    if (msg.type === 'apply') {
      const receipt = applyResult(msg.result);
      if (typeof send === 'function') send({ type: 'applied', receipt, world: snapshot() });
    } else if (msg.type === 'chrome') {
      const c = msg.chrome || {};
      if (c.op === 'pending') ir.pending(c.target, c.on !== false);
      else if (c.op === 'shadowMorph') ir.shadowMorph(c.target, c.patch);
      else if (c.op === 'filterCached') ir.filterCached(c.kvKey, c.query, c.outTarget);
      else if (c.op === 'clearShadows') ir.clearShadows();
      if (typeof send === 'function') send({ type: 'chrome_applied', world: snapshot() });
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
      continuations: lastContinuations,
    };
  }

  /**
   * Wire an <input> to coalesce → Intent. Enter/blur flush immediately.
   */
  function bindSearchInput(el, { action = 'search.type', submitIntent: submit, key = null } = {}) {
    const post = submit || submitIntent;
    if (!el || typeof post !== 'function') return () => {};
    const ckey = key || action;
    const onInput = () => {
      ir.pending('search', true);
      ir.coalesceIntent(ckey, { q: el.value, ms: 40 }, (args) => {
        post(action, args);
      });
    };
    const onFlush = () => {
      if (!ir.flush(ckey)) {
        post(action, { q: el.value, ms: 0 });
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

  return { onMessage, applyResult, ir, world: w, snapshot, bindSearchInput, send, matchContinuation };
}
