"""The drawn icon key set `icons-key-v1` read back from its committed draft set, and child 3's sheet rule (I1-I3) applied to it as measured (`TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET`).

Reads `visual_assets/drafts/icons-key-v1/` (the 8x nearest-neighbour previews that `draft keep` hashed) and nothing else; pure Python, read-only. The verdict is recorded by running
`python -m visual_assets.review evaluate --set icons-key-v1`, never asserted by a test (a test must not decide the result on art, as with AM5-S). Thin data after
`TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI`: the shared reading lives in `sprites.py`, the command in `sets.py` and `__main__.py`.
"""

from __future__ import annotations

import json
from pathlib import Path

from visual_assets.review import icon_palette
from visual_assets.review import icon_sheet_rule as rule
from visual_assets.review.icon_sheet_synthetic import LADDER_CLASSES, real_tiles
from visual_assets.review.pilot_colour_vision import mean
from visual_assets.review.sprites import DRAFTS, SCALE, draft_set_hash, glyph_live_area, grid_of, lint_summary, sprite_from_preview  # noqa: F401  (re-exported: other tools read them from here)

SET_ID = "icons-key-v1"
TIERS = ("e", "d", "c", "b", "a", "s", "ss", "sss")
SIZES = {
    "icon.plate.location": 16, "icon.marker.enemy_camp": 16, "icon.building.blacksmith": 24, "icon.class.warrior": 24,
    **{f"icon.tier.{t}": 8 for t in TIERS}, "icon.status.frame_buff": 16, "icon.status.frame_debuff": 16,
}
GROUPS = {"tiers": [[f"icon.tier.{t}" for t in cls] for cls in LADDER_CLASSES], "status": [["icon.status.frame_buff"], ["icon.status.frame_debuff"]]}


def draft_sprites(root: Path = DRAFTS, set_id: str = SET_ID) -> dict[str, rule.Sprite]:
    entries = json.loads((root / set_id / "draft_set.json").read_text())["entries"]
    return {e["visual_key"]: sprite_from_preview((root / set_id / e["draft_id"] / "preview.png").read_bytes(), SIZES[e["visual_key"]]) for e in entries}


def evaluate_draft_set(root: Path = DRAFTS, set_id: str = SET_ID) -> dict:
    sprites = draft_sprites(root, set_id)
    tile_means = {k: mean(t) for k, t in real_tiles().items()}
    report = rule.evaluate_sheet({k: s for k, s in sprites.items() if k != "icon.plate.location"}, GROUPS, {"icon.plate.location": sprites["icon.plate.location"]}, tile_means,
                                 palette=rule.committed_palette(icon_palette.PALETTE_FILE))
    report["set_id"] = set_id
    report["draft_set_hash"] = draft_set_hash(set_id, root)
    report["lint"] = lint_summary(sprites)
    report["glyph_live_area"] = glyph_live_area(sprites["icon.marker.enemy_camp"])
    return report
