---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES
phase: done
date: 2026-10-06
tags: [architecture, hud, testing]
---

# TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES

## Title
Register the icon key set's visual keys, each with a stated fallback

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET`. The key set needs registered keys before any draft can name them. Families are free strings
(D19 note), so no schema change is expected.

## Scope
- Add to `visual_assets/catalog/definitions/visual_keys.yaml`, `variant_axes: []` on every key (D17):
  - `icon.plate.location` (16x16 map plate, the backing shape for every location marker)
  - `icon.marker.enemy_camp` (16x16 glyph drawn on the plate)
  - `icon.building.blacksmith` (24x24 panel icon)
  - `icon.class.warrior` (24x24 panel icon)
  - `icon.tier.e` ... `icon.tier.sss` (8 keys, 8x8 badges)
  - `icon.status.frame_buff`, `icon.status.frame_debuff` (16x16 frames)
  Exact names may follow repo naming rules if they differ; tell the planner before renaming.
- Each key's description names its size, scale x1, and its **fallback**: today's Lucide icon or emoji, or for tiers the
  colour chip plus letter. Classify each per `docs/assets/fallback_safety.md` (a tier badge carries meaning: say so).
- Docs: `store_contract.md` (the `icon.*` family), `registry_hash` change noted. Re-point any guard that pins the key count, by equality.
- **Corrected 2026-10-06 (planner error):** the registry hash change DOES matter here: `rc-0005` and `rc-0004` can no longer be exported (`registry_mismatch`), which fails two committed fresh-export guards. The user answered by blocking question (asked by asset-implementer): "Assemble rc-0006" (same 34 slots on the new registry). Scope therefore also includes: assemble `pilot/rc-0006`, re-export the terrainset fixture, re-point the guards (below) and record the rc in `docs/assets/pilot_terrain_key.md` and `store_contract.md`.
- Guide fix (planner ruling, 2026-10-06): plate and glyph are separate keys on 16x16 canvases; the glyph's live area is 12x12 with a 2 px margin; the plate fills 16x16.

## Out of Scope
- Art, palette, frontend wiring. Keys for the rest of the icons (next batch).

## Acceptance Criteria
- [ ] `verify` (or the registry loader) accepts the file; key count guards re-pinned to the new exact count.
- [ ] Every new key states size and fallback; none declares a variant axis.

## Related Tickets
- TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET (epic), TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION (D20)

## Related Docs
- docs/assets/store_contract.md, docs/assets/fallback_safety.md, ADR D17/D19

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES/ (plan, investigation, test_plan, mutant_proof.txt)

## Related Code Areas
- visual_assets/catalog/definitions/visual_keys.yaml, tests/visual_assets/ (adopted_facts.py and key-count guards)

## Assumptions / Open Questions
- Corrected: "nothing is assembled here" was wrong (see Scope). `release` assembles every adopted slot, so no forest-only rc exists on the new registry; the pilot fixture guard was re-pointed by the planner's ruling (forest slots of a fresh rc-0006 export, plus equality with rc-0004's stored candidate).
- Whether the draft tooling and preview accept non-16 sizes (24, 8) is unverified; `MAX_DIM` is 128. If anything assumes 16x16, report it to the planner rather than working around it.

## Implementation Notes
- 14 `icon.*` keys, all `optional: true`, `variant_axes: []`, no detail axis; classes: plate decorative, glyph/building/class/tier/status identifying (the tier badge carries the grade by shape; its text letter stays). Names unchanged from the ticket.
- `pilot/rc-0006` assembled (34 entries equal to rc-0005's); terrainset fixture manifest re-exported (the 34 PNGs are byte-identical).
- Guards re-pointed by equality: key set (`test_registry.py`), `RELEASE_CANDIDATES`, release count 5 to 6, terrainset rc-0006 pin plus an "entries equal rc-0005's" test; pilot fixture: two checks (see test_pilot_fixture.py docstring). Nothing loosened.
- Style guide Map glyph row and layout paragraph fixed per the planner's ruling.
- Reported, not changed: `frontend/src/visualAssets/fallback.ts` has no typed glyph for family `icon` (wiring batch).

## Test Summary
- `pytest tests/visual_assets tests/docs tests/static`: 1683 passed, 2 skipped, 1 xfailed. `vitest run src/visualAssets`: 230 passed. `store verify`: ok. `pilot_colour_vision` runs.
- Mutant proof: a flipped forest PNG byte, a dropped slot and an unmoved registry each fail the new pilot guard for the stated reason (`mutant_proof.txt`).

## Files Changed
- visual_assets/catalog/definitions/visual_keys.yaml, manifests/candidates/pilot/rc-0006.json, frontend terrainset fixture manifest, tests/visual_assets (test_registry, test_pilot_fixture, test_terrainset_fixture, adopted_facts, test_catalog_integrity, test_store_tools_stdio), docs/assets (icon_style_guide, pilot_terrain_key, store_contract), ticket and stored artifacts.

## Completion Summary
14 icon keys registered with size, class and fallback each; rc-0006 assembled with the user's approval; every pinned guard re-pointed by equality.
