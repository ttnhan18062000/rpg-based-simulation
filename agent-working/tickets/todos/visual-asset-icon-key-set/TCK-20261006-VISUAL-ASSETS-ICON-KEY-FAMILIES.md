---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES
phase: open
date: 2026-10-06
tags: [architecture, hud, testing]
---

# TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES

## Title
Register the icon key set's visual keys, each with a stated fallback

## Status
OPEN

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
- Docs: `store_contract.md` (the `icon.*` family), `registry_hash` change noted (matters only for a new release
  candidate, none assembled here). Re-point any guard that pins the key count, by equality.

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


## Related Code Areas
- visual_assets/catalog/definitions/visual_keys.yaml, tests/visual_assets/ (adopted_facts.py and key-count guards)

## Assumptions / Open Questions
- Whether the draft tooling and preview accept non-16 sizes (24, 8) is unverified; `MAX_DIM` is 128. If anything assumes 16x16, report it to the planner rather than working around it.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

