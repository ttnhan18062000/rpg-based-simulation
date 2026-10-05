"""The colour-vision check of a whole draft set, as predeclared in `docs/assets/pilot_terrain_m5_criteria.md` (section "AM5-S: the set colour-vision rule").

Reuses the pilot check's Machado simulation, Lab and CIE76 code (`pilot_colour_vision`); nothing is copied. For every unordered pair of terrain keys and each
vision it compares the distance between the two tiles' mean colours (`dE_tile`) with the distance between the two flat fills (`dE_fill`). Pure Python, read-only.

    python -m tests.visual_assets.set_colour_vision [set_id]      # prints the evidence as JSON (default set: terrain-v1)
"""

from __future__ import annotations

import itertools
import json
import re
import sys
from pathlib import Path

from tests.visual_assets.pilot_colour_vision import (
    EXPORT,
    REPO,
    VISIONS,
    Rgb,
    delta_e,
    from_hex,
    mean,
    texture,
    tile_fills,
)
from visual_assets.store import pixels

DRAFTS = REPO / "visual_assets" / "drafts"
DRAFT_KEYS_TS = REPO / "frontend" / "src" / "visualAssets" / "terrainDrafts.ts"
FOREST_KEY = "terrain.forest"
TOLERANCE = 2.0  # S1: the tiles may be at most this much closer than the flat fills ...
FLOOR = 10.0  # ... unless they are at least this far apart
TEXTURE_MIN = 2.0  # S2: standard deviation of L* over every tile, in every vision
SCALE = 8  # draft previews are 8x nearest-neighbour copies of the 16-pixel tile

Tile = list[Rgb]


def draft_keys() -> dict[str, int]:
    """visual key -> Live Map terrain code, from `TERRAIN_DRAFT_KEYS` in terrainDrafts.ts (the code-to-key contract)."""
    block = DRAFT_KEYS_TS.read_text().split("export const TERRAIN_DRAFT_KEYS", 1)[1].split("})", 1)[0]
    return {key: int(code) for code, key in re.findall(r"(\d+):\s*'(terrain\.[a-z_]+)'", block)}


def _opaque(image: pixels.DecodedImage, step: int) -> Tile:
    out: Tile = []
    for y in range(0, image.height, step):
        for x in range(0, image.width, step):
            i = (y * image.width + x) * 4
            assert image.rgba[i + 3] == 255, "a terrain tile is fully opaque"
            out.append((image.rgba[i] / 255, image.rgba[i + 1] / 255, image.rgba[i + 2] / 255))
    return out


def tile_from_preview(png: bytes) -> Tile:
    """The 256 pixels of a draft's 8x preview; every 8 x 8 block must be one colour (a nearest-neighbour copy), otherwise the file is not what the set claims."""
    image = pixels.decode_png(png)
    assert (image.width, image.height) == (16 * SCALE, 16 * SCALE)
    for by, bx in itertools.product(range(16), range(16)):
        first = (by * SCALE * image.width + bx * SCALE) * 4
        for dy, dx in itertools.product(range(SCALE), range(SCALE)):
            at = ((by * SCALE + dy) * image.width + bx * SCALE + dx) * 4
            assert image.rgba[at : at + 4] == image.rgba[first : first + 4], f"preview block ({bx},{by}) is not uniform"
    return _opaque(image, SCALE)


def draft_tiles(set_id: str, root: Path = DRAFTS) -> dict[str, Tile]:
    """visual key -> tile for every `terrain.` entry of a committed draft set (the set's own forest entry, if any, is under its key like the rest)."""
    entries = json.loads((root / set_id / "draft_set.json").read_text())["entries"]
    # AM5-S is a rule about terrain tiles; the `border.*` mask drafts in the same set are transparent shapes, not tiles, and are checked by test_border_masks.py.
    return {e["visual_key"]: tile_from_preview((root / set_id / e["draft_id"] / "preview.png").read_bytes()) for e in entries if e["visual_key"].startswith("terrain.")}


def adopted_forest(export: Path = EXPORT) -> dict[str, Tile]:
    """Forest's adopted slots (plain, bush, tree) from the committed pilot runtime export, as 16-pixel tiles."""
    manifest = json.loads((export / "runtime_manifest.json").read_text())
    out: dict[str, Tile] = {}
    for entry in manifest["entries"]:
        if entry["visual_key"] == FOREST_KEY:
            image = pixels.decode_png((export / entry["file"]).read_bytes())
            assert (image.width, image.height) == (16, 16)
            out[entry["detail"]] = _opaque(image, 1)
    return out


def evaluate_set(tiles: dict[str, Tile], fills: dict[str, str], variants: dict[str, Tile] | None = None) -> dict:
    """The rule applied to `tiles` (key -> pixels; forest is its adopted `plain`) against `fills` (key -> '#rrggbb'). Every number and the verdict.

    S1 per pair-vision: `dE_tile >= dE_fill - 2.0` or `dE_tile >= 10.0`. S2 per tile-vision: texture >= 2.0. `PASS` iff S1 holds everywhere;
    wording "better" (S2 too), "same" (S2 fails somewhere), "worse" (S1 fails). `variants` (forest bush/tree) are reported, never part of the verdict.
    """
    assert set(tiles) == set(fills), "every tile needs a flat fill and vice versa"
    keys = sorted(tiles)
    means = {k: mean(tiles[k]) for k in keys}
    flat = {k: from_hex(fills[k]) for k in keys}
    pairs = []
    for a, b in itertools.combinations(keys, 2):
        row = {"a": a, "b": b}
        for vision in VISIONS:
            tile_d = delta_e(means[a], means[b], vision)
            fill_d = delta_e(flat[a], flat[b], vision)
            row[vision] = {"dE_tile": round(tile_d, 3), "dE_fill": round(fill_d, 3), "margin": round(tile_d - fill_d, 3),
                           "s1": tile_d >= fill_d - TOLERANCE or tile_d >= FLOOR}
        pairs.append(row)
    textures = {k: {v: round(texture(tiles[k], v), 3) for v in VISIONS} for k in keys}
    failing = [{"a": p["a"], "b": p["b"], "vision": v, **{n: p[v][n] for n in ("dE_tile", "dE_fill", "margin")}} for p in pairs for v in VISIONS if not p[v]["s1"]]
    flat_tiles = sorted(k for k in keys if any(textures[k][v] < TEXTURE_MIN for v in VISIONS))
    s1, s2 = not failing, not flat_tiles
    report = {
        "rule": {"s1": f"dE_tile >= dE_fill - {TOLERANCE} or dE_tile >= {FLOOR}", "s2": f"texture >= {TEXTURE_MIN}"},
        "tiles": len(keys), "pairs": len(pairs), "pair_visions": len(pairs) * len(VISIONS),
        "s1": s1, "s2": s2, "result": "PASS" if s1 else "FAIL", "wording": "worse" if not s1 else ("better" if s2 else "same"),
        "failing_pair_visions": sorted(failing, key=lambda f: f["margin"]), "tiles_below_texture": flat_tiles,
        "min_dE_tile": min(p[v]["dE_tile"] for p in pairs for v in VISIONS), "textures": textures, "pair_table": pairs,
        "note": "The flat-fill baseline is hue-only, not colour-vision safe: a pass means the tiles are not worse than it (or are at least 10 dE apart).",
    }
    if variants:
        report["forest_variants"] = {
            d: {"texture": {v: round(texture(t, v), 3) for v in VISIONS},
                "min_dE_to_others": {v: round(min(delta_e(mean(t), means[k], v) for k in keys if k != FOREST_KEY), 3) for v in VISIONS}}
            for d, t in sorted(variants.items())
        }
    return report


def live_set(set_id: str = "terrain-v1") -> dict:
    """The committed set plus forest's adopted slots, against the Live Map fills."""
    codes, fills = draft_keys(), tile_fills()
    forest = adopted_forest()
    tiles = {k: t for k, t in draft_tiles(set_id).items() if k != FOREST_KEY}
    tiles[FOREST_KEY] = forest["plain"]
    return evaluate_set(tiles, {k: fills[c] for k, c in codes.items()}, {d: t for d, t in forest.items() if d != "plain"})


if __name__ == "__main__":
    print(json.dumps(live_set(sys.argv[1] if len(sys.argv) > 1 else "terrain-v1"), indent=2))
