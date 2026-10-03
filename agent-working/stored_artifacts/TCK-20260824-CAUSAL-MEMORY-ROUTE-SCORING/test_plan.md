---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING
artifact_type: test_plan
tags: [adventure, cognition]
---

# Test Plan — TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING

## Regression Surface

**Unit — memory domain:**
- `tests/unit/domains/memory/test_phase13_causal_attribution_service.py` — `CausalAttributionService.attribute()`
  branch logic must stay unchanged (this ticket does not touch `attribution.py`'s logic, only adds a
  live caller).
- `tests/unit/domains/memory/test_phase13_spatial_memory_update_service.py` — `SpatialMemoryUpdateService`
  unchanged.
- `tests/unit/domains/time/test_phase13_temporal_pressure_service.py` — `TemporalPressureService`
  unchanged.
- `tests/unit/entity/test_phase13_temporal_model.py`, `tests/unit/entity/test_phase11_cognition_model_schema.py`
  — `CognitionModel`/`TemporalModel` schema unchanged (this ticket adds a sibling `EntityUpdate` field,
  not a schema change to `CognitionModel` itself).

**Unit — adventure scoring:**
- `tests/unit/domains/adventure/test_memory_informed_scoring.py` (7 tests: `test_avoid_enemy_advice_suppresses_hunt_weak_enemy_score`,
  `test_boost_party_trust_advice_promotes_form_party_score`, `test_no_matching_causal_memory_is_a_no_op`,
  `test_future_advice_tuple_with_multiple_values_handled`, `test_memory_term_does_not_mutate_entity_cognition`,
  `test_memory_term_reads_only_entity_local_state`, `test_capacity_evicted_causal_entries_do_not_affect_scoring`)
  — must all keep passing unchanged; this ticket does not touch `scoring.py`'s memory_adjustment logic
  per the Out-of-Scope decision (see investigation.md Risks).
- `tests/unit/domains/adventure/test_phase3_route_scoring.py`, `test_depletion_scoring.py`,
  `test_capability_confidence_scoring.py` — full `AdventureRouteScorer.score()` regression surface
  (STRAT-227's other covered terms), unaffected by this ticket.

**Integration — memory phase (signature-affected):**
- `tests/integration/domains/memory/test_phase13_memory_update_phase.py` — 2 tests; 1 requires the
  `trigger_event=`→`trigger_events=[...]` call-site update (see New Tests / signature note below),
  the other (`test_phase_updates_temporal_staleness_after_old_fact`) is unaffected.
- `tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py` — 1 test,
  same call-site update required.

**Integration — combat / action routing (producer-affected):**
- `tests/integration/domains/adventure/` (existing full directory) — regression surface for any
  behavior change in `combat_actions.py::execute_attack()`'s `defender_up` construction.
- Any existing `src/engine/domain/combat_actions.py` / `src/engine/combat.py` unit or integration
  tests (locate via `pytest --collect-only` scoped to `tests/*/*/combat*` and `tests/*/*/*combat_actions*`
  before implementation, since the exact directory was not enumerated as part of this investigation's
  Related Code Areas — flag as an implementer-time discovery step) must keep passing: this ticket adds
  a new `WorldEvent` append to an existing `EntityUpdate`/`StateUpdate` construction path and must not
  change `damage_taken`, `alive_set`, `outcome_kind`, or any other existing `CombatUpdate` field.

**Pipeline-level regression (new phase registration):**
- Any existing full-pipeline / `AuthoritativeApplyPipeline.refine()` smoke or determinism test (e.g.
  under `tests/integration/` or `tests/architecture/` covering `run_phase()` registration order or
  `metric_counters`/`sub_phase_costs` keys) must keep passing with the new `"memory_update"` phase
  name added — since the new flag defaults OFF (`ENABLE_MEMORY_UPDATE`), the phase should no-op
  (`metric_counters["skip_memory_update"]` increments) in any existing test/corpus profile that does
  not explicitly enable it, so no assertion on fixed phase counts/costs should break — but any test
  that snapshots the *exact set* of `metric_counters` keys must be checked and updated to expect the
  new `skip_memory_update`/`run_memory_update` key.
- `docs/parity_ledger/strategic_cognition.yaml` STRAT-227's `test_path` entries (4 files, listed
  above under "Unit — adventure scoring" + this ticket's new end-to-end scenario) — the parity-updater
  agent will re-verify these at the Parity phase; the implementer should not attempt to update the
  ledger itself (per Gate Integrity — that is a separate agent's authoritative step).

## New Tests Required

**AC1 — pipeline.py registers MemoryUpdatePhase's call site between actor_validity and self_model:**
- Test name: `test_memory_update_phase_registered_between_actor_validity_and_self_model`
- Category: architecture guard (source-inspection or pipeline-ordering test, not a behavioral test)
- Verifies: `run_phase("memory_update", ...)` appears in `AuthoritativeApplyPipeline.refine()`'s
  source strictly after the `actor_validity` `run_phase` call and strictly before the `self_model`
  `run_phase` call (e.g. via `inspect.getsource()` line-position comparison, matching how other
  phase-ordering architecture guards in this repo are typically written — check
  `tests/architecture/` for an existing phase-ordering-guard pattern to follow before writing a new
  one from scratch).
- Location: `tests/architecture/test_memory_update_phase_pipeline_ordering.py` (new file) or an
  existing `tests/architecture/test_pipeline_phase_ordering*.py` if one already covers phase ordering
  generically — check before creating a new file.

**AC1b — MemoryUpdatePhase.apply() only mutates cognition via typed EntityUpdate, never state.entities directly:**
- Test name: `test_memory_update_phase_apply_does_not_mutate_state_entities`
- Category: architecture guard
- Verifies: calling `MemoryUpdatePhase.apply(state, StateUpdate())` on a frozen `AuthoritativeState`
  leaves `state.entities` object-identical (same `id()`/no in-place field mutation) and returns a
  `StateUpdate` whose `entity_updates[entity_id].cognition_bundle_set` is a new `CognitionModel`
  distinct from `state.entities[entity_id].cognition`.
- Location: `tests/unit/domains/memory/test_memory_update_phase_apply.py` (new file, sibling to the
  existing `test_phase13_*` unit tests in that directory).

**AC1c — CognitionPatch / EntityUpdate.cognition_bundle_set apply-path correctness:**
- Test name: `test_cognition_bundle_set_applies_to_entity_cognition_field`
- Category: unit
- Verifies: an `EntityUpdate(entity_id=..., cognition_bundle_set=<CognitionModel instance>)` run
  through `extract_patches()` + `ApplyPath._fast_replace_entity()` (or the public apply-path entry
  point used elsewhere in `tests/unit/` for `self_model_bundle_set`) produces a new `EntityState`
  whose `.cognition` is exactly the set value, and that `.self_model` is untouched (proves the two
  fields are correctly independent, guarding against the CausalMemoryEntry/SelfModelBundle naming
  confusion noted in investigation.md).
- Location: `tests/unit/engine/test_patches.py` if it exists (check first), else
  `tests/unit/domains/memory/test_memory_update_phase_apply.py` alongside AC1b.

**AC2 — real, live trigger_event producer (combat_loss) feeds a genuine in-tick event, not a test dict:**
- Test name: `test_combat_loss_world_event_emitted_when_defender_survives_and_takes_damage`
- Category: unit or integration (whichever matches `combat_actions.py`'s existing test file's level —
  check `tests/unit/engine/domain/test_combat_actions.py` or equivalent before writing, per the
  Regression Surface note above about locating existing combat_actions tests)
- Verifies: `CombatActions.execute_attack()` (or the specific function modified) returns/produces a
  `WorldEvent(category=WorldEventCategory.COMBAT_LOSS, ...)` in the resulting `StateUpdate.world_events_add`
  when the defender's `combat_up.alive_set is not False` and `combat_up.damage_taken > 0`, with
  correct `region_id`/`subject`/`tick`.
- Test name: `test_combat_loss_world_event_not_emitted_when_defender_takes_no_damage_or_dies`
- Category: unit
- Verifies: no `COMBAT_LOSS` `WorldEvent` is emitted when `damage_taken == 0` (miss/no-op) or when
  `alive_set is False` (defender died — no future entity to receive the memory).
- Location: same file as the existing `execute_attack`/`resolve_attack` test coverage.

**AC2b — MemoryUpdatePhase.apply() consumes recent_world_events with correct one-tick lag:**
- Test name: `test_memory_update_phase_reads_prior_tick_combat_loss_world_events`
- Category: integration
- Verifies: a `state.recent_world_events` list containing a `COMBAT_LOSS` event for entity X, when
  passed through `MemoryUpdatePhase.apply(state, update)`, produces exactly one new
  `CausalMemoryEntry` with `event_kind == "combat_loss"` for entity X, and does nothing for any other
  entity_id.
- Location: `tests/integration/domains/memory/test_memory_update_phase_apply.py` (new, or appended to
  the AC1b file if integration-level fixtures are more natural there).

**AC3 — end-to-end scenario: after a real triggering event, entity.cognition.memory.causal.entries
becomes non-empty and AdventureRouteScorer.score() produces a nonzero memory_adjustment:**
- Test name: `test_combat_loss_end_to_end_produces_nonzero_memory_adjustment_next_tick`
- Category: integration (scenario-level, ≥2 ticks through `AuthoritativeApplyPipeline.refine()` with
  `ENABLE_MEMORY_UPDATE` explicitly enabled via `rollout_profile`/`feature_flags`, per the one-tick-lag
  design)
- Verifies: (1) tick N — an attacker/defender pair resolves an attack via `action_routing` where the
  defender survives and takes damage but does **not** cross the `hp_pct < 0.3` / `stamina < 20` /
  `weapon_dur < 0.2` thresholds (constructed fixture: healthy defender, modest damage) so the
  `avoid_enemy` fallback branch fires; (2) tick N+1 — `state.entities[defender_id].cognition.memory.causal.entries`
  is non-empty and contains `future_advice` including `"avoid_enemy"`; (3) calling
  `AdventureRouteScorer.score()` on the defender for a `HUNT_WEAK_ENEMY`-family route produces
  `memory_adjustment == -1.0` (nonzero, matching STRAT-227/§6.11's documented constant).
- Location: `tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py` (new file, naming
  avoids embedding a ticket ID or phase number per project convention).

**AC4 — MemoryUpdatePhase.run()'s signature redesign, multi-entity same-tick coverage:**
- Test name: `test_run_updates_multiple_entities_with_distinct_trigger_events_same_tick`
- Category: unit
- Verifies: `MemoryUpdatePhase.run([entity_a, entity_b, entity_c], tick=T, trigger_events=[trigger_a,
  trigger_b])` (entity_c has no matching trigger) produces: entity_a and entity_b each with exactly
  one new `CausalMemoryEntry` matching their respective trigger's `event_kind`/`region_id`, and
  entity_c unchanged (only temporal/spatial-visit updates, no causal entry appended) — proving the
  old single-`trigger_event`-dict linear-match is fully replaced by a dict-keyed lookup and multiple
  simultaneous triggers are no longer silently dropped.
- Location: `tests/integration/domains/memory/test_phase13_memory_update_phase.py` (append to
  existing file, alongside the 2 existing tests that need their call sites updated).

**Existing test call-site updates required (not new tests, but must ship in the same commit):**
- `tests/integration/domains/memory/test_phase13_memory_update_phase.py:18` —
  `phase.run([entity], tick=10, trigger_event=trigger)` → `phase.run([entity], tick=10,
  trigger_events=[trigger])`.
- `tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py:25` —
  `phase.run([entity], tick=150, trigger_event=trigger)` → `phase.run([entity], tick=150,
  trigger_events=[trigger])`.

## Scoped Pytest Commands

```
# Memory domain (unit + integration) + scenario
pytest tests/unit/domains/memory/ tests/unit/entity/test_phase13_temporal_model.py \
       tests/unit/entity/test_phase11_cognition_model_schema.py \
       tests/unit/domains/time/test_phase13_temporal_pressure_service.py \
       tests/integration/domains/memory/ \
       tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py \
       tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py -v

# Adventure scoring domain (regression + confirm untouched)
pytest tests/unit/domains/adventure/ tests/integration/domains/adventure/ -v

# Combat action routing (producer-affected)
pytest tests/unit/engine/domain/ tests/integration/domains/combat_engagement/ -v -k "combat or attack"

# Pipeline / architecture guards (new phase registration)
pytest tests/architecture/ -v -k "phase_order or memory_update or pipeline"

# Full combined scoped run before Verify
pytest tests/unit/domains/memory/ tests/unit/domains/adventure/ tests/unit/entity/test_phase13_temporal_model.py \
       tests/unit/entity/test_phase11_cognition_model_schema.py tests/unit/domains/time/ \
       tests/integration/domains/memory/ tests/integration/domains/adventure/ \
       tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py \
       tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py \
       tests/architecture/ -q
```

Never `pytest tests/` — always scoped to the domains above. If `combat_actions.py`'s existing test
file cannot be located by the paths guessed above, the implementer/test-scoper must locate it via
`grep -rl "execute_attack\|CombatResolutionSystem" tests/` before finalizing the scoped command, and
add it explicitly.

## Anti-Drift Test Guards

- **`test_memory_term_does_not_mutate_entity_cognition`** and
  **`test_memory_term_reads_only_entity_local_state`** (existing, `test_memory_informed_scoring.py`)
  already guard that `AdventureRouteScorer.score()` stays read-only — re-running these unmodified is
  itself an anti-drift guard proving this ticket did not accidentally touch scoring.py's read/mutate
  boundary.
- **`test_avoid_enemy_advice_suppresses_hunt_weak_enemy_score`** and
  **`test_boost_party_trust_advice_promotes_form_party_score`** (existing) passing unchanged, combined
  with the new AC3 end-to-end test asserting the *same* `-1.0`/`+1.0` constants, together guard against
  silent scope-creep into extending the future_advice→RouteFamily mapping — if a future accidental
  edit adds a new mapped advice string, these two existing tests' exact assertions (no other family
  affected) would need updating and the diff would surface the change for review.
- **`test_phase_updates_temporal_staleness_after_old_fact`** (existing, unaffected by signature
  change) guards that the temporal-urgency-only code path (no trigger_events at all) keeps working —
  proves the new `trigger_events` default (`None` → empty dict lookup) doesn't regress the no-trigger
  case.
- **New `test_combat_loss_world_event_not_emitted_when_defender_takes_no_damage_or_dies`** guards
  against the two most likely over-eager producer bugs: emitting `COMBAT_LOSS` on a miss (no damage)
  or on the defender's actual death (where no future memory update is meaningful since the entity is
  gone).
- **New `test_memory_update_phase_apply_does_not_mutate_state_entities`** guards the Durable State
  Rule directly — the single highest-value architecture guard for this ticket, since the entire
  investigation's central risk is `MemoryUpdatePhase.run()`'s raw-`EntityState`-list shape tempting an
  implementer into a direct-mutation shortcut when wiring it into `refine()`.
- **Pipeline `metric_counters` key-set check** (see Regression Surface) guards that the new
  `ENABLE_MEMORY_UPDATE`-gated phase defaults OFF and does not silently change behavior or timing in
  any existing SimQ/corpus profile that doesn't explicitly opt in.
