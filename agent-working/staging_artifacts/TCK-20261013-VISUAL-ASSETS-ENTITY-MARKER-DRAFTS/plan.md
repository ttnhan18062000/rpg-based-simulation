---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS
artifact_type: plan
tags: [architecture, testing, mcp]
---

# Plan

## Constraint until the owner names the key family
No registry edit, no key names in any committed file, no change to `tools/visual_assets_sample_map.py`. Specs, sheets and filenames are keyed by `kind` only. A literal placeholder is never committed.

## Precedent
The 2026-10-13 batch-A decision: the owner answered the key-set question in `TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN` and no D-record was written. The family answer here follows that route.

## Byte budget (arithmetic)
- Registry now: 42,024 B (`visual_assets/catalog/definitions/visual_keys.yaml`), 83 keys plus 8 aliases; bound `MAX_REGISTRY_BYTES` = 458,752 B.
- Average per key today: 42,024 / 83 = 506 B (the budgets row's own ~450 B per real icon key is lower; 506 B is the conservative figure, a label entry included).
- 11 keys x 506 B = 5,566 B -> about 47,590 B = 10.4 % of the bound (11 keys x 450 B = 4,950 B -> 46,974 B, 10.2 %). It fits with more than 89 % headroom; no bound raise, no owner budget question.
- Key count: 83 + 11 = 94 of `MAX_VISUAL_KEYS` 1024 (`visual_assets/store/config.py:83`); the headroom is ample. (An earlier draft said 4096: wrong, corrected after asset-planner's review.)
- Runtime manifest and evidence crops: the manifest is 27,268 B at rc-0011 and grows by about one entry per key. The committed evidence crops (120,273 B of 262,144 B) are only re-rendered in the later rc batch; this batch re-renders none.

## Guarded files
Nothing under `visual_assets/store`, `drawing` or the build config changes. The registry (`visual_assets/catalog/definitions/`), `icon_specs.yaml`, tests that are not marked guarded, `tools/visual_assets_sample_map.py` and docs are outside the guarded set. If any guarded file comes into scope: STOP and tell asset-planner (that means a proof refresh).

## Phases
1. Now (no art, no key names): this plan, `investigation.md`, `test_plan.md`. Review by asset-planner.
2. Specs and reference study per kind (theme D21; reads as / must not read as, class-icon and place-glyph collisions, distractors). The committed form waits for the family name; until then they live here.
3. Silhouette sheet for the owner: large labelled PNG canvases plus README in `~/Work/asset-review/entity-markers-silhouettes/`. Content, per asset-planner's review:
   - Treatment comparison for worker, guard and sentinel: (a) a bare object emblem, (b) the same emblem on a shared round unit token (a disc base, which also matches today's coloured-circle fallback), (c) a figure silhouette. The other 8 kinds show their A/B candidates in treatment (b), labelled as a preview of that treatment.
   - Every row shows the candidate on a 16 px cell beside the nearest existing glyph from the collision map, side by side at 1:1 and at x8, so the collision risk is visible.
   - The treatment is an owner question for the whole set, not decided here (see below). Asks asset-planner for an art slot first (one run, foreground, `systemd-run --user --scope -q -p MemoryMax=3G`).
4. After the owner approves silhouettes and the family name arrives: registry keys (label, `safety_class`, `fallback` = today's coloured circle), `icon_specs.yaml` entries, drawing with the MCP tools (intake by the store CLI from this worktree, then `draft keep`), compliance table, blind naming check by two fresh agents.
5. Sample-map tool: entity kinds map to the new family instead of the class icons (my ownership, after the family answer).
6. Owner review folder `~/Work/asset-review/entity-markers-v1/` and owner `adopt-set` (neutral options, filled commands, via asset-planner and lead). No push; push and PR go through lead.

## Owner question at the silhouette gate (not decided in this plan)
Which treatment for all 11 markers on a map cell? Neutral fixed-order options: (a) a bare object emblem; (b) the emblem on a shared round unit token; (c) a figure silhouette. Asked through asset-planner and lead after the sheet exists, with no recommendation. Reason it is open: on a map cell a bare object (a spade, a scale) can read as a dropped item or a resource node, not as a unit; the class icons are objects but are 24 px panel icons, not map glyphs.

## Scope guard
No `src/` or `frontend/` change; no item icons; no species/size markers; no animation; no bound raise.
