---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS
phase: open
date: 2026-10-13
tags: [architecture, testing, mcp]
---

# TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS

## Title
Map markers: entity markers on V2 entity names or properties (gated on rpg's #523 and its M1 answer)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`. The owner's #523 answer: markers follow V2 kind names as the presenter emits them. rpg (#519): M1 moves kinds to properties (diet, size), so markers keyed on properties would outlast role markers; hero retires in M1 (D63). The sample worlds hold 11 entity kinds today, including `wild_creature`, which arrived in #536.

## Scope
- **Preconditions (do not start before both):** (1) rpg's #523 is merged; (2) rpg-planner has answered #548 which entity names or properties the presenter will emit after M1, and whether they are stable enough to key art on. If either is missing when child 2's set is adopted, STOP: asset-planner takes the "objects only, entities in their own batch" question to the owner.
- **Owner-only step 1 (blocking, neutral fixed-order options):** role markers or property markers, from child 1's option table with rpg's answer.
- Keys per the decision and child 1's design (labels, `safety_class`, `fallback` = today's coloured circle), with the red set listed exactly.
- Specs, reference study, **owner-approved silhouette sheet** (`~/Work/asset-review/entity-markers-silhouettes/`), drawing with the MCP tools, compliance table, blind naming check: the same process rule as child 2. A marker must read on a 16 px cell next to the object markers and must not be confused with a class icon or a place glyph.
- **Owner review folder** `~/Work/asset-review/entity-markers-v1/` and **owner `adopt-set`** of the whole set.

## Out of Scope
- No `src/` or `frontend/` change, no activation. The live client draws none of this (#519). The client-side kind -> key resolution belongs to rpg (#523: option (a) build-time registry read, or (b) an asset alias export with its own owner D-record).
- No item icons: `grass_cover`/`raw_meat` are a later item-icon ticket (#543 decision).
- No multi-tile structures (G7), connecting tiles (G5) or chests (G11, no data). No new terrain.
- No bound raise, and no store or drawing-tool code change unless child 1 proves one is needed. If it does, STOP: that is its own owner question.
- No animation. `TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY` stays in the backlog unless a marker is animated.

## Acceptance Criteria
- [ ] Both preconditions met and recorded (the #523 merge sha; rpg's answer, linked).
- [ ] The owner chose role or property markers; keys in the registry; the red set listed exactly.
- [ ] Specs, owner-approved silhouettes, compliance table, blind check; the owner adopted the set with `adopt-set`.

## Related Tickets
- Parent: `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`; needs `TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN`; runs after or alongside `TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS`
- GitHub #523 (precondition), #519

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G6, G8, G9, G10, G11; "Input list for candidate A"), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, the 2026-10-12 re-measurement, ~450 B per real icon key), `docs/assets/store_contract.md` (registry-only aliases Known gap; a registry edit makes older candidates unexportable), `docs/assets/icon_style_guide.md` (family conventions, per-icon specs, the recognisability process rule), `docs/assets/fallback_safety.md` (`safety_class`, `fallback`), `docs/assets/icon_criteria.md`
- GitHub #523 (owner: V2 names canonical; markers follow V2 kind names as the presenter emits them), #519 (rpg's kinds and counts), #543 (cover_patch nodes in A)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN/` (the last budget review), `agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS/` (if present)

## Related Code Areas
- `visual_assets/catalog/definitions/visual_keys.yaml`, `visual_assets/icons/icon_specs.yaml`, `tests/visual_assets/**`; `src/api/presenters/state_presenter.py:69` (read only: the emitted entity `kind`)

## Assumptions / Open Questions
- rpg-planner's answer on post-M1 entity names or properties is outstanding: GitHub #548 (filed 2026-10-13).

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

