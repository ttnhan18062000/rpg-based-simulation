"""Exact facts about what the committed catalog holds (TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION; build and rc-0005 added by TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN; the icon key set added by
TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION).

The owner adopted draft set `terrain-v1` themselves on 2026-10-05T18:17:03Z (UTC): one `adopt-set`, tiles and border masks together. These constants pin the committed truth: the guards that
used to say "the catalog holds only the pilot forest" compare against them with equality, never `>=`, so a stray adoption or a missing file still fails. If the catalog changes again (a new
adoption, a revocation), these facts change in the same commit as that decision, with its own ticket.

Two owner decisions are recorded: `terrain-v1` (2026-10-05T18:17:03Z, 31 sources next to the pilot forest's three) and `icons-key-v1` (2026-10-06T15:21:47Z, 14 icon sources). `TERRAIN_ERA_SOURCES` is
the 34 of the first, `ICON_SOURCES` the 14 of the second and `ADOPTED_SOURCES` everything the catalog holds (48). `build` and `release` have covered only the 34 terrain-era sources: no artifact and no
release candidate covers an icon slot (rc-0006 and rc-0007 have 34 entries; the icon keys are `optional: true`).
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

ADOPTED_SOURCES = sorted(TERRAIN_ERA_SOURCES + ICON_SOURCES)
SET_ADOPTION_IDS = sorted([SET_ADOPTION_ID, ICON_SET_ADOPTION_ID])
# Counts under the committed catalog: one adoption per source, two intake provenance files (record and review) per adoption.
ADOPTION_COUNT = 48
INTAKE_FILE_COUNT = 96
assert (len(ADOPTED_SOURCES), ADOPTION_COUNT, INTAKE_FILE_COUNT) == (48, 48, 2 * 48)
# `build` and `release` (TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN, approved by the user on 2026-10-06): one generated artifact directory per adopted source, and the candidate pilot/rc-0005 holds all 34 slots.
# rc-0004 still holds the forest's three slots only. rc-0006 (`TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES`, approved by the user on 2026-10-06) is rc-0005's 34 slots on the registry that added the 14 `icon.*` keys; rc-0007 (`TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC`, approved by the user on 2026-10-07) is the same 34 slots on the registry that added the 22 icon set v2 keys.
GENERATED = sorted(f"{source}--x1" for source in TERRAIN_ERA_SOURCES)  # no icon has been built yet
RELEASE_CANDIDATES = ["rc-0001.json", "rc-0002.json", "rc-0003.json", "rc-0004.json", "rc-0005.json", "rc-0006.json", "rc-0007.json"]
