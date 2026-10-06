"""Exact facts about what the committed catalog holds (TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION; build and rc-0005 added by TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN).

The owner adopted draft set `terrain-v1` themselves on 2026-10-05T18:17:03Z (UTC): one `adopt-set`, tiles and border masks together. These constants pin the committed truth: the guards that
used to say "the catalog holds only the pilot forest" compare against them with equality, never `>=`, so a stray adoption or a missing file still fails. If the catalog changes again (a new
adoption, a revocation), these facts change in the same commit as that decision, with its own ticket.
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
ADOPTED_SOURCES = sorted(FOREST_SOURCES + TERRAIN_SOURCES + BORDER_SOURCES)

assert (len(TERRAIN_SOURCES), len(BORDER_SOURCES), len(ADOPTED_SOURCES)) == (22, 9, 34)
SET_SOURCES = sorted(TERRAIN_SOURCES + BORDER_SOURCES)  # the 31 the set adoption covers
# Counts under the committed catalog: one adoption per source, two intake provenance files (record and review) per adoption.
ADOPTION_COUNT = 34
INTAKE_FILE_COUNT = 68
# `build` and `release` (TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN, approved by the user on 2026-10-06): one generated artifact directory per adopted source, and the candidate pilot/rc-0005 holds all 34 slots.
# rc-0004 still holds the forest's three slots only.
GENERATED = sorted(f"{source}--x1" for source in ADOPTED_SOURCES)
RELEASE_CANDIDATES = ["rc-0001.json", "rc-0002.json", "rc-0003.json", "rc-0004.json", "rc-0005.json"]
