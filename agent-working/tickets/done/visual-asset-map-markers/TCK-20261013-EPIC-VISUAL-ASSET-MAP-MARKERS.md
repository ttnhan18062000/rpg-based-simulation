---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS
phase: done
date: 2026-10-13
tags: [architecture, planning, live-map]
---

# TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS

## Title
Visual asset map markers: buildings, places, resource nodes and entities on the map, keyed on V2 kind names

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Candidate A from the sample-map gap report: markers for the things a world places on the map. Dispatched by lead-planner under the owner's 2026-10-11 grant (2026-10-13): "start batch A scoping now; nothing blocks it". Order: start with the `MAX_REGISTRY_BYTES` budget review, use V2 kind names (owner answer on #523, 2026-10-12: "Entity and place markers (asset batch A) follow V2's kind names as the presenter emits them"), include the `cover_patch` nodes (#543), and name rpg's #523 as the implementation precondition. Art-only drafting that doesn't depend on rpg's final kind list may go to asset-implementer once filed.

What the three sample worlds hold on main 06aa3a20c (`python -m tools.visual_assets_sample_map data --all`):
- buildings: shop 3, inn 3, blacksmith 2, healer_hut 2, town_hall 1, mine_entrance 1, watchtower 1 (no icon: healer_hut, town_hall, mine_entrance, watchtower; `shop` only through `icon.building.store`, unconfirmed). G6.
- resource nodes: cover_patch_high 20 (new in #536), herb_patch 3, iron_vein 3, wood_node 2, berry_thicket 2, crystal_outcrop 1, silver_vein 1, spirit_wisp 1, healing_flower_patch 1, frost_shard_cluster 1 (10 kinds, no key; `icon.marker.resource_grove` exists, nothing maps to it). G8.
- places: CITY 2, RUIN 2, CAMP 1, NEST 1 (no glyph: CITY, NEST; LAIR, DUNGEON, LANDMARK unused in the samples). G9.
- entities: 11 kinds, 85 entities: worker 16, predator_hunter 13, scout 14, sentinel 12, merchant 7, guard 8, wild_creature 6 (new in #536), raider 4, blacksmith 2, alpha 2, leader 1. `icon.class.*` holds warrior, ranger, mage, rogue only. rpg: M1 moves kinds to properties (diet, size), so markers keyed on properties would outlast role markers. G10.

## Scope
- Child 1 `TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN`: the `MAX_REGISTRY_BYTES` budget review for about 20-30 new keys, and the marker key design (names, families, sizes, safety class and fallback, aliases, the owner's options). **Planner gate before any registry edit.**
- Child 2 `TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS`: object markers (buildings, places, resource nodes). Keys in the registry, specs, silhouette sheet (owner), drafts, review folder, owner `adopt-set`. **Does not wait for #523:** these kind names come from the authored world data and are stable V2 names.
- Child 3 `TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS`: entity markers. **Preconditions: rpg's #523 is merged, and rpg-planner has answered which entity names or properties the presenter will emit after M1.** Then the owner chooses role or property markers. Keys, specs, silhouettes, drafts, `adopt-set`.
- Child 4 `TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE`: build, rc-0011 on the owner's answer, the sample-map renderer draws the markers, gap report and budgets updated, closure.
- If child 3's preconditions are not met when child 2's set is adopted, child 4 releases the object markers only and child 3 moves to its own batch. That is an owner question, asked at that point.

## Out of Scope
- No `src/` or `frontend/` change, no activation. The live client draws none of this (#519). The client-side kind -> key resolution belongs to rpg (#523: option (a) build-time registry read, or (b) an asset alias export with its own owner D-record).
- No item icons: `grass_cover`/`raw_meat` are a later item-icon ticket (#543 decision).
- No multi-tile structures (G7), connecting tiles (G5) or chests (G11, no data). No new terrain.
- No bound raise, and no store or drawing-tool code change unless child 1 proves one is needed. If it does, STOP: that is its own owner question.
- No animation. `TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY` stays in the backlog unless a marker is animated.

## Acceptance Criteria
- [ ] Children 1, 2 and 4 DONE (child 3 DONE, or moved out on the owner's answer), each commit reviewed and approved by `asset-planner`.
- [ ] Owner approved the key set and silhouettes, adopted each set with `adopt-set`, and approved rc-0011.
- [ ] The sample map draws the markers; the gap report's G6, G8, G9, G10 rows carry the new numbers.
- [ ] One PR, pushed and merged only on the user's own answer.

## Related Tickets
- Children: `TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN`, `TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS`, `TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS`, `TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE`
- Previous: `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS` (PR #545, rc-0010), `TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP` (PR #526)
- Next (not filed): item icons for `grass_cover`, `raw_meat` (#543)
- GitHub #523, #519, #543, #548 (entity vocabulary question to rpg-planner)

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G6, G8, G9, G10, G11; "Input list for candidate A"), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, the 2026-10-12 re-measurement, ~450 B per real icon key), `docs/assets/store_contract.md` (registry-only aliases Known gap; a registry edit makes older candidates unexportable), `docs/assets/icon_style_guide.md` (family conventions, per-icon specs, the recognisability process rule), `docs/assets/fallback_safety.md` (`safety_class`, `fallback`), `docs/assets/icon_criteria.md`
- GitHub #523 (owner: V2 names canonical; markers follow V2 kind names as the presenter emits them), #519 (rpg's kinds and counts), #543 (cover_patch nodes in A)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN/` (the last budget review), `agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS/` (if present)

## Related Code Areas
- `visual_assets/catalog/definitions/visual_keys.yaml`, `visual_assets/icons/icon_specs.yaml`, `visual_assets/catalog/**`, `visual_assets/store/**` (read), `tools/visual_assets_sample_map.py`, `tools/visual_assets_sample_map_render.py`, `tests/visual_assets/**`; `src/api/presenters/state_presenter.py`, `src/core/state.py` (`PlaceKind`), `src/worldbuilding/compiler.py` (read only, for the emitted kind names)

## Assumptions / Open Questions
- Planner decisions in `SEQUENCE.md`.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary
Children 1, 2, 4 and 5 (`TCK-20261014-VISUAL-ASSETS-REFUSE-PLACEHOLDER-APPROVALS`, filed during the batch) DONE; **child 3 moved out on the owner's answer** ("Objects now, entities later", 2026-10-14) to `agent-working/tickets/todos/visual-asset-entity-markers/`, status OPEN. 18 object markers adopted (set adoption `sa-6690e2619d4abb3e`), 5 registry-only aliases, rc-0011 (105 entries) assembled on the owner's answer, sample map draws all objects (0 gaps). The PR lands on the user's own answer.
