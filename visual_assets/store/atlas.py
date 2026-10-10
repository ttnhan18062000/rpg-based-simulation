"""Opt-in runtime atlases (`export-runtime --atlas`): one deterministic sheet per family next to the unchanged per-file export.

Pure: no file, clock or path access. Packing is a fixed shelf: entries sorted by (visual key, detail), placed left to right on shelves at most `SHELF_WIDTH` wide, each in a
cell of its size plus a 1 px EXTRUDE (its own edge pixels repeated, so a scaled or filtered sample never bleeds a neighbour) and a 1 px transparent GUTTER between cells and
around the sheet. The PNG is written by one minimal encoder (IHDR, IDAT, IEND; filter 0; zlib level 9), so the same input gives the same bytes and no time or text chunk exists.
`verify_atlas` re-decodes the sheet and checks every rectangle against its source pixel hash and its extrude border: export refuses to write a sheet that fails it.
"""

from __future__ import annotations

import struct
import zlib
from collections.abc import Mapping, Sequence

from visual_assets.store import config, pixels
from visual_assets.store.contracts.atlas import AtlasEntry, AtlasManifest
from visual_assets.store.contracts.base import canonical_json
from visual_assets.store.contracts.runtime import RuntimeEntry
from visual_assets.store.errors import BuildError
from visual_assets.store.intake.validator import file_hash

SHELF_WIDTH = 1024
EXTRUDE = 1
GUTTER = 1


def encode_png(width: int, height: int, rgba: bytes) -> bytes:
    """A deterministic RGBA8 PNG: IHDR, one IDAT, IEND."""
    stride = width * 4
    raw = b"".join(b"\x00" + rgba[row * stride : (row + 1) * stride] for row in range(height))

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    return pixels.SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def _order(entry: RuntimeEntry) -> tuple[str, str]:
    return entry.visual_key, entry.detail or ""


def pack(entries: Sequence[RuntimeEntry]) -> tuple[int, int, list[tuple[RuntimeEntry, int, int]]]:
    """(sheet width, sheet height, [(entry, x, y)]) with x, y the image's top-left pixel (extrude excluded)."""
    placed: list[tuple[RuntimeEntry, int, int]] = []
    x, y, shelf_height, used_width = GUTTER, GUTTER, 0, 0
    for entry in sorted(entries, key=_order):
        cell_w, cell_h = entry.width + 2 * EXTRUDE, entry.height + 2 * EXTRUDE
        if x > GUTTER and x + cell_w + GUTTER > SHELF_WIDTH:  # next shelf
            y += shelf_height + GUTTER
            x, shelf_height = GUTTER, 0
        placed.append((entry, x + EXTRUDE, y + EXTRUDE))
        x += cell_w + GUTTER
        shelf_height = max(shelf_height, cell_h)
        used_width = max(used_width, x)
    return used_width, y + shelf_height + GUTTER, placed


def build_atlas(family: str, entries: Sequence[RuntimeEntry], images: Mapping[str, pixels.DecodedImage], *, catalog_id: str, release_id: str) -> tuple[bytes, bytes]:
    """(atlas PNG bytes, atlas JSON bytes) for the entries of one family. `images` maps a pixel hash to its decoded artifact."""
    width, height, placed = pack(entries)
    if width > config.MAX_ATLAS_DIM or height > config.MAX_ATLAS_DIM:
        raise BuildError("atlas_too_large", f"the {family} atlas would be {width}x{height}, over the {config.MAX_ATLAS_DIM} px bound")
    sheet = bytearray(width * height * 4)
    rows: list[AtlasEntry] = []
    for entry, x, y in placed:
        image = images[entry.pixel_hash]
        w, h, stride = image.width, image.height, image.width * 4
        for row in range(-EXTRUDE, h + EXTRUDE):
            source_row = min(max(row, 0), h - 1)
            line = image.rgba[source_row * stride : (source_row + 1) * stride]
            left, right = line[:4], line[stride - 4 :]
            start = ((y + row) * width + (x - EXTRUDE)) * 4
            sheet[start : start + (w + 2 * EXTRUDE) * 4] = left * EXTRUDE + line + right * EXTRUDE
        rows.append(AtlasEntry(visual_key=entry.visual_key, detail=entry.detail, pixel_hash=entry.pixel_hash, x=x, y=y, width=w, height=h))
    png = encode_png(width, height, bytes(sheet))
    manifest = AtlasManifest(
        record_type="runtime_atlas", schema_version=1, catalog_id=catalog_id, release_id=release_id, family=family, file=f"atlas-{family}.png",
        file_hash=file_hash(png), width=width, height=height, extrude=EXTRUDE, gutter=GUTTER, entries=tuple(rows),
    )
    data = canonical_json(manifest)
    verify_atlas(png, manifest)
    return png, data


def verify_atlas(png: bytes, manifest: AtlasManifest) -> None:
    """Decode the sheet and check size, file hash, every rectangle's pixel hash and every extrude border; raise `BuildError("atlas_mismatch")` on the first difference."""
    if file_hash(png) != manifest.file_hash:
        raise BuildError("atlas_mismatch", f"{manifest.file} does not match its recorded file hash")
    sheet = pixels.decode_png(png, max_dim=config.MAX_ATLAS_DIM)
    if (sheet.width, sheet.height) != (manifest.width, manifest.height):
        raise BuildError("atlas_mismatch", f"{manifest.file} is {sheet.width}x{sheet.height}, its manifest says {manifest.width}x{manifest.height}")
    def crop(x: int, y: int, w: int, h: int) -> pixels.DecodedImage:
        return pixels.DecodedImage(w, h, b"".join(sheet.rgba[((y + r) * sheet.width + x) * 4 : ((y + r) * sheet.width + x + w) * 4] for r in range(h)))

    expected = bytearray(len(sheet.rgba))  # the gutter and everything not inside a cell is transparent black
    for e in manifest.entries:
        inner = crop(e.x, e.y, e.width, e.height)
        if pixels.pixel_hash_of(inner) != e.pixel_hash:
            raise BuildError("atlas_mismatch", f"the {e.visual_key} rectangle in {manifest.file} does not hold its artifact's pixels")
        stride = e.width * 4
        for row in range(-EXTRUDE, e.height + EXTRUDE):
            line = inner.rgba[min(max(row, 0), e.height - 1) * stride : (min(max(row, 0), e.height - 1) + 1) * stride]
            start = ((e.y + row) * sheet.width + (e.x - EXTRUDE)) * 4
            expected[start : start + (e.width + 2 * EXTRUDE) * 4] = line[:4] * EXTRUDE + line + line[stride - 4 :] * EXTRUDE
    if bytes(expected) != sheet.rgba:
        raise BuildError("atlas_mismatch", f"{manifest.file} differs from its entries (a wrong extrude border, a stray pixel or overlapping cells)")
