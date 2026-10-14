---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC
phase: done
date: 2026-10-07
tags: [architecture, hud, testing]
---

# TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC

## Title
Register every icon v2 key in one change and assemble the next release candidate on the new registry

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2`. Registering keys moves `registry_hash`, which breaks the guards that fresh-export the current
release candidate (learned in child 2 of the key-set batch: rc-0006). All v2 keys are therefore registered **once**,
after child 1 fixes the item families, so the batch needs one new candidate, not several.

## Scope
- Add every v2 key (`optional: true`, `variant_axes: []`, size, scale x1, fallback-safety class and fallback in the
  description, same form as the 14 key-set keys): 5 location markers (16x16 glyphs on `icon.plate.location`),
  5 buildings (24x24), 3 classes (24x24), 3 rarity badges (8x8), and the item families from child 1 (24x24).
- **Release candidate:** ask the user by blocking question to assemble the next candidate (rc-0007 expected: exactly
  rc-0006's 34 slots, since the adopted icons are unbuilt) on the new registry, as rc-0004/rc-0006
  were. Re-point the fixture guards by equality, following rc-0006's precedent (pilot fixture: fresh forest slots plus
  stored rc-0004; terrainset fixture; icondraft freshness ignores `registry_hash` only).
- Docs: store_contract, pilot_terrain_key (rc list), icon_key_set_review unchanged.

## Out of Scope
- Art, rule, building icons into artifacts (a release that covers icons is not asked for here).

## Acceptance Criteria
- [ ] All v2 keys registered; `store verify` ok; key-count guards re-pointed by equality.
- [ ] The candidate is assembled only after the user's own answer, recorded verbatim.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (epic), TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS, TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES (precedent)

## Related Docs
- docs/assets/store_contract.md, docs/assets/pilot_terrain_key.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC/ (plan, investigation, test_plan, mutant_proof.txt)

## Related Code Areas
- visual_assets/catalog/definitions/visual_keys.yaml, visual_assets/catalog/manifests/candidates/pilot/, tests/visual_assets/

## Assumptions / Open Questions
- If the user declines a new candidate, stop and tell the planner (keys then wait for the drawing ticket). The user did NOT decline (below).
- Key count checked against the planner's: 5 locations + 5 buildings + 3 classes + 3 rarity badges + 6 item families = 22 (enemy_camp, blacksmith and warrior already exist in the key set).

## Implementation Notes
- **The user's answer, verbatim (blocking question I asked myself, 2026-10-07):** "Assemble rc-0007" (option text: register the 22 keys once, assemble `pilot/rc-0007` with rc-0006's 34 slots, re-export the terrain-set fixture, re-point the guards by equality, nothing loosened). The candidate was assembled only after it.
- **22 keys, all `optional: true`, `variant_axes: []`, no detail axis:** `icon.marker.{resource_grove,ruins,dungeon_entrance,shrine,boss_arena}` (16x16 glyph over the plate), `icon.building.{store,guild,inn,hero_house,class_hall}` (24x24), `icon.class.{ranger,mage,rogue}` (24x24), `icon.rarity.{common,uncommon,rare}` (8x8), `icon.item.{weapon,armor,trinket,tool,consumable,material}` (24x24, the six families of child 1; the key list is tied to `visual_assets/icons/item_families.yaml` by a test). Each description states size, scale x1, class (all identifying) and the fallback from what the UI shows today (emoji labels with their colours, Lucide icons, rarity colours, item_type text; the class hall has no icon today). No legendary badge (user, 2026-10-07).
- **`pilot/rc-0007`:** 34 entries equal to rc-0006's, new registry hash `sha256:d07c83487ef9f766ed61b60caa6fe2b1fe979672a1077af3b315e54dc9e5d9bc`; terrain-set fixture manifest re-exported (PNGs identical).
- **Guards re-pointed by equality, following rc-0006 exactly:** pilot fixture guard now fresh-exports `rc-0007` (forest slots) plus stored `rc-0004`; terrain-set fixture guard fresh-exports `rc-0007` and a new "rc-0007 lists exactly rc-0006's entries" test (the rc-0006 and rc-0005 history tests stay); `adopted_facts.RELEASE_CANDIDATES` gains `rc-0007.json`; stdio release count 6 to 7; registry pin extended by the 22 keys (names and sizes from the shared `icon_v2_keys.py`); `test_icon_draft_set` and `test_icon_set_adoption` now say the registry holds the 14 key-set keys plus the 22 v2 keys; the icondraft freshness guard needed no change (it ignores only `registry_hash`). Frontend `iconScene.test.ts`: the 14 drawn keys still match the registry's descriptions and the registry holds 14 + 22.
- **New `test_icon_v2_keys.py`:** registered once, optional, axis-free, size, scale, class and fallback stated, 5/5/3/3/6, six item keys equal the families, three rarity keys and none for legendary, no adoption, artifact or release slot for any v2 key.
- **Docs:** `store_contract.md` and `pilot_terrain_key.md` (rc-0007 paragraph with the registry hash).

## Test Summary
- `pytest tests/visual_assets tests/docs tests/static` and frontend `vitest run src/visualAssets`: pytest tests/visual_assets + docs + static: all passed (1747 incl. 5 new); whole frontend vitest: all passed; `store verify` ok.
- Mutants (mutant_proof.txt): a dropped item key, a v2 key with a variant axis, and a description that loses its fallback each fail for the stated reason (the first axis mutant was malformed and failed in the registry loader; redone with a valid axis).

## Files Changed
- visual_assets/catalog/definitions/visual_keys.yaml, manifests/candidates/pilot/rc-0007.json, frontend terrainset fixture manifest, tests/visual_assets/{icon_v2_keys,test_icon_v2_keys,test_pilot_fixture,test_terrainset_fixture,adopted_facts,test_catalog_integrity,test_icon_draft_set,test_icon_set_adoption}.py and the registry and stdio guards, frontend iconScene.test.ts, docs/assets/{store_contract,pilot_terrain_key}.md, ticket and stored artifacts.

## Completion Summary
22 icon set v2 keys registered once; rc-0007 assembled after the user's answer; every pinned guard re-pointed by equality.
