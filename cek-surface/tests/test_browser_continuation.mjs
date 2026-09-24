/**
 * The browser peer submits a pre-minted timer continuation. It does not mint.
 */
import assert from "node:assert/strict";
import { mountBrowserPeer } from "../src/cek_surface/js/browser_peer.mjs";

const calls = [];
const peer = mountBrowserPeer({
  submitIntent: (action, args, cap) => calls.push({ action, args, cap }),
});

peer.onMessage({
  type: "apply",
  result: {
    kind: "ok",
    ops: [{ ns: "kv", name: "set", payload: { key: "search.pending", value: "widget" } }],
  },
  continuations: [
    {
      event: "timer.fired:search-debounce",
      action: "search.commit",
      cap: "CAP",
      args_from: { q: "store:search.pending" },
      static_args: { ms: 0 },
    },
  ],
});

await new Promise((resolve) => setTimeout(resolve, 30));
assert.equal(calls.length, 1);
assert.equal(calls[0].action, "search.commit");
assert.equal(calls[0].args.q, "widget");
assert.equal(calls[0].cap, "CAP");
assert.equal(calls[0].args.ms, 0);

peer.onMessage({
  type: "apply",
  result: { kind: "authority_refusal", ops: [], error: "cap required" },
  continuations: [
    { event: "timer.fired:search-debounce", action: "search.commit", cap: "NO", static_args: { ms: 0 } },
  ],
});
await new Promise((resolve) => setTimeout(resolve, 30));
assert.equal(calls.length, 1);
console.log("browser continuation ok");
