"""Core render() behavior: valid PNG output, golden-hash determinism, no state mutation.

TCK-20260821-WORLD-RENDER-CORE.
"""
from __future__ import annotations

import hashlib
import struct
import zlib
from pathlib import Path

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.rendering.render import render


def _build_state() -> AuthoritativeState:
    """Builds a small, deterministic AuthoritativeState with mixed-case terrain
    strings, buildings, blocked tiles, and both an alive and a dead entity — each
    call constructs independent Python objects with content-equal data."""
    terrain = {}
    for x in range(4):
        for y in range(4):
            terrain[(x, y)] = "PLAIN"
    terrain[(1, 1)] = "plain"
    terrain[(2, 2)] = "forest"
    terrain[(3, 3)] = "FOREST"

    entities = {
        1: (
            V2EntityBuilder(1)
            .kind("TEST_ALIVE")
            .location(2.0, 2.0)
            .combat(readiness=100.0)
            .build()
        ),
        2: (
            V2EntityBuilder(2)
            .kind("TEST_DEAD")
            .location(0.0, 0.0)
            .combat(readiness=0.0, alive=False)
            .build()
        ),
    }

    return AuthoritativeState(
        tick=0,
        seed=42,
        entities=entities,
        terrain=terrain,
        building_tiles={(0, 3): "SHOP"},
        blocked_tiles={(3, 0)},
    )


def _read_chunks(png_bytes: bytes) -> list[tuple[bytes, bytes]]:
    """Hand-walks the PNG chunk structure (length/tag/data/CRC32), mirroring
    png_writer.write_png's own chunk-building logic, without any new dependency."""
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    chunks = []
    offset = 8
    while offset < len(png_bytes):
        (length,) = struct.unpack(">I", png_bytes[offset : offset + 4])
        tag = png_bytes[offset + 4 : offset + 8]
        data = png_bytes[offset + 8 : offset + 8 + length]
        (crc,) = struct.unpack(">I", png_bytes[offset + 8 + length : offset + 12 + length])
        assert crc == zlib.crc32(tag + data) & 0xFFFFFFFF, f"bad CRC32 for chunk {tag!r}"
        chunks.append((tag, data))
        offset += 12 + length
    return chunks


def test_render_produces_valid_png(tmp_path):
    state = _build_state()
    out_path = str(tmp_path / "frame.png")

    stats = render(state, out_path, scale=2)

    png_bytes = Path(out_path).read_bytes()
    assert len(png_bytes) > 0
    chunks = _read_chunks(png_bytes)
    tags = [tag for tag, _ in chunks]
    assert tags[0] == b"IHDR"
    assert b"IDAT" in tags
    assert tags[-1] == b"IEND"
    assert tags[-1] == b"IEND" and chunks[-1][1] == b""

    ihdr_data = chunks[0][1]
    width, height, bit_depth, color_type = struct.unpack(">IIBB", ihdr_data[:10])
    assert (width, height) == (stats["width_px"], stats["height_px"])
    assert bit_depth == 8
    assert color_type == 2  # RGB, no alpha
    assert width == stats["grid_w"] * 2
    assert height == stats["grid_h"] * 2


def test_render_golden_hash_bit_identical_across_three_independent_runs(tmp_path):
    hashes = []
    for i in range(3):
        state = _build_state()  # independently constructed, content-equal object
        out_path = str(tmp_path / f"frame_{i}.png")
        render(state, out_path)
        digest = hashlib.sha256(Path(out_path).read_bytes()).hexdigest()
        hashes.append(digest)

    assert hashes[0] == hashes[1] == hashes[2]


def test_render_does_not_mutate_authoritative_state(tmp_path):
    state = _build_state()

    terrain_before = dict(state.terrain)
    blocked_before = set(state.blocked_tiles)
    building_before = dict(state.building_tiles)
    entity_ids_before = set(state.entities.keys())
    entity_positions_before = {
        eid: ent.navigation.position for eid, ent in state.entities.items()
    }
    entity_alive_before = {eid: ent.combat.alive for eid, ent in state.entities.items()}

    render(state, str(tmp_path / "frame.png"))

    assert dict(state.terrain) == terrain_before
    assert set(state.blocked_tiles) == blocked_before
    assert dict(state.building_tiles) == building_before
    assert set(state.entities.keys()) == entity_ids_before
    assert {
        eid: ent.navigation.position for eid, ent in state.entities.items()
    } == entity_positions_before
    assert {
        eid: ent.combat.alive for eid, ent in state.entities.items()
    } == entity_alive_before
