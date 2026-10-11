"""Bounded reader for the facts intake checks in an Aseprite file. Pure: bytes in, facts and problems out.

Layout: Aseprite file format specification (docs/ase-file-specs.md in the Aseprite repository), all values
little-endian. Only the 128-byte header, the 16-byte frame headers and the 6-byte chunk headers are walked, plus the
few fixed fields of the layer, cel, tags and palette chunks that give counts. Cel pixel data is never decoded or
decompressed. Every size field is checked against the bytes actually present before it is used to advance, and the
walk is bounded by the file length (callers cap that at `config.MAX_SOURCE_BYTES`), so a hostile file cannot make
this loop long or allocate.

Palette size means "the palette size Aseprite reports after loading the file", because that is what the drawing tools
(and a human) see. Verified against Aseprite 1.3.18.6 by round-tripping files through the real binary: the stored entry
count is reported exactly, with one exception. A palette whose every stored entry is opaque black (the untouched default
that a never-edited first revision carries) is not used: Aseprite rebuilds the palette from the image, so the size it
reports is 1 plus the number of distinct opaque colours in the pixels (blank canvas 1, one red pixel 2, ...). Deriving
that needs cel pixel decoding, which intake does not do, so `palette_size` is None and a `PALETTE_UNVERIFIABLE` problem
is reported (the candidate is quarantined; any edit re-saves a verifiable palette). Aseprite writes either a new palette
chunk (0x2019) or an old one (0x0004), always with the header colour count equal to the stored entry count; a file that
breaks that, or has no palette chunk at all, is not something Aseprite writes and is reported as malformed.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from pydantic import TypeAdapter, ValidationError

from visual_assets.store import config
from visual_assets.store.contracts.animation import TagName
from visual_assets.store.contracts.intake import IntakeFindingCode as Code
from visual_assets.store.contracts.slices import SliceName

MAGIC_FILE = 0xA5E0
MAGIC_FRAME = 0xF1FA
HEADER_BYTES = 128
FRAME_HEADER_BYTES = 16
CHUNK_HEADER_BYTES = 6
DEPTH_RGBA = 32

CHUNK_OLD_PALETTE = 0x0004
CHUNK_OLD_PALETTE_6BIT = 0x0011
CHUNK_LAYER = 0x2004
CHUNK_CEL = 0x2005
CHUNK_TAGS = 0x2018
CHUNK_SLICE = 0x2022
CHUNK_PALETTE = 0x2019


@dataclass(frozen=True)
class RawTag:
    """One animation tag as the file stores it (direction is Aseprite's byte 0..3). Validated by `read_facts`, turned into a contract record by `store/animation.py`."""

    name: str
    from_frame: int
    to_frame: int
    direction: int
    repeat: int


@dataclass(frozen=True)
class RawSliceKey:
    """One slice key as the file stores it: from `frame` on, the rectangle (x, y, w, h) in sprite pixels; the 9-slice centre (x, y, w, h) and the pivot (x, y) are relative to the slice's own corner."""

    frame: int
    x: int
    y: int
    w: int
    h: int
    center: tuple[int, int, int, int] | None
    pivot: tuple[int, int] | None


@dataclass(frozen=True)
class RawSlice:
    """One slice chunk as the file stores it. Validated by `read_facts`, turned into a contract record by `store/slices.py`."""

    name: str
    keys: tuple[RawSliceKey, ...]


@dataclass(frozen=True)
class AsepriteFacts:
    width: int
    height: int
    frames: int
    color_depth: int
    layers: int
    cels: int
    tags: int
    palette_size: int | None  # None when it cannot be verified without decoding pixels (see module docstring)
    frame_durations_ms: tuple[int, ...] = ()  # one per frame, read from the frame headers, at most MAX_ANIMATION_FRAMES entries
    animation_tags: tuple[RawTag, ...] = ()  # at most MAX_ANIMATION_TAGS entries; never walked past that bound
    slices: tuple[RawSlice, ...] = ()  # at most MAX_SOURCE_SLICES entries of at most MAX_SLICE_KEYS keys each; never walked past those bounds


Problem = tuple[Code, str]

MAX_PALETTE_ENTRIES = 65536  # a palette larger than this is refused as malformed (never allocated or iterated)
TAG_FIXED_BYTES = 19  # from(2) to(2) direction(1) repeat(2) reserved(6) colour(3) extra(1) + the name's length word(2); the smallest legal tag, with an empty name
TAGS_HEADER_BYTES = 10  # tag count(2) + reserved(8)
DIRECTIONS = 4  # forward, reverse, ping-pong, ping-pong reverse
SLICE_HEADER_BYTES = 14  # key count(4) + flags(4) + reserved(4) + the name's length word(2); the smallest legal slice chunk, with an empty name and no keys
SLICE_KEY_BYTES = 20  # frame(4) x(4) y(4) w(4) h(4); the 9-slice flag adds 16 bytes (centre x, y, w, h), the pivot flag adds 8 (x, y)
SLICE_FLAG_NINE = 1
SLICE_FLAG_PIVOT = 2
_TAG_NAME = TypeAdapter(TagName)
_SLICE_NAME = TypeAdapter(SliceName)


def _read_tags(data: bytes, body: int, end: int, found: list[RawTag]) -> tuple[int, list[Problem]]:
    """Walk one tags chunk body (declared count first). Returns (declared count, problems). Every size is checked against the chunk's own bytes BEFORE it is used,
    and the walk stops at MAX_ANIMATION_TAGS entries in total, so a hostile chunk can neither run past its bytes nor make this allocate or loop long."""
    if end - body < TAGS_HEADER_BYTES:
        return 0, [(Code.SOURCE_TRUNCATED_CHUNK, "tags chunk is too short for its header")]
    (declared,) = struct.unpack_from("<H", data, body)
    if len(found) + declared > config.MAX_ANIMATION_TAGS:
        return declared, [(Code.ANIMATION_OUT_OF_BOUNDS, f"{len(found) + declared} tags; limit is {config.MAX_ANIMATION_TAGS}")]
    if body + TAGS_HEADER_BYTES + TAG_FIXED_BYTES * declared > end:
        return declared, [(Code.SOURCE_TRUNCATED_CHUNK, f"tags chunk declares {declared} tags but is too short to hold them")]
    problems: list[Problem] = []
    pos = body + TAGS_HEADER_BYTES
    for number in range(1, declared + 1):  # findings name a tag by its position, never by its text: a hostile name can expand past a finding's length limit when quoted
        if pos + TAG_FIXED_BYTES > end:
            return declared, [*problems, (Code.SOURCE_TRUNCATED_CHUNK, "a tag runs past the end of the tags chunk")]
        from_frame, to_frame, direction, repeat = struct.unpack_from("<HHBH", data, pos)
        (length,) = struct.unpack_from("<H", data, pos + TAG_FIXED_BYTES - 2)
        name_start = pos + TAG_FIXED_BYTES
        if name_start + length > end:
            return declared, [*problems, (Code.SOURCE_TRUNCATED_CHUNK, "a tag name runs past the end of the tags chunk")]
        pos = name_start + length
        try:
            name = _TAG_NAME.validate_python(data[name_start:pos].decode("utf-8"))
        except (UnicodeDecodeError, ValidationError):
            problems.append((Code.ANIMATION_TAG_INVALID, "a tag name is empty, over 32 characters, not plain text or not UTF-8"))
            continue
        if direction >= DIRECTIONS:
            problems.append((Code.ANIMATION_TAG_INVALID, f"tag {number} has the unknown direction {direction}"))
            continue
        found.append(RawTag(name, from_frame, to_frame, direction, repeat))
    return declared, problems


def _read_slice(data: bytes, body: int, end: int, found: list[RawSlice], number: int) -> list[Problem]:
    """Read one slice chunk body. Every count and length is checked against the chunk's own bytes BEFORE it is used; the slice count and the key count are checked against their
    bounds before any entry is read, so a hostile chunk can neither run past its bytes nor make this allocate or loop long. Findings name a slice by its chunk position (`number`, counting rejected chunks too), never by text."""
    if end - body < SLICE_HEADER_BYTES:
        return [(Code.SOURCE_TRUNCATED_CHUNK, "slice chunk is too short for its header")]
    if number > config.MAX_SOURCE_SLICES:
        return [(Code.SLICE_OUT_OF_BOUNDS, f"more than {config.MAX_SOURCE_SLICES} slices")]
    count, flags = struct.unpack_from("<II", data, body)
    (length,) = struct.unpack_from("<H", data, body + 12)
    name_start = body + SLICE_HEADER_BYTES
    if name_start + length > end:
        return [(Code.SOURCE_TRUNCATED_CHUNK, f"the name of slice {number} runs past its chunk")]
    if count > config.MAX_SLICE_KEYS:
        return [(Code.SLICE_OUT_OF_BOUNDS, f"slice {number} has {count} keys; limit is {config.MAX_SLICE_KEYS}")]
    if count == 0:
        return [(Code.SLICE_INVALID, f"slice {number} has no keys")]
    if flags & ~(SLICE_FLAG_NINE | SLICE_FLAG_PIVOT):
        return [(Code.SLICE_INVALID, f"slice {number} has unknown flag bits")]
    key_bytes = SLICE_KEY_BYTES + (16 if flags & SLICE_FLAG_NINE else 0) + (8 if flags & SLICE_FLAG_PIVOT else 0)
    pos = name_start + length
    if pos + key_bytes * count > end:
        return [(Code.SOURCE_TRUNCATED_CHUNK, f"slice {number} declares {count} keys but its chunk is too short to hold them")]
    try:
        name = _SLICE_NAME.validate_python(data[name_start:pos].decode("utf-8"))
    except (UnicodeDecodeError, ValidationError):
        return [(Code.SLICE_INVALID, f"the name of slice {number} is empty, over 32 characters, not plain text or not UTF-8")]
    keys: list[RawSliceKey] = []
    for _ in range(count):
        frame, x, y, w, h = struct.unpack_from("<IiiII", data, pos)
        pos += SLICE_KEY_BYTES
        center = pivot = None
        if flags & SLICE_FLAG_NINE:
            center = struct.unpack_from("<iiII", data, pos)
            pos += 16
        if flags & SLICE_FLAG_PIVOT:
            pivot = struct.unpack_from("<ii", data, pos)
            pos += 8
        keys.append(RawSliceKey(frame, x, y, w, h, center, pivot))
    found.append(RawSlice(name, tuple(keys)))
    return []


def _old_palette(data: bytes, start: int, end: int, nonblack: set[int]) -> int | None:
    """Entries covered by an old-style palette chunk body (adds non-black indexes to `nonblack`), or None on overrun."""
    if end - start < 2:
        return None
    (packets,) = struct.unpack_from("<H", data, start)
    pos, index = start + 2, 0
    for _ in range(packets):
        if pos + 2 > end:
            return None
        skip, count = data[pos], data[pos + 1] or 256
        pos += 2
        if pos + 3 * count > end:
            return None
        index += skip
        for i in range(count):
            if data[pos + 3 * i : pos + 3 * i + 3] != b"\x00\x00\x00":
                nonblack.add(index + i)
            else:
                nonblack.discard(index + i)
        pos += 3 * count
        index += count
    return index


def _new_palette(data: bytes, start: int, end: int, nonblack: set[int]) -> tuple[int, str | None]:
    """(declared size, problem text). Walks the entries of one 0x2019 chunk body, bounded by the chunk's own bytes."""
    if end - start < 20:
        return 0, "palette chunk is too short"
    size, first, last = struct.unpack_from("<III", data, start)
    if size > MAX_PALETTE_ENTRIES or first > last or last >= max(size, 1):
        return size, "palette chunk declares an impossible range"
    pos = start + 20
    for index in range(first, last + 1):
        if pos + 6 > end:
            return size, "palette entries run past the chunk"
        flags = struct.unpack_from("<H", data, pos)[0]
        red, green, blue, alpha = data[pos + 2 : pos + 6]
        pos += 6
        if flags & 1:  # entry has a name: WORD length + bytes
            if pos + 2 > end:
                return size, "palette entry name runs past the chunk"
            pos += 2 + struct.unpack_from("<H", data, pos)[0]
            if pos > end:
                return size, "palette entry name runs past the chunk"
        if (red, green, blue, alpha) != (0, 0, 0, 255):
            nonblack.add(index)
        else:
            nonblack.discard(index)
    return size, None


def read_facts(data: bytes) -> tuple[AsepriteFacts | None, list[Problem]]:
    """Return the facts (None when the header cannot be trusted at all) and every structural problem found."""
    problems: list[Problem] = []
    if len(data) < HEADER_BYTES:
        return None, [(Code.SOURCE_TRUNCATED, f"file is {len(data)} bytes; the header alone needs {HEADER_BYTES}")]
    size_field, magic, frames, width, height, depth = struct.unpack_from("<IHHHHH", data, 0)
    if magic != MAGIC_FILE:
        return None, [(Code.SOURCE_BAD_MAGIC, f"magic is 0x{magic:04X}, expected 0x{MAGIC_FILE:04X}")]
    if size_field != len(data):
        problems.append((Code.SOURCE_HEADER_SIZE_MISMATCH, f"header says {size_field} bytes, file has {len(data)}"))
    (header_colors,) = struct.unpack_from("<H", data, 32)

    layers = cels = tags = 0
    durations: list[int] = []
    raw_tags: list[RawTag] = []
    raw_slices: list[RawSlice] = []
    slice_chunks = 0
    new_palette: int | None = None
    old_palette = 0
    nonblack_new: set[int] = set()
    nonblack_old: set[int] = set()
    offset = HEADER_BYTES
    walked = 0
    broken = False
    for _ in range(frames):
        if offset + FRAME_HEADER_BYTES > len(data):
            problems.append((Code.SOURCE_TRUNCATED, f"frame {walked + 1} header is cut off"))
            broken = True
            break
        frame_bytes, frame_magic = struct.unpack_from("<IH", data, offset)
        if frame_magic != MAGIC_FRAME or frame_bytes < FRAME_HEADER_BYTES:
            problems.append((Code.SOURCE_MALFORMED, f"frame {walked + 1} header is invalid"))
            broken = True
            break
        end = offset + frame_bytes
        if end > len(data):
            problems.append((Code.SOURCE_TRUNCATED, f"frame {walked + 1} runs past the end of the file"))
            broken = True
            break
        if len(durations) < config.MAX_ANIMATION_FRAMES:
            durations.append(struct.unpack_from("<H", data, offset + 8)[0])  # the frame header's duration word, in ms
        pos = offset + FRAME_HEADER_BYTES
        while pos < end:
            if pos + CHUNK_HEADER_BYTES > end:
                problems.append((Code.SOURCE_TRUNCATED_CHUNK, f"chunk header at byte {pos} is cut off"))
                broken = True
                break
            chunk_bytes, chunk_type = struct.unpack_from("<IH", data, pos)
            body, chunk_end = pos + CHUNK_HEADER_BYTES, pos + chunk_bytes
            if chunk_bytes < CHUNK_HEADER_BYTES or chunk_end > end:
                problems.append((Code.SOURCE_TRUNCATED_CHUNK, f"chunk 0x{chunk_type:04X} at byte {pos} overruns its frame"))
                broken = True
                break
            if chunk_type == CHUNK_LAYER:
                layers += 1
            elif chunk_type == CHUNK_CEL:
                cels += 1
            elif chunk_type == CHUNK_TAGS:
                if chunk_end - body < 2:
                    problems.append((Code.SOURCE_TRUNCATED_CHUNK, f"tags chunk at byte {pos} is too short"))
                    broken = True
                    break
                declared, tag_problems = _read_tags(data, body, chunk_end, raw_tags)
                tags += declared
                problems += tag_problems
                if any(code is Code.SOURCE_TRUNCATED_CHUNK for code, _ in tag_problems):
                    broken = True
                    break
            elif chunk_type == CHUNK_SLICE:
                slice_chunks += 1
                slice_problems = _read_slice(data, body, chunk_end, raw_slices, slice_chunks)
                problems += slice_problems
                if any(code is Code.SOURCE_TRUNCATED_CHUNK for code, _ in slice_problems):
                    broken = True
                    break
            elif chunk_type == CHUNK_PALETTE:
                declared, bad = _new_palette(data, body, chunk_end, nonblack_new)
                if bad is not None:
                    problems.append((Code.SOURCE_TRUNCATED_CHUNK, f"palette chunk at byte {pos}: {bad}"))
                    broken = True
                    break
                new_palette = declared
            elif chunk_type in (CHUNK_OLD_PALETTE, CHUNK_OLD_PALETTE_6BIT):
                entries = _old_palette(data, body, chunk_end, nonblack_old)
                if entries is None:
                    problems.append((Code.SOURCE_TRUNCATED_CHUNK, f"old palette chunk at byte {pos} overruns itself"))
                    broken = True
                    break
                old_palette = max(old_palette, entries)
            pos = chunk_end  # unknown chunk types are skipped by their declared size
        if broken:
            break
        walked += 1
        offset = end
    if not broken and offset != len(data):
        problems.append((Code.SOURCE_MALFORMED, f"{len(data) - offset} unexpected bytes after the last frame"))

    if new_palette is not None:
        palette, nonblack = new_palette, nonblack_new
    elif old_palette:
        palette, nonblack = old_palette, nonblack_old
        if header_colors != old_palette:
            problems.append((Code.SOURCE_MALFORMED, f"header colour count {header_colors} disagrees with the {old_palette} stored palette entries"))
    else:
        palette, nonblack = 0, {0}
        if not broken:
            problems.append((Code.SOURCE_MALFORMED, "the file has no palette chunk"))
    palette_size: int | None = palette
    if not nonblack:
        palette_size = None
        problems.append((Code.PALETTE_UNVERIFIABLE, "the stored palette is all opaque black, so its loaded size depends on pixel data"))
    problems += _animation_problems(frames, durations, raw_tags)
    problems += _slice_problems(frames, width, height, raw_slices)
    facts = AsepriteFacts(width, height, frames, depth, layers, cels, tags, palette_size, tuple(durations), tuple(raw_tags), tuple(raw_slices))
    return facts, problems


def _animation_problems(frames: int, durations: list[int], tags: list[RawTag]) -> list[Problem]:
    """Bounds and consistency of the animation metadata. A one-frame source is not animation, so only its tag ranges are checked (a tag outside its one frame is wrong either way)."""
    out: list[Problem] = []
    if frames > config.MAX_ANIMATION_FRAMES:
        out.append((Code.ANIMATION_OUT_OF_BOUNDS, f"{frames} frames; limit is {config.MAX_ANIMATION_FRAMES}"))
    elif frames > 1 and 0 in durations:
        out.append((Code.ANIMATION_FRAME_DURATION_INVALID, f"frame {durations.index(0) + 1} has a duration of 0 ms"))
    for number, tag in enumerate(tags, 1):
        if not 0 <= tag.from_frame <= tag.to_frame < frames:
            out.append((Code.ANIMATION_TAG_RANGE_INVALID, f"tag {number} covers frames {tag.from_frame}..{tag.to_frame} of {frames}"))
    names = [t.name for t in tags]
    if len(set(names)) != len(names):
        out.append((Code.ANIMATION_TAG_INVALID, "two tags share a name"))
    return out


def _slice_problems(frames: int, width: int, height: int, slices: list[RawSlice]) -> list[Problem]:
    """Consistency of the slices that were read: unique names, key frames in range and increasing, rectangles inside the canvas, centres and pivots inside their slice. Positions, never names."""
    out: list[Problem] = []
    names = [s.name for s in slices]
    if len(set(names)) != len(names):
        out.append((Code.SLICE_INVALID, "two slices share a name"))
    for number, one in enumerate(slices, 1):
        frames_seen = [k.frame for k in one.keys]
        if any(f >= frames for f in frames_seen):
            out.append((Code.SLICE_INVALID, f"slice {number} has a key past the {frames} frames"))
        if frames_seen != sorted(set(frames_seen)):
            out.append((Code.SLICE_INVALID, f"the keys of slice {number} are not in increasing frame order"))
        for key in one.keys:
            if key.w < 1 or key.h < 1 or key.x < 0 or key.y < 0 or key.x + key.w > width or key.y + key.h > height:
                out.append((Code.SLICE_GEOMETRY_INVALID, f"slice {number} has a rectangle outside the {width}x{height} canvas or without area"))
                break
            if key.center is not None:
                cx, cy, cw, ch = key.center
                if cw < 1 or ch < 1 or cx < 0 or cy < 0 or cx + cw > key.w or cy + ch > key.h:
                    out.append((Code.SLICE_GEOMETRY_INVALID, f"slice {number} has a 9-slice centre outside its slice or without area"))
                    break
            if key.pivot is not None and not (0 <= key.pivot[0] <= key.w and 0 <= key.pivot[1] <= key.h):
                out.append((Code.SLICE_GEOMETRY_INVALID, f"slice {number} has a pivot outside its slice"))
                break
    return out
