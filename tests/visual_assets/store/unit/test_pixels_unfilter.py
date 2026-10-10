"""The fast PNG unfilter equals the plain per-byte definition on every input (TCK-20261010-VISUAL-ASSETS-PNG-DECODER-SPEEDUP).

`reference_unfilter` is the pre-speed-up decoder loop, kept verbatim as the executable definition. The corpus test decodes every PNG committed in the repository with both and
requires identical RGBA and pixel hashes; the random tests cover every filter type, every channel count and widths from 1 pixel up, with per-row mixed filters.
"""

from __future__ import annotations

import random
import subprocess
from pathlib import Path

import pytest

from tests.visual_assets.store import builders as b
from visual_assets.store import config, pixels
from visual_assets.store.errors import PngDecodeError

REPO = Path(__file__).resolve().parents[4]


def reference_unfilter(raw: bytes, width_bytes: int, height: int, bpp: int) -> bytearray:
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
            raise pixels._fail("malformed", f"row {row} has the unknown filter type {ftype}")
    return out


def committed_pngs() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z", "*.png"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split("\0")[:-1]
    return [REPO / name for name in out]


def random_raw(rng, stride, height, bpp, filters):
    raw = bytearray()
    for row in range(height):
        raw.append(filters[row % len(filters)] if filters else rng.randrange(5))
        raw += bytes(rng.randrange(256) for _ in range(stride))
    return bytes(raw)


@pytest.mark.parametrize("bpp", [1, 2, 3, 4])
@pytest.mark.parametrize("width", [1, 2, 3, 7, 16, 33])
@pytest.mark.parametrize("filters", [[0], [1], [2], [3], [4], None])
def test_fast_unfilter_equals_the_reference_on_random_rows(bpp, width, filters):
    rng = random.Random(f"{bpp}-{width}-{filters}")
    for height in (1, 2, 5):
        raw = random_raw(rng, width * bpp, height, bpp, filters)
        assert pixels._unfilter(raw, width * bpp, height, bpp) == reference_unfilter(raw, width * bpp, height, bpp)


def test_extreme_bytes_wrap_the_same_way():
    for fill in (0x00, 0x7F, 0x80, 0xFF):
        for ftype in range(5):
            raw = b"".join(bytes([ftype]) + bytes([fill]) * 16 for _ in range(3))
            assert pixels._unfilter(raw, 16, 3, 4) == reference_unfilter(raw, 16, 3, 4)


def test_an_unknown_filter_type_is_refused_in_both():
    raw = bytes([9]) + b"\x00" * 4
    for fn in (pixels._unfilter, reference_unfilter):
        with pytest.raises(PngDecodeError) as err:
            fn(raw, 4, 1, 4)
        assert err.value.code == "malformed"


def test_add_bytes_is_a_bytewise_wrapping_add():
    rng = random.Random(1)
    for n in (0, 1, 5, 64):
        x, y = bytes(rng.randrange(256) for _ in range(n)), bytes(rng.randrange(256) for _ in range(n))
        assert pixels._add_bytes(x, y) == bytes((p + q) & 255 for p, q in zip(x, y))


def test_every_committed_png_decodes_identically_with_the_reference(monkeypatch):
    files = committed_pngs()
    assert len(files) > 100, len(files)  # the corpus is the whole repository's committed PNGs, not a sample
    fast = {}
    for path in files:
        data = path.read_bytes()
        try:
            image = pixels.decode_png(data, max_dim=4096)
        except PngDecodeError as exc:
            fast[path] = exc.code
            continue
        fast[path] = (image.width, image.height, image.rgba, pixels.pixel_hash_of(image))
    pixels.decode_png.cache_clear()
    monkeypatch.setattr(pixels, "_unfilter", reference_unfilter)
    for path in files:
        data = path.read_bytes()
        try:
            image = pixels.decode_png(data, max_dim=4096)
            slow = (image.width, image.height, image.rgba, pixels.pixel_hash_of(image))
        except PngDecodeError as exc:
            slow = exc.code
        assert fast[path] == slow, path
    monkeypatch.undo()
    pixels.decode_png.cache_clear()


def test_a_mixed_filter_png_round_trips_through_the_real_decoder():
    rng = random.Random(3)
    px = [(rng.randrange(256), rng.randrange(256), rng.randrange(256), rng.randrange(256)) for _ in range(40 * 30)]
    png = b.png_encode(40, 30, px, filters=[0, 1, 2, 3, 4])
    image = pixels.decode_png(png, max_dim=64)
    assert image.rgba == bytes(v for p in px for v in p)


# ---- the decode memo ----

def test_the_same_bytes_are_decoded_once_and_a_refusal_is_not_cached(monkeypatch):
    pixels.decode_png.cache_clear()
    png = b.png_encode(4, 4, [(1, 2, 3, 255)] * 16)
    calls = []
    real = pixels._unfilter
    monkeypatch.setattr(pixels, "_unfilter", lambda *a: calls.append(1) or real(*a))
    first = pixels.decode_png(png, max_dim=16)
    assert pixels.decode_png(png, max_dim=16) is first and len(calls) == 1
    with pytest.raises(PngDecodeError):
        pixels.decode_png(png, max_dim=2)  # another limit is another key, and it refuses
    with pytest.raises(PngDecodeError):
        pixels.decode_png(png, max_dim=2)
    monkeypatch.setattr(config, "MAX_DECODED_BYTES", 10)
    with pytest.raises(PngDecodeError) as err:
        pixels.decode_png(png, max_dim=16)  # the decoded-size bound is part of the key: a cached success cannot bypass a tightened bound
    assert err.value.code == "too_large"


def test_the_memo_keeps_at_most_four_images():
    pixels.decode_png.cache_clear()
    for width in range(1, 9):
        pixels.decode_png(b.png_encode(width, 1, [(0, 0, 0, 255)] * width), max_dim=16)
    assert pixels._decode.cache_info().currsize == 4


def test_a_bytearray_still_decodes_and_an_oversize_file_is_never_kept(monkeypatch):
    pixels.decode_png.cache_clear()
    png = b.png_encode(4, 4, [(1, 2, 3, 255)] * 16)
    assert pixels.decode_png(bytearray(png), max_dim=16) == pixels.decode_png(png, max_dim=16)
    pixels.decode_png.cache_clear()
    monkeypatch.setattr(config, "MAX_DECODED_BYTES", 70)  # the 4x4 image needs 68 decoded bytes; the file itself is longer than 70
    pixels.decode_png(png, max_dim=16)
    assert pixels._decode.cache_info().currsize == 0
