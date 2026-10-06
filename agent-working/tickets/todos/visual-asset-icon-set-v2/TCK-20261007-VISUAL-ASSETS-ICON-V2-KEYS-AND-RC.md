---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC
phase: open
date: 2026-10-07
tags: [architecture, hud, testing]
---

# TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC

## Title
Register every icon v2 key in one change and assemble the next release candidate on the new registry

## Status
OPEN

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


## Related Code Areas
- visual_assets/catalog/definitions/visual_keys.yaml, visual_assets/catalog/manifests/candidates/pilot/, tests/visual_assets/

## Assumptions / Open Questions
- If the user declines a new candidate, stop and tell the planner (keys then wait for the drawing ticket).

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

