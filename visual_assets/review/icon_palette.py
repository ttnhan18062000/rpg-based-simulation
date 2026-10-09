"""The icon palette `icons-v1` and how it is derived (`TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE`, D20).

The committed file `visual_assets/palettes/icons-v1.json` is exactly what `build_palette()` returns, so its derivation is code, not prose:

1. **Terrain base.** The 23 Live Map terrain fills (`frontend/src/constants/colors.ts`, read the same way the AM5-S check reads them), one per `terrain-v1` key. Each fill is checked against
   the adopted tile: the mean colour of the tile's 256 pixels must be within `FILL_TOLERANCE` of the fill (the re-tint of `TCK-20261005-...-REDRAW` makes the 22 drafts equal; `terrain.forest` is the pilot tile adopted
   before that re-tint and is 2.42 units off, the one reason the tolerance is not 1.0).
2. **Ramps.** For each of `RAMP_SEEDS` (seven terrain fills chosen for hue spread), `make_ramp(seed, 4, base_index=1)`: one shadow step, the seed itself, two lighter steps (the drawing tool's own
   hue-shifted ramp; docs/assets/pixel_art_technique.md rule 1). The seed is exactly the terrain fill, so the ramp is traced to a terrain colour.
3. **Accents.** Eight hand-picked colours (`ACCENTS`): the outline, the plate rim and six signal colours. They are the only colours not traced to a terrain fill; each has its reason. They are
   proposals for the user's review at the owner gate with the art (`icons-key-v1`), not a decided set.

Pure Python, read-only. `python -m visual_assets.review.icon_palette` prints the palette (add `--write` to rewrite the committed file).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from visual_assets.review import set_colour_vision as scv
from visual_assets.review.pilot_colour_vision import REPO, from_hex, mean, tile_fills
from visual_assets.drawing.technique.ramps import make_ramp

PALETTE_FILE = REPO / "visual_assets" / "palettes" / "icons-v1.json"
SET_ID = "terrain-v1"
FILL_TOLERANCE = 2.5  # sRGB 0-255 units, per channel, between a terrain fill and the mean of its adopted tile
RAMP_STEPS, RAMP_BASE_INDEX = 4, 1
RAMP_SEEDS = ("terrain.wall", "terrain.farmland", "terrain.shallow_water", "terrain.lava", "terrain.dungeon_entrance", "terrain.road", "terrain.snow")
ACCENTS = (
    ("#0e1018", "outline", "near-black cool outline for glyphs and badges (L* about 5)"),
    ("#9ea4b6", "plate_rim", "mid-light plate rim: about L* 67: the lightness that stays furthest (18 L*) from every terrain-v1 tile mean, which run from L* 11 to 86 (the sheet rule's I3, `tests/visual_assets/icon_sheet_rule.py`)"),
    ("#e8c040", "accent_gold", "top tiers (S and above) and the lit edge of stars"),
    ("#d04030", "accent_ember", "debuff and hostile signal"),
    ("#48b858", "accent_leaf", "buff and friendly signal"),
    ("#50a8e0", "accent_sky", "neutral information signal"),
    ("#9060d0", "accent_violet", "magic and effects signal"),
    ("#f0ecd8", "accent_bone", "highlights and text-like glyph strokes"),
)


def _tiles() -> dict[str, list]:
    forest = scv.adopted_forest()
    tiles = {k: t for k, t in scv.draft_tiles(SET_ID).items() if k != scv.FOREST_KEY}
    tiles[scv.FOREST_KEY] = forest["plain"]
    return tiles


def terrain_fills() -> dict[str, str]:
    codes, fills = scv.draft_keys(), tile_fills()
    return {key: fills[code].lower() for key, code in sorted(codes.items())}


def fill_deviation() -> dict[str, float]:
    """Largest per-channel distance (0-255 units) between each terrain fill and the mean of its adopted tile."""
    out = {}
    for key, tile in _tiles().items():
        m = mean(tile)
        f = from_hex(terrain_fills()[key])
        out[key] = round(max(abs(m[i] - f[i]) * 255 for i in range(3)), 3)
    return dict(sorted(out.items()))


def build_palette() -> dict:
    fills = terrain_fills()
    entries: list[dict] = []
    seen: dict[str, int] = {}

    def add(colour: str, role: str, source: str) -> None:
        if colour in seen:
            entries[seen[colour]]["also"] = entries[seen[colour]].get("also", []) + [f"{role}: {source}"]
            return
        seen[colour] = len(entries)
        entries.append({"color": colour, "role": role, "source": source})

    for key, colour in fills.items():
        add(colour, "terrain", key)
    for seed in RAMP_SEEDS:
        ramp = make_ramp(fills[seed], RAMP_STEPS, base_index=RAMP_BASE_INDEX)
        for step, colour in enumerate(ramp):
            add(colour, "ramp", f"{seed} ramp step {step} of {RAMP_STEPS} (seed at step {RAMP_BASE_INDEX})")
    for colour, role, why in ACCENTS:
        add(colour, role, why)
    return {
        "record_type": "icon_palette", "palette_id": "icons-v1", "decision": "D20 (user, 2026-10-06): terrain-v1 base + 3-4 step ramps + a small accent set",
        "derivation": "tests/visual_assets/icon_palette.py::build_palette (the file is exactly its output)", "terrain_set": SET_ID,
        "colors": [e["color"] for e in entries], "entries": entries,
    }


if __name__ == "__main__":
    palette = build_palette()
    text = json.dumps(palette, indent=1) + "\n"
    if "--write" in sys.argv:
        PALETTE_FILE.parent.mkdir(parents=True, exist_ok=True)
        PALETTE_FILE.write_text(text)
    print(text)
