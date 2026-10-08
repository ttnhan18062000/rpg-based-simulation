"""Exact facts about what the committed catalog holds (TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION; build and rc-0005 added by TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN; the icon key set added by
TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION; icon set v2 added by TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION).

The owner adopted draft set `terrain-v1` themselves on 2026-10-05T18:17:03Z (UTC): one `adopt-set`, tiles and border masks together. These constants pin the committed truth: the guards that
used to say "the catalog holds only the pilot forest" compare against them with equality, never `>=`, so a stray adoption or a missing file still fails. If the catalog changes again (a new
adoption, a revocation), these facts change in the same commit as that decision, with its own ticket.

Three owner decisions are recorded: `terrain-v1` (2026-10-05T18:17:03Z, 31 sources next to the pilot forest's three), `icons-key-v1` (2026-10-06T15:21:47Z, 14 icon sources) and `icons-v2` (2026-10-08T00:40:15Z, 22 icon sources). `TERRAIN_ERA_SOURCES` is
the 34 of the first, `ICON_SOURCES` the 14 of the second, `ICON_V2_SOURCES` the 22 of the third and `ADOPTED_SOURCES` everything the catalog holds (70). `build` and `release` have covered only the 34 terrain-era sources: no artifact and no
release candidate covers an icon slot (rc-0006 and rc-0007 have 34 entries; the icon keys are `optional: true`), the 36 icons included.
"""

from __future__ import annotations

SET_ID = "terrain-v1"
SET_ADOPTION_ID = "sa-f4c541f25f112221"
DRAFT_SET_HASH = "sha256:287ab36c0299f9180b2ebf47afc84c95babf612818f80af3e0eeb78457023eb2"
DECIDED_AT = "2026-10-05T18:17:03Z"
APPROVER = ("nhan", "owner")

# The pilot (forest) slots: adopted before the set, unchanged by it.
FOREST_SOURCES = ["terrain_forest", "terrain_forest_bush", "terrain_forest_tree"]
# The 22 other Live Map terrains, one source each; the nine border masks, one source per (kind, variant).
TERRAIN_SOURCES = sorted(f"terrain_{name}" for name in (
    "bridge", "camp", "cave", "desert", "dungeon_entrance", "farmland", "floor", "grassland", "graveyard", "jungle", "lava", "mountain", "road", "ruins", "sanctuary",
    "shallow_water", "snow", "swamp", "town", "volcanic", "wall", "water"))
BORDER_SOURCES = sorted(f"border_{kind}_{variant}" for kind in ("edge", "inner_corner", "outer_corner") for variant in ("v1", "v2", "v3"))
TERRAIN_ERA_SOURCES = sorted(FOREST_SOURCES + TERRAIN_SOURCES + BORDER_SOURCES)

assert (len(TERRAIN_SOURCES), len(BORDER_SOURCES), len(TERRAIN_ERA_SOURCES)) == (22, 9, 34)
SET_SOURCES = sorted(TERRAIN_SOURCES + BORDER_SOURCES)  # the 31 the terrain-v1 set adoption covers

# The owner's second set adoption: the icon key set, one `adopt-set`, 14 sources (source asset id = the key with dots as underscores).
ICON_SET_ID = "icons-key-v1"
ICON_SET_ADOPTION_ID = "sa-b4bb738d6b5526f0"
ICON_DRAFT_SET_HASH = "sha256:29854e8b32bcd9701f5e717a2e01dce5934cc04af63d4c6e3bc156c78ce5cbbd"
ICON_DECIDED_AT = "2026-10-06T15:21:47Z"
ICON_APPROVER = ("nhan", "owner")
ICON_SOURCES = sorted(
    ["icon_plate_location", "icon_marker_enemy_camp", "icon_building_blacksmith", "icon_class_warrior", "icon_status_frame_buff", "icon_status_frame_debuff"]
    + [f"icon_tier_{tier}" for tier in ("e", "d", "c", "b", "a", "s", "ss", "sss")])
assert len(ICON_SOURCES) == 14

# The owner's third set adoption: icon set v2, one `adopt-set`, 22 sources (the draft set hash is the one the review doc and the adopt-set template printed).
ICON_V2_SET_ID = "icons-v2"
ICON_V2_SET_ADOPTION_ID = "sa-c9082d078b954f6b"
ICON_V2_DRAFT_SET_HASH = "sha256:bb41c3eef245f6eab3488d5c7a940e574a463112a0bfba611b0c5cfd012737f4"
ICON_V2_DECIDED_AT = "2026-10-08T00:40:15Z"
ICON_V2_APPROVER = ("nhan", "owner")
ICON_V2_SOURCES = sorted(
    [f"icon_marker_{n}" for n in ("resource_grove", "ruins", "dungeon_entrance", "shrine", "boss_arena")]
    + [f"icon_building_{n}" for n in ("store", "guild", "inn", "hero_house", "class_hall")]
    + [f"icon_class_{n}" for n in ("ranger", "mage", "rogue")]
    + [f"icon_item_{n}" for n in ("weapon", "armor", "trinket", "tool", "consumable", "material")]
    + [f"icon_rarity_{n}" for n in ("common", "uncommon", "rare")])
assert len(ICON_V2_SOURCES) == 22

ADOPTED_SOURCES = sorted(TERRAIN_ERA_SOURCES + ICON_SOURCES + ICON_V2_SOURCES)
SET_ADOPTION_IDS = sorted([SET_ADOPTION_ID, ICON_SET_ADOPTION_ID, ICON_V2_SET_ADOPTION_ID])
# Counts under the committed catalog: one adoption per source, two intake provenance files (record and review) per adoption.
ADOPTION_COUNT = 70
INTAKE_FILE_COUNT = 140
assert (len(ADOPTED_SOURCES), ADOPTION_COUNT, INTAKE_FILE_COUNT) == (70, 70, 2 * 70)
# `build` and `release` (TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN, approved by the user on 2026-10-06): one generated artifact directory per adopted source, and the candidate pilot/rc-0005 holds all 34 slots.
# rc-0004 still holds the forest's three slots only. rc-0006 (`TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES`, approved by the user on 2026-10-06) is rc-0005's 34 slots on the registry that added the 14 `icon.*` keys; rc-0007 (`TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC`, approved by the user on 2026-10-07) is the same 34 slots on the registry that added the 22 icon set v2 keys.
GENERATED = sorted(f"{source}--x1" for source in TERRAIN_ERA_SOURCES)  # no icon has been built yet: the 14 key-set icons and the 22 v2 icons are adopted sources without an artifact
RELEASE_CANDIDATES = ["rc-0001.json", "rc-0002.json", "rc-0003.json", "rc-0004.json", "rc-0005.json", "rc-0006.json", "rc-0007.json"]
