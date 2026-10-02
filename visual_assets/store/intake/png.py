"""Header-only reader for a preview PNG. Pure. Checks the signature and the IHDR chunk, nothing is decoded."""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class PngHeader:
    width: int
    height: int


class PngError(ValueError):
    """`signature` is True when the 8-byte signature itself is wrong (as opposed to a damaged IHDR)."""

    def __init__(self, message: str, *, signature: bool = False) -> None:
        super().__init__(message)
        self.signature = signature


def read_header(data: bytes) -> PngHeader:
    if data[:8] != SIGNATURE:
        raise PngError("not a PNG: wrong signature", signature=True)
    if len(data) < 8 + 8 + 13 + 4:
        raise PngError("PNG is too short to hold an IHDR chunk")
    length, ctype = struct.unpack_from(">I4s", data, 8)
    if ctype != b"IHDR" or length != 13:
        raise PngError("first PNG chunk is not a 13-byte IHDR")
    body = data[16:29]
    (crc,) = struct.unpack_from(">I", data, 29)
    if zlib.crc32(b"IHDR" + body) & 0xFFFFFFFF != crc:
        raise PngError("IHDR checksum does not match")
    width, height = struct.unpack(">II", body[:8])
    if width < 1 or height < 1:
        raise PngError("PNG has a zero dimension")
    return PngHeader(width, height)
