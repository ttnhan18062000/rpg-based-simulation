"""Tests for src.rendering.render_annotated's annotated/gridlined renderer.

TCK-20260821-VISUAL-AGENT-REVIEW. Mirrors test_render_core.py's `_build_state`/
`_read_chunks` fixture conventions -- `render_annotated()` writes PNGs via the same
`png_writer.write_png`, so the same chunk-walking helper applies unchanged.
"""
from __future__ import annotations

import ast
import hashlib
import struct
import zlib
from pathlib import Path

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.rendering.render import terrain_color
from src.rendering.render_annotated import render_annotated

_RENDER_ANNOTATED_MODULE_PATH = (
    Path(__file__).resolve().parents[3] / "src" / "rendering" / "render_annotated.py"
)


def _build_state() -> AuthoritativeState:
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


def test_annotated_renderer_produces_valid_png_and_matches_plain_terrain_palette(tmp_path):
    state = _build_state()
    out_path = str(tmp_path / "frame_annotated.png")
    scale = 6

    render_annotated(state, out_path, scale=scale)

    png_bytes = Path(out_path).read_bytes()
    assert len(png_bytes) > 0
    chunks = _read_chunks(png_bytes)
    tags = [tag for tag, _ in chunks]
    assert tags[0] == b"IHDR"
    assert b"IDAT" in tags
    assert tags[-1] == b"IEND"
    assert chunks[-1][1] == b""

    ihdr_data = chunks[0][1]
    width, height, bit_depth, color_type = struct.unpack(">IIBB", ihdr_data[:10])
    assert bit_depth == 8
    assert color_type == 2  # RGB, no alpha

    # grid spans (0,0)-(3,3) inclusive -> grid_w == grid_h == 4; margin = 20 (Step 1).
    grid_w = grid_h = 4
    margin = 20
    assert width == grid_w * scale + margin
    assert height == grid_h * scale + margin

    # A plain render() of the same state has no margin term -- this distinguishes the
    # annotated variant structurally, not just by filename convention.
    assert width != grid_w * scale
    assert height != grid_h * scale

    # Tile (3,0) is "PLAIN", far from any grid_every=10 multiple row/column (grid_every
    # default of 10 exceeds this 4x4 fixture's extent entirely, so no gridline is drawn
    # anywhere inside the terrain area), and has no entity overlapping it -- entities
    # sit at (2,2) and (0,0) (both lifecycle-active and therefore both entity-colored by
    # render_annotated, which -- unlike render.py's render() -- draws every
    # lifecycle-active entity in one color regardless of combat.alive).
    expected_color = terrain_color("PLAIN")
    px, py = margin + 3 * scale + 1, margin + 0 * scale + 1  # interior of the (3,0) block
    raw = bytearray()
    for tag, data in chunks:
        if tag == b"IDAT":
            raw = bytearray(zlib.decompress(data))
    row_stride = 1 + width * 3
    row_start = py * row_stride
    pixel_offset = row_start + 1 + px * 3
    pixel = tuple(raw[pixel_offset : pixel_offset + 3])
    assert pixel == expected_color


@pytest.mark.regression
def test_annotated_renderer_golden_hash_bit_identical_across_three_independent_runs(tmp_path):
    # regression: TCK-20260821-VISUAL-AGENT-REVIEW -- mirrors
    # test_render_core.py::test_render_golden_hash_bit_identical_across_three_independent_runs.
    hashes = []
    for i in range(3):
        state = _build_state()  # independently constructed, content-equal object
        out_path = str(tmp_path / f"frame_annotated_{i}.png")
        render_annotated(state, out_path)
        digest = hashlib.sha256(Path(out_path).read_bytes()).hexdigest()
        hashes.append(digest)

    assert hashes[0] == hashes[1] == hashes[2]


def test_annotated_render_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline():
    tree = ast.parse(_RENDER_ANNOTATED_MODULE_PATH.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_names = [
                base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                for base in node.bases
            ]
            assert "PillarScorer" not in base_names, (
                "render_annotated.py must not subclass PillarScorer"
            )
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert "simulation_quality" not in name, f"render_annotated.py must not import {name}"
            assert "observability.events" not in name, f"render_annotated.py must not import {name}"
