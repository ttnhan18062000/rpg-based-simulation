"""The 22 icon set v2 keys (`TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC`): names and sizes as the user-approved families fix them (`docs/assets/icon_style_guide.md`, "Icon set v2 decisions").

One list, used by every guard that describes the registry, so a v2 key cannot be added, renamed or resized in one place only.
"""

from __future__ import annotations

from tests.visual_assets.icon_item_families import load_mapping

LOCATIONS = ("resource_grove", "ruins", "dungeon_entrance", "shrine", "boss_arena")  # enemy_camp is a key-set key
BUILDINGS = ("store", "guild", "inn", "hero_house", "class_hall")  # blacksmith is a key-set key
CLASSES = ("ranger", "mage", "rogue")  # warrior is a key-set key
RARITIES = ("common", "uncommon", "rare")

SIZES: dict[str, int] = {
    **{f"icon.marker.{n}": 16 for n in LOCATIONS},
    **{f"icon.building.{n}": 24 for n in BUILDINGS},
    **{f"icon.class.{n}": 24 for n in CLASSES},
    **{f"icon.rarity.{n}": 8 for n in RARITIES},
    **{f"icon.item.{family}": 24 for family in sorted(set(load_mapping().values()))},
}
KEYS = sorted(SIZES)
assert len(KEYS) == 22 and (len(LOCATIONS), len(BUILDINGS), len(CLASSES), len(RARITIES)) == (5, 5, 3, 3)
