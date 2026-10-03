---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH
phase: done
date: 2026-09-02
tags: [lifecycle, world]
---

# TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH

## Title
Magical/demonic-being reproduction path — reuse Calamity substrate, full-adult spawn (no childhood)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child ticket 3 of 6 under the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION), covering the magical/demonic branch of idea 32 (Reproduction). Magical/demonic beings spawn off the existing `CalamityService`/`CalamityPressurePropagator` substrate (`src/world/calamity.py`) rather than a parent-pair mechanism, and per the design's own resolved decision, spawn at full adult capability with no childhood/maturation clock — this is settled, not an open question. Depends on TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA landing first.

## Scope
- A calamity/pressure event at or above its existing trigger threshold produces a new magical/demonic entity via `CalamityService`, following its existing intensity/trigger pattern (`src/world/calamity.py`).
- The new entity spawns directly as an ADULT life stage with no CHILD→ADULT maturation clock (explicit resolved design decision — magical beings do not have a childhood).
- No tracked parent pair — `parent_a_entity_id`/`parent_b_entity_id` (from TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA) are left None for this path, same as the natural-creature path.
- The spawn is committed via a typed `EntityUpdate`/`StateUpdate` through the authoritative apply path, reusing `CalamityService`'s existing mutation pattern.

## Out of Scope
- The natural-creature and human/humanoid reproduction paths (separate child tickets).
- Genetics inheritance — magical/demonic beings do not use `GeneticsSystem`/`GeneticProfile`; confirm this boundary at Plan time.
- The population-pressure feedback-loop closure — TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE, a separate later child ticket. Note: whether magical/demonic spawns even participate in the population-pressure gate at all (vs. being purely calamity-intensity-driven) is an open question for Plan — the atlas's population-pressure gate language is written primarily with natural/human reproduction in mind.

## Acceptance Criteria
- [x] A calamity/pressure event at or above its trigger threshold produces a new magical/demonic entity, verifiable against `CalamityService`'s existing intensity/trigger constants.
- [x] The new entity is spawned directly at ADULT life stage — no CHILD→ADULT transition or maturation clock is applied to this path.
- [x] The new entity's birth-record fields are populated with `parent_a_entity_id=None`, `parent_b_entity_id=None`, correct `birth_tick`, and correct `birth_city_id`/region (or the calamity's origin location if no city applies).
- [x] The spawn is committed through the authoritative apply path, not a direct mutation.
- [x] New unit test(s) added following the pattern of `tests/unit/world/test_calamity_raid.py::test_calamity_raid_maturity_advancement` / `::test_calamity_intensity_shift`.
- [x] `docs/mechanics/05_world_evolution.md` documents this reproduction path (including the explicit "no childhood" rule); a `docs/parity_ledger/world_dynamics.yaml` entry cites it.

## Related Tickets
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (parent epic)
- TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA (hard dependency — must land first)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 32 card — cross-race pairing / magical maturation explicitly resolved by design, treat as settled)
- docs/mechanics/05_world_evolution.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/world/calamity.py
- src/core/updates.py

## Assumptions / Open Questions
- Whether magical/demonic spawns are gated by the same regional population-pressure signal as natural/human paths, or purely by calamity intensity, is unresolved — a Plan-phase decision, not assumed here.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH/plan.md`
exactly, following its 7 steps and 3 pre-resolved Decisions (no population-pressure gate;
additive same-trigger branch, in-service flag check; reuse `role=EntityRole.MONSTER,
faction=Faction.MONSTER_HORDE`, `kind="magical_demonic_entity"`).

1. Registered `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` (default `FeatureMode.OFF`) in
   `src/domains/optimization/feature_flags.py`, immediately after
   `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`, with a DEV-002-style comment naming this
   ticket. Its own distinct key — not an alias of the sibling flag.
2. Added `EntityGenerator.spawn_magical_demonic_entity()` in
   `src/systems/world_systems/generator.py`, placed immediately after
   `spawn_natural_creature_offspring()` (before `spawn_goblin()`). Modeled on
   `spawn_natural_creature_offspring()` but with the `life_stage=LifeStage.CHILD` kwarg and
   `.lifecycle(age_ticks=...)` maturation-clock call both omitted — `IdentityComponent.life_stage`
   defaults to `ADULT` and `LifecycleComponent.age_ticks` defaults to `0`, satisfying the
   "no childhood" requirement by omission. Parentless birth record via
   `.birth_record(parent_a_entity_id=None, parent_b_entity_id=None, birth_tick=birth_tick,
   birth_city_id=None)`.
3. Added a third, additive branch inside `CalamityService.process_world_dynamics`
   (`src/world/calamity.py`), nested inside the existing `if should_spawn:` /
   `if high_intensity_regions:` block, after the existing `boss = generator.spawn_monster(...)`
   call and its `updates.replace(...)`. Reuses the already-selected `target_region.center` and
   `state.tick`. The `flags = getattr(state, "feature_flags", None) or {}` line was added once,
   near the top of the method (mirroring `CampService.process_camps`'s idiom), and only the new
   branch is wrapped in `if flags.get("ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH", "OFF") == "ON":`.
   The maturity-advancement block and the existing boss-spawn logic remain fully unconditional.
4. Added `tests/unit/world/test_calamity_magical_demonic_reproduction.py` (7 tests): trigger
   spawn, ADULT/no-maturation-clock (`age_ticks == 0`, no `life_stage=CHILD`), parentless
   birth-record fields + position, flag-off regression (only `world_boss` in `entities_add`),
   no-genetics-reference guard, no-population-cohorts-write guard, flag-registered-as-distinct-key
   guard.
5. Appended `test_magical_demonic_entity_spawn_commits_through_authoritative_apply_path` to
   `tests/integration/optimization/test_component_patch_apply_parity.py`, round-tripping a
   `spawn_magical_demonic_entity()`-built entity through `ApplyPath.apply_generation()` and
   asserting all birth-record fields and `life_stage == ADULT` survive.
6. Added a "Magical/Demonic Reproduction" subsection to `docs/mechanics/05_world_evolution.md`
   §6, immediately after "Natural-Creature Reproduction", with explicit "No childhood" and
   "No population-pressure suppression gate" bullets contrasting with the sibling subsection.
7. Added parity ledger entry `WORLD-121` to `docs/parity_ledger/world_dynamics.yaml` via
   `tools/parity_ledger_writer.py::write_entry()` (never a raw YAML edit) — `status: verified`,
   `priority: P2`, citing `SOC-259` (birth-record schema) but not `WORLD-DEMO-001` (population
   gate does not apply, per Decision 1), `test_path` pointing at the new file's primary spawn
   test. `WORLD-023`–`WORLD-028` and `WORLD-120` were left untouched (confirmed via `git diff`
   showing the new entry as a pure append at end-of-file).

No deviations from the plan. Full scoped regression suite from `test_plan.md`'s "Scoped Pytest
Commands" section (67 tests across the unit/integration regression surface plus the new test
files) passes.

## Test Summary

Ran (via `.venv/bin/python3 -m pytest`, since bare `python3` lacks `pydantic` in this environment):

```
pytest tests/unit/world/test_calamity_raid.py tests/unit/world/test_calamity_pressure_propagator.py \
  tests/unit/world/test_camp_lifecycle.py tests/unit/world/test_natural_creature_reproduction.py \
  tests/unit/progression/test_lifecycle.py tests/unit/world/test_world_dynamics.py \
  tests/unit/world/test_calamity_magical_demonic_reproduction.py \
  tests/integration/optimization/test_component_patch_apply_parity.py \
  tests/integration/optimization/test_apply_plan_parity.py \
  tests/integration/world/test_phase9_stability.py -v
```

Result: **67 passed, 0 failed.** All existing regression-surface tests (boss spawn, maturity
advancement, calamity intensity, camp lifecycle, natural-creature reproduction sibling, lifecycle/
birth-record schema, world dynamics, apply-plan parity, 1000-tick stability) pass unchanged
alongside the 7 new unit tests and 1 new integration test this ticket adds.

## Files Changed

- `src/domains/optimization/feature_flags.py` — registered `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`
  (default OFF)
- `src/systems/world_systems/generator.py` — added `EntityGenerator.spawn_magical_demonic_entity()`
- `src/world/calamity.py` — added the flag-gated magical/demonic spawn branch inside
  `CalamityService.process_world_dynamics`
- `tests/unit/world/test_calamity_magical_demonic_reproduction.py` — new unit test file (7 tests)
- `tests/integration/optimization/test_component_patch_apply_parity.py` — appended one new
  authoritative-apply-path round-trip test
- `docs/mechanics/05_world_evolution.md` — added "Magical/Demonic Reproduction" subsection under §6
- `docs/parity_ledger/world_dynamics.yaml` — added parity ledger entry `WORLD-121`
- `docs/parity_ledger/infrastructure.yaml` — Parity-phase fix: `INFRA-258`'s `calamity.py:56` line
  citation drifted to `:56` -> `:57` because this ticket's new `flags = ...` line shifted the
  pre-existing `last_calamity_tick_set=state.tick` statement down by one line; corrected the
  citation in both `text` and `v2_evidence`, no behavioral change to the underlying claim
- `tickets/inprogress/TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH.md` — this ticket, updated
  with Implementation Notes / Test Summary / Files Changed / Completion Summary / Status /
  Acceptance Criteria checkboxes
- `staging_artifacts/TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH/investigation.md`,
  `plan.md`, `test_plan.md` — pre-existing staging artifacts for this ticket (created earlier in
  this run's own Investigate/Plan phases, prior to this Implement phase)
- `agent-monitoring/tools.jsonl` — auto-updated by the monitoring tooling during this run

## Completion Summary

Added a fully flag-gated (`ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`, default OFF), additive
magical/demonic-entity spawn branch inside `CalamityService.process_world_dynamics`, reusing the
existing world-boss spawn's exact trigger and target region. The entity is built via a new
`EntityGenerator.spawn_magical_demonic_entity()` method, spawns directly at ADULT life stage with
no maturation clock, carries a fully parentless birth record (`parent_a_entity_id=None`,
`parent_b_entity_id=None`) via the existing `V2EntityBuilder.birth_record()` path, and is committed
exclusively through `StateUpdate.entities_add` and the authoritative apply pipeline. Per the
plan's pre-resolved Decision 1, this path is purely calamity-intensity-driven and carries no
regional population-pressure gate (unlike the sibling natural-creature path). New unit and
integration tests (7 + 1), a Mechanics Bible subsection, and parity ledger entry `WORLD-121` were
added; a drifted `INFRA-258` line citation (`calamity.py:56` -> `:57`, caused by this ticket's new
`flags = ...` line) was corrected in the same session with no behavioral change to the underlying
claim. The full scoped regression surface (67 tests) passes with no deviations from the approved
plan.
