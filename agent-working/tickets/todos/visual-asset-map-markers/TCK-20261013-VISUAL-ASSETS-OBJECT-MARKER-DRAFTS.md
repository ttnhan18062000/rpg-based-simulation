---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS
phase: open
date: 2026-10-13
tags: [architecture, testing, mcp]
---

# TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS

## Title
Map markers: object markers for buildings, places and resource nodes (keys, specs, silhouettes, drafts, owner adopt-set)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`. Lead: art-only drafting that does not depend on rpg's final kind list may start once filed. Building, place and resource-node kinds come from the authored world data (`spec.buildings`, `PlaceKind`, resource node kinds) and are already V2 names, so this child does not wait for #523. Needs child 1's approved design and the owner's answers.

## Scope
- Add the approved object keys and aliases to `visual_keys.yaml` (labels, `safety_class`, `fallback`). Registry edit -> rc-0010 becomes unexportable (Known gap). Expected red until child 4: list exactly which tests, nothing else may fail.
- **Specs before drawing** (style guide process rule): one `icon_specs.yaml` entry per new key (theme, orientation, proportions in px, parts, reads as, must not read as, synonyms, distractors, modern lookalikes to avoid). The `--table` in the style guide is regenerated.
- **Reference study:** for each subject, note what makes it read as itself at 16 px (healer's hut vs inn, watchtower vs town hall, iron vs silver vein, a cover patch vs a herb patch).
- **Owner-only step 1 (blocking, neutral fixed-order options):** the silhouette sheet. One-colour silhouettes of the whole set at 1x and 4x in a review folder, `~/Work/asset-review/object-markers-silhouettes/`. Draw nothing shaded before the owner approves.
- Draw with the `aseprite-pixel-art` MCP tools (the first `new_sprite` confirms the server pin; if it refuses, STOP and tell asset-planner). Follow `pixel_art_technique.md`, the icon palette and the sheet rule. Lint clean or justified. Intake PASS for each. Compliance table against each spec.
- **Recognisability checks:** the blind naming check with distractors (theme/era pass included). An icon that misreads gets redrawn before the owner gate, not explained.
- **Owner review folder:** `~/Work/asset-review/object-markers-v1/`. Large labelled PNG canvases: each marker at 1x, 4x and on a 16 px map cell over grassland, plus the sample-map crops with the markers drawn (sample-map renderer, offline), and a README. Not the Vite page.
- **Owner-only step 2:** the owner reviews the WHOLE set and runs `adopt-set`. Redraws on request.

## Out of Scope
- No `src/` or `frontend/` change, no activation. The live client draws none of this (#519). The client-side kind -> key resolution belongs to rpg (#523: option (a) build-time registry read, or (b) an asset alias export with its own owner D-record).
- No item icons: `grass_cover`/`raw_meat` are a later item-icon ticket (#543 decision).
- No multi-tile structures (G7), connecting tiles (G5) or chests (G11, no data). No new terrain.
- No bound raise, and no store or drawing-tool code change unless child 1 proves one is needed. If it does, STOP: that is its own owner question.
- No animation. `TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY` stays in the backlog unless a marker is animated.

## Acceptance Criteria
- [ ] Keys and aliases in the registry per the approved design; the red set listed exactly.
- [ ] Specs, reference notes, owner-approved silhouettes, compliance table, blind check results recorded.
- [ ] The owner adopted the object set with `adopt-set`.

## Related Tickets
- Parent: `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`; needs `TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN`
- Precedents: `TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS`, `TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET`, `TCK-20261008-VISUAL-ASSETS-ICON-V2-RECOGNISABILITY-REDRAW`

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G6, G8, G9, G10, G11; "Input list for candidate A"), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, the 2026-10-12 re-measurement, ~450 B per real icon key), `docs/assets/store_contract.md` (registry-only aliases Known gap; a registry edit makes older candidates unexportable), `docs/assets/icon_style_guide.md` (family conventions, per-icon specs, the recognisability process rule), `docs/assets/fallback_safety.md` (`safety_class`, `fallback`), `docs/assets/icon_criteria.md`
- GitHub #523 (owner: V2 names canonical; markers follow V2 kind names as the presenter emits them), #519 (rpg's kinds and counts), #543 (cover_patch nodes in A)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN/` (the last budget review), `agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS/` (if present)

## Related Code Areas
- `visual_assets/catalog/definitions/visual_keys.yaml`, `visual_assets/icons/icon_specs.yaml`, `docs/assets/icon_style_guide.md` (generated table), `tools/visual_assets_sample_map_render.py`, `tests/visual_assets/**`

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

