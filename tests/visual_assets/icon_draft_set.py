"""The drawn icon key set `icons-key-v1` read back from its committed draft set, and child 3's sheet rule (I1-I3) applied to it as measured (`TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET`).

Reads `visual_assets/drafts/icons-key-v1/` (the 8x nearest-neighbour previews that `draft keep` hashed) and nothing else; pure Python, read-only. The verdict is recorded by running this module, never asserted by
a test (a test must not decide the result on art, as with AM5-S):

    python -m tests.visual_assets.icon_draft_set      # prints the evidence as JSON
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from tests.visual_assets import icon_palette
from tests.visual_assets import icon_sheet_rule as rule
from tests.visual_assets.icon_sheet_synthetic import LADDER_CLASSES, real_tiles
from tests.visual_assets.pilot_colour_vision import REPO, mean
from visual_assets.drawing.technique.lint import lint_grid
from visual_assets.store import config, pixels

SET_ID = "icons-key-v1"
DRAFTS = REPO / "visual_assets" / "drafts"
SCALE = 8  # `export_handoff` makes 8x previews
TIERS = ("e", "d", "c", "b", "a", "s", "ss", "sss")
SIZES = {
    "icon.plate.location": 16, "icon.marker.enemy_camp": 16, "icon.building.blacksmith": 24, "icon.class.warrior": 24,
    **{f"icon.tier.{t}": 8 for t in TIERS}, "icon.status.frame_buff": 16, "icon.status.frame_debuff": 16,
}
GROUPS = {"tiers": [[f"icon.tier.{t}" for t in cls] for cls in LADDER_CLASSES], "status": [["icon.status.frame_buff"], ["icon.status.frame_debuff"]]}


def sprite_from_preview(png: bytes, size: int) -> rule.Sprite:
    """The 1x sprite of an 8x preview; every 8 x 8 block must be one RGBA value (a nearest-neighbour copy), otherwise the file is not what the draft claims."""
    image = pixels.decode_png(png, max_dim=config.MAX_PREVIEW_DIM)
    assert (image.width, image.height) == (size * SCALE, size * SCALE), f"preview is {image.width}x{image.height}, expected {size * SCALE}"
    out = []
    for by in range(size):
        for bx in range(size):
            first = (by * SCALE * image.width + bx * SCALE) * 4
            value = tuple(image.rgba[first : first + 4])
            for dy in range(SCALE):
                for dx in range(SCALE):
                    at = ((by * SCALE + dy) * image.width + bx * SCALE + dx) * 4
                    assert tuple(image.rgba[at : at + 4]) == value, f"preview block ({bx},{by}) is not uniform"
            out.append(value if value[3] else (0, 0, 0, 0))
    return rule.Sprite(size, size, tuple(out))


def draft_sprites(root: Path = DRAFTS, set_id: str = SET_ID) -> dict[str, rule.Sprite]:
    entries = json.loads((root / set_id / "draft_set.json").read_text())["entries"]
    return {e["visual_key"]: sprite_from_preview((root / set_id / e["draft_id"] / "preview.png").read_bytes(), SIZES[e["visual_key"]]) for e in entries}


def grid_of(sprite: rule.Sprite) -> list[list[str]]:
    return [[f"#{p[0]:02x}{p[1]:02x}{p[2]:02x}{p[3]:02x}" for p in sprite.rgba[y * sprite.width : (y + 1) * sprite.width]] for y in range(sprite.height)]


def lint_summary(sprites: dict[str, rule.Sprite]) -> dict:
    out = {}
    for key, sprite in sorted(sprites.items()):
        report = lint_grid(grid_of(sprite))
        out[key] = {"ok": report["ok"], "colors": report["stats"]["colors"], "color_budget": report["stats"]["color_budget"],
                    "findings": sorted({f["code"] for f in report["findings"]}), "warnings": sorted({f["code"] for f in report["findings"] if f["level"] == "warn"})}
    return out


def evaluate_draft_set(root: Path = DRAFTS, set_id: str = SET_ID) -> dict:
    sprites = draft_sprites(root, set_id)
    tile_means = {k: mean(t) for k, t in real_tiles().items()}
    report = rule.evaluate_sheet({k: s for k, s in sprites.items() if k != "icon.plate.location"}, GROUPS, {"icon.plate.location": sprites["icon.plate.location"]}, tile_means,
                                 palette=rule.committed_palette(icon_palette.PALETTE_FILE))
    report["set_id"] = set_id
    report["draft_set_hash"] = "sha256:" + __import__("hashlib").sha256((root / set_id / "draft_set.json").read_bytes()).hexdigest()
    report["lint"] = lint_summary(sprites)
    report["glyph_live_area"] = glyph_live_area(sprites["icon.marker.enemy_camp"])
    return report


def glyph_live_area(sprite: rule.Sprite) -> dict:
    """Bounding box of the glyph's opaque pixels: the style guide's live area is 12x12 with a 2 px margin on a 16x16 canvas."""
    xs = [i % sprite.width for i, p in enumerate(sprite.rgba) if p[3]]
    ys = [i // sprite.width for i, p in enumerate(sprite.rgba) if p[3]]
    return {"bbox": [min(xs), min(ys), max(xs), max(ys)], "margin": [min(xs), min(ys), sprite.width - 1 - max(xs), sprite.height - 1 - max(ys)]}


if __name__ == "__main__":
    print(json.dumps(evaluate_draft_set(Path(sys.argv[1]) if len(sys.argv) > 1 else DRAFTS), indent=1))
