---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP
artifact_type: test_plan
tags: [simulation-quality, cognition, stasis]
---

# Test Plan — TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP

## Regression Surface

Existing tests that must keep passing after any change to `src/engine/tactical.py`,
`src/domains/adventure/*`, `src/systems/strategic_systems/intelligence.py`, `src/ai/goals/*`, or
`src/engine/intent/action_intent.py`.

**Unit — tactical / combat (tactical.py is shared by combat target-selection logic; do not regress
combat while fixing the objective-pursuit branch):**
- `tests/unit/tactical/test_target_stickiness.py`
- `tests/unit/combat/test_anti_stalemate.py`
- `tests/unit/combat/test_tactical_legality.py`
- `tests/unit/combat/test_engagement_behavior.py`
- `tests/unit/combat/test_tactical_hardening.py`
- `tests/unit/combat/test_target_selection_contract.py`
- `tests/unit/movement/test_tactical_movement.py`
- `tests/unit/movement/test_mob_leashing.py`

**Unit — Adventure domain (System A: route generation, scoring, mapping, decision service,
resolver):**
- `tests/unit/domains/adventure/test_phase3_route_scoring.py`
- `tests/unit/domains/adventure/test_phase3_route_generator.py`
- `tests/unit/domains/adventure/test_phase3_route_families.py`
- `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py`
- `tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py`
- `tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py` (currently the only
  consumer of `ObjectiveIntentResolver` — if the fix wires this resolver into production, this file
  becomes load-bearing regression, not just isolated unit coverage)
- `tests/unit/domains/adventure/test_hero_quest_scoring.py`
- `tests/unit/domains/adventure/test_depletion_scoring.py`
- `tests/unit/domains/adventure/test_abandonment_rate.py`
- `tests/unit/domains/adventure/test_scoring_plan_bonus.py`

**Integration — Adventure domain / pipeline:**
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`
- `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`
- `tests/perf/test_phase3_adventure_decision_budget.py` (perf budget — a routing-layer change must
  not blow the tick-cost budget)

**Unit/Integration — Strategic cognition (System B: `fused_strategic_pass`, `GoalRegistry`,
`HarvestScorer`):**
- `tests/unit/strategic/test_strategic_cognition_regression.py`
- `tests/unit/strategic/test_strategic_hardening.py`
- `tests/unit/strategic/test_strategic_lifecycle_v2.py`
- `tests/unit/strategic/test_strategic_lifecycle.py`
- `tests/unit/strategic/test_strategic_reprioritization.py`
- `tests/unit/strategic/test_phase6_strategic_cognition.py`
- `tests/unit/strategic/test_strategic_detour_ph6.py`
- `tests/unit/strategic/test_cognition_authoritative_path.py`
- `tests/unit/strategic/test_expanded_goals.py`
- `tests/unit/strategic/test_routine_biasing.py`
- `tests/unit/strategic/test_capacity_enforcement.py`
- `tests/unit/strategic/test_enum_drift.py`
- `tests/integration/pipeline/test_strategic_cadence.py`

**Integration — action intent adapter (if `ObjectiveIntentResolver`/`ActionIntentAdapter` gets
wired into production, its existing dispatch-table tests become regression-critical):**
- Any existing `tests/unit/`/`tests/integration/` files exercising
  `src/engine/intent/action_intent.py::ActionIntentAdapter` directly (locate via
  `grep -rl "ActionIntentAdapter" tests/` at Implement time — not enumerated here since this
  investigation did not exhaustively trace them).

**Architecture guard:**
- `tests/integrity/test_logic_guards.py` (already references `GoalRegistry`/strategic goal wiring;
  re-run to confirm no authoritative-mutation-boundary violation is introduced).

## New Tests Required

Per the ticket's Acceptance Criteria:

1. **`test_objective_kind_acquire_item_produces_executable_action`**
   - Category: unit
   - Verifies: given an entity with `current_project_id`/`current_objective_id` set to a
     `ProjectState(kind=ProjectKind.CRAFTING)` / `ObjectiveState(kind=ObjectiveKind.ACQUIRE_ITEM)`,
     `TacticalDecisionSystem.evaluate_entity_intent` (or whatever replaces/extends the Pillar 5.1
     branch per the chosen fix shape) returns a non-idle `EntityUpdate` — i.e. a real `task`/
     `navigation`/`interaction` payload, not the bare `EntityUpdate(entity_id=entity.id)` fallback
     at `tactical.py:319`. This is the direct regression test for the confirmed root cause.
   - Location: `tests/unit/tactical/test_objective_pursuit_coverage.py` (new file) or added to
     `tests/unit/strategic/test_strategic_cognition_regression.py` if Plan prefers colocating with
     existing strategic-objective tests.

2. **`test_objective_kind_reach_resource_produces_executable_action`**
   - Category: unit
   - Verifies: the same, for `ObjectiveKind.REACH_RESOURCE` (System A's `GATHER_RESOURCE` mapping).
   - Location: same file as above.

3. **`test_crafting_project_reaches_craft_system`** (end-to-end unit, mocked/constructed state)
   - Category: unit
   - Verifies: an entity with an active CRAFTING project, known recipe, and sufficient
     materials/gold, when driven through one or more ticks of the fixed pipeline, results in a
     call that reaches `CraftingSystem.craft()` (or the equivalent authoritative crafting entry
     point chosen in Plan) and produces an `InventoryUpdate` with `items_add` matching the recipe's
     `result_item_id`.
   - Location: `tests/unit/domains/adventure/test_craft_upgrade_execution.py` (new) or
     `tests/unit/economy/test_crafting.py` if such a file already exists (check at Implement time).

4. **`test_harvesting_project_produces_resource_harvested_event`**
   - Category: integration
   - Verifies: a full-pipeline run (using `AuthoritativeApplyPipeline`/`pipeline.py`'s tick loop, not
     hand-constructed state) with an entity positioned near a resource node and no competing
     higher-utility `GoalKind` present produces a state diff that `event_extractor.py` translates
     into a `resource_harvested` `SimulationEvent`. This is the direct test for AC's "real
     calibration run... produces a real event" requirement, at integration-test scale rather than a
     full calibration run.
   - Location: `tests/integration/domains/adventure/test_harvest_to_event.py` (new) or
     `tests/integration/pipeline/` if Plan prefers grouping with other event-derivation integration
     tests.

5. **`test_two_project_systems_do_not_silently_clobber_each_other`**
   - Category: unit / architecture guard
   - Verifies: when both System A (`adventure_decision`) and System B (`strategic_intelligence`)
     produce a `StrategicUpdate` for the same entity in the same tick, the merged result
     (`StrategicUpdate.merge`, `src/core/updates.py:530-566`) is the one Plan's chosen fix shape
     intends — i.e. either explicitly documents/tests that System B wins (current last-write-wins
     behavior) or, if Plan changes the merge/ownership model, tests the new explicit rule. This
     closes Open Question 1 from `investigation.md` with a concrete regression guard rather than
     leaving it implicit.
   - Location: `tests/unit/strategic/test_strategic_cognition_regression.py` or a new
     `tests/unit/strategic/test_project_system_precedence.py`.

6. **`test_craft_item_opportunity_is_generated`** (only if Open Question 3 confirms the gap is
   real)
   - Category: unit
   - Verifies: some opportunity/candidate-generation path actually produces a `RouteFamily.CRAFT_UPGRADE`
     `AdventureRouteOption` under realistic entity/world conditions (entity has a known recipe,
     lacks the crafted item, is near a blacksmith/forge). If Plan finds no such provider exists,
     this test instead documents the newly-added provider's behavior.
   - Location: `tests/unit/domains/adventure/test_phase3_route_generator.py` (extend existing file)
     or `tests/unit/world/test_craft_opportunity_provider.py` (new, if a new provider is added).

7. **`test_objective_intent_resolver_is_reachable_from_production_pipeline`** (only if Plan chooses
   fix shape (b) — wiring `ObjectiveIntentResolver` into production)
   - Category: architecture guard
   - Verifies: `ObjectiveIntentResolver.resolve` is called somewhere reachable from
     `src/engine/pipeline.py`'s tick loop (not just from its own unit test) — a grep-based or
     call-graph-based guard preventing this bridge from silently becoming orphaned again.
   - Location: `tests/integrity/test_logic_guards.py` (extend) or new
     `tests/integrity/test_objective_execution_reachability.py`.

## Scoped Pytest Commands

```bash
# Tactical / combat regression (tactical.py is shared with combat target-selection)
pytest tests/unit/tactical/ tests/unit/combat/ tests/unit/movement/ -v

# Adventure domain (System A) regression
pytest tests/unit/domains/adventure/ tests/integration/domains/adventure/ tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py -v

# Strategic cognition (System B) regression
pytest tests/unit/strategic/ tests/integration/pipeline/test_strategic_cadence.py -v

# Perf budget guard (adventure decision phase)
pytest tests/perf/test_phase3_adventure_decision_budget.py tests/perf/test_perf_strategic.py -v

# Architecture / integrity guard
pytest tests/integrity/test_logic_guards.py -v

# New tests added by this ticket (adjust paths to match final Implement placement)
pytest tests/unit/tactical/test_objective_pursuit_coverage.py tests/unit/domains/adventure/test_craft_upgrade_execution.py tests/integration/domains/adventure/test_harvest_to_event.py -v
```

Do not run `pytest tests/` (repo-wide). Do not scope only to `tests/unit/strategic/` — the fix
touches `tactical.py`, which is shared infrastructure for combat, movement, and the Adventure
domain; all four regression groups above must be run.

## Anti-Drift Test Guards

- **Combat target-selection must not regress.** `tactical.py`'s "Pillar 5.1: Objective Pursuit"
  branch (lines 205-282) sits inside the same `evaluate_entity_intent` method as combat target
  selection, kiting, bracketing, and anti-stalemate logic (lines 321-666). Any edit to the
  objective-pursuit branch must re-run the full combat/tactical regression group, not just
  strategic-cognition tests, to catch accidental control-flow changes to the hostile-handling
  branches earlier in the same method.
- **`ObjectiveKind.REACH_LOCATION`'s existing node/building disambiguation must not change
  behavior.** `tactical.py:216-237` already correctly handles `TRAIN_SKILL`, `SCOUT_LOCATION`,
  `FORM_PARTY`, `PROTECT_TARGET` (all map to `REACH_LOCATION` via `RouteToProjectMapper`) plus
  System B's hardcoded `reach_location` objectives for every `GoalKind`. A guard test should assert
  these continue to resolve identically (same target type, same distance-gate behavior) after the
  fix — do not let a CRAFTING/HARVESTING-specific fix accidentally widen or narrow the
  `REACH_LOCATION` branch's existing semantics.
- **`GoalKind` must not silently gain a `CRAFTING`/`TRADE` member without a corresponding scorer.**
  If Plan's fix shape adds new `GoalKind` values, a test should assert `GoalRegistry` has a
  registered scorer for every `GoalKind` member (an enum/registry-completeness guard) — this exact
  class of gap (enum member exists, no registered handler) is the ticket's own root-cause shape and
  should not be reintroduced one layer up.
- **`ObjectiveIntentResolver`'s existing unit test behavior must not change** if it gets wired into
  production — `tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py` currently
  tests it in isolation; if Implement wires it into the pipeline, re-run this file specifically to
  confirm its mapping table (`ACQUIRE_ITEM → REQUEST_CRAFT`, etc.) is unchanged, since production
  wiring should not require behavior changes to an already-correct resolver.
- **`EconomyScorer` event-type coverage must not be touched.** Per ticket Out of Scope; a guard is
  simply "no diff touches `src/simulation_quality/scorers/economy.py`" — verify at review time, not
  a pytest assertion.
- **Merge-order guard (Open Question 1).** If the fix changes how System A and System B's
  `StrategicUpdate`s combine for the same entity/tick (rather than leaving last-write-wins as-is),
  add an explicit unit test asserting the new precedence rule — do not leave this as an emergent,
  untested property of phase ordering in `pipeline.py`, which is exactly how the current gap went
  undetected.
