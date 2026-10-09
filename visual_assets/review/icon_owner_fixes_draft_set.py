"""The owner-fix revisions `icons-owner-fixes-v1` read back from their committed draft set, and every check applied as measured (`TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES`).

Six drawings (ruins, common bead, buff frame, rogue, enemy camp, tool) are new revisions (`r0002`, parent `r0001`) of ADOPTED sources, so they live in their own draft set and `icons-v2` and `icons-key-v1` stay untouched as history. The owner kept the adopted ruins and enemy camp, so only four are PROPOSED. This module overlays the four on the
adopted icons ("the set as it would stand after the owner adopts them") and runs the sheet rule on both rule families (the key-set groups and the v2 groups, thresholds unchanged), the spec compliance table (`CHECKS_R2`), and the look-alike report. Pure Python,
read-only; the verdict is recorded by running this module, never asserted by a test.

    python -m visual_assets.review.icon_owner_fixes_draft_set      # prints the evidence as JSON
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from visual_assets.review import icon_compliance as cp
from visual_assets.review import icon_draft_set as keyset
from visual_assets.review import icon_lookalikes as la
from visual_assets.review import icon_palette
from visual_assets.review import icon_sheet_rule as rule
from visual_assets.review import icon_v2_groups as groups
from visual_assets.review.icon_sheet_synthetic import real_tiles
from visual_assets.review.pilot_colour_vision import mean

SET_ID = "icons-owner-fixes-v1"
KEYS = ("icon.marker.ruins", "icon.rarity.common", "icon.status.frame_buff", "icon.class.rogue", "icon.marker.enemy_camp", "icon.item.tool", "icon.building.hero_house", "icon.status.frame_debuff", "icon.building.inn")
# Owner decision (planner's blocking question, 2026-10-08, answer verbatim: "Keep current versions"): the ruins arch and the spear-tent camp are NOT revised and are not proposed for adoption (the adopted
# brick wall and crossed swords stay: both drafts still misread in free text and the adopted versions read better). The drafts stay in the set as never-adopted drafts, because the store has no command to drop a
# draft slot (`draft` has keep, export and verify only) and editing `draft_set.json` by hand would bypass its record. They are never presented as candidates.
PROPOSED = ("icon.status.frame_buff", "icon.class.rogue", "icon.item.tool", "icon.rarity.common", "icon.building.hero_house", "icon.status.frame_debuff", "icon.building.inn")
NOT_PROPOSED = {
    "icon.marker.ruins": "owner decision: keep the adopted brick wall (the arch still misread in free text, \"document with arrow\", and the adopted version reads better)",
    "icon.marker.enemy_camp": "owner decision: keep the adopted crossed swords (the tent still misread in free text, \"crossed tools on red mound\", and the adopted version reads better)",
}
# Proposed slots whose CURRENT draft was rejected and is waiting for a redraw: the evaluation and the review folder leave the old draft out (the adopted drawing stays in its place) until the new draft is kept.
# The tool's toolbox was rejected by the owner for the theme (D21, 2026-10-08: "Hammer and tongs"); the replacement silhouette awaits the owner's approval before any drawing.
PENDING: dict[str, str] = {}  # empty now: every proposed slot has its drafted revision (the tool, the cottage, the debuff frame and the tankard were drawn after the owner approved their silhouettes on 2026-10-08)
assert set(PROPOSED) | set(NOT_PROPOSED) == set(KEYS) and not set(PROPOSED) & set(NOT_PROPOSED) and set(PENDING) <= set(PROPOSED)
EVALUATED = tuple(k for k in PROPOSED if k not in PENDING)
SIZES = {"icon.marker.ruins": 16, "icon.rarity.common": 8, "icon.status.frame_buff": 16, "icon.class.rogue": 24, "icon.marker.enemy_camp": 16, "icon.item.tool": 24, "icon.building.hero_house": 24, "icon.status.frame_debuff": 16, "icon.building.inn": 24}
DRAFTS = keyset.DRAFTS


def fix_sprites(root: Path = DRAFTS, set_id: str = SET_ID) -> dict[str, rule.Sprite]:
    entries = json.loads((root / set_id / "draft_set.json").read_text())["entries"]
    return {e["visual_key"]: keyset.sprite_from_preview((root / set_id / e["draft_id"] / "preview.png").read_bytes(), SIZES[e["visual_key"]]) for e in entries}


def proposed_sprites(root: Path = DRAFTS) -> dict[str, rule.Sprite]:
    """The 36 icons as they would stand if the owner adopts the four PROPOSED revisions: those four replace their adopted r0001 drawings; the two drafts that are not proposed are left out."""
    fixes = fix_sprites(root)
    return {**la.all_icon_sprites(), **{k: fixes[k] for k in EVALUATED}}


def evaluate(root: Path = DRAFTS) -> dict:
    sprites = proposed_sprites(root)
    palette = rule.committed_palette(icon_palette.PALETTE_FILE)
    key_set = {k: sprites[k] for k in keyset.SIZES}
    tile_means = {k: mean(t) for k, t in real_tiles().items()}
    v1 = rule.evaluate_sheet({k: s for k, s in key_set.items() if k != "icon.plate.location"}, keyset.GROUPS, {"icon.plate.location": key_set["icon.plate.location"]}, tile_means, palette=palette)
    v2 = rule.evaluate_sheet({k: s for k, s in sprites.items() if k != "icon.plate.location"}, groups.GROUPS, {}, {}, palette=palette, shape_only=groups.SHAPE_ONLY)
    mine = {k: s for k, s in fix_sprites(root).items() if k in EVALUATED}
    tiers = [sprites[k] for k in groups.TIER_KEYS.values()]
    compliance = cp.measure(sprites, list(EVALUATED), checks=cp.CHECKS_R2)
    return {
        "set_id": SET_ID,
        "proposed": list(PROPOSED),
        "pending_redraw": PENDING,
        "not_proposed": NOT_PROPOSED,
        "draft_set_hash": "sha256:" + hashlib.sha256((root / SET_ID / "draft_set.json").read_bytes()).hexdigest(),
        "result": "PASS" if v1["result"] == "PASS" and v2["result"] == "PASS" else "FAIL",
        "key_set_rule": v1,
        "v2_rule": v2,
        "lint": keyset.lint_summary(mine),
        "compliance": {k: [{"item": r.item, "spec": r.spec, "measured": r.measured, "ok": r.ok} for r in rows] for k, rows in compliance.items()},
        "compliance_all_ok": all(r.ok for rows in compliance.values() for r in rows),
        "rarity_vs_tier_min_shape_px": {k: min(rule.shape_distance(mine[k], t) for t in tiers) for k in groups.RARITY_KEYS if k in mine},
        "lookalike_close_pairs": la.report(sprites)["close_pairs"],
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(Path(sys.argv[1]) if len(sys.argv) > 1 else DRAFTS), indent=1))
