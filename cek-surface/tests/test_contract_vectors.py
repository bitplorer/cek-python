"""Aligned contract family — load the Rust JSON fixtures.

Source of truth: cek-runtime/crates/cek-contract/vectors
Vendored copy:   cek-surface/vectors/contract  (for cek-python CI)

One adapter: Cap-dict claims → published hex-token. No third refuse reason.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_host import Host, args_hash, result_digest

ORACLE = "96e4f83e3793b646323a67f314b51044"
SECRET = b"contract-vector-secret-32b!!!!!!"

# Hot family G5 / W9. Phase 2 (ed25519, lineage, idem, law-gen) stays in runtime.
ALIGNED_IDS = {
    "empty-action-refuse",
    "cap-refuse-action-mismatch",
    "cap-refuse-expired",
    "once-second-use",
    "sealed-args-mismatch",
    "sealed-args-match",
    "subject-bind-mismatch",
    "subject-bind-ok",
    "subject-bind-missing",
    "scope-denies-key",
    "scope-allows-key",
    "empty-scope-token",
    "cap-sig-tamper",
    "cap-sig-missing",
}


def _vector_roots() -> tuple[Path, Path]:
    # tests/ → cek-surface → cek-python → cek (workspace sibling)
    sibling = ROOT.parent.parent / "cek-runtime" / "crates" / "cek-contract" / "vectors"
    vendored = ROOT / "vectors" / "contract"
    return sibling, vendored


def load_aligned() -> list[dict]:
    sibling, vendored = _vector_roots()
    root = sibling if sibling.is_dir() else vendored
    cases: list[dict] = []
    for p in sorted(root.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("id") in ALIGNED_IDS:
            cases.append(data)
    missing = ALIGNED_IDS - {c["id"] for c in cases}
    assert not missing, f"missing fixtures in {root}: {sorted(missing)}"
    return cases


def test_oracle():
    assert args_hash({"sku": "abc-123", "qty": 2}) == ORACLE


def test_vendored_matches_runtime_when_present():
    sibling, vendored = _vector_roots()
    if not sibling.is_dir():
        return
    for p in vendored.glob("*.json"):
        other = sibling / p.name
        assert other.is_file(), p.name
        assert p.read_text(encoding="utf-8") == other.read_text(encoding="utf-8"), p.name


def _project_ops(case: dict, intent: dict) -> list[dict]:
    if case.get("expect_ops"):
        return list(case["expect_ops"])
    args = intent.get("args") or {}
    if (intent.get("action") or "") == "kv.write":
        return [{"ns": "kv", "name": "set", "payload": {"key": args.get("key"), "value": args.get("value")}}]
    return [{"ns": "sys", "name": "noop", "payload": {}}]


def _mint(host: Host, cap: dict, intent_args: dict, expect_kind: str, case_id: str) -> str:
    action = str(cap.get("action") or "")
    if not action.strip():
        return "not-a-valid-cap"
    kw: dict = {"once": bool(cap.get("once")), "jti": str(cap.get("id") or "") or None}
    if cap.get("scopes") is not None:
        kw["scopes"] = list(cap["scopes"])
    if cap.get("subject") is not None:
        kw["subject"] = cap["subject"]
    if cap.get("not_after") is not None:
        kw["not_after"] = float(cap["not_after"])
    seal = "sealed_args_bind" in cap
    mint_args = dict(intent_args)
    if seal and expect_kind != "ok":
        mint_args = {"_sealed_to": "other"}
    tok = host.mint(action, args=mint_args if seal else (intent_args or None), seal_args=seal, **kw)
    if case_id == "cap-sig-tamper":
        body, sig = tok.rsplit(".", 1)
        tok = body + "." + ("0" if sig[0] != "0" else "1") + sig[1:]
    if case_id == "cap-sig-missing":
        tok = tok.rsplit(".", 1)[0]
    return tok


def run_case(case: dict) -> None:
    host = Host(secret=SECRET)
    if case.get("now") is not None:
        now = float(case["now"])
        host.caps.now_fn = lambda: now

    tokens: dict[str, str] = {}

    def token_for(cap: dict | None, args: dict, expect_kind: str) -> str | None:
        if not cap:
            return None
        jti = str(cap.get("id") or "")
        if jti and jti in tokens and case["id"] == "once-second-use":
            return tokens[jti]
        tok = _mint(host, cap, args, expect_kind, case["id"])
        if jti:
            tokens[jti] = tok
        return tok

    if case.get("prior_intent"):
        prior = case["prior_intent"]
        pargs = dict(prior.get("args") or {})
        ptok = token_for(prior.get("cap"), pargs, "ok")
        pr = host.submit(
            action=prior.get("action") or "",
            args=pargs,
            cap=ptok,
            project_ops=_project_ops(case, prior),
        )
        if case.get("prior_must_ok"):
            assert pr.kind == "ok", (case["id"], pr)

    intent = case["intent"]
    args = dict(intent.get("args") or {})
    tok = token_for(intent.get("cap"), args, case["expect_kind"])
    r = host.submit(
        action=intent.get("action") or "",
        args=args,
        cap=tok,
        project_ops=_project_ops(case, intent),
    )
    assert r.kind == case["expect_kind"], (case["id"], r.kind, r.error, case["expect_kind"])
    if case.get("expect_ops_empty"):
        assert r.ops == [], (case["id"], r.ops)
    if case.get("expect_ops") is not None and r.kind == "ok":
        assert r.ops == case["expect_ops"], (case["id"], r.ops)
    assert r.digest and r.digest.startswith("cek1:"), case["id"]
    assert r.digest == result_digest(r.kind, r.ops, r.error)


def test_aligned_family():
    cases = load_aligned()
    assert len(cases) == len(ALIGNED_IDS)
    for case in cases:
        run_case(case)


if __name__ == "__main__":
    test_oracle()
    test_vendored_matches_runtime_when_present()
    for case in load_aligned():
        run_case(case)
        print(f"  contract ok: {case['id']}")
    print("contract family ok")
