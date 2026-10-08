---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS
phase: done
date: 2026-10-07
tags: [architecture, hud, documentation]
---

# TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS

## Title
Icon v2 family decisions: item-family mapping from content categories, the rarity badge ladder and glyph choices, user-approved before any key or art

## Status
DONE

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
count over content files, re-measure from the catalog) [**CORRECTED 2026-10-07 by the planner after re-measurement: that count was a raw grep over tags in every position, not the presenter's first-tag derivation. The real catalog has 37 items and SIX first categories: material 19, weapon 10, trinket 2, armor 2, tool 2, consumable 2.**]. An icon per tag would be noise; families must be decided.

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
- agent-working/stored_artifacts/TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS/ (plan, investigation, test_plan, mutant_proof.txt)

## Related Code Areas
- src/api/presenters/metadata_presenter.py (read only), content item definitions (read only)

## Assumptions / Open Questions
- Whether item families appear anywhere in today's UI beyond the `item_type` text in LootPanel: said so in the question. `item_type` is text only in LootPanel, InspectPanel and BuildingPanel (which filters on 'material'); nothing uses it as an icon. The user chose knowing wiring is out of scope.
- Re-check against what landed (told to the planner before asking): the catalog has 6 first categories (not ~15) and 4 rarity values (common, uncommon, rare, legendary), while the app's RARITY_COLORS has 3.

## Implementation Notes
- **User answers (blocking question, 2026-10-07, neutral options, real numbers):** item families = **6, one per category** (weapon, armor, trinket, tool, consumable, material) over an 8-family split of `material`; rarity badges = **3** (common, uncommon, rare; the one legendary item, `ancient_core`, gets none); glyphs and rarity shapes **accepted as proposed** (locations: tree, broken column, arched door, obelisk, skull; buildings: coin purse, banner, mug, small house, open book; classes: bow, pointed hat, dagger; badges: round bead, kite gem, four-point sparkle gem).
- **Honest note on the question:** the planner's two extra framing points (state that "~8 families" came from the wrong ~15 count, and a documented second-tag precedence if 8) reached me after the user had answered. They were moot once the user chose six one-to-one, so no split rule was written. The question did show the real six categories and counts.
- **Mapping as data:** `visual_assets/icons/item_families.yaml` (first category to family; a first category not listed is not defaulted). It cannot live in `visual_assets/catalog/definitions/`: `store verify` allows only its own definition files there (found by running verify; `UNEXPECTED_FILE`). Helper `tests/visual_assets/icon_item_families.py` (`family_of`, strict: no categories or an unknown first category raises `UnmappedCategory`), guard `tests/visual_assets/test_icon_item_families.py` over the REAL catalog loaded with `CatalogRepository("data/content")` (tests may import `src`; only the `visual_assets/` package may not).
- **Mutants (mutant_proof.txt):** dropping `tool`, adding an unused `gemstone`, and merging armor into weapon each fail for the stated reason; a planted unknown category and a planted catalog item both fail the check.
- **Record:** a dated v2 section in `docs/assets/icon_style_guide.md` (decisions, the corrected count, the family table, the glyph table, building types follow the UI's six types not the catalog's building definitions).

## Test Summary
- `pytest tests/visual_assets`: 1608 passed (6 new). `store verify` ok.
- Mutants caught (see Implementation Notes).

## Files Changed
- visual_assets/icons/item_families.yaml, tests/visual_assets/{icon_item_families,test_icon_item_families}.py, docs/assets/icon_style_guide.md, ticket and stored artifacts.

## Completion Summary
Item families (6), rarity badges (3) and glyph list recorded with the user's answers of 2026-10-07; the mapping is committed data with a guard over the real catalog.
