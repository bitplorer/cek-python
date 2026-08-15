"""Ed25519 (RFC 8032) — Host policy only. No extra deps."""

from __future__ import annotations

import hashlib

_P = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_I = pow(2, (_P - 1) // 4, _P)
_B = (
    15112221349535400772501151409588531511454012693041857206046113283949847762202,
    46316835694926478169428394003475163141307993866256225615783033603165251855960,
)


def _inv(x: int) -> int:
    return pow(x, _P - 2, _P)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * _inv(_D * y * y + 1)
    x = pow(xx, (_P + 3) // 8, _P)
    if (x * x - xx) % _P != 0:
        x = (x * _I) % _P
    if x % 2 != 0:
        x = _P - x
    return x


def _edwards(p, q):
    (x1, y1), (x2, y2) = p, q
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + _D * x1 * x2 * y1 * y2)
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - _D * x1 * x2 * y1 * y2)
    return (x3 % _P, y3 % _P)


def _scalarmult(p, e: int):
    if e == 0:
        return (0, 1)
    q = _scalarmult(p, e // 2)
    q = _edwards(q, q)
    if e & 1:
        q = _edwards(q, p)
    return q


def _encodeint(y: int) -> bytes:
    return y.to_bytes(32, "little")


def _encodepoint(p) -> bytes:
    x, y = p
    bits = bytearray(_encodeint(y))
    bits[-1] |= 0x80 if x & 1 else 0
    return bytes(bits)


def _bit(h: bytes, i: int) -> int:
    return (h[i // 8] >> (i % 8)) & 1


def _decodeint(s: bytes) -> int:
    return int.from_bytes(s, "little")


def _decodepoint(s: bytes):
    y = _decodeint(s) & ((1 << 255) - 1)
    x = _xrecover(y)
    if bool(x & 1) != bool(s[31] >> 7):
        x = _P - x
    p = (x, y)
    if not _isoncurve(p):
        raise ValueError("point")
    return p


def _isoncurve(p) -> bool:
    x, y = p
    return (-x * x + y * y - 1 - _D * x * x * y * y) % _P == 0


def _hint(m: bytes) -> int:
    return _decodeint(hashlib.sha512(m).digest())


def public_key(seed: bytes) -> bytes:
    if len(seed) != 32:
        raise ValueError("seed must be 32 bytes")
    h = hashlib.sha512(seed).digest()
    a = 2**254 + sum(2**i * _bit(h, i) for i in range(3, 254))
    return _encodepoint(_scalarmult(_B, a))


def sign(seed: bytes, msg: bytes) -> bytes:
    if len(seed) != 32:
        raise ValueError("seed must be 32 bytes")
    h = hashlib.sha512(seed).digest()
    a = 2**254 + sum(2**i * _bit(h, i) for i in range(3, 254))
    a_pub = _encodepoint(_scalarmult(_B, a))
    r = _hint(h[32:] + msg)
    r_pt = _scalarmult(_B, r)
    r_enc = _encodepoint(r_pt)
    k = _hint(r_enc + a_pub + msg)
    s = (r + k * a) % _L
    return r_enc + _encodeint(s)


def verify(pk: bytes, msg: bytes, sig: bytes) -> bool:
    if len(pk) != 32 or len(sig) != 64:
        return False
    try:
        a = _decodepoint(pk)
        r = _decodepoint(sig[:32])
        s = _decodeint(sig[32:])
    except ValueError:
        return False
    if s >= _L:
        return False
    k = _hint(sig[:32] + pk + msg)
    return _scalarmult(_B, s) == _edwards(r, _scalarmult(a, k))
