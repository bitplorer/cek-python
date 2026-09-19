"""Taught kernel carrier — in-process cek_peer_pyo3. No second Peer kernel.

Live B-set (kv.*, log.append, ui.dom.*) runs when the PyO3 module is present.
Fail-closed and leftover-teaching assertions always run (CI stays green).
"""

from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parent / "cek-host" / "src"))

from cek_surface.carrier import open_carrier
from cek_surface.kernel_peer import (
    PYO3_INSTALL,
    KernelPeerCarrier,
    apply_via_kernel,
    find_cek_peer_pyo3,
    load_cek_peer_pyo3,
    reset_pyo3_cache,
)


B_SET = [
    {
        "id": "kv.set",
        "result": {
            "kind": "ok",
            "ops": [{"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}}],
        },
        "profile": "baseline",
        "check": lambda resp: resp.get("kv", {}).get("a") == 1
        and len((resp.get("receipt") or {}).get("landed") or []) == 1,
    },
    {
        "id": "kv.delete",
        "result": {
            "kind": "ok",
            "ops": [
                {"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}},
                {"ns": "kv", "name": "delete", "payload": {"key": "a"}},
            ],
        },
        "profile": "baseline",
        "check": lambda resp: "a" not in (resp.get("kv") or {})
        and len((resp.get("receipt") or {}).get("landed") or []) == 2,
    },
    {
        "id": "log.append",
        "result": {
            "kind": "ok",
            "ops": [{"ns": "log", "name": "append", "payload": {"message": "hello"}}],
        },
        "profile": "baseline",
        "check": lambda resp: resp.get("log") == ["hello"],
    },
    {
        "id": "ui.dom.morph",
        "result": {
            "kind": "ok",
            "ops": [
                {
                    "ns": "ui.dom",
                    "name": "morph",
                    "payload": {
                        "target": "hdr",
                        "patch": {"t": "n"},
                        "snapshot": {"t": "o"},
                    },
                }
            ],
        },
        "profile": "ui",
        "check": lambda resp: (resp.get("ui") or {}).get("hdr") == {"t": "n"},
    },
    {
        "id": "ui.dom.restore",
        "result": {
            "kind": "ok",
            "ops": [
                {
                    "ns": "ui.dom",
                    "name": "morph",
                    "payload": {
                        "target": "hdr",
                        "patch": {"t": "n"},
                        "snapshot": {"t": "o"},
                    },
                },
                {
                    "ns": "ui.dom",
                    "name": "restore",
                    "payload": {"target": "hdr", "snapshot": {"t": "o"}},
                },
            ],
        },
        "profile": "ui",
        "check": lambda resp: (resp.get("ui") or {}).get("hdr") == {"t": "o"},
    },
    {
        "id": "refuse",
        "result": {"kind": "authority_refusal", "ops": [], "error": "no"},
        "profile": "baseline",
        "check": lambda resp: (resp.get("kv") or {}) == {}
        and not ((resp.get("receipt") or {}).get("landed") or []),
    },
]


class _FakeAbi:
    """Canned receipt fixture — not a Peer kernel."""

    calls: list[str]

    def __init__(self) -> None:
        self.calls = ["construct"]
        self.released = False

    @staticmethod
    def construct() -> _FakeAbi:
        return _FakeAbi()

    def bind(self) -> None:
        self.calls.append("bind")

    def apply(self, req: dict) -> dict:
        self.calls.append("apply")
        assert not self.released
        ops = (req.get("result") or {}).get("ops") or []
        return {
            "receipt": {"landed": ops, "failed": []},
            "kv": {"a": 1} if ops else {},
            "ui": {},
            "log": [],
        }

    def release(self) -> None:
        self.calls.append("release")
        self.released = True


def _install_fake_mod() -> types.ModuleType:
    reset_pyo3_cache()
    mod = types.ModuleType("cek_peer_pyo3")
    mod.PeerAbi = _FakeAbi  # type: ignore[attr-defined]
    sys.modules["cek_peer_pyo3"] = mod
    return mod


def _clear_fake_mod() -> None:
    reset_pyo3_cache()
    sys.modules.pop("cek_peer_pyo3", None)


def test_taught_path_fails_closed_without_pyo3():
    _clear_fake_mod()
    env = os.environ.get("CEK_PEER_PYO3")
    carrier = os.environ.get("CEK_KERNEL_CARRIER")
    os.environ.pop("CEK_PEER_PYO3", None)
    os.environ.pop("CEK_KERNEL_CARRIER", None)
    try:
        with mock.patch(
            "cek_surface.kernel_peer.find_cek_peer_pyo3", return_value=None
        ), mock.patch.dict(sys.modules, {"cek_peer_pyo3": None}):
            # None in sys.modules → import raises ImportError
            try:
                load_cek_peer_pyo3()
                raise AssertionError("taught path must fail closed")
            except ImportError as e:
                msg = str(e)
                assert "cek_peer_pyo3" in msg
                assert "cargo build -p cek-peer-pyo3" in msg
                assert "--features extension-module" in msg
                assert "CEK_PEER_PYO3" in msg
                assert "CEK_KERNEL_CARRIER=subprocess" in msg
                assert PYO3_INSTALL[:40] in msg
            try:
                KernelPeerCarrier()
                raise AssertionError("open taught carrier must fail closed")
            except ImportError as e:
                assert "cek_peer_pyo3" in str(e)
            try:
                open_carrier("kernel")
                raise AssertionError("open_carrier(kernel) must fail closed")
            except ImportError as e:
                assert "cek_peer_pyo3" in str(e)
    finally:
        if env is not None:
            os.environ["CEK_PEER_PYO3"] = env
        if carrier is not None:
            os.environ["CEK_KERNEL_CARRIER"] = carrier


def test_bin_path_is_leftover_only():
    carrier = os.environ.get("CEK_KERNEL_CARRIER")
    os.environ.pop("CEK_KERNEL_CARRIER", None)
    try:
        try:
            apply_via_kernel({"kind": "ok", "ops": []}, bin_path="/tmp/cek")
            raise AssertionError("bin_path without leftover backend must raise")
        except ValueError as e:
            assert "leftover" in str(e).lower()
            assert "subprocess" in str(e)
        try:
            KernelPeerCarrier(bin_path="/tmp/cek")
            raise AssertionError("bin_path without leftover backend must raise")
        except ValueError as e:
            assert "leftover" in str(e).lower()
    finally:
        if carrier is not None:
            os.environ["CEK_KERNEL_CARRIER"] = carrier


def test_taught_lifecycle_and_return_contract():
    _install_fake_mod()
    try:
        with mock.patch("cek_surface.kernel_peer.subprocess.run") as ran:
            c = KernelPeerCarrier(profile="baseline")
            assert c.name == "kernel"
            applied = c.apply(
                {
                    "kind": "ok",
                    "ops": [{"ns": "kv", "name": "set", "payload": {"key": "a", "value": 1}}],
                }
            )
            assert applied["type"] == "applied"
            assert applied["receipt"]["landed"]
            assert applied["world"]["kv"]["a"] == 1
            assert applied["world"]["ui"] == {}
            assert applied["world"]["log"] == []
            c.close()
            ran.assert_not_called()
        via = apply_via_kernel(
            {"kind": "ok", "ops": [{"ns": "kv", "name": "set", "payload": {"key": "z", "value": 9}}]},
            profile="baseline",
        )
        assert via["kv"]["a"] == 1
        assert via["receipt"]["landed"]
    finally:
        _clear_fake_mod()


def test_open_carrier_kernel_kind():
    _install_fake_mod()
    try:
        c = open_carrier("kernel", profile="ui")
        assert c.name == "kernel"
        ack = c.stamp([{"ns": "kv", "name": "set"}])
        assert ack["type"] == "stamp_ack"
        assert ack["kernel_apply"] == "profile"
        c.close()
    finally:
        _clear_fake_mod()


def test_kernel_peer_source_has_no_mint():
    text = (ROOT / "src" / "cek_surface" / "kernel_peer.py").read_text(encoding="utf-8")
    assert "def mint" not in text
    assert ".mint(" not in text
    assert "host-json" not in text
    assert "construct" in text and "bind" in text and "release" in text


def test_taught_default_is_not_subprocess():
    text = (ROOT / "src" / "cek_surface" / "kernel_peer.py").read_text(encoding="utf-8")
    assert "Taught path" in text
    assert "Leftover (untaught" in text
    assert '("pyo3"' in text or '"pyo3"' in text
    assert '_apply_via_subprocess_leftover' in text


def _have_pyo3() -> bool:
    _clear_fake_mod()
    try:
        load_cek_peer_pyo3()
        return True
    except ImportError:
        return False


def test_live_b_set_when_pyo3_present():
    if not _have_pyo3():
        print("kernel peer live B-set skip (no cek_peer_pyo3 — see PYO3_INSTALL)")
        return
    c = KernelPeerCarrier(profile="ui")
    assert c.name == "kernel"
    try:
        for case in B_SET:
            resp = apply_via_kernel(case["result"], profile=case["profile"])
            assert case["check"](resp), case["id"]
            applied = KernelPeerCarrier(profile=case["profile"]).apply(case["result"])
            # carrier close after one-shot apply
            assert applied["type"] == "applied"
            wrapped = {
                "receipt": applied["receipt"],
                "kv": applied["world"]["kv"],
                "ui": applied["world"]["ui"],
                "log": applied["world"]["log"],
            }
            assert case["check"](wrapped), f"carrier {case['id']}"
    finally:
        c.close()
    print("kernel peer live B-set ok")


def test_parity_vs_subprocess_leftover_when_both_present():
    if not _have_pyo3():
        print("kernel peer leftover parity skip (no cek_peer_pyo3)")
        return
    from cek_host.rust_wrap import find_cek_bin

    exe = find_cek_bin()
    if not exe:
        print("kernel peer leftover parity skip (no cek binary)")
        return
    for case in B_SET:
        taught = apply_via_kernel(case["result"], profile=case["profile"])
        leftover = apply_via_kernel(
            case["result"],
            profile=case["profile"],
            backend="subprocess",
            bin_path=exe,
        )
        assert json.dumps(taught, sort_keys=True) == json.dumps(leftover, sort_keys=True), case["id"]
    print("kernel peer leftover parity ok")


if __name__ == "__main__":
    test_taught_path_fails_closed_without_pyo3()
    test_bin_path_is_leftover_only()
    test_taught_lifecycle_and_return_contract()
    test_open_carrier_kernel_kind()
    test_kernel_peer_source_has_no_mint()
    test_taught_default_is_not_subprocess()
    test_live_b_set_when_pyo3_present()
    test_parity_vs_subprocess_leftover_when_both_present()
    print("kernel peer ok")
