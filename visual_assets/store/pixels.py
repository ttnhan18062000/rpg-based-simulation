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


def _unfilter(raw: bytes, width_bytes: int, height: int, bpp: int) -> bytearray:
    stride = width_bytes
    out = bytearray(stride * height)
    for row in range(height):
        base = row * (stride + 1)
        ftype = raw[base]
        line = raw[base + 1 : base + 1 + stride]
        dst = row * stride
        prev = dst - stride  # offset of the previous output row (valid when row > 0)
        if ftype == 0:
            out[dst : dst + stride] = line
        elif ftype == 1:  # Sub
            for i in range(stride):
                left = out[dst + i - bpp] if i >= bpp else 0
                out[dst + i] = (line[i] + left) & 255
        elif ftype == 2:  # Up
            if row == 0:
                out[dst : dst + stride] = line
            else:
                for i in range(stride):
                    out[dst + i] = (line[i] + out[prev + i]) & 255
        elif ftype == 3:  # Average
            for i in range(stride):
                left = out[dst + i - bpp] if i >= bpp else 0
                up = out[prev + i] if row else 0
                out[dst + i] = (line[i] + ((left + up) >> 1)) & 255
        elif ftype == 4:  # Paeth
            for i in range(stride):
                a = out[dst + i - bpp] if i >= bpp else 0
                b = out[prev + i] if row else 0
                c = out[prev + i - bpp] if (row and i >= bpp) else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                out[dst + i] = (line[i] + pred) & 255
        else:
            raise _fail("malformed", f"row {row} has the unknown filter type {ftype}")
    return out


def decode_png(data: bytes, *, max_dim: int | None = None) -> DecodedImage:
    """Decode `data` to RGBA or raise `PngDecodeError`. `max_dim` defaults to `config.MAX_DIM` (read at call time)."""
    limit = config.MAX_DIM if max_dim is None else max_dim
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
    if expected > config.MAX_DECODED_BYTES:
        raise _fail("too_large", f"the decoded size {expected} is over the {config.MAX_DECODED_BYTES} byte bound")
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
