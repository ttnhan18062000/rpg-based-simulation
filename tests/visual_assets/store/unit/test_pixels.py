"""The bounded PNG reader and the `pixels-v1` hash (D4): encoding-independent, hand-verifiable, strict about everything else."""

from __future__ import annotations

import hashlib
import struct
import time
import zlib

import pytest

from tests.visual_assets.store import builders as b
from visual_assets.store import config, pixels
from visual_assets.store.errors import PngDecodeError

W, H = 9, 7
PIXELS = b.sample_pixels(W, H)


def code_of(data: bytes, **kw) -> str:
    with pytest.raises(PngDecodeError) as err:
        pixels.decode_png(data, **kw)
    return err.value.code


def expected_hash(width: int, height: int, rgba: list[b.Pixel]) -> str:
    """The documented definition, written out independently of `pixels.py`."""
    body = b""
    for r, g, b_, a in rgba:
        body += bytes((0, 0, 0, 0)) if a == 0 else bytes((r, g, b_, a))
    return "pixels-v1:" + hashlib.sha256(b"pixels-v1\x00" + struct.pack(">II", width, height) + body).hexdigest()


def test_the_hash_equals_a_value_computed_by_hand_from_the_documented_definition():
    assert pixels.pixel_hash(b.png_encode(W, H, PIXELS)) == expected_hash(W, H, PIXELS)
    tiny = [(255, 0, 0, 255), (0, 0, 0, 0), (1, 2, 3, 128), (9, 9, 9, 0)]
    manual = hashlib.sha256(b"pixels-v1\x00" + b"\x00\x00\x00\x02" + b"\x00\x00\x00\x02"
                            + bytes([255, 0, 0, 255, 0, 0, 0, 0, 1, 2, 3, 128, 0, 0, 0, 0])).hexdigest()
    assert pixels.pixel_hash(b.png_encode(2, 2, tiny)) == "pixels-v1:" + manual


ENCODINGS = {
    "rgba_filter0_level9": dict(),
    "rgba_level0": dict(level=0),
    "rgba_level1": dict(level=1),
    "rgba_sub": dict(filters=[1]),
    "rgba_up": dict(filters=[2]),
    "rgba_average": dict(filters=[3]),
    "rgba_paeth": dict(filters=[4]),
    "rgba_mixed_rows": dict(filters=[0, 1, 2, 3, 4]),
    "rgba_split_idat": dict(idat_split=17),
    "rgba_ancillary_chunks": dict(extra=[(b"tEXt", b"Comment\x00hello"), (b"gAMA", struct.pack(">I", 45455)), (b"pHYs", struct.pack(">IIB", 2835, 2835, 1))]),
    "indexed_with_trns": dict(ctype=3),
    "indexed_paeth": dict(ctype=3, filters=[4]),
}


@pytest.mark.parametrize("name", sorted(ENCODINGS))
def test_different_encodings_of_the_same_pixels_have_the_same_hash(name):
    assert pixels.pixel_hash(b.png_encode(W, H, PIXELS, **ENCODINGS[name])) == expected_hash(W, H, PIXELS), name


def test_rgb_and_grey_encodings_match_their_rgba_equivalents():
    opaque = [(r, g, bl, 255) for r, g, bl, _ in b.sample_pixels(W, H)]
    assert pixels.pixel_hash(b.png_encode(W, H, opaque, ctype=2, filters=[1, 4])) == expected_hash(W, H, opaque)
    grey = [(v, v, v, 255) for v in range(W * H)]
    assert pixels.pixel_hash(b.png_encode(W, H, grey, ctype=0)) == expected_hash(W, H, grey)
    grey_alpha = [(v, v, v, (v * 3) % 256) for v in range(W * H)]
    assert pixels.pixel_hash(b.png_encode(W, H, grey_alpha, ctype=4, filters=[2])) == expected_hash(W, H, grey_alpha)


def test_the_rgb_under_a_fully_transparent_pixel_does_not_matter():
    one = b.png_encode(W, H, b.sample_pixels(W, H, transparent_rgb=(0, 0, 0)))
    two = b.png_encode(W, H, b.sample_pixels(W, H, transparent_rgb=(250, 3, 99)))
    assert one != two and pixels.pixel_hash(one) == pixels.pixel_hash(two)


def test_semi_transparent_pixels_keep_their_colour():
    a = b.sample_pixels(W, H)
    c = list(a)
    index = next(i for i, p in enumerate(a) if p[3] == 128)
    c[index] = (c[index][0] ^ 1, *c[index][1:])  # same alpha, one colour bit differs
    assert pixels.pixel_hash(b.png_encode(W, H, a)) != pixels.pixel_hash(b.png_encode(W, H, c))


def test_one_visible_pixel_the_width_or_swapping_width_and_height_changes_the_hash():
    base = pixels.pixel_hash(b.png_encode(W, H, PIXELS))
    changed = list(PIXELS)
    index = next(i for i, p in enumerate(PIXELS) if p[3] == 255)
    changed[index] = (changed[index][0], changed[index][1], changed[index][2] ^ 1, 255)
    assert pixels.pixel_hash(b.png_encode(W, H, changed)) != base
    alpha_only = list(PIXELS)
    alpha_only[index] = (*alpha_only[index][:3], 254)
    assert pixels.pixel_hash(b.png_encode(W, H, alpha_only)) != base
    assert pixels.pixel_hash(b.png_encode(W + 1, H, b.sample_pixels(W + 1, H))) != base
    assert pixels.pixel_hash(b.png_encode(H, W, PIXELS)) != base  # same samples, width and height swapped
    assert pixels.pixel_hash(b.png_encode(H, W, PIXELS)) == expected_hash(H, W, PIXELS)


def test_decoding_returns_the_exact_rgba_rows():
    image = pixels.decode_png(b.png_encode(W, H, PIXELS, filters=[0, 1, 2, 3, 4]))
    assert (image.width, image.height) == (W, H)
    assert image.rgba == b"".join(bytes(p) for p in PIXELS)


# --------------------------------------------------------------------------- refusals

GOOD = b.png_encode(W, H, PIXELS)


def chunks_of(data: bytes) -> list[tuple[bytes, bytes]]:
    pos, out = 8, []
    while pos < len(data):
        length, kind = struct.unpack_from(">I4s", data, pos)
        out.append((kind, data[pos + 8 : pos + 8 + length]))
        pos += 12 + length
    return out


def rebuild(chunks: list[tuple[bytes, bytes]]) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"".join(b.png_chunk(k, v) for k, v in chunks)


def ihdr(**changes) -> bytes:
    fields = dict(width=W, height=H, depth=8, ctype=6, compression=0, filt=0, interlace=0)
    fields.update(changes)
    return struct.pack(">IIBBBBB", *fields.values())


def with_ihdr(**changes) -> bytes:
    parts = chunks_of(GOOD)
    parts[0] = (b"IHDR", ihdr(**changes))
    return rebuild(parts)


def test_a_wrong_signature_is_refused():
    for blob in (b"", b"GIF89a", b"\x89PNG\r\n\x1a\x00" + GOOD[8:], b"x" + GOOD, GOOD[1:]):
        assert code_of(blob) == "signature", blob[:8]


def test_a_bad_crc_is_refused_in_any_chunk():
    for index in range(len(chunks_of(GOOD))):
        pos = 8
        for _ in range(index):
            pos += 12 + struct.unpack_from(">I", GOOD, pos)[0]
        length = struct.unpack_from(">I", GOOD, pos)[0]
        damaged = bytearray(GOOD)
        damaged[pos + 8 + length + 3] ^= 0xFF  # the last CRC byte of that chunk
        assert code_of(bytes(damaged)) == "crc", index


def test_unsupported_kinds_are_refused():
    assert code_of(with_ihdr(depth=16)) == "unsupported"
    for depth in (1, 2, 4):
        assert code_of(with_ihdr(depth=depth)) == "unsupported"
    assert code_of(with_ihdr(ctype=1)) == "unsupported"
    assert code_of(with_ihdr(interlace=1)) == "unsupported"
    parts = chunks_of(GOOD)
    parts.insert(1, (b"acTL", struct.pack(">II", 1, 0)))
    assert code_of(rebuild(parts)) == "unsupported"  # APNG
    parts = chunks_of(GOOD)
    parts.insert(1, (b"fdAT", b"\x00\x00\x00\x01abc"))
    assert code_of(rebuild(parts)) == "unsupported"
    parts = chunks_of(GOOD)
    parts.insert(1, (b"ZZZZ", b"x"))  # an unknown CRITICAL chunk (uppercase first letter)
    assert code_of(rebuild(parts)) == "unsupported"
    parts = chunks_of(b.png_encode(W, H, PIXELS, ctype=2))
    parts.insert(1, (b"tRNS", b"\x00\x00\x00\x00\x00\x00"))  # a colour-key tRNS on RGB
    assert code_of(rebuild(parts)) == "unsupported"


def test_an_unknown_ancillary_chunk_is_ignored():
    parts = chunks_of(GOOD)
    parts.insert(1, (b"zzZz", b"private ancillary data"))
    assert pixels.pixel_hash(rebuild(parts)) == pixels.pixel_hash(GOOD)


def test_dimensions_over_the_limit_are_refused(monkeypatch):
    assert code_of(b.png_encode(129, 2, b.sample_pixels(129, 2))) == "dimensions"
    assert code_of(b.png_encode(2, 129, b.sample_pixels(2, 129))) == "dimensions"
    assert pixels.decode_png(b.png_encode(128, 2, b.sample_pixels(128, 2)))  # at the limit is fine
    assert pixels.decode_png(b.png_encode(129, 2, b.sample_pixels(129, 2)), max_dim=200)  # a caller-chosen limit (previews)
    monkeypatch.setattr(config, "MAX_DIM", 8)
    assert code_of(GOOD) == "dimensions"  # config is read at call time


def test_zero_dimensions_and_bad_methods_are_malformed():
    assert code_of(with_ihdr(width=0)) == "malformed" and code_of(with_ihdr(height=0)) == "malformed"
    assert code_of(with_ihdr(compression=1)) == "malformed" and code_of(with_ihdr(filt=1)) == "malformed"


def test_truncated_image_data_is_refused():
    parts = chunks_of(GOOD)
    kinds = [k for k, _ in parts]
    idat = kinds.index(b"IDAT")
    short = zlib.compress(b"\x00" * (W * 4 + 1))  # one row only
    parts[idat] = (b"IDAT", short)
    assert code_of(rebuild(parts)) == "truncated"
    parts[idat] = (b"IDAT", GOOD and parts[idat][1][: len(parts[idat][1]) // 2])
    assert code_of(rebuild(parts)) == "truncated"
    assert code_of(rebuild([c for c in chunks_of(GOOD) if c[0] != b"IDAT"])) == "truncated"
    assert code_of(GOOD[:-12]) == "truncated"  # IEND cut off


def test_decompressed_size_above_the_bound_is_refused_without_inflating_it():
    parts = chunks_of(GOOD)
    idat = [k for k, _ in parts].index(b"IDAT")
    expected = (W * 4 + 1) * H
    bomb = zlib.compress(b"\x00" * 60_000_000, 9)  # tiny on disk, 60 MB inflated
    assert len(bomb) < 100_000
    parts[idat] = (b"IDAT", bomb)
    started = time.monotonic()
    assert code_of(rebuild(parts)) == "too_large"
    assert time.monotonic() - started < 1.0  # at most expected + 1 bytes were ever inflated
    parts[idat] = (b"IDAT", zlib.compress(b"\x00" * (expected + 1)))
    assert code_of(rebuild(parts)) == "too_large"


def test_the_declared_decoded_size_is_bounded_before_inflating(monkeypatch):
    monkeypatch.setattr(config, "MAX_DECODED_BYTES", 100)
    assert code_of(GOOD) == "too_large"


def test_data_after_iend_and_surplus_stream_bytes_are_refused():
    assert code_of(GOOD + b"\x00") == "trailing_data"
    assert code_of(GOOD + GOOD) == "trailing_data"
    parts = chunks_of(GOOD)
    idat = [k for k, _ in parts].index(b"IDAT")
    parts[idat] = (b"IDAT", parts[idat][1] + b"\x00\x00")
    assert code_of(rebuild(parts)) == "trailing_data"  # bytes after the zlib stream ends


def test_structural_problems_are_malformed():
    parts = chunks_of(GOOD)
    assert code_of(rebuild(parts[1:])) == "malformed"  # IHDR is not first
    parts = chunks_of(GOOD)
    parts.insert(1, parts[0])
    assert code_of(rebuild(parts)) == "malformed"  # second IHDR
    parts = chunks_of(GOOD)
    parts[-1] = (b"IEND", b"x")
    assert code_of(rebuild(parts)) == "malformed"  # IEND with data
    parts = chunks_of(GOOD)
    idat = [k for k, _ in parts].index(b"IDAT")
    data = parts[idat][1]
    parts[idat:idat + 1] = [(b"IDAT", data[:5]), (b"tEXt", b"a\x00b"), (b"IDAT", data[5:])]
    assert code_of(rebuild(parts)) == "malformed"  # IDAT chunks not contiguous
    bad_filter = b.filter_rows(b"".join(bytes(p) for p in PIXELS), W * 4, H, 4, [0])
    parts = chunks_of(GOOD)
    parts[idat] = (b"IDAT", zlib.compress(b"\x09" + bad_filter[1:]))
    assert code_of(rebuild(parts)) == "malformed"  # unknown filter type


def test_indexed_images_are_checked():
    good = b.png_encode(W, H, PIXELS, ctype=3)
    parts = chunks_of(good)
    assert code_of(rebuild([c for c in parts if c[0] != b"PLTE"])) == "malformed"
    plte = [k for k, _ in parts].index(b"PLTE")
    bad = list(parts)
    bad[plte] = (b"PLTE", parts[plte][1][:-1])
    assert code_of(rebuild(bad)) == "malformed"  # length not a multiple of 3
    trns = [k for k, _ in parts].index(b"tRNS")
    bad = list(parts)
    bad[trns] = (b"tRNS", parts[trns][1] + b"\xff")
    assert code_of(rebuild(bad)) == "malformed"  # more alpha entries than palette entries
    two = b.png_encode(2, 1, [(1, 2, 3, 255), (4, 5, 6, 255)], ctype=3)
    parts = chunks_of(two)
    idat = [k for k, _ in parts].index(b"IDAT")
    parts[idat] = (b"IDAT", zlib.compress(b"\x00\x00\x07"))
    assert code_of(rebuild(parts)) == "malformed"  # a pixel indexes past the palette
    late = list(chunks_of(good))
    plte_chunk = late.pop(plte)
    late.insert([k for k, _ in late].index(b"IDAT") + 1, plte_chunk)
    assert code_of(rebuild(late)) == "malformed"  # PLTE after IDAT
    grey = chunks_of(b.png_encode(W, H, PIXELS, ctype=0))
    grey.insert(1, (b"PLTE", b"\x00\x00\x00"))
    assert code_of(rebuild(grey)) == "malformed"  # PLTE on a greyscale image


def test_every_truncation_and_every_single_byte_corruption_raises_only_png_decode_error():
    small = b.png_encode(4, 3, b.sample_pixels(4, 3), filters=[0, 1, 2, 3, 4])
    for length in range(len(small)):
        try:
            pixels.decode_png(small[:length])
        except PngDecodeError:
            pass
        else:
            raise AssertionError(f"a truncated PNG of {length} bytes decoded")
    for index in range(len(small)):
        broken = bytearray(small)
        broken[index] ^= 0x55
        try:
            pixels.decode_png(bytes(broken))
        except PngDecodeError:
            pass  # a corrupted file is refused; a corruption confined to pixel data can only be seen by the hash changing
    assert pixels.pixel_hash(small) == expected_hash(4, 3, b.sample_pixels(4, 3))


def test_a_large_paeth_image_decodes_in_reasonable_time():
    started = time.monotonic()
    image = pixels.decode_png(b.png_encode(256, 256, b.sample_pixels(256, 256), filters=[4]), max_dim=300)
    assert image.width == 256 and time.monotonic() - started < 5.0


def test_the_pixels_layer_is_pure():
    import ast
    from pathlib import Path

    tree = ast.parse(Path(pixels.__file__).read_text())
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert imported <= {"__future__", "hashlib", "struct", "zlib", "dataclasses", "functools", "itertools", "visual_assets"}
    assert not any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "open" for n in ast.walk(tree))
