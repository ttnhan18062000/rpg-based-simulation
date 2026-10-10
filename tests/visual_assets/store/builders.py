"""Synthetic candidate files for intake tests: a small pure-Python Aseprite writer, a PNG writer, package builders.

These write only what the intake checks read (header, frame headers, chunk headers and the fixed fields of the layer,
cel, tags and palette chunks). They are cross-checked against files written by real Aseprite in the integration tests.
"""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

from visual_assets.store.contracts import canonical_json, parse_record
from visual_assets.store.contracts.handoff import CandidateHandoffPackage
from visual_assets.store.intake.validator import file_hash

ASSERTION = "HANDOFF_IS_NOT_ADOPTION_PUBLICATION_OR_ACTIVATION"


def _string(text: str) -> bytes:
    raw = text.encode()
    return struct.pack("<H", len(raw)) + raw


def _chunk(kind: int, body: bytes) -> bytes:
    return struct.pack("<IH", 6 + len(body), kind) + body


def layer_chunk(name: str = "layer") -> bytes:
    return _chunk(0x2004, struct.pack("<HHHHHHB3x", 3, 0, 0, 0, 0, 0, 255) + _string(name))


def cel_chunk(layer_index: int = 0) -> bytes:
    body = struct.pack("<HhhBHh5x", layer_index, 0, 0, 255, 0, 0) + struct.pack("<HH", 1, 1) + b"\xff\x00\x00\xff"
    return _chunk(0x2005, body)


def tags_chunk(count: int) -> bytes:
    body = struct.pack("<H8x", count)
    for i in range(count):
        body += struct.pack("<HHBH6x3xB", 0, 0, 0, 0, 0) + _string(f"tag{i}")
    return _chunk(0x2018, body)


def tags_chunk_of(specs: list[tuple[str, int, int, int, int]]) -> bytes:
    """A tags chunk from (name, from_frame, to_frame, direction byte, repeat) tuples, laid out exactly as `tags_chunk` does."""
    body = struct.pack("<H8x", len(specs))
    for name, from_frame, to_frame, direction, repeat in specs:
        body += struct.pack("<HHBH6x3xB", from_frame, to_frame, direction, repeat, 0) + _string(name)
    return _chunk(0x2018, body)


def slice_chunk(name: str, keys: list[tuple], *, nine: bool = False, pivot: bool = False, flags: int | None = None, count: int | None = None) -> bytes:
    """A slice chunk (0x2022). Each key is (frame, x, y, w, h) plus, when `nine`, (cx, cy, cw, ch) and, when `pivot`, (px, py), in that order. `flags` and `count` override what the keys imply (hostile cases)."""
    declared = (1 if nine else 0) | (2 if pivot else 0) if flags is None else flags
    body = struct.pack("<III", len(keys) if count is None else count, declared, 0) + _string(name)
    for key in keys:
        body += struct.pack("<IiiII", *key[:5])
        rest = key[5:]
        if nine:
            body += struct.pack("<iiII", *rest[:4])
            rest = rest[4:]
        if pivot:
            body += struct.pack("<ii", *rest[:2])
    return _chunk(0x2022, body)


def palette_chunk(size: int, *, black: bool = False, named: bool = False, transparent: bool = False) -> bytes:
    """A new-style palette chunk. By default entries are non-black (so the size is reported exactly)."""
    entries = max(size, 1)
    body = struct.pack("<III8x", size, 0, entries - 1)
    for i in range(entries):
        red = 0 if (black or transparent) else (i + 1) % 256
        alpha = 0 if transparent else 255
        if named:
            body += struct.pack("<HBBBB", 1, red, 0, 0, alpha) + _string(f"c{i}")
        else:
            body += struct.pack("<HBBBB", 0, red, 0, 0, alpha)
    return _chunk(0x2019, body)


def old_palette_chunk(packets: list[tuple[int, int]], *, black: bool = False) -> bytes:
    body = struct.pack("<H", len(packets))
    for skip, count in packets:
        body += bytes([skip, count % 256]) + (b"\x00\x00\x00" if black else b"\x01\x02\x03") * (count or 256)
    return _chunk(0x0004, body)


def unknown_chunk(size_body: int = 4) -> bytes:
    return _chunk(0x7FFF, b"\x00" * size_body)


def frame(chunks: list[bytes], duration: int = 100) -> bytes:
    body = b"".join(chunks)
    return struct.pack("<IHHHxxI", 16 + len(body), 0xF1FA, len(chunks), duration, 0) + body


def aseprite(
    width: int = 16,
    height: int = 16,
    frames: int = 1,
    layers: int = 1,
    cels: int | None = None,
    tags: int = 0,
    palette: int = 8,
    depth: int = 32,
    *,
    extra_first_frame: list[bytes] | None = None,
    palette_chunks: list[bytes] | None = None,
    header_colors: int | None = None,
    durations: list[int] | None = None,
    tag_specs: list[tuple[str, int, int, int, int]] | None = None,
    slice_chunks: list[bytes] | None = None,
) -> bytes:
    """A syntactically valid sprite. `cels` defaults to one per layer per frame, spread over the frames. `durations` are the frame header durations in ms (one per frame, default 100);
    `tag_specs` replaces the anonymous `tags` chunk with named ones (name, from_frame, to_frame, direction byte, repeat); `slice_chunks` (see `slice_chunk`) go in the first frame."""
    total_cels = layers * frames if cels is None else cels
    frame_chunks: list[list[bytes]] = [[] for _ in range(frames)]
    frame_chunks[0] += palette_chunks if palette_chunks is not None else [palette_chunk(palette)]
    frame_chunks[0] += [layer_chunk(f"layer{i}") for i in range(layers)]
    for n in range(total_cels):
        frame_chunks[n % frames].append(cel_chunk(n % max(layers, 1)))
    if tag_specs is not None:
        frame_chunks[0].append(tags_chunk_of(tag_specs))
    elif tags:
        frame_chunks[0].append(tags_chunk(tags))
    frame_chunks[0] += slice_chunks or []
    frame_chunks[0] += extra_first_frame or []
    times = durations if durations is not None else [100] * frames
    assert len(times) == frames
    body = b"".join(frame(chunks, times[n]) for n, chunks in enumerate(frame_chunks))
    header = struct.pack("<IHHHHHIHII", 128 + len(body), 0xA5E0, frames, width, height, depth, 1, 100, 0, 0)
    colors = palette if header_colors is None else header_colors  # real Aseprite files: header count == stored entries
    header += b"\x00" + b"\x00\x00\x00" + struct.pack("<H", colors) + b"\x01\x01" + b"\x00" * 92
    assert len(header) == 128, len(header)
    return header + body


def png(width: int, height: int) -> bytes:
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x20\x40\x60\xff" * width for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def package_dict(source: bytes, preview: bytes, **overrides) -> dict:
    """A valid MANUAL-style package whose claims match `source` and `preview` (read from the builder's own layout)."""
    from visual_assets.store.intake.aseprite import read_facts

    facts, _ = read_facts(source)
    assert facts is not None
    data = dict(
        record_type="candidate_handoff_package", schema_version=1, candidate_id="cand-0123456789abcdef",
        source_file_name="source.aseprite", preview_file_name="preview.png",
        source_hash=file_hash(source), source_revision="r0001", expected_parent="NOT_APPLICABLE",
        producer_class="MANUAL", creator="Fixture Author", editor="NOT_APPLICABLE", adapter="NOT_APPLICABLE",
        tool="UNAVAILABLE", tool_version="UNAVAILABLE", source_format="ASEPRITE",
        width=facts.width, height=facts.height, frame_count=facts.frames, layer_count=facts.layers,
        cel_count=facts.cels, tag_count=facts.tags, palette_size=1 if facts.palette_size is None else facts.palette_size,
        preview_hash=file_hash(preview), brief_id="fixture-brief", human_review_ref="NOT_APPLICABLE",
        licence_state="CLEARED", licence_evidence_ref="fixture-licence-note", producer_state="ACTIVE",
        producer_validation="NOT_RUN", declared_limitations=[], assertion=ASSERTION,
    )
    data.update(overrides)
    return data


def package_bytes(source: bytes, preview: bytes, **overrides) -> bytes:
    """Canonical package.json bytes (validated, so an invalid override raises here, not inside intake)."""
    return canonical_json(parse_record(CandidateHandoffPackage, json.dumps(package_dict(source, preview, **overrides)).encode()))


def write_dir(directory: Path, package: bytes, source: bytes, preview: bytes) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "package.json").write_bytes(package)
    (directory / "source.aseprite").write_bytes(source)
    (directory / "preview.png").write_bytes(preview)
    return directory


def good_files(**source_kw) -> tuple[bytes, bytes, bytes]:
    source = aseprite(**source_kw)
    preview = png(source_kw.get("width", 16) * 8, source_kw.get("height", 16) * 8)
    return package_bytes(source, preview), source, preview


def bad_files(**source_kw) -> tuple[bytes, bytes, bytes]:
    """A defective candidate with its OWN package.json (distinct candidate id): the source has a wrong magic number."""
    source = aseprite(**source_kw)
    preview = png(source_kw.get("width", 16) * 8, source_kw.get("height", 16) * 8)
    package = package_bytes(source, preview, candidate_id="cand-badbadbadbad0001")
    return package, source[:4] + b"\x00\x00" + source[6:], preview


# --------------------------------------------------------------------------- a real PNG encoder (all filters, colour types, chunks)

Pixel = tuple[int, int, int, int]


def png_chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)


def filter_rows(samples: bytes, stride: int, height: int, bpp: int, types: list[int]) -> bytes:
    """Apply PNG filter `types[row % len(types)]` to each row of `samples` (the inverse of what the reader undoes)."""
    out = bytearray()
    for row in range(height):
        ftype = types[row % len(types)]
        line = samples[row * stride : (row + 1) * stride]
        prev = samples[(row - 1) * stride : row * stride] if row else bytes(stride)
        out.append(ftype)
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b_ = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            predicted = (0, a, b_, (a + b_) >> 1, _paeth(a, b_, c))[ftype]
            out.append((line[i] - predicted) & 255)
    return bytes(out)


def png_encode(
    width: int,
    height: int,
    pixels: list[Pixel],
    *,
    ctype: int = 6,
    filters: list[int] | None = None,
    level: int = 9,
    extra: list[tuple[bytes, bytes]] | None = None,
    idat_split: int = 0,
) -> bytes:
    """Encode `pixels` (RGBA tuples, row-major) as a PNG of colour type 6 (RGBA), 2 (RGB), 0 (grey), 4 (grey+alpha) or 3 (indexed)."""
    assert len(pixels) == width * height
    palette: list[Pixel] = []
    if ctype == 6:
        samples, bpp = b"".join(bytes(p) for p in pixels), 4
    elif ctype == 2:
        samples, bpp = b"".join(bytes(p[:3]) for p in pixels), 3
    elif ctype == 0:
        samples, bpp = bytes(p[0] for p in pixels), 1
    elif ctype == 4:
        samples, bpp = b"".join(bytes((p[0], p[3])) for p in pixels), 2
    else:
        palette = sorted(set(pixels))
        samples, bpp = bytes(palette.index(p) for p in pixels), 1
    raw = filter_rows(samples, width * bpp, height, bpp, filters or [0])
    chunks = [png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, ctype, 0, 0, 0))]
    chunks += [png_chunk(k, v) for k, v in (extra or []) if k not in (b"IDAT",)]
    if ctype == 3:
        chunks.append(png_chunk(b"PLTE", b"".join(bytes(p[:3]) for p in palette)))
        chunks.append(png_chunk(b"tRNS", bytes(p[3] for p in palette)))
    data = zlib.compress(raw, level)
    if idat_split:
        chunks += [png_chunk(b"IDAT", data[i : i + idat_split]) for i in range(0, len(data), idat_split)]
    else:
        chunks.append(png_chunk(b"IDAT", data))
    chunks.append(png_chunk(b"IEND", b""))
    return b"\x89PNG\r\n\x1a\n" + b"".join(chunks)


def sample_pixels(width: int, height: int, *, transparent_rgb: tuple[int, int, int] = (0, 0, 0)) -> list[Pixel]:
    """A deterministic image with opaque, semi-transparent and fully transparent pixels."""
    out: list[Pixel] = []
    for y in range(height):
        for x in range(width):
            if (x + y) % 5 == 0:
                out.append((*transparent_rgb, 0))  # fully transparent: the RGB under it must not matter
            elif (x * y) % 7 == 0:
                out.append(((x * 31) % 256, (y * 17) % 256, (x * y) % 256, 128))
            else:
                out.append(((x * 29 + 3) % 256, (y * 43 + 5) % 256, ((x + y) * 11) % 256, 255))
    return out
