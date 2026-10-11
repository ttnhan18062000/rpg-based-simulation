"""Bounded pure-Python PNG decoding and the canonical `pixels-v1` hash (decision D4). Stdlib only; no I/O, no clock.

Why decoded pixels and not file bytes: PNG byte output is not guaranteed stable across Aseprite versions, so an artifact's identity is the
image it shows. Two PNGs with the same visible pixels get the same hash whatever their filter choice, compression level, colour type or
ancillary chunks, and whatever RGB sits under a fully transparent pixel.

`pixels-v1` is: sha256 over `b"pixels-v1\\0"`, then width and height as unsigned 32-bit big-endian integers, then the image as 8-bit
NON-premultiplied RGBA rows from top to bottom, where every pixel with alpha 0 is written as `00 00 00 00`. The hash string is `pixels-v1:` + hex.

The reader accepts only what the drawing tools and Aseprite write: non-interlaced 8-bit greyscale, greyscale+alpha, RGB, RGBA and indexed
(with `tRNS` alpha). It checks every chunk CRC, bounds the dimensions and the decompressed size BEFORE inflating (`zlib` is asked for at most the expected
number of bytes), and rejects anything else: wrong signature, bad CRC, 16-bit or other depths, interlacing, APNG, a colour-key `tRNS`, unknown critical
chunks, truncated or surplus image data, and any byte after `IEND`.
"""

from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import dataclass
from functools import lru_cache
from itertools import accumulate

from visual_assets.store import config
from visual_assets.store.errors import PngDecodeError

SIGNATURE = b"\x89PNG\r\n\x1a\n"
HASH_PREFIX = "pixels-v1:"
_HASH_MAGIC = b"pixels-v1\x00"
_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}  # colour type -> samples per pixel at 8 bits
_KNOWN_CRITICAL = {b"IHDR", b"PLTE", b"IDAT", b"IEND"}
_APNG = {b"acTL", b"fcTL", b"fdAT"}


@dataclass(frozen=True)
class DecodedImage:
    width: int
    height: int
    rgba: bytes  # width * height * 4, non-premultiplied, rows top to bottom


def _fail(code: str, message: str) -> PngDecodeError:
    return PngDecodeError(code, message)


def _chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    """Every chunk as (type, body), CRC-checked, ending exactly at IEND with nothing after it."""
    if data[:8] != SIGNATURE:
        raise _fail("signature", "not a PNG: wrong signature")
    out: list[tuple[bytes, bytes]] = []
    pos = 8
    while True:
        if pos + 8 > len(data):
            raise _fail("truncated", "the chunk list ends before IEND")
        length, kind = struct.unpack_from(">I4s", data, pos)
        end = pos + 8 + length + 4
        if length > len(data) or end > len(data):
            raise _fail("truncated", f"chunk {kind!r} runs past the end of the data")
        body = data[pos + 8 : pos + 8 + length]
        (crc,) = struct.unpack_from(">I", data, end - 4)
        if zlib.crc32(kind + body) & 0xFFFFFFFF != crc:
            raise _fail("crc", f"chunk {kind!r} has a bad checksum")
        out.append((kind, body))
        pos = end
        if kind == b"IEND":
            if length != 0:
                raise _fail("malformed", "IEND must be empty")
            break
    if pos != len(data):
        raise _fail("trailing_data", f"{len(data) - pos} bytes follow IEND")
    return out


def _add_bytes(x: bytes, y: bytes) -> bytes:
    """Byte-wise `(x + y) & 255` of two equal-length byte strings, in C-speed big-integer arithmetic (a SWAR add: the low 7 bits of every byte are added without
    carrying into the next byte, then the top bits are folded back with xor)."""
    n = len(x)
    if not n:
        return b""
    low = int.from_bytes(b"\x7f" * n, "big")
    a, b = int.from_bytes(x, "big"), int.from_bytes(y, "big")
    return (((a & low) + (b & low)) ^ ((a ^ b) & ~low & ((1 << (8 * n)) - 1))).to_bytes(n, "big")


def _unfilter(raw: bytes, width_bytes: int, height: int, bpp: int) -> bytearray:
    """Undo the per-row PNG filters. Same output as the plain per-byte definition (the corpus test compares them), but each filter works per colour channel on
    slices: Sub is a running sum, Up one big-integer add, Average and Paeth carry their left/up-left neighbours in local variables instead of indexing."""
    stride = width_bytes
    out = bytearray(stride * height)
    prev = bytes(stride)  # the row above row 0 is all zeros, so no filter needs a first-row special case
    view = memoryview(raw)
    for row in range(height):
        base = row * (stride + 1)
        ftype = raw[base]
        line = bytes(view[base + 1 : base + 1 + stride])
        dst = row * stride
        if ftype == 0:
            cur = line
        elif ftype == 1:  # Sub
            cur = bytearray(stride)
            for ch in range(min(bpp, stride)):
                cur[ch::bpp] = bytes(map((255).__and__, accumulate(line[ch::bpp])))
        elif ftype == 2:  # Up
            cur = _add_bytes(line, prev)
        elif ftype == 3:  # Average
            cur = bytearray(stride)
            for ch in range(min(bpp, stride)):
                a = 0
                res = bytearray()
                push = res.append
                for x, b in zip(line[ch::bpp], prev[ch::bpp]):
                    a = (x + ((a + b) >> 1)) & 255
                    push(a)
                cur[ch::bpp] = res
        elif ftype == 4:  # Paeth
            cur = bytearray(stride)
            for ch in range(min(bpp, stride)):
                a = c = 0
                res = bytearray()
                push = res.append
                for x, b in zip(line[ch::bpp], prev[ch::bpp]):
                    pa = b - c
                    pb = a - c
                    pc = pa + pb
                    if pa < 0:
                        pa = -pa
                    if pb < 0:
                        pb = -pb
                    if pc < 0:
                        pc = -pc
                    a = (x + (a if (pa <= pb and pa <= pc) else (b if pb <= pc else c))) & 255
                    push(a)
                    c = b
                cur[ch::bpp] = res
        else:
            raise _fail("malformed", f"row {row} has the unknown filter type {ftype}")
        out[dst : dst + stride] = cur
        prev = bytes(cur)
    return out


def decode_png(data: bytes, *, max_dim: int | None = None) -> DecodedImage:
    """Decode `data` to RGBA or raise `PngDecodeError`. `max_dim` defaults to `config.MAX_DIM` (read at call time).

    A pure function, so the last few results are memoised by (bytes, dimension limit, decoded-size bound): `adopt`, `review` and `intake` look at the same preview
    several times and now pay for one decode. A refusal is never cached (it is raised again each time); `decode_png.cache_clear()` empties it."""
    data = bytes(data)  # hashable for the memo (a bytearray or memoryview works as before)
    limit = config.MAX_DIM if max_dim is None else max_dim
    if len(data) > config.MAX_DECODED_BYTES:
        return _decode.__wrapped__(data, limit, config.MAX_DECODED_BYTES)  # a file bigger than the decoded-size bound (any legal PNG is about that size) is decoded (or refused) but never kept resident
    return _decode(data, limit, config.MAX_DECODED_BYTES)


@lru_cache(maxsize=4)  # at most 4 decoded images (each at most MAX_DECODED_BYTES) are kept
def _decode(data: bytes, limit: int, max_decoded: int) -> DecodedImage:
    chunks = _chunks(data)
    if chunks[0][0] != b"IHDR" or len(chunks[0][1]) != 13:
        raise _fail("malformed", "the first chunk is not a 13-byte IHDR")
    width, height, depth, ctype, compression, filt, interlace = struct.unpack(">IIBBBBB", chunks[0][1])
    if width < 1 or height < 1:
        raise _fail("malformed", "the image has a zero dimension")
    if width > limit or height > limit:
        raise _fail("dimensions", f"{width}x{height} is over the {limit} pixel limit")
    if depth != 8:
        raise _fail("unsupported", f"bit depth {depth} is not supported (8 only)")
    if ctype not in _CHANNELS:
        raise _fail("unsupported", f"colour type {ctype} is not supported")
    if interlace != 0:
        raise _fail("unsupported", "interlaced PNGs are not supported")
    if compression != 0 or filt != 0:
        raise _fail("malformed", "unknown compression or filter method")

    palette: list[tuple[int, int, int]] = []
    alphas: list[int] = []
    idat: list[bytes] = []
    seen_idat = seen_plte = False
    for kind, body in chunks[1:-1]:
        if kind == b"IHDR":
            raise _fail("malformed", "a second IHDR chunk")
        if kind in _APNG:
            raise _fail("unsupported", "animated PNG (APNG) chunks are not supported")
        if kind == b"IDAT":
            if idat and not seen_idat:
                raise _fail("malformed", "IDAT chunks are not contiguous")
            idat.append(body)
            seen_idat = True
            continue
        if seen_idat and idat and kind != b"IEND":
            seen_idat = False  # a non-IDAT chunk ends the IDAT run; another IDAT after it is refused above
        if kind == b"PLTE":
            if idat or seen_plte or ctype == 0 or ctype == 4:
                raise _fail("malformed", "PLTE is in the wrong place for this colour type")
            if len(body) % 3 or not 3 <= len(body) <= 768:
                raise _fail("malformed", "PLTE has an impossible length")
            palette = [tuple(body[i : i + 3]) for i in range(0, len(body), 3)]  # type: ignore[misc]
            seen_plte = True
        elif kind == b"tRNS":
            if ctype != 3:
                raise _fail("unsupported", "a colour-key tRNS chunk is not supported")
            alphas = list(body)
        elif kind[0:1].isupper() and kind not in _KNOWN_CRITICAL:
            raise _fail("unsupported", f"unknown critical chunk {kind!r}")
    if not idat:
        raise _fail("truncated", "there is no image data")
    if ctype == 3 and not palette:
        raise _fail("malformed", "an indexed image needs a PLTE chunk")
    if len(alphas) > len(palette):
        raise _fail("malformed", "tRNS has more entries than the palette")

    channels = _CHANNELS[ctype]
    stride = width * channels
    expected = (stride + 1) * height
    if expected > max_decoded:
        raise _fail("too_large", f"the decoded size {expected} is over the {max_decoded} byte bound")
    inflater = zlib.decompressobj()
    try:
        raw = inflater.decompress(b"".join(idat), expected + 1)  # never inflate more than one byte past what is expected
    except zlib.error as exc:
        raise _fail("truncated", f"the image data cannot be inflated ({exc})") from None
    if len(raw) > expected or inflater.unconsumed_tail:
        raise _fail("too_large", "the image data inflates to more than its dimensions allow")
    if len(raw) < expected or not inflater.eof:
        raise _fail("truncated", "the image data is shorter than its dimensions need")
    if inflater.unused_data:
        raise _fail("trailing_data", "bytes follow the end of the image data stream")

    pixels = _unfilter(raw, stride, height, channels)
    rgba = bytearray(width * height * 4)
    if ctype == 6:
        rgba[:] = pixels
    elif ctype == 2:
        rgba[0::4], rgba[1::4], rgba[2::4], rgba[3::4] = pixels[0::3], pixels[1::3], pixels[2::3], b"\xff" * (width * height)
    elif ctype == 0:
        rgba[0::4] = rgba[1::4] = rgba[2::4] = pixels  # type: ignore[assignment]
        rgba[3::4] = b"\xff" * (width * height)
    elif ctype == 4:
        rgba[0::4] = rgba[1::4] = rgba[2::4] = pixels[0::2]  # type: ignore[assignment]
        rgba[3::4] = pixels[1::2]
    else:  # indexed
        table = [bytes((r, g, b, alphas[i] if i < len(alphas) else 255)) for i, (r, g, b) in enumerate(palette)]
        for i, index in enumerate(pixels):
            if index >= len(table):
                raise _fail("malformed", "a pixel indexes past the palette")
            rgba[4 * i : 4 * i + 4] = table[index]
    return DecodedImage(width, height, bytes(rgba))


decode_png.cache_clear = _decode.cache_clear  # type: ignore[attr-defined]


def pixel_hash_of(image: DecodedImage) -> str:
    """The `pixels-v1:<hex>` hash of a decoded image."""
    body = bytearray(image.rgba)
    alpha = body[3::4]
    if 0 in alpha:
        for index, value in enumerate(alpha):
            if value == 0:
                body[4 * index : 4 * index + 3] = b"\x00\x00\x00"
    digest = hashlib.sha256(_HASH_MAGIC + struct.pack(">II", image.width, image.height) + bytes(body)).hexdigest()
    return HASH_PREFIX + digest


def pixel_hash(png: bytes, *, max_dim: int | None = None) -> str:
    """Decode `png` (bounded) and return its `pixels-v1` hash."""
    return pixel_hash_of(decode_png(png, max_dim=max_dim))
