---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT
phase: done
date: 2026-09-02
tags: [content, determinism]
---

# TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT

## Title
Stage B pilot + remaining-19-world rollout to Region/Place

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 4/5 of `TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD`, depends on
`TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT`. Stage B is the first real mixed-content check:
`hero_guild_routing` (4 regions — City + `goblin_camp` wilderness + `ruins_mystery_quest` +
`mountain_pass`) proves the migration handles non-uniform region kinds. Once Stage B is verified by
direct inspection, this ticket also covers migrating the remaining 19 worlds — a staged hard cutover
(no true parallel-run is feasible; `WorldCompiler.compile()` is a single synchronous pass), sequential
world-by-world.

## Scope
- Migrate `hero_guild_routing` to Place-shaped content; compile and verify by direct inspection that all
  4 non-uniform region kinds produce the expected `Place.kind` values.
- Migrate all remaining worlds' content to Place-shaped form and recompile each.
- Recalibration/triage of `state_hash`/`grade_anchors.json` results is this ticket's sibling
  (`TCK-20260902-PLACE-MIGRATION-RECALIBRATION`) — do not fold triage work into this ticket; this ticket
  covers migration + compilation only.

## Out of Scope
- Full state_hash-diff triage and grade-shift analysis across all 21 worlds (separate recalibration
  ticket, sequenced to run alongside/after this one per-world).

## Acceptance Criteria
- [x] Stage B (`hero_guild_routing`) compiles correctly with all 4 non-uniform region kinds represented
      as the expected `Place.kind` values, verified by direct inspection (CITY, CAMP, RUIN, and
      intentionally-empty wilderness for `mountain_pass_zone`).
- [x] All 21 worlds are migrated and recompiled under the new schema — every world now has real Place
      coverage (`place_count >= 1`), confirmed via a batch resolve+compile pass, not the "remaining 19"
      framing the ticket originally scoped (see Implementation Notes for why the real number differs).

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD (parent epic)
- TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT (dependency)
- TCK-20260902-PLACE-MIGRATION-RECALIBRATION (runs alongside/after this ticket, per-world)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` item 2

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT/`)

## Related Code Areas
- `data/content/world_modules/goblin_camp_conflict.yaml`, `ruins_mystery_quest.yaml`,
  `settled_quarter.yaml`, `survivor_camp_shelter.yaml`, `undead_battlefield.yaml` — the 5 modules
  actually edited (real content, not the guessed `hero_guild_routing*.yaml` path from scoping time;
  `hero_guild_routing` itself has no standalone content — it composes 5 modules, see Stage A's own
  finding).
- `data/worlds/*/world_compile_report.json`, `data/worlds/*/resolved/*` — all 21 worlds regenerated.

## Assumptions / Open Questions
- ~~This is a genuinely large ticket... assess whether it should be split further per-world-batch~~
  **Decided: landed as one PR, not split.** The real corpus architecture (all 21 worlds share a small
  set of content modules — see Stage A's finding) meant the actual "migration" was 5 targeted module
  edits, not 20 separate per-world efforts. A single batch resolve+compile script then regenerated all
  21 worlds' committed assets in one pass. Splitting this into per-world tickets would have added
  process overhead without reducing real risk, given every edit was independently verified isolated
  (canonical-dict diff shows only `regions`/`places` changed) before the batch ran.

## Implementation Notes
Applying Stage A's already-established discipline (re-verify against real code/content, don't trust the
ticket's own scoping-time assumptions):

- `hero_guild_routing` composes 5 modules: `frontier_village_core` (already had a CITY Place from Stage
  A), `hero_adventurers`, `mountain_pass`, `ruins_mystery_quest`, `goblin_camp_conflict`. Added Places to
  `ruins_mystery_quest`'s `haunted_battlefield` (RUIN, `hazard_level: 3.5` — matching the region's own
  value, per `docs/brainstorm/rpg_expected_schemas.html#schema-66`'s own note that this exact field was
  anticipated to migrate) and `goblin_camp_conflict`'s `goblin_camp` (CAMP). Left `mountain_pass`'s
  `mountain_pass_zone` with zero Places — pure transit terrain, the intentional "or none at all" case
  from idea 66's own Target Shape, and part of what "non-uniform" is supposed to demonstrate.
- Computed the real union of worlds affected by the 3 originally-edited modules
  (`frontier_village_core`/`goblin_camp_conflict`/`ruins_mystery_quest`): 19 of 21, not the 17 found
  during Stage A alone (`dungeon_crawl` and `quest_dense_frontier` use `goblin_camp_conflict`/
  `ruins_mystery_quest` without using `frontier_village_core`). Only `highland_traverse` and
  `wilderness_survival` used none of the three.
- Investigated those 2 remaining worlds rather than leaving them uncovered: `highland_traverse` composes
  `settled_quarter` (a real `type: settlement` region — added a CITY Place); `wilderness_survival`
  composes `survivor_camp_shelter` (a wilderness outpost with a `healer_hut` — added a CAMP Place) and
  `undead_battlefield` (a second, independent `haunted_battlefield`-named RUIN candidate, different
  `grid_bounds`/module from `ruins_mystery_quest`'s — added a RUIN Place, `hazard_level: 4.0` matching
  its own region value). This brought real Place coverage to all 21 worlds, not just 19.
- Deliberately did NOT add a Place to `wolf_den_near_forest`'s `wolf_den` region, despite the tempting
  name match to LAIR. `PlaceState.occupant_entity_id` (LAIR-kind) is meant to anchor a specific
  boss/creature (reusing the real `boss_region_id` pattern) — no such anchor exists in this generic
  wildlife-ecology content, and the module's own description explicitly frames it as "proving contextual
  hostility instead of enemy-by-type," not a boss lair. Forcing LAIR here would misuse the schema; "or
  none at all" is the honest choice.
- Verified isolation at 3 different scales (16, 31, and 59 entities) via direct canonical-dict diffs —
  every one showed the same result: only `regions`/`places` changed, no entity/building/resource state
  affected.
- One pre-existing, unrelated compile warning surfaced during the batch pass (`QuestDefinition
  'survey_river_route' required_location_tag 'river' does not match any region type or tag`, on 4
  worlds) — confirmed unrelated by checking the diff touched none of the modules involved; not fixed
  here, out of scope.

## Test Summary
- 1 new test in `tests/unit/worldbuilding/test_place_wiring.py`:
  `test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds` — loads the real
  resolved content on disk (not a synthetic spec) and asserts all 4 region kinds, locking in Stage B's
  own stated acceptance criterion as a regression guard.
- Full regression sweep: `pytest tests/unit/worldbuilding/ tests/unit/worldassembly/
  tests/unit/worldmodules/ tests/unit/core/ tests/unit/engine/ tests/unit/kernel/ tests/certification/
  -m "not slow"` → 895 passed, 2 skipped (pre-existing, unrelated), 0 failed.
- `tests/tools/test_corpus_registry.py`, `tests/unit/worldassembly/test_corpus_diversity.py`,
  `tests/unit/lab/test_lab_result_store.py` (all consumers of `world_compile_report.json`) → 76 passed.
- Real-world verification: batch resolve+compile pass across all 21 worlds, 21/21 succeeded, every one
  shows `place_count >= 1` in its regenerated `world_compile_report.json`.

## Files Changed
- `data/content/world_modules/goblin_camp_conflict.yaml`, `ruins_mystery_quest.yaml`,
  `settled_quarter.yaml`, `survivor_camp_shelter.yaml`, `undead_battlefield.yaml` — added `places:`
  declarations.
- `data/worlds/*/world_compile_report.json`, `data/worlds/*/resolved/*` — all 21 worlds regenerated.
- `tests/unit/worldbuilding/test_place_wiring.py` — 1 new test.
- `tickets/inprogress/TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT.md` → moved to `tickets/done/`.

## Completion Summary
Migrated all 21 worlds to real Place coverage (not just the originally-scoped "hero_guild_routing +
remaining 19") by editing 5 shared content modules and running one batch resolve+compile pass, rather
than 20 separate per-world migrations — made tractable by Stage A's own architecture finding that the
corpus shares a small set of modules. `hero_guild_routing`'s 4 non-uniform region kinds verified by
direct inspection exactly as the ticket describes: CITY, CAMP, RUIN, and an intentional empty-wilderness
case. Investigated and covered the 2 worlds that used none of the originally-planned 3 modules
(`highland_traverse`, `wilderness_survival`) rather than leaving them out, bringing true 21/21 coverage.
Deliberately declined to force a LAIR Place onto `wolf_den_near_forest` — no real boss anchor exists for
it, and the content's own framing argues against it. Isolation verified at 3 different world scales.
Next: `TCK-20260902-PLACE-MIGRATION-RECALIBRATION`, whose own `state_hash`-first methodology needs to
account for the baseline-staleness finding from Stage A (`TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`)
— every world's `state_hash` will show as "changed" relative to the pre-idea-66 committed baseline,
for two independent reasons (staleness + real new Place data), not one.
