"""Exact facts about what the committed catalog holds (TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION; build and rc-0005 added by TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN; the icon key set added by
TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION; icon set v2 added by TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION).

The owner adopted draft set `terrain-v1` themselves on 2026-10-05T18:17:03Z (UTC): one `adopt-set`, tiles and border masks together. These constants pin the committed truth: the guards that
used to say "the catalog holds only the pilot forest" compare against them with equality, never `>=`, so a stray adoption or a missing file still fails. If the catalog changes again (a new
adoption, a revocation), these facts change in the same commit as that decision, with its own ticket.

Four owner decisions are recorded (the fourth, `icons-owner-fixes-v1`, is seven revisions of adopted icons: 77 adoptions, still 70 sources): `terrain-v1` (2026-10-05T18:17:03Z, 31 sources next to the pilot forest's three), `icons-key-v1` (2026-10-06T15:21:47Z, 14 icon sources) and `icons-v2` (2026-10-08T00:40:15Z, 22 icon sources). `TERRAIN_ERA_SOURCES` is
the 34 of the first, `ICON_SOURCES` the 14 of the second, `ICON_V2_SOURCES` the 22 of the third and `ADOPTED_SOURCES` everything the catalog holds (70). `build` covered only the 34 terrain-era sources until `TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE` built the 36 icons (one `x1` artifact each, owner-approved candidate `pilot/rc-0008` = rc-0007's 34 entries + the 36 icons).
rc-0001 to rc-0007 list no icon slot (rc-0006 and rc-0007 have 34 entries; the icon keys are `optional: true`).
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

# The owner's fourth decision (2026-10-08T14:23:46Z to 14:24:07Z): seven REVISIONS of adopted icons, each `adopt --parent r0001` -> `r0002`, from the draft set `icons-owner-fixes-v1`
# (TCK-20261008-VISUAL-ASSETS-RECORD-ICON-OWNER-FIXES-ADOPTION). They add adoptions, intakes and revision files but NO new source asset: the 70 sources stay. The set's other two drafts
# (`icon.marker.ruins`, `icon.marker.enemy_camp`) were not proposed ("Keep current versions") and are not adopted.
ICON_FIX_SET_ID = "icons-owner-fixes-v1"
ICON_FIX_DRAFT_SET_HASH = "sha256:bab784060aedc76838ebc246a3534d88559c9493082b1e076a1bdedb8b8fc6e0"
ICON_FIX_APPROVER = ("nhan", "owner")
ICON_FIX_ADOPTIONS = {  # source asset id -> (adoption id, intake id, decided_at); every one has parent r0001 and creates r0002
    "icon_building_hero_house": ("ad-0f04b1794541543e", "in-cce3e6b4fb609dc5", "2026-10-08T14:23:46Z"),
    "icon_building_inn": ("ad-c4edd43de67dbfa0", "in-ca88fbc521414581", "2026-10-08T14:23:50Z"),
    "icon_class_rogue": ("ad-9e51d5d4bf9ee568", "in-f332aa813db19054", "2026-10-08T14:23:54Z"),
    "icon_item_tool": ("ad-eb148a100d2249a8", "in-7d3825eda1fdb00e", "2026-10-08T14:23:57Z"),
    "icon_rarity_common": ("ad-a5eeb524eaeb0814", "in-db5985f18b3164cf", "2026-10-08T14:24:00Z"),
    "icon_status_frame_buff": ("ad-b21e0f1d680a6c73", "in-a927d82fcd493c0a", "2026-10-08T14:24:03Z"),
    "icon_status_frame_debuff": ("ad-e92bdc4e6b959a2b", "in-6ee2b5282280c703", "2026-10-08T14:24:07Z"),
}
ICON_FIX_SOURCES = sorted(ICON_FIX_ADOPTIONS)
assert len(ICON_FIX_SOURCES) == 7 and set(ICON_FIX_SOURCES) <= set(ICON_SOURCES + ICON_V2_SOURCES)

ADOPTED_SOURCES = sorted(TERRAIN_ERA_SOURCES + ICON_SOURCES + ICON_V2_SOURCES)
SET_ADOPTION_IDS = sorted([SET_ADOPTION_ID, ICON_SET_ADOPTION_ID, ICON_V2_SET_ADOPTION_ID])
# Counts under the committed catalog: one adoption per source plus one per revision (7), two intake provenance files (record and review) per adoption.
ADOPTION_COUNT = 77
INTAKE_FILE_COUNT = 154
REVISION_COUNT = 77  # r0001 of each of the 70 sources + r0002 of the 7 revised icons (what `store list --kind source` counts)
assert (len(ADOPTED_SOURCES), ADOPTION_COUNT, INTAKE_FILE_COUNT) == (70, 70 + len(ICON_FIX_SOURCES), 2 * 77)
# `build` and `release` (TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN, approved by the user on 2026-10-06): one generated artifact directory per adopted source, and the candidate pilot/rc-0005 holds all 34 slots.
# rc-0004 still holds the forest's three slots only. rc-0006 (`TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES`, approved by the user on 2026-10-06) is rc-0005's 34 slots on the registry that added the 14 `icon.*` keys; rc-0007 (`TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC`, approved by the user on 2026-10-07) is the same 34 slots on the registry that added the 22 icon set v2 keys.
TERRAIN_GENERATED = sorted(f"{source}--x1" for source in TERRAIN_ERA_SOURCES)  # the 34 built by `TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN`
ICON_GENERATED = sorted(f"{source}--x1" for source in ICON_SOURCES + ICON_V2_SOURCES)  # the 36 built by `TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE`, each at its newest revision
GENERATED = sorted(TERRAIN_GENERATED + ICON_GENERATED)  # one x1 artifact directory per adopted source (70)
assert len(ICON_GENERATED) == 36 and len(GENERATED) == 70
RELEASE_CANDIDATES = ["rc-0001.json", "rc-0002.json", "rc-0003.json", "rc-0004.json", "rc-0005.json", "rc-0006.json", "rc-0007.json", "rc-0008.json"]
# rc-0008 (the owner's answer, 2026-10-09: "Assemble rc-0008"): rc-0007's 34 entries + one entry per icon, 70 in all, on the registry that carries the structured fallbacks.
RC_0008_ICON_ENTRIES = 36

# The draft sets whose owner decision is recorded are CLOSED gates: their committed preview fixtures are the evidence of what the owner saw, so they are checked against the gate's own record
# (`tests/visual_assets/closed_draft_fixture.py`), not against the moving store, which grows references whenever art is built after the gate. Set id -> the adoption records that closed it.
CLOSED_DRAFT_SETS = {
    SET_ID: {"kind": "set_adoption", "adoption_ids": (SET_ADOPTION_ID,), "draft_set_hash": DRAFT_SET_HASH},
    ICON_SET_ID: {"kind": "set_adoption", "adoption_ids": (ICON_SET_ADOPTION_ID,), "draft_set_hash": ICON_DRAFT_SET_HASH,
                  "fixture_manifest_sha256": "sha256:f227efc175eb80d1040b7aa8ff30aed2fd64164cdc3dc05c2a92dc0e4c624ad2"},
    ICON_V2_SET_ID: {"kind": "set_adoption", "adoption_ids": (ICON_V2_SET_ADOPTION_ID,), "draft_set_hash": ICON_V2_DRAFT_SET_HASH,
                     "fixture_manifest_sha256": "sha256:3552998bb94054fb4f86613c6251c021c90779dc34ba3bacb2e19ff9162e174e"},
    # `fixture_manifest_sha256` pins the committed fixture's `draft_preview_manifest.json` (the owner's gate evidence, frozen at the gate): the fresh-export checks prove the record is still TRUE of the store, this proves the record itself was not rewritten (`icon_draft_fixture --write` on a closed set).
    # Seven per-slot `adopt --parent` records; they name no set hash, which is pinned by `test_icon_owner_fixes_adoption`.
    ICON_FIX_SET_ID: {"kind": "slot_adoptions", "adoption_ids": tuple(a for a, _, _ in ICON_FIX_ADOPTIONS.values()), "draft_set_hash": ICON_FIX_DRAFT_SET_HASH,
                        "fixture_manifest_sha256": "sha256:b9da86ddbea9fb313f9f02d01d6556b0801c35abf359c46650c8474462359944"},
}
