---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS
phase: open
date: 2026-10-07
tags: [architecture, hud, documentation]
---

# TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS

## Title
Icon v2 family decisions: item-family mapping from content categories, the rarity badge ladder and glyph choices, user-approved before any key or art

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 1 of `TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2`. User decisions (blocking questions, 2026-10-07, after PR #388 merged): the next icon batch is **draw only, no
wiring**: using adopted art in the live app is gated (AM-M6 is NO-GO until the owner signs its charter, and AM-M6
covers one forest tile only; HUD icons are broad rollout, beyond it). Families: **map locations (5), buildings +
classes (8), rarity badges (3), item families (~8)**.
Items have no `item_type` field: the API derives it from each item's first `categories` tag
(`src/api/presenters/metadata_presenter.py`), about 15 distinct values (material 19, weapon 10, mineral 4, organic 3,
animal 3, trinket, tool, elemental, consumable, armor 2 each, trophy, spiritual, rare, metal, dark 1 each; a planner
count over content files, re-measure from the catalog). An icon per tag would be noise; families must be decided.

## Scope
- **Item families:** measure the distinct first categories from the loaded content catalog (the same derivation the
  presenter uses, read-only). Propose 6-8 families (the brainstorm's contours: weapon, armour, tool, consumable,
  material, trinket, organic trophy, crystal/essence) and a total mapping from every first category to one family, with
  counts. Ask the user by blocking question (neutral options; the mapping table in the question). Write the approved
  mapping as data (e.g. `visual_assets/catalog/definitions/icon_item_families.yaml`) with a test that every item in
  the catalog maps to exactly one family (a new category fails the test, it never falls through silently).
- **Rarity badges (common, uncommon, rare):** 8x8, shape-escalating, visually distinct from the tier badges
  (different base shape), letter or name stays as text. Propose; user confirms in the same question.
- **Glyph choices** for the 5 locations, 5 buildings, 3 classes (one line each, e.g. shrine = obelisk). Propose; the
  user may change any.
- Record answers in `docs/assets/icon_style_guide.md` (a dated v2 section) and the ticket.

## Out of Scope
- Keys, art, rule changes (later children). Changing item content or the presenter.

## Acceptance Criteria
- [ ] Mapping, rarity ladder and glyph list recorded with the user's answer and date.
- [ ] Mapping data committed with a test over the real catalog; a planted unknown category fails it.

## Related Tickets
- TCK-20261007-EPIC-VISUAL-ASSET-ICON-SET-V2 (epic)

## Related Docs
- docs/brainstorm/render-and-art/visual-system-planning.md (section 11 item structure, 15 iconography)

## Related Stored Artifacts


## Related Code Areas
- src/api/presenters/metadata_presenter.py (read only), content item definitions (read only)

## Assumptions / Open Questions
- Whether item families appear anywhere in today's UI beyond the `item_type` text in LootPanel: say so in the question; the user chose them knowing wiring is out of scope.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

