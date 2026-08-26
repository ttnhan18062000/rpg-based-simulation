---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING
phase: done
date: 2026-08-24
tags: [adventure, cognition]
---

# TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING

## Title
Wire Causal Memory into Adventure Route Scoring (Expertise Earned Through Living)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
MemoryUpdatePhase has zero call sites, so its consumer (AdventureRouteScorer.score()) already reads only 2 of 10 possible advice values from causal memory that never actually populates. The author wants MemoryUpdatePhase wired in, at the proposed insertion point between PP-02 and PP-03.

## Scope
- Register MemoryUpdatePhase's call site in src/engine/pipeline.py between actor_validity (PP-02) and self_model (PP-03) for all active/alive entities
- Build at least one real, live trigger_event producer (e.g. combat_loss) that feeds a genuine in-tick event, not just test dicts
- Redesign/loop MemoryUpdatePhase.run()'s single trigger_event-dict-matched-by-entity_id signature so multiple entities triggering in the same tick are all updated
- Verify in an end-to-end scenario that after a real triggering event, entity.cognition.memory.causal.entries becomes non-empty and AdventureRouteScorer.score() produces a nonzero memory_adjustment
- Correct docs/simulation/domains/memory_contract.md's Domain Interactions row, which currently falsely asserts causal memory already feeds route scoring in production

## Out of Scope
- The 7 orphaned mechanisms tracked by TCK-20260824-WIRE-ORPHANED-MECHANISMS -- MemoryUpdatePhase is explicitly excluded from that ticket's scope and owned here
- Extending the future_advice->RouteFamily mapping beyond the current 2-of-10 advice values read -- that is TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING's own separately-flagged, larger scope; this ticket should decide whether to extend that mapping or purely wire the phase, not silently do both

## Acceptance Criteria
- [x] pipeline.py registers MemoryUpdatePhase's call site between actor_validity (PP-02) and self_model (PP-03) for all active/alive entities
- [x] At least one real, live trigger_event producer feeds a genuine in-tick event, not just test dicts
- [x] In an end-to-end scenario, after a real triggering event, entity.cognition.memory.causal.entries becomes non-empty and AdventureRouteScorer.score() produces a nonzero memory_adjustment
- [x] MemoryUpdatePhase.run()'s signature is redesigned/looped so multiple entities triggering in the same tick are all updated

## Related Tickets
- TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING
- TCK-20260529-COG-PHASE13-MEMORY
- TCK-20260824-WIRE-ORPHANED-MECHANISMS

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/engine/kernel.md
- docs/simulation/domains/memory_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/memory/phase.py
- src/domains/adventure/scoring.py
- src/domains/memory/attribution.py
- src/core/cognition.py
- src/engine/pipeline.py
- src/engine/combat.py

## Assumptions / Open Questions
- Whether to extend the future_advice->RouteFamily mapping beyond 2-of-10 values in this same ticket, or purely wire the phase and leave the mapping extension for TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING, is an open decision
- Building a genuine trigger_event source (combat_loss/failed_search/failed_craft/party_abandoned) is materially larger than "add one phase call" and should be scoped/estimated accordingly
- layer set to `strategy` (bounded cognition / goal hierarchy) rather than `engine`, since the substantive scope is causal memory driving cognitive route advice, not the tick-loop mechanics itself; the pipeline.py call-site registration is a means to that end

## Implementation Notes

Implemented plan.md's Steps 1-5 exactly as specified (Step 6 doc updates are out of scope for the
implementer per the task instructions -- handled by the separate Document-Update phase).

- **Step 1** (`src/domains/memory/phase.py`): `MemoryUpdatePhase.run()`'s `trigger_event: Optional[dict]`
  parameter became `trigger_events: Optional[List[dict]]`, matched internally via
  `trigger_by_entity = {t["entity_id"]: t for t in (trigger_events or [])}`. The 2 existing call
  sites (`tests/integration/domains/memory/test_phase13_memory_update_phase.py`,
  `tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py`) were
  updated to `trigger_events=[trigger]`. Added
  `test_run_updates_multiple_entities_with_distinct_trigger_events_same_tick` to the first file
  proving 3 entities with 2 distinct simultaneous triggers are each independently matched.
- **Step 2** (`src/core/updates.py`, `src/engine/patches.py`, `src/domains/memory/phase.py`): added
  `EntityUpdate.cognition_bundle_set: Optional[Any] = None` (mirroring `self_model_bundle_set`,
  including its `is_noop()`/`merge()` clauses) and a new `CognitionPatch(ComponentPatch)` mirroring
  `SelfModelPatch` (writes `changes["cognition"]`), registered in `extract_patches()`. Added
  `MemoryUpdatePhase.apply(state, update, trigger_events=None) -> StateUpdate` as a `@staticmethod`
  that instantiates `MemoryUpdatePhase()` (its `run()` is an instance method, unlike
  `SelfModelUpdatePhase.run()`), filters to active/alive entities, calls `run()` once in bulk, and
  writes results into `entity_updates[id].cognition_bundle_set` via `dataclasses.replace` --
  never touching `state.entities` directly.
- **Step 3** (`src/engine/pipeline.py`, `src/domains/optimization/feature_flags.py`,
  `src/engine/phase_graph.py`): registered `run_phase("memory_update", ...)` in
  `AuthoritativeApplyPipeline.refine()` strictly between the `actor_validity` and `self_model`
  `run_phase` calls, gated by new `ENABLE_MEMORY_UPDATE` flag (default OFF). `trigger_events` is
  sourced from `state.recent_world_events` filtered to `WorldEventCategory.COMBAT_LOSS`, with the
  required `int(e.subject)` conversion (WorldEvent.subject is `Optional[str]`; entity ids are
  `int`) -- this is a one-tick lag by design (action_routing, which produces the event, runs later
  in the same tick). Added a `"memory_update"` `PhaseMetadata` entry to `PhaseDependencyGraph.PHASES`
  for consistency with sibling Enhanced-RPG phases (optional per plan.md, added anyway).
- **Step 4** (`src/domains/world_emergence/schema.py`, `src/engine/pipeline_phases/actions.py`):
  added `WorldEventCategory.COMBAT_LOSS`. `ActionRoutingPhase.route()` now emits a `COMBAT_LOSS`
  `WorldEvent` for the defender of an `ATTACK` whenever `combat_upd.alive_set is not False and
  combat_upd.damage_taken > 0`, deliberately independent of `NearDeathHardeningPhase`'s hp_pct<=10%
  threshold (coupling to that would starve `CausalAttributionService`'s `avoid_enemy` fallback
  branch). A local `new_world_events_add` list is threaded through every intermediate
  `replace(update, ...)` call in `route()`'s per-actor loop and the final return, so it accumulates
  onto (never overwrites) events already written by `diplomatic_transitions`/`military_conflict`
  earlier in the same tick.
- **Step 5** (`tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py`, new): a 3-tick
  scenario driving the real pipeline (`AuthoritativeApplyPipeline.refine()` +
  `ApplyPath.apply_generation()`) with `ENABLE_MEMORY_UPDATE=ON` -- tick 1 resolves a real ATTACK
  where the defender survives with modest damage (hp_pct stays well above 0.3, default
  stamina/weapon-durability keep the other two combat_loss branches from firing), confirms no
  causal memory yet exists at that point (one-tick lag); tick 2 confirms
  `entity.cognition.memory.causal.entries` is non-empty with `"avoid_enemy"` in `future_advice`;
  `AdventureRouteScorer.score()` (untouched) then returns `memory_adjustment == -1.0` for a
  `HUNT_WEAK_ENEMY` route.
- **Scope guard honored**: `AdventureRouteScorer.score()`'s `future_advice`->`RouteFamily` mapping
  in `src/domains/adventure/scoring.py` was not touched -- AC3 is satisfiable via the existing
  `avoid_enemy` mapping alone, per the plan's Scope Guards.
- Also added AC1b/AC1c architecture-guard/unit tests (`tests/unit/domains/memory/test_memory_update_phase_apply.py`),
  an AC2b integration test for the one-tick-lag consumption
  (`tests/integration/domains/memory/test_memory_update_phase_apply_trigger_events.py` -- renamed
  from the plan's suggested `test_memory_update_phase_apply.py` to avoid a pytest module-name
  collision with the unit-level file of the same basename in a different directory, since neither
  `tests/unit/domains/memory/` nor `tests/integration/domains/memory/` has an `__init__.py`), an
  AC1 pipeline-ordering architecture guard
  (`tests/architecture/test_memory_update_phase_pipeline_ordering.py`), and AC2 unit tests for the
  `COMBAT_LOSS` producer (`tests/unit/actions/test_action_routing_combat_loss_world_event.py`,
  sibling to the existing `test_action_routing_task_reset.py`).
- Ran `graphify update .` after the `src/` edits per project convention.

## Test Summary

All new and regression-surface tests pass (venv: `/home/u24desktop/Working/venv/bin/python3`, since
the sandbox's bare `python3` lacks `pydantic`):

- Memory/adventure/pipeline scoped run (35 tests):
  `tests/unit/domains/memory/`, `tests/unit/entity/test_phase13_temporal_model.py`,
  `tests/unit/entity/test_phase11_cognition_model_schema.py`, `tests/unit/domains/time/`,
  `tests/integration/domains/memory/`,
  `tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py`,
  `tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py`,
  `tests/architecture/test_memory_update_phase_pipeline_ordering.py`,
  `tests/unit/actions/test_action_routing_combat_loss_world_event.py`,
  `tests/unit/actions/test_action_routing_task_reset.py` -- 35 passed.
- Adventure scoring regression: `tests/unit/domains/adventure/`, `tests/integration/domains/adventure/`
  -- 95 passed (confirms `scoring.py`'s memory_adjustment logic is unchanged).
- Combat/action-routing/pipeline/architecture regression: `tests/unit/combat/`, `tests/unit/actions/`,
  `tests/integration/pipeline/`, `tests/integration/domains/test_fused_loop.py`,
  `tests/integration/test_scenario_feature_flag_defaults.py`, `tests/architecture/` -- 308 passed.
- Optimization/phase-skip parity + engine unit tests: `tests/integration/optimization/`,
  `tests/unit/engine/` -- 196 passed, 1 skipped (pre-existing).

## Files Changed

- `src/domains/memory/phase.py` -- `trigger_events` list signature; new `MemoryUpdatePhase.apply()`.
- `src/core/updates.py` -- `EntityUpdate.cognition_bundle_set` field + `is_noop()`/`merge()` clauses.
- `src/engine/patches.py` -- new `CognitionPatch`; registered in `extract_patches()`.
- `src/engine/pipeline.py` -- registers `memory_update` phase call site between `actor_validity`
  and `self_model`.
- `src/domains/optimization/feature_flags.py` -- new `ENABLE_MEMORY_UPDATE` flag (default OFF).
- `src/engine/phase_graph.py` -- new `"memory_update"` `PhaseMetadata` entry.
- `src/domains/world_emergence/schema.py` -- new `WorldEventCategory.COMBAT_LOSS`.
- `src/engine/pipeline_phases/actions.py` -- emits `COMBAT_LOSS` `WorldEvent` for a surviving,
  damaged defender; accumulates `world_events_add` across the per-actor loop.
- `tests/integration/domains/memory/test_phase13_memory_update_phase.py` -- call-site update +
  new multi-entity same-tick test.
- `tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py` --
  call-site update.
- `tests/unit/domains/memory/test_memory_update_phase_apply.py` (new) -- AC1b/AC1c unit tests.
- `tests/integration/domains/memory/test_memory_update_phase_apply_trigger_events.py` (new) --
  AC2b integration test.
- `tests/architecture/test_memory_update_phase_pipeline_ordering.py` (new) -- AC1 architecture guard.
- `tests/unit/actions/test_action_routing_combat_loss_world_event.py` (new) -- AC2 producer tests.
- `tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py` (new) -- AC3 end-to-end scenario.
- `docs/simulation/domains/memory_contract.md` -- corrected the Domain Interactions row that
  falsely asserted causal memory already fed route scoring in production; now documents the real
  `ENABLE_MEMORY_UPDATE`-gated wiring and the one-tick lag via `recent_world_events`.
- `docs/mechanics/04_strategic_cognition.md` -- updated causal memory / route scoring section to
  reflect the live pipeline wiring instead of the prior dormant-mechanism description.
- `docs/engine/authoritative_pipeline.md` -- added the `memory_update` phase's call-site position
  (between `actor_validity`/PP-02 and `self_model`/PP-03) to the refinement sequence.
- `docs/parity_ledger/strategic_cognition.yaml` -- updated/added entry for `MemoryUpdatePhase`
  wiring status (verified, with `v2_evidence` pointing at the new e2e test).
- `docs/parity_ledger/combat_movement.yaml` -- updated/added entry for the new `COMBAT_LOSS`
  `WorldEvent` producer in `ActionRoutingPhase.route()`.
- `docs/parity_ledger/infrastructure.yaml` -- updated/added entry for the `ENABLE_MEMORY_UPDATE`
  feature flag and its default-OFF rollout status.
- `docs/guidelines/intentional_divergences.md` -- recorded the one-tick lag between the
  `COMBAT_LOSS` event and its consumption by `MemoryUpdatePhase` as an intentional divergence
  (phase-ordering constraint, not a bug), with rationale class and verification path.
- `staging_artifacts/TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING/investigation.md`,
  `staging_artifacts/TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING/plan.md`,
  `staging_artifacts/TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING/test_plan.md` -- created earlier in
  this run's Investigate/Plan phases (not authored by the implementer, but part of this run's
  changeset).

## Completion Summary

Wired `MemoryUpdatePhase` into `AuthoritativeApplyPipeline.refine()` for the first time (previously
zero call sites), behind a default-OFF `ENABLE_MEMORY_UPDATE` flag, using a new typed
`EntityUpdate.cognition_bundle_set` -> `CognitionPatch` authoritative-apply path that never mutates
`state.entities` directly. Built a real `WorldEventCategory.COMBAT_LOSS` producer in
`ActionRoutingPhase.route()` (defender survives and takes damage) that feeds the phase via the
existing one-tick-lagged `recent_world_events` channel, redesigned `MemoryUpdatePhase.run()` to
accept a list of `trigger_events` matched by `entity_id` so multiple simultaneous triggers are no
longer dropped, and proved the full chain end-to-end with a 3-tick scenario test showing
`entity.cognition.memory.causal.entries` becomes non-empty and `AdventureRouteScorer.score()`
(left untouched, per scope) produces the documented `-1.0` `memory_adjustment` for `HUNT_WEAK_ENEMY`.
