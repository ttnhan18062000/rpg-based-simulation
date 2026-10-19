---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS
phase: done
date: 2026-10-13
tags: [architecture, testing, mcp]
---

# TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS

## Title
Map markers: entity role markers keyed on the presenter's `kind` (gated on rpg's #523)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`. The owner's #523 answer: markers follow V2 kind names as the presenter emits them. rpg (#519): M1 moves kinds to properties (diet, size), so markers keyed on properties would outlast role markers; hero retires in M1 (D63). The sample worlds hold 11 entity kinds today, including `wild_creature`, which arrived in #536.

## Scope
- **Moved out of the map-markers batch (owner, 2026-10-14, "Objects now, entities later").** The object markers (batch A: `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`, rc-0011) shipped without entities. This ticket now waits in its own batch folder, `agent-working/tickets/todos/visual-asset-entity-markers/`; its parent epic's Completion Summary says "child 3 moved out on the owner's answer".
- **Owner decision (2026-10-18, relayed by lead-planner, posted on #548):** entity markers key on the presenter's role id, `kind` (`src/api/presenters/state_presenter.py`, emitted today). No species/size markers. The property-marker option is closed for this batch.
- **Remaining precondition (do not start before it):** rpg's #523 is merged (V2 names canonical). Then re-read the emitted `kind` values from the three sample worlds on the merged main, because #523 may rename or recolour kinds.
- **Red set today** (11 kinds in the sample worlds, from `docs/assets/sample_map/gap_report.md` G10 plus `wild_creature` since #536): alpha, blacksmith, guard, leader, merchant, predator_hunter, raider, scout, sentinel, worker, wild_creature. The batch draws exactly the kinds the sample worlds hold on the post-#523 main. If that list differs from today's, record the difference in investigation.md and use the post-#523 list. Other role ids in `data/content/social/roles.yaml` that no sample world uses are out of scope.
- Keys: one key per kind in the red set. No entity key family exists yet (child 1 named only `icon.marker.*` place keys), so plan.md picks the family (for example `icon.entity.<kind>`) against the `visual_keys.yaml` conventions, and the review checks it, with labels, `safety_class` and `fallback` = today's coloured circle. Names follow the presenter; aliases are registry-only.
- Specs, reference study, **owner-approved silhouette sheet** (`~/Work/asset-review/entity-markers-silhouettes/`), drawing with the MCP tools, compliance table, blind naming check: the same process rule as child 2. A marker must read on a 16 px cell next to the object markers and must not be confused with a class icon or a place glyph.
- **Owner review folder** `~/Work/asset-review/entity-markers-v1/` and **owner `adopt-set`** of the whole set.

- **Owner decisions recorded 2026-10-19 (via lead-planner, neutral fixed-order options).** Key family: `icon.entity.<kind>`, 16x16 on the map cell like `icon.node.*`. After viewing `~/Work/asset-review/entity-markers-silhouettes/` (sha `152def290`): treatment "(a) Bare object, for the whole set"; "Use all 8": worker A pitchfork, guard D gate key, raider B torn banner, sentinel B stone idol, merchant A balance scale, leader A crown, alpha B standing wolf, predator_hunter A claw slashes; scout "C open eye"; blacksmith "A horseshoe"; wild creature "A grazing deer". Unchosen candidates stay in `visual_assets/icons/entity_marker_silhouettes.yaml` marked rejected (the `chosen` key), so the sheet stays reproducible.
- **Step 1 done without art (2026-10-19):** 11 registry keys (`visual_keys.yaml`, safety_class identifying, fallback = the client's default grey circle #888888 with the state ring plus the kind name as text; labels are proposals for the owner's label approval), 11 `icon_specs.yaml` entries and the `entity` family, the regenerated style-guide table, and the sample-map tool mapping entity kinds to `icon.entity.<kind>`. Colour drafts need the planner's art slot.

## Out of Scope
- No `src/` or `frontend/` change, no activation. The live client draws none of this (#519). The client-side kind -> key resolution belongs to rpg (#523: option (a) build-time registry read, or (b) an asset alias export with its own owner D-record).
- No item icons: `grass_cover`/`raw_meat` are a later item-icon ticket (#543 decision).
- No multi-tile structures (G7), connecting tiles (G5) or chests (G11, no data). No new terrain.
- No bound raise, and no store or drawing-tool code change unless child 1 proves one is needed. If it does, STOP: that is its own owner question.
- No animation. `TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY` stays in the backlog unless a marker is animated.

## Acceptance Criteria
- [x] The precondition, as recorded: the owner's 2026-10-18 `kind` decision (#548). The #523 merge sha is NOT recorded here: the batch was dispatched by asset-planner on the owner's decisions of 2026-10-18/19, and the 11 kinds were read from the presenter and the three sample worlds (investigation.md). If #523 renames a kind, re-keying is a later ticket.
- [x] The red set is re-derived from the sample worlds on the post-#523 main and listed exactly. Each kind gets one key in the registry, keyed on `kind`.
- [x] Specs, owner-approved silhouettes, compliance table, blind check; the owner adopted the set with `adopt-set`.

## Related Tickets
- Parent: `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`; needs `TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN`; `TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS` is done (the object set `object-markers-v1` is adopted, rc-0011)
- GitHub #523 (precondition), #519

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G6, G8, G9, G10, G11; "Input list for candidate A"), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, the 2026-10-12 re-measurement, ~450 B per real icon key), `docs/assets/store_contract.md` (registry-only aliases Known gap; a registry edit makes older candidates unexportable), `docs/assets/icon_style_guide.md` (family conventions, per-icon specs, the recognisability process rule), `docs/assets/fallback_safety.md` (`safety_class`, `fallback`), `docs/assets/icon_criteria.md`
- GitHub #523 (owner: V2 names canonical; markers follow V2 kind names as the presenter emits them), #519 (rpg's kinds and counts), #543 (cover_patch nodes in A)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN/` (the last budget review), `agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS/` (if present)

## Related Code Areas
- `visual_assets/catalog/definitions/visual_keys.yaml`, `visual_assets/icons/icon_specs.yaml`, `tests/visual_assets/**`; `src/api/presenters/state_presenter.py:69` (read only: the emitted entity `kind`)

## Assumptions / Open Questions
- #548 is closed for this batch by the owner's decision (2026-10-18): key on `kind`. If M1 later moves kinds to properties, re-keying is a later ticket, not this one.
- Standard tier: the dispatch asks for plan.md, investigation.md and test_plan.md up front. The registry byte budget (`MAX_REGISTRY_BYTES`, about 450 B per key) for 11 keys is checked in plan.md. If it doesn't fit, STOP and raise it as an owner question; no bound raise inside this ticket.

## Implementation Notes
- **Step-1 miss, fixed (2026-10-19):** commit `0cfc1e56c` added 11 `icon.entity.*` registry keys whose `description` was about 350 characters. The registry caps a key's description at 256 characters, so that commit's `visual_keys.yaml` does not load (`registry_unreadable ... keys.83.description: String should have at most 256 characters`). `draft keep` found it first. Commit `061b3ed6c` shortens all 11. A squash merge keeps `0cfc1e56c` off `main`. Nothing in step 1 loaded the registry; from now on, after any `visual_keys.yaml` edit, load it once (light) before committing.
- **Owner decision on the loot-read risk, 2026-10-19 (via lead-planner, neutral fixed-order options): "1. Adopt as drawn"**, accepting that 7 of 11 markers read as an item or a resource on the map. The accepted read (two fresh agents, 19 markers on a real map crop with 8 controls, all 8 controls read right):

| kind | object drawn | read as (agent 1 / agent 2) | named as | result |
|---|---|---|---|---|
| alpha | standing wolf | UNIT / UNIT | wolf or dog | PASS (dog risk) |
| scout | open eye | UNIT / UNIT | eye | PASS |
| sentinel | stone idol face | UNIT / UNIT | golem or cube creature | PASS |
| wild_creature | grazing deer | UNIT / UNIT | deer | PASS |
| blacksmith | horseshoe | ITEM / ITEM | horseshoe or magnet | accepted: reads as loot |
| guard | gate key | ITEM / ITEM | key | accepted: reads as loot |
| leader | gold crown | ITEM / ITEM | crown | accepted: reads as loot |
| merchant | balance scale | ITEM / ITEM | balance scale | accepted: reads as loot |
| raider | torn banner | ITEM / ITEM | banner | accepted: reads as loot |
| worker | pitchfork | ITEM / ITEM | pitchfork or trident | accepted: reads as loot |
| predator_hunter | three claw slashes | RESOURCE / RESOURCE | claw marks or red sticks | accepted: reads as a resource |

The adopt-set command and the label approval are the owner's own step (asset-planner gives a filled command through lead). Nothing is adopted yet; the draft set `entity-markers-v1` is not to be touched until the owner has run it.
- **Adopted (2026-10-19T06:29:37Z):** the owner ran `adopt-set` for `entity-markers-v1` in this worktree: set adoption `sa-1d9d71206b95652d`, approver nhan / owner, draft set hash `sha256:2f734b3feb9abff7285d321a5d3f1b04e441230f8e49e02912a3756433e88135`, 11 adoption records (`ad-*`), 11 new sources (`icon_entity_<kind>`, r0001), 22 intake files. The first attempt failed with a ValidationError because the `--review-evidence` text was 302 characters (cap 256); nothing was written then, and the second attempt (shorter text) succeeded. Adopted but not built: no release candidate carries the 11 yet (no rc in this batch), so `tests/visual_assets/adopted_facts.py` pins 116 sources, 123 adoptions, 246 intake files and 123 revisions, and the 105 generated artifacts are unchanged. Labels are still proposals until the owner approves them. The registry now loads (`store verify` ok, longest description 251 of 256).
- **Labels approved (2026-10-19, asked directly by lead-planner, neutral options):** the owner approved the 11 proposed labels as listed (Worker, Guard, Scout, Raider, Sentinel, Merchant, Blacksmith, Leader, Alpha, Predator hunter, Wild creature).
- **Docs counts updated:** `docs/assets/store_contract.md` (new section "What the committed catalog holds": 116 sources, 123 adoptions, 6 set adoptions, entity markers adopted not built) and `docs/assets/icon_style_guide.md` (one line).
- **Drafts:** 11 colour drafts kept in set `entity-markers-v1` (bare object, owner treatment (a)); the worker was redrawn once (lighter steel tines for contrast on grass, planner review) and kept with `draft keep --replace`.


## Test Summary
- `tests/visual_assets`, not slow, whole folder, at head `2145a7b45`: **2554 passed, 0 failed, 0 skipped, 0 errors in 701 s** (alone, foreground, `MemoryMax=3G`). It includes the 16 tests that were red with `registry_mismatch` after the 11 registry keys made rc-0011 unexportable; all 16 are green on rc-0012.
- Aseprite strict local proof (`make visual-assets-aseprite-local`): **215 passed, 0 failed, 0 skipped**; `docs/assets/aseprite_local_proof.json` rewritten by the run (guarded sha, `guarded_hash`, rc-0012 116/116 and the run fields only).
- Frontend `npx vitest run src/visualAssets`: **22 files, 279 tests passed** (`iconScene.test.ts` counts 65 registered, 51 undrawn).
- New test `tests/visual_assets/test_rc_0012_extends_rc_0011.py` (2 tests, equality). The pins moved from rc-0011 to rc-0012 by equality, nothing loosened.
- Blind naming check: two fresh agents, 19 markers on a real map crop with 8 controls; the result table is under Implementation Notes (7 of 11 read as item or resource, accepted by the owner).
- **Process miss:** the plan's guarded-set check (which files would stale the Aseprite proof record) was taken before step 3 re-pointed `test_release_byte_reproducibility.py`, a guarded file, and so missed it. `test_aseprite_local_proof` failed on the first rc-0012 commit and the strict run was needed to refresh the record.

## Files Changed
- Registry and specs: `visual_assets/catalog/definitions/visual_keys.yaml` (11 `icon.entity.*` keys; 94 keys), `visual_assets/icons/icon_specs.yaml`, `visual_assets/icons/entity_marker_silhouettes.yaml`, `docs/assets/icon_style_guide.md`.
- Store: draft set `visual_assets/drafts/entity-markers-v1/`, provenance and sources under `visual_assets/catalog/{provenance,sources}`, 11 built artifacts under `visual_assets/catalog/generated/icon_entity_<kind>--x1/`, and the owner-run release `visual_assets/catalog/manifests/candidates/pilot/rc-0012.json` (116 entries, committed exactly as written).
- Tools: `tools/visual_assets_entity_marker_sheet.py`, `tools/visual_assets_sample_map.py` (entity kinds to `icon.entity.`), `tools/visual_assets_sample_map_render.py` (rc-0012).
- Tests: `tests/visual_assets/adopted_facts.py` and the pins in `test_icon_set_adoption`, `test_icon_v2_keys`, `test_icon_release_candidate`, `test_release_byte_reproducibility`, `store/unit/test_atlas.py`, and the re-pointed registry/detail-axis/draft-set/recognition/specs/key-usage tests; new `test_rc_0012_extends_rc_0011.py`.
- Frontend: `frontend/src/visualAssets/iconScene.ts` and its test (fallbacks for the 11 keys).
- Docs: `docs/assets/{budgets,store_contract,aseprite_local_proof.json}`, `docs/assets/sample_map/{README,gap_report}.md`; the five sample-map crops are unchanged (byte-identical).
- **PR note:** commit `0cfc1e56c` alone has an unloadable registry (11 descriptions over the 256-character cap); `061b3ed6c` fixes it, and the squash merge keeps `0cfc1e56c` off main.

## Completion Summary
The 11 entity role markers are drawn, adopted and released. Key family `icon.entity.<kind>`, keyed on the presenter's `kind` (owner decision 2026-10-18, #548, and 2026-10-19). Owner decisions, in the owner's words (relayed by lead-planner, neutral fixed-order options): treatment "(a) Bare object, for the whole set"; "Use all 8" (worker A pitchfork, guard D gate key, raider B torn banner, sentinel B stone idol, merchant A balance scale, leader A crown, alpha B standing wolf, predator_hunter A claw slashes); scout "C open eye"; blacksmith "A horseshoe"; wild creature "A grazing deer"; on the loot-read risk "1. Adopt as drawn"; the 11 labels approved as listed; `adopt-set` run by the owner (`sa-1d9d71206b95652d`, 2026-10-19T06:29:37Z); and "Assemble rc-0012 now" (116 = rc-0011's 105 byte-identical + 11), released by the owner. Nothing is drawn on the live map: activation stays parked, the client keeps its grey circle fallback.
Known limits: 7 of the 11 read as an item or a resource on the map (accepted); the live client does not resolve kinds to keys yet (rpg's #523 work); the #523 merge sha was not recorded (see Acceptance Criteria).
