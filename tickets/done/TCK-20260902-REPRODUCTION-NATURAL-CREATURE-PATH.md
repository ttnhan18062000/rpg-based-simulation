---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH
phase: done
date: 2026-09-02
tags: [lifecycle, world]
---

# TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH

## Title
Natural-creature reproduction path — reuse Camp maturity/spawn pattern for parentless offspring

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child ticket 2 of 6 under the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION), covering the natural-creature branch of idea 32 (Reproduction). Natural creatures (non-sapient wildlife) reproduce without a tracked parent pair — the design reuses `CampService.process_camps()`'s existing maturity-accrual/spawn/raid-trigger pattern (`src/world/camp.py`) rather than inventing a new mechanism. Depends on TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA landing first (needs the birth-record fields to exist, even though this path leaves parent_a/parent_b as None).

## Scope
- A camp/territory at or above its existing maturity threshold produces a new same-kind entity with a short CHILD→ADULT maturation clock, following `CampService`'s existing maturity/spawn constants (`MATURITY_PER_TICK`/`RAID_MATURITY_THRESHOLD`-style thresholds in `src/world/camp.py`).
- The new entity has no tracked parent pair — `parent_a_entity_id`/`parent_b_entity_id` from the birth-record schema (TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA) are left None for this path.
- The spawn is committed via a typed `EntityUpdate`/`StateUpdate` through the authoritative apply path, reusing `CampService`'s existing mutation pattern.
- Eligibility is gated by the population-pressure signal: suppress spawn when `compute_regional_scarcity()` (`src/domains/demographics/cohort.py`) for the camp's region exceeds the region's cohort `migration_threshold` (0.7 default) — reuse this existing computation, do not add a new one.

## Out of Scope
- The magical/demonic and human/humanoid reproduction paths (separate child tickets).
- Genetics inheritance — natural creatures do not use `GeneticsSystem`/`GeneticProfile` per this ticket's scope (genetics wiring is scoped to the human/humanoid path only in TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE; confirm this boundary at Plan time rather than assuming).
- The population-pressure feedback-loop closure itself (nudging `population_cohorts` on a successful birth) — that is TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE, a separate later child ticket.

## Acceptance Criteria
- [x] A camp/territory at or above its maturity threshold produces a new same-kind entity with a short CHILD→ADULT maturation clock, verifiable against `CampService`'s existing maturity/spawn constants.
- [x] The new entity's birth-record fields (from TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA) are populated with `parent_a_entity_id=None`, `parent_b_entity_id=None`, correct `birth_tick`, and correct `birth_city_id`/region.
- [x] Spawn eligibility is suppressed when `compute_regional_scarcity()` exceeds the region's `migration_threshold` for the camp's region — a test proves both the allowed and suppressed cases.
- [x] The spawn is committed through the authoritative apply path (`EntityUpdate`/`StateUpdate`), not a direct mutation.
- [x] New unit test(s) added following the pattern of `tests/unit/world/test_camp_lifecycle.py::test_camp_maturity_and_spawn` / `::test_camp_raid_trigger`.
- [x] `docs/mechanics/05_world_evolution.md` documents this reproduction path; a `docs/parity_ledger/world_dynamics.yaml` entry cites it.

## Related Tickets
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (parent epic)
- TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA (hard dependency — must land first)
- TCK-20260831-CREATURE-TERRITORY-LIFECYCLE (sibling precedent — reused CampService's trauma-multiplier maturity shape for a different settlement-population tier)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 32 card)
- docs/mechanics/05_world_evolution.md
- docs/parity_ledger/world_dynamics.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/world/camp.py
- src/domains/demographics/cohort.py
- src/core/updates.py

## Assumptions / Open Questions
- Whether this path needs any genetics involvement at all is an open boundary question for Plan — flagged as likely "no" (natural creatures don't inherit the human/humanoid GeneticProfile system) but not yet confirmed.

## Implementation Notes

Implemented all 6 steps exactly per `staging_artifacts/TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH/plan.md`,
no deviations.

1. **Flag registration** (`src/domains/optimization/feature_flags.py`): added
   `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH: FeatureMode.OFF` to `FeatureFlagManager.__init__`'s
   `self._flags`, after `ENABLE_ROLE_MODEL_IMITATION`, with a DEV-002 default-OFF comment matching
   the established style. No other flag touched.
2. **`EntityGenerator.spawn_natural_creature_offspring()`** (`src/systems/world_systems/generator.py`):
   new method, added immediately before `spawn_goblin()`. Mirrors `spawn_monster()`'s stat/level
   scaling verbatim, adds `.identity(..., life_stage=LifeStage.CHILD)`, `.lifecycle(age_ticks=3000 -
   CampService.CAMP_SPAWN_INTERVAL)` (2970), and `.birth_record(parent_a_entity_id=None,
   parent_b_entity_id=None, birth_tick=birth_tick, birth_city_id=None)`. `spawn_monster()` and every
   other existing generator method left byte-for-byte unmodified.
3. **`CampService.process_camps()` wiring** (`src/world/camp.py`): added a new "4. Natural-Creature
   Reproduction" block inside the existing per-camp loop, after the "3. Raid Trigger" block, gated by
   `flags.get("ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH", "OFF") == "ON"` (flags read once before the
   loop via the established `getattr(state, "feature_flags", None) or {}` idiom). Triggers on
   `camp.maturity >= RAID_MATURITY_THRESHOLD` and `state.tick % CAMP_SPAWN_INTERVAL == 0`. Eligibility
   check reuses the same `region` variable already computed once per camp for the trauma multiplier
   (not recomputed); when `region.population_cohorts` is non-empty, reads the `"young"` bracket's
   `migration_threshold` (falling back to the `PopulationCohort` dataclass default 0.7 only if the
   bracket is absent) and compares against a freshly-computed `compute_regional_scarcity(region.id,
   state)`; when `region` is `None` or `population_cohorts` is empty, treats the camp as eligible
   (mirrors `cohort.py`'s own skip-when-empty convention at `_check_migration`/
   `DemographicCycleService.process_demographics` — do not modify `cohort.py` itself, and did not).
   The existing garrison-spawn (block 2) and raid-trigger (block 3) blocks are unmodified; the new
   entity flows through the existing `entities_add`/`StateUpdate` return with no `world_dynamics.py`
   change needed.
4. **Tests**: `tests/unit/world/test_natural_creature_reproduction.py` (new, 9 tests — the 7
   plan-specified tests plus 2 extra: the explicit no-cohort-data-eligible case called out separately
   in the plan text, and a flag-off regression guard) plus one round-trip integration test
   (`test_natural_creature_spawn_commits_through_authoritative_apply_path`) appended to
   `tests/integration/optimization/test_component_patch_apply_parity.py`. All pass; full regression
   surface from `test_plan.md`'s Scoped Pytest Commands (136 tests across
   `test_camp_lifecycle.py`, `test_creature_territory_lifecycle.py`, `test_demographics.py`,
   `tests/unit/progression/test_lifecycle.py`, `test_component_patch_apply_parity.py`,
   `test_apply_plan_parity.py`, `tests/integration/scenarios/test_demographics.py`,
   `test_spawn_cadence.py`, plus the new file) passes unchanged.
5. **`docs/mechanics/05_world_evolution.md`**: added a new subsection "Natural-Creature Reproduction
   (TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH)" under `## 6. Calamities & World Threats`,
   immediately after the existing "Creature Territory Lifecycle" subsection. Documents the flag, the
   trigger constants, the parentless birth-record population, the short-maturation-clock mechanism
   (explicitly noting it does not touch §5's global 3000/7000 thresholds), and the population-pressure
   suppression gate (citing §5's Migration Law and the skip-when-empty convention). `make
   knowledge-index-update` run afterward.
6. **Parity ledger**: added `WORLD-120` (`status: verified`, `priority: P2`) to
   `docs/parity_ledger/world_dynamics.yaml` via `tools/parity_ledger_writer.py`'s `write_entry()`
   (never hand-edited), citing `src/world/camp.py`, `src/systems/world_systems/generator.py`,
   `src/domains/optimization/feature_flags.py`, cross-referencing `WORLD-DEMO-001` and `SOC-259`.
   The writer's in-process index rebuild completed successfully (`entry_count: 2124`, `shard_count: 9`).
   YAML validated post-write: 129 entries, all ids unique, `WORLD-119` unchanged.

`graphify update .` run after the `src/`/`tests/` changes (no topology changes detected).

## Test Summary

- `tests/unit/world/test_natural_creature_reproduction.py` — 9 new tests, all pass.
- `tests/integration/optimization/test_component_patch_apply_parity.py` — 1 new round-trip test
  (`test_natural_creature_spawn_commits_through_authoritative_apply_path`) plus the 4 pre-existing
  tests in that file, all pass.
- Regression surface run: `pytest tests/unit/world/test_camp_lifecycle.py
  tests/unit/world/test_creature_territory_lifecycle.py tests/unit/world/test_demographics.py
  tests/unit/progression/test_lifecycle.py tests/integration/optimization/test_component_patch_apply_parity.py
  tests/integration/optimization/test_apply_plan_parity.py tests/integration/scenarios/test_demographics.py
  tests/unit/world/test_spawn_cadence.py tests/unit/world/test_natural_creature_reproduction.py`
  → 136 passed, 0 failed.
- Flag sanity check: `FeatureFlagManager().get_flag_mode('ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH')
  == FeatureMode.OFF` confirmed.
- Not run: full suite (per repo convention, scoped only).

## Files Changed

- `src/domains/optimization/feature_flags.py` — registered `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` (default OFF)
- `src/systems/world_systems/generator.py` — added `EntityGenerator.spawn_natural_creature_offspring()`
- `src/world/camp.py` — added flag-gated "4. Natural-Creature Reproduction" branch to `CampService.process_camps()`
- `tests/unit/world/test_natural_creature_reproduction.py` — new, 9 unit tests
- `tests/integration/optimization/test_component_patch_apply_parity.py` — added 1 round-trip integration test
- `docs/mechanics/05_world_evolution.md` — added "Natural-Creature Reproduction" subsection under §6
- `docs/parity_ledger/world_dynamics.yaml` — added `WORLD-120` entry via `tools/parity_ledger_writer.py`
- `tickets/inprogress/TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH.md` — this ticket, updated
- `staging_artifacts/TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH/investigation.md` — created earlier this run (Investigate phase)
- `staging_artifacts/TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH/plan.md` — created earlier this run (Plan phase)
- `staging_artifacts/TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH/test_plan.md` — created earlier this run (Investigate phase)
- `agent-monitoring/tools.jsonl` — auto-updated by monitoring hook during this run

## Completion Summary

Implemented the natural-creature reproduction path as a flag-gated (`ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`,
default OFF) fourth branch inside `CampService.process_camps()`: a camp at or above
`RAID_MATURITY_THRESHOLD` on the `CAMP_SPAWN_INTERVAL` cadence spawns a parentless same-kind
offspring (via the new `EntityGenerator.spawn_natural_creature_offspring()`, reusing the shipped
`V2EntityBuilder.birth_record()` API with both parent ids `None`) pre-aged to `age_ticks=2970` so
the existing global aging pipeline carries it to `ADULT` after one more spawn-cadence cycle, with
population-pressure eligibility gated on `compute_regional_scarcity()` against the region's `young`
cohort `migration_threshold`, treating cohort-less regions as eligible per the existing Migration
Law skip-when-empty convention. Shipped with 9 new unit tests, 1 new integration round-trip test,
a new `docs/mechanics/05_world_evolution.md` subsection, and parity ledger entry `WORLD-120`.
