"""Shared reading of draft sets for the review tools: previews back to 1x sprites, the lint summary, the glyph live area, the draft set hash.

Read-only. A preview is the 8x nearest-neighbour copy `export_handoff` makes and `draft keep` hashed; every 8x8 block must be one RGBA value, otherwise the file is not what the draft claims
(`TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI`: extracted from `icon_draft_set` so every per-set definition shares one reader).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from visual_assets.drawing.technique.lint import lint_grid
from visual_assets.review import icon_sheet_rule as rule
from visual_assets.review.pilot_colour_vision import REPO
from visual_assets.store import config, pixels

DRAFTS = REPO / "visual_assets" / "drafts"
SCALE = 8  # `export_handoff` makes 8x previews


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


def grid_of(sprite: rule.Sprite) -> list[list[str]]:
    return [[f"#{p[0]:02x}{p[1]:02x}{p[2]:02x}{p[3]:02x}" for p in sprite.rgba[y * sprite.width : (y + 1) * sprite.width]] for y in range(sprite.height)]


def lint_summary(sprites: dict[str, rule.Sprite]) -> dict:
    out = {}
    for key, sprite in sorted(sprites.items()):
        report = lint_grid(grid_of(sprite))
        out[key] = {"ok": report["ok"], "colors": report["stats"]["colors"], "color_budget": report["stats"]["color_budget"],
                    "findings": sorted({f["code"] for f in report["findings"]}), "warnings": sorted({f["code"] for f in report["findings"] if f["level"] == "warn"})}
    return out


def glyph_live_area(sprite: rule.Sprite) -> dict:
    """Bounding box of the glyph's opaque pixels: the style guide's live area is 12x12 with a 2 px margin on a 16x16 canvas."""
    xs = [i % sprite.width for i, p in enumerate(sprite.rgba) if p[3]]
    ys = [i // sprite.width for i, p in enumerate(sprite.rgba) if p[3]]
    return {"bbox": [min(xs), min(ys), max(xs), max(ys)], "margin": [min(xs), min(ys), sprite.width - 1 - max(xs), sprite.height - 1 - max(ys)]}


def draft_set_hash(set_id: str, root: Path = DRAFTS) -> str:
    """The hash of the exact `draft_set.json` bytes (what `adopt-set` prints and the review folder shows)."""
    return "sha256:" + hashlib.sha256((root / set_id / "draft_set.json").read_bytes()).hexdigest()
