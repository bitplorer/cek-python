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

KERNEL_ACTIONS = {"kv.write", "kv.delete", "log.append", "ui.morph", "ui.restore"}

# Hot family G5 / W9 + Phase 2 (idem, lineage, ed25519, law-gen).
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
    "empty-idempotency-key",
    "idempotency-replay",
    "idempotency-conflict",
    "lineage-reverse-on-end",
    "receipt-landed-first-reverse",
    "kv-delete-prior-reverse",
    "kv-delete-no-prior-non-reversible",
    "ui-morph-snapshot-reverse",
    "ed25519-ok",
    "ed25519-missing",
    "ed25519-tamper",
    "law-gen-blank",
    "law-gen-unknown",
    "law-gen-accepted",
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


def _project_ops(case: dict, intent: dict) -> list[dict] | None:
    action = intent.get("action") or ""
    if action in KERNEL_ACTIONS:
        return None  # BoundAsk-only: Host._project
    if case.get("expect_ops"):
        return list(case["expect_ops"])
    return [{"ns": "sys", "name": "noop", "payload": {}}]


def _mint(host: Host, cap: dict, intent_args: dict, expect_kind: str, case: dict) -> str:
    action = str(cap.get("action") or "")
    if not action.strip():
        return "not-a-valid-cap"
    case_id = case["id"]
    kw: dict = {"once": bool(cap.get("once")), "jti": str(cap.get("id") or "") or None}
    if cap.get("scopes") is not None:
        kw["scopes"] = list(cap["scopes"])
    if cap.get("subject") is not None:
        kw["subject"] = cap["subject"]
    if cap.get("not_after") is not None:
        kw["not_after"] = float(cap["not_after"])
    if "law_generation" in cap:
        kw["law_generation"] = cap["law_generation"]
    attach = case_id != "ed25519-missing"
    kw["attach_ed25519"] = attach
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
    raw_sig = cap.get("sig")
    if isinstance(raw_sig, str) and raw_sig.startswith("ed25519:"):
        claims = host.caps.decode(tok)
        forged = raw_sig.split(":", 1)[1]
        tok = host.caps.mint(
            action,
            once=bool(claims.get("once")),
            not_after=claims.get("not_after"),
            scopes=claims.get("scopes"),
            subject=claims.get("subject"),
            jti=claims.get("jti"),
            law_generation=claims.get("law_generation"),
            args_hash_value=claims.get("args_hash"),
            ed25519=forged,
        )
    return tok


def _host_for(case: dict) -> Host:
    kw: dict = {"secret": SECRET}
    if case.get("ed25519_seed"):
        kw["ed25519_seed"] = bytes.fromhex(case["ed25519_seed"])
    if case.get("accept_generations"):
        kw["accepted_generations"] = list(case["accept_generations"])
    host = Host(**kw)
    if case.get("now") is not None:
        now = float(case["now"])
        host.caps.now_fn = lambda: now
    return host


def _submit(host: Host, case: dict, intent: dict, expect_kind: str, tokens: dict[str, str]):
    args = dict(intent.get("args") or {})
    cap = intent.get("cap")
    tok = None
    if cap:
        jti = str(cap.get("id") or "")
        if jti and jti in tokens and case["id"] in ("once-second-use", "idempotency-replay", "idempotency-conflict"):
            tok = tokens[jti]
        else:
            tok = _mint(host, cap, args, expect_kind, case)
            if jti:
                tokens[jti] = tok
    return host.submit(
        action=intent.get("action") or "",
        args=args,
        cap=tok,
        activity_id=intent.get("activity_id"),
        idempotency_key=intent.get("idempotency_key"),
        project_ops=_project_ops(case, intent),
    )


def run_case(case: dict) -> None:
    host = _host_for(case)
    tokens: dict[str, str] = {}

    if case.get("prior_intent"):
        prior = case["prior_intent"]
        pr = _submit(host, case, prior, "ok", tokens)
        if case.get("prior_must_ok"):
            assert pr.kind == "ok", (case["id"], pr)

    intent = case["intent"]
    r = _submit(host, case, intent, case["expect_kind"], tokens)
    assert r.kind == case["expect_kind"], (case["id"], r.kind, r.error, case["expect_kind"])
    if case.get("expect_ops_empty"):
        assert r.ops == [], (case["id"], r.ops)
    if case.get("expect_ops") is not None and r.kind == "ok":
        assert r.ops == case["expect_ops"], (case["id"], r.ops)
    assert r.digest and r.digest.startswith("cek1:"), case["id"]
    assert r.digest == result_digest(r.kind, r.ops, r.error)

    if case.get("report_receipt") and r.kind == "ok":
        aid = intent.get("activity_id")
        assert aid
        host.report_receipt(str(aid), r.ops)

    if case.get("end_activity"):
        rev = host.end_activity(case["end_activity"])
        if case.get("expect_reverse_ops") is not None:
            assert rev.ops == case["expect_reverse_ops"], (case["id"], rev.ops)
        if "expect_used_landed" in case:
            assert rev.used_landed is case["expect_used_landed"], (case["id"], rev.used_landed)


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
