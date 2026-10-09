"""The must-differ groups of icon set v2 (`TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS`), as the user answered on 2026-10-07 (`docs/assets/icon_criteria.md`, "Icon set v2").

- `rarity` (8x8): the three rarity badges among themselves, I1 and I2.
- `badges` (8x8): every rarity badge against every tier badge (E and D still share a class), I1 ONLY: two ladders next to their own text, eleven values cannot be told apart by brightness (the best
  11-step palette ladder is 4.5 L*), so shape alone separates them.
- `locations` (16x16), `buildings` (24x24), `classes` (24x24), `items` (24x24): different subjects, not an ordered ladder, I1 ONLY (the user's answer).
Group members come from the key set (enemy_camp, blacksmith, warrior, the tiers) and from the 22 v2 keys.
"""

from __future__ import annotations

from tests.visual_assets import icon_v2_keys as v2
from tests.visual_assets.icon_sheet_synthetic import GRADES, LADDER_CLASSES

SHAPE_ONLY = frozenset({"badges", "locations", "buildings", "classes", "items"})  # I1 alone; `rarity` keeps I1 and I2
TIER_KEYS = {g: f"icon.tier.{g}" for g in GRADES}
RARITY_KEYS = [f"icon.rarity.{r}" for r in v2.RARITIES]


def _single(keys: list[str]) -> list[list[str]]:
    return [[k] for k in keys]


GROUPS: dict[str, list[list[str]]] = {
    "rarity": _single(RARITY_KEYS),
    "badges": [[TIER_KEYS[g] for g in cls] for cls in LADDER_CLASSES] + _single(RARITY_KEYS),
    "locations": _single(["icon.marker.enemy_camp"] + [f"icon.marker.{n}" for n in v2.LOCATIONS]),
    "buildings": _single(["icon.building.blacksmith"] + [f"icon.building.{n}" for n in v2.BUILDINGS]),
    "classes": _single(["icon.class.warrior"] + [f"icon.class.{n}" for n in v2.CLASSES]),
    "items": _single([k for k in v2.KEYS if k.startswith("icon.item.")]),
}
SIZE = {"rarity": 8, "badges": 8, "locations": 16, "buildings": 24, "classes": 24, "items": 24}
