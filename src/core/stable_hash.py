"""Process-independent integer ids derived from a tuple of ids.

Python's built-in ``hash()`` of a ``str`` (and of any tuple holding one) is salted per
process by ``PYTHONHASHSEED``, so an id built from it differs between two runs of the same
world and seed. Ids that reach hashed or ordered authoritative state must not depend on the
salt; this module derives them from a blake2b digest of a canonical encoding instead
(TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID).
"""
from __future__ import annotations

import hashlib
from typing import Union

IdPart = Union[str, int]

_INT31_MODULUS = 2 ** 31


def _encode_part(part: IdPart) -> bytes:
    """Encode one part with a type tag and length prefix, so distinct tuples never collide by concatenation."""
    if isinstance(part, bool) or not isinstance(part, (str, int)):
        raise TypeError(f"stable_int31 accepts str and int parts only, got {type(part).__name__}")
    tag = b"s" if isinstance(part, str) else b"i"
    body = str(part).encode("utf-8")
    return tag + len(body).to_bytes(4, "big") + body


def stable_int31(*parts: IdPart) -> int:
    """Return a non-negative int below 2**31 that depends only on *parts*, never on the process.

    Equal parts give the same value in every process; the order of parts matters.
    """
    digest = hashlib.blake2b(b"".join(_encode_part(p) for p in parts), digest_size=8).digest()
    return int.from_bytes(digest, "big") % _INT31_MODULUS
