"""The drawn icon set v2 `icons-v2` read back from its committed draft set, and the sheet rule applied to it as measured (`TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET`).

Reads `visual_assets/drafts/icons-v2/` (the 8x nearest-neighbour previews `draft keep` hashed) and, for the groups that include icons of the adopted key set (enemy camp, blacksmith, warrior, the tiers), the
kept drafts of `icons-key-v1`, which are the adopted art. The groups, thresholds and the shape-only rule are the user's answers of 2026-10-07 (`icon_v2_groups`, `docs/assets/icon_criteria.md`). Pure Python,
read-only. The verdict is recorded by running this module, never asserted by a test (a test must not decide the result on art):

    python -m tests.visual_assets.icon_v2_draft_set      # prints the evidence as JSON
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from tests.visual_assets import icon_draft_set as v1
from tests.visual_assets import icon_palette
from tests.visual_assets import icon_sheet_rule as rule
from tests.visual_assets import icon_v2_groups as groups
from tests.visual_assets import icon_v2_keys as v2

SET_ID = "icons-v2"
DRAFTS = v1.DRAFTS
LOCATION_GLYPHS = [f"icon.marker.{n}" for n in v2.LOCATIONS]


def v2_sprites(root: Path = DRAFTS, set_id: str = SET_ID) -> dict[str, rule.Sprite]:
    entries = json.loads((root / set_id / "draft_set.json").read_text())["entries"]
    return {e["visual_key"]: v1.sprite_from_preview((root / set_id / e["draft_id"] / "preview.png").read_bytes(), v2.SIZES[e["visual_key"]]) for e in entries}


def all_sprites(root: Path = DRAFTS) -> dict[str, rule.Sprite]:
    """The v2 drafts plus the adopted key-set drafts the groups compare against (the plate is not in any group)."""
    key_set = {k: s for k, s in v1.draft_sprites(root).items() if k != "icon.plate.location"}
    return {**key_set, **v2_sprites(root)}


def evaluate(root: Path = DRAFTS) -> dict:
    sprites = all_sprites(root)
    report = rule.evaluate_sheet(sprites, groups.GROUPS, {}, {}, palette=rule.committed_palette(icon_palette.PALETTE_FILE), shape_only=groups.SHAPE_ONLY)
    report["set_id"] = SET_ID
    report["draft_set_hash"] = "sha256:" + hashlib.sha256((root / SET_ID / "draft_set.json").read_bytes()).hexdigest()
    mine = v2_sprites(root)
    report["lint"] = v1.lint_summary(mine)
    report["glyph_live_area"] = {k: v1.glyph_live_area(mine[k]) for k in LOCATION_GLYPHS}
    tiers = [sprites[k] for k in groups.TIER_KEYS.values()]
    report["rarity_vs_tier_min_shape_px"] = {k: min(rule.shape_distance(mine[k], t) for t in tiers) for k in groups.RARITY_KEYS}
    report["panel_live_area"] = {k: _bbox(mine[k]) for k in sorted(mine) if v2.SIZES[k] == 24}
    return report


def _bbox(sprite: rule.Sprite) -> list[int]:
    xs = [i % sprite.width for i, p in enumerate(sprite.rgba) if p[3]]
    ys = [i // sprite.width for i, p in enumerate(sprite.rgba) if p[3]]
    return [min(xs), min(ys), max(xs), max(ys)]


if __name__ == "__main__":
    print(json.dumps(evaluate(Path(sys.argv[1]) if len(sys.argv) > 1 else DRAFTS), indent=1))
