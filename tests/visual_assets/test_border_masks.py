"""The committed border masks of draft set terrain-v1 (TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-MASKS) against the border contract in `docs/assets/pilot_terrain_m5_criteria.md` (AM5-B):
nine slots, 16 x 16, 1-bit alpha, within the approved 4 px depth cap for their kind, ragged but with no isolated pixel, edge profiles that meet seamlessly. Pure Python, no Aseprite."""

from __future__ import annotations

import itertools
import json

from visual_assets.review.set_colour_vision import DRAFTS, SCALE
from visual_assets.store import pixels

DEPTH = 4  # the approved cap (user, 2026-10-06); the client's BORDER_DEPTH is tested equal to it
KINDS = ("edge", "outer_corner", "inner_corner")
VARIANTS = ("v1", "v2", "v3")
SIZE = 16


def committed_masks() -> dict[tuple[str, str], set[tuple[int, int]]]:
    """(kind, variant) -> opaque pixels of the 16 x 16 mask, read from the draft previews (each an 8x nearest-neighbour copy)."""
    root = DRAFTS / "terrain-v1"
    entries = json.loads((root / "draft_set.json").read_text())["entries"]
    out = {}
    for e in entries:
        if not e["visual_key"].startswith("border."):
            continue
        image = pixels.decode_png((root / e["draft_id"] / "preview.png").read_bytes())
        assert (image.width, image.height) == (SIZE * SCALE, SIZE * SCALE)
        opaque = set()
        for by, bx in itertools.product(range(SIZE), range(SIZE)):
            block = {image.rgba[((by * SCALE + dy) * image.width + bx * SCALE + dx) * 4 + 3] for dy in range(SCALE) for dx in range(SCALE)}
            assert len(block) == 1 and block <= {0, 255}, f"{e['visual_key']}[{e['detail']}] block ({bx},{by}) is not uniformly 0 or 255 alpha (1-bit mask)"
            if block == {255}:
                opaque.add((bx, by))
        out[(e["visual_key"].split(".", 1)[1], e["detail"])] = opaque
    return out


def allowed(kind: str, x: int, y: int, depth: int = DEPTH) -> bool:
    north, east = y < depth, x >= SIZE - depth
    return north if kind == "edge" else (north and east) if kind == "outer_corner" else (north or east)


def test_the_set_holds_exactly_the_nine_mask_slots():
    assert sorted(committed_masks()) == sorted(itertools.product(KINDS, VARIANTS))


def test_every_mask_is_a_1_bit_non_empty_shape_within_the_depth_cap_for_its_kind():
    for (kind, variant), opaque in committed_masks().items():
        assert opaque, f"{kind}[{variant}] is empty"
        outside = sorted(p for p in opaque if not allowed(kind, *p))
        assert not outside, f"{kind}[{variant}] has pixels beyond the {DEPTH} px cap or outside its corner: {outside[:4]}"


def test_no_mask_has_an_isolated_pixel():
    for (kind, variant), opaque in committed_masks().items():
        for x, y in opaque:
            assert any((x + dx, y + dy) in opaque for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))), f"{kind}[{variant}] has an isolated pixel at ({x},{y})"


def test_edge_variants_are_ragged_rows_from_the_cell_edge_that_meet_at_depth_two():
    masks = committed_masks()
    profiles = {}
    for variant in VARIANTS:
        opaque = masks[("edge", variant)]
        depths = []
        for x in range(SIZE):
            column = sorted(y for px, y in opaque if px == x)
            assert column == list(range(len(column))) and column, f"edge[{variant}] column {x} is not a run from the cell edge"
            depths.append(len(column))
        profiles[variant] = depths
        assert depths[0] == depths[-1] == 2, f"edge[{variant}] must start and end at depth 2 so any two variants meet seamlessly"
        assert max(abs(a - b) for a, b in zip(depths, depths[1:])) <= 1, f"edge[{variant}] changes depth by more than 1 per column"
        assert len(set(depths)) >= 3, f"edge[{variant}] is not ragged"
    assert len({tuple(p) for p in profiles.values()}) == 3  # the variants differ


def test_the_inner_corner_is_the_edge_plus_its_east_side_turn():
    masks = committed_masks()
    for variant in VARIANTS:
        north = masks[("edge", variant)]
        east = {(SIZE - 1 - y, x) for x, y in north}
        assert masks[("inner_corner", variant)] == north | east


def test_outer_corners_are_small_blobs_in_the_north_east_corner():
    for variant in VARIANTS:
        blob = committed_masks()[("outer_corner", variant)]
        assert (15, 0) in blob and 5 <= len(blob) <= DEPTH * DEPTH
