---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING
artifact_type: test_plan
tags: [cognition, adventure]
---

# Test Plan — TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING

## Regression Surface

Existing tests that must keep passing (all under `tests/unit/domains/adventure/` unless noted — no test currently constructs an entity with non-empty `cognition.memory.causal.entries`, so a correctly-implemented memory term must be a strict no-op by default/absence):

**Unit — `AdventureRouteScorer`:**
- `tests/unit/domains/adventure/test_phase3_route_scoring.py` — personality bias, need urgency, determinism, E11C weight-calibration tests (`test_greed_weight_is_0_50_on_gather_route`, `test_sociability_weight_is_0_40_on_form_party_route`, etc.)
- `tests/unit/domains/adventure/test_depletion_scoring.py` — GATHER_RESOURCE depletion-fraction multiplier
- `tests/unit/domains/adventure/test_hero_quest_scoring.py` — QUEST_OPPORTUNITY capability-match scaling
- `tests/unit/domains/adventure/test_scoring_plan_bonus.py` — `plan_advance_bonus` term (E61C)
- `tests/unit/domains/adventure/test_craft_upgrade_execution.py`
- `tests/unit/domains/adventure/test_abandonment_rate.py`

**Unit — `AdventureRouteGenerator`:**
- `tests/unit/domains/adventure/test_phase3_route_generator.py`
- `tests/unit/domains/adventure/test_phase3_route_families.py`

**Integration / boundary:**
- `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py`
- `tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py`
- `tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py`
- `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py`
- `tests/unit/domains/adventure/test_eligibility_cognition_profile.py`
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` (legacy-named; still exercises the live `AdventureGoalScorer`/`decide()` chain per prior epic tickets)

**Memory domain (must stay green — untouched by this ticket, but shares `CausalMemoryEntry`/`CausalAttributionService`):**
- `tests/integration/domains/memory/test_phase13_memory_update_phase.py`
- `tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py`
- Any `tests/unit/domains/memory/` file exercising `CausalAttributionService.attribute()` (confirm exact list at implementation time via `find tests/unit/domains/memory/ -name '*.py'`)

## New Tests Required

Per AC1 ("A route family whose `CausalMemoryEntry.future_advice` already exists... measurably suppresses/promotes the matching route family's score/benefit vs. an entity with no matching causal memory") — scope the new tests to whatever mapping Plan actually decides (see investigation.md Risk #1); the two AC-named cases below are the minimum, non-negotiable set:

1. **`test_avoid_enemy_advice_suppresses_[mapped_family]_score`**
   - Category: unit
   - Verifies: an entity with a `CausalMemoryEntry(event_kind="combat_loss", future_advice=("avoid_enemy",), ...)` in `cognition.memory.causal.entries` scores the mapped route family strictly lower than an otherwise-identical entity with empty `cognition.memory.causal.entries`, for an identical `AdventureRouteOption`.
   - Must also assert the *documented dead-code caveat* if `HUNT_WEAK_ENEMY` is the chosen mapping (see investigation.md Risk #1) — i.e. the test proves the scoring-level suppression works even though `AdventureRouteGenerator` never emits this family live; do not silently pick a different family to dodge the caveat without Plan sign-off.
   - Location: `tests/unit/domains/adventure/test_memory_informed_scoring.py` (new file)

2. **`test_boost_party_trust_advice_promotes_form_party_score`**
   - Category: unit
   - Verifies: an entity with `CausalMemoryEntry(event_kind="party_abandoned", future_advice=("boost_party_trust", "realign_directive"), ...)` scores `RouteFamily.FORM_PARTY` in the direction Plan decides (promote or suppress — assert whichever direction plan.md commits to; do not assume promote), strictly different from an entity with no matching entry.
   - Location: `tests/unit/domains/adventure/test_memory_informed_scoring.py`

3. **`test_no_matching_causal_memory_is_a_no_op`**
   - Category: unit (anti-drift/regression guard)
   - Verifies: an entity with a non-empty `cognition.memory.causal.entries` whose `future_advice` values do **not** match the route family under test produces an identical score to an entity with fully empty `cognition.memory` — proves the new term is additive/targeted, not a blanket bonus/penalty.
   - Location: `tests/unit/domains/adventure/test_memory_informed_scoring.py`

4. **`test_future_advice_tuple_with_multiple_values_handled`**
   - Category: unit (regression-prone edge case)
   - Verifies: a `CausalMemoryEntry` whose `future_advice` tuple has 2 elements (the real shape for `failed_search`/`failed_craft`/`party_abandoned` per `CausalAttributionService.attribute()`) is handled correctly — e.g. both mapped families adjust, or whichever behavior Plan specifies — not silently truncated to `future_advice[0]`.
   - Location: `tests/unit/domains/adventure/test_memory_informed_scoring.py`

5. **`test_memory_term_does_not_mutate_entity_cognition`**
   - Category: architecture guard (per CLAUDE.md's "Architecture tests: verify read-only logic did not mutate live state")
   - Verifies: `AdventureRouteScorer.score(entity, route)` returns without mutating `entity.cognition.memory` — assert `entity.cognition is entity_before.cognition` (identity check on the frozen dataclass) after the call, consistent with `scoring.py`'s existing read-only contract.
   - Location: `tests/unit/domains/adventure/test_memory_informed_scoring.py`

6. **`test_memory_term_reads_only_entity_local_state`** (documents/enforces the "subjective self-model" opacity boundary for the new code path)
   - Category: unit / boundary guard
   - Verifies: `AdventureRouteScorer.score()` produces the memory-informed adjustment using only `entity` (no new `state`-derived argument) — a signature/behavior check that the new code does not introduce a `state` read for this term, matching the documented "reads only subjective... aspects" boundary.
   - Location: `tests/unit/domains/adventure/test_memory_informed_scoring.py`

7. **`test_capacity_evicted_causal_entries_do_not_affect_scoring`** (edge case)
   - Category: unit
   - Verifies: a `CausalMemory` at its 30-entry capacity, where the relevant entry has already been evicted (per `MemoryUpdatePhase`'s FIFO eviction at phase.py:72-73), produces no suppress/promote effect — i.e. the scorer only ever sees `entries` as passed on `entity`, with no independent history lookup. (Mostly a documentation-of-intent test confirming the scorer is stateless per call.)
   - Location: `tests/unit/domains/adventure/test_memory_informed_scoring.py`

If Plan's mapping table (Risk #1) ends up covering more than the 2 AC-named advice strings (e.g. `heal_first`/`seek_trusted_guide`/`acquire_mats`), add one test per additional mapped family following the same promote/suppress-vs-no-op pattern as tests 1-3 above — do not leave an implemented mapping branch untested.

## Scoped Pytest Commands

```
pytest tests/unit/domains/adventure/ -v
pytest tests/integration/domains/adventure/ -v
pytest tests/integration/domains/memory/ tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py -v
```

Never `pytest tests/` — scoped to the adventure domain (primary change surface) plus the memory domain (regression surface for the shared `CausalMemoryEntry`/`CausalAttributionService` types, unmodified but load-bearing).

## Anti-Drift Test Guards

- **`test_no_matching_causal_memory_is_a_no_op`** (above) is the primary guard against the new term silently becoming a blanket score modifier instead of a targeted, advice-matched one.
- **Re-run `test_greed_weight_is_0_50_on_gather_route`, `test_sociability_weight_is_0_40_on_form_party_route`, and the E11C calibration tests** with an entity that has empty `cognition.memory` (the default `V2EntityBuilder` state, since `CognitionModel()` defaults to empty `MemoryModel()`) — these must produce byte-identical scores to before this ticket, proving the new term is correctly gated on non-empty matching memory only.
- **`test_memory_term_does_not_mutate_entity_cognition`** (above) guards against the new code accidentally writing to `entity.cognition` from inside the read-only scoring path — the one durable-state rule most directly at risk here, since `MemoryUpdatePhase` (the legitimate mutator) uses the same `dataclasses.replace` pattern this new code must NOT reach for.
- **Confirm `AdventureDecisionService.decide()` and `AdventureGoalScorer.score()` are untouched** by re-running `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py` and `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` unmodified — any diff required in either file is a scope-creep signal per the ticket's Out of Scope item 3.
- **STRAT-227 test_path guard**: whichever test file(s) end up covering the new memory term must be added to STRAT-227's `test_path` string in `docs/parity_ledger/strategic_cognition.yaml` in the same session (parity-updater phase) — verify post-implementation that the listed path(s) actually exist and actually pass, per the Authoritative Mechanics Rule's P0/P1 test_path requirement (STRAT-227 is P1).
- **Dead-code caveat guard**: if `HUNT_WEAK_ENEMY` is the family chosen for `avoid_enemy`, add an explicit assertion/comment in the new test tying back to `docs/simulation/domains/adventure_contract.md`'s documented dead-code note, so a future reader isn't misled into thinking this suppression is observable via `AdventureRouteGenerator.generate()` output in a live run.
