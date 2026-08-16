/**
 * Browser Peer shell — apply Result.ops + Peer IR (coalesce/flush/shadow).
 * Carrier: postMessage or WebSocket JSON (same message shapes as peer.mjs).
 *
 * Continuations: Peer never mints. Host injects events (e.g. timer.fired);
 * Peer fills declared slots and submits the pre-minted Cap back to Host.
 */

import { createPeerIR } from "./peer_ir.mjs";
import { applyS, createWorld, snapshotS, setStamp } from "./apply_s.mjs";

export function createBrowserWorld() {
  return createWorld();
}

export function matchContinuation(conts, event) {
  const et = String(event?.type || "");
  const key = event?.id != null ? `${et}:${event.id}` : et;
  return (conts || []).find((c) => c.event === key || c.event === et) || null;
}

export function resolveContinuationArgs(cont, { store = {}, event = {} } = {}) {
  const args = { ...(cont.static_args || {}) };
  for (const [name, src] of Object.entries(cont.args_from || {})) {
    if (String(src).startsWith("store:")) args[name] = store[src.slice(6)];
    else if (String(src).startsWith("event:")) args[name] = event[src.slice(6)];
    else args[name] = src;
  }
  return args;
}

function renderPatch(el, patch) {
  if (!el || patch == null) return;
  if (typeof patch !== "object") {
    el.textContent = String(patch);
    return;
  }
  if (patch.attrs && typeof patch.attrs === "object") {
    for (const [k, v] of Object.entries(patch.attrs)) {
      if (k === "id") continue;
      if (v == null) el.removeAttribute(k);
      else el.setAttribute(k, String(v));
    }
  }
  if (Array.isArray(patch.children)) {
    el.replaceChildren();
    if (patch.text) el.appendChild(document.createTextNode(String(patch.text)));
    for (const child of patch.children) {
      const node = document.createElement((child && child.tag) || "div");
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

  function paint(op) {
    if (typeof document === "undefined" || op.ns !== "ui.dom") return;
    const p = op.payload || {};
    const el = document.getElementById(p.target);
    if (!el) return;
    renderPatch(el, op.name === "morph" ? p.patch : p.snapshot);
  }

  function applyOp(op) {
    applyS(w, op);
    paint(op);
  }

  function applyResult(result) {
    const receipt = { landed: [], failed: [] };
    if (result?.continuations) lastContinuations = result.continuations;
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

  function onMessage(msg) {
    if (msg.continuations) lastContinuations = msg.continuations;
    if (msg.type === "stamp") {
      setStamp(msg.pairs || []);
      if (typeof send === "function") send({ type: "stamp_ack", pairs: msg.pairs || [] });
    } else if (msg.type === "apply") {
      const receipt = applyResult(msg.result);
      if (typeof send === "function") send({ type: "applied", receipt, world: snapshot() });
    } else if (msg.type === "chrome") {
      const c = msg.chrome || {};
      if (c.op === "pending") ir.pending(c.target, c.on !== false);
      else if (c.op === "shadowMorph") ir.shadowMorph(c.target, c.patch);
      else if (c.op === "filterCached") ir.filterCached(c.kvKey, c.query, c.outTarget);
      else if (c.op === "clearShadows") ir.clearShadows();
      if (typeof send === "function") send({ type: "chrome_applied", world: snapshot() });
    }
  }

  function snapshot() {
    return snapshotS(w, {
      chrome: ir.snapshotChrome(),
      continuations: lastContinuations,
    });
  }

  function bindSearchInput(el, { action = "search.type", submitIntent: submit, key = null } = {}) {
    const post = submit || submitIntent;
    if (!el || typeof post !== "function") return () => {};
    const ckey = key || action;
    const onInput = () => {
      ir.pending("search", true);
      ir.coalesceIntent(ckey, { q: el.value, ms: 40 }, (args) => {
        post(action, args);
      });
    };
    const onFlush = () => {
      if (!ir.flush(ckey)) {
        post(action, { q: el.value, ms: 0 });
      }
    };
    el.addEventListener("input", onInput);
    el.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") onFlush();
    });
    el.addEventListener("blur", onFlush);
    return () => {
      el.removeEventListener("input", onInput);
      ir.flush(ckey);
    };
  }

  return { onMessage, applyResult, ir, world: w, snapshot, bindSearchInput, send, matchContinuation };
}
