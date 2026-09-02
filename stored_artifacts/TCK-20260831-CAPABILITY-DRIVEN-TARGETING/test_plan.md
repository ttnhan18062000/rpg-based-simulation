---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260831-CAPABILITY-DRIVEN-TARGETING
artifact_type: test_plan
tags: [cognition, combat]
---

# Test Plan — TCK-20260831-CAPABILITY-DRIVEN-TARGETING

## Regression Surface

Existing tests that must keep passing, grouped by domain:

**Unit — tactical target selection / engagement (`src/engine/tactical.py` consumers):**
- `tests/unit/combat/test_target_selection_contract.py` — `select_best_target()`'s own `(hp, dist,
  id)` tuple; untouched method, must stay byte-identical (this ticket does not touch
  `select_best_target`).
- `tests/unit/combat/test_tactical_hardening.py` — `test_tactical_trust_obedience` exercises
  `target_score()` directly via `evaluate_entity_intent()` with two hostiles both `.kind("monster")`
  (identical enemy id → capability signal is a constant across both candidates in this fixture, per
  investigation.md Risk 3 — existing HP/distance/group-bias ordering must still decide the outcome);
  `test_protector_guarding` (no hostiles, unaffected); `test_frozen_state_mutation_tripwire` (n/a,
  different file).
- `tests/unit/combat/test_anti_stalemate.py` — stalemate-break behavior; hostiles constructed with
  uniform `.kind("hero")`/faction setup, must not regress under the new sort key.
- `tests/unit/combat/test_engagement_behavior.py`, `tests/unit/combat/test_tactical_legality.py`,
  `tests/unit/combat/test_tactical_wound_scar_wiring.py` — hostile fixtures use `.kind("monster")`
  uniformly; cover-seeking, retreat, and wound/scar-distress branches downstream of target selection
  must be unaffected by the new signal being a no-op/constant in these fixtures.
- `tests/unit/tactical/test_target_stickiness.py`, `tests/unit/tactical/test_objective_pursuit_coverage.py`
  — hysteresis (`is_current_target`) and non-hostile objective-pursuit branches; must not regress.
- `tests/unit/movement/test_tactical_movement.py`, `tests/unit/movement/test_mob_leashing.py` —
  movement/leash decisions downstream of `evaluate_entity_intent()`.
- `tests/unit/social/test_domain_7_social.py` — `test_tactical_trust_obedience`-adjacent group/trust
  scenarios (focus-fire bias) — must keep resolving the same way.
- `tests/unit/core/test_read_only_guard.py` — frozen-state mutation tripwire wrapping
  `TacticalDecisionSystem.evaluate_entity_intent`; guards against any new write-back introduced by
  this ticket.
- `tests/integration/combat/test_relation_combat_integration.py`,
  `tests/integration/strategic/test_occupation_change_reachability.py` — end-to-end scenarios
  through `evaluate_entity_intent()`.
- `tests/integrity/test_logic_guards.py` — references `tactical.py`'s Pillar 5.1 objective-pursuit
  branch; must remain accurate.

**Unit — capability estimation (must remain untouched, per AC3):**
- `tests/unit/cognition/test_phase2_capability_estimate_service.py` — combat/travel/gather/craft
  formulas, `None` context → empty; exercises `capability_estimate.py` directly and is unaffected as
  long as that file is not modified.

**Unit — self-model phase (must remain untouched — confirms the "never populated" gap is not
silently fixed by this ticket):**
- `tests/unit/cognition/test_phase2_self_model_phase.py` — asserts `capability_context=` behavior at
  the `run()` level; must still show `capability_context is None` is the default/production behavior
  after this ticket (no upstream `SelfModelUpdatePhase.apply()` wiring added).

**Integration:**
- `tests/integration/scenarios/test_phase2_self_model_scenarios.py` — capability-estimate trace
  event emission (unit-level, `capability_context` passed explicitly by the test itself, unrelated
  call path to this ticket's ad-hoc `tactical.py` call).

**Arena-combat:** No dedicated arena-combat suite directory was found scoped narrowly to this
mechanism; the combat/tactical unit and integration suites above are the closest equivalent and are
the ones that exercise real multi-hostile target-selection outcomes end-to-end.

## New Tests Required

Per acceptance criteria (exact tuple placement/polarity to be finalized by Plan — see
investigation.md Risk 1; tests below assert on the *presence and directionality* of the new signal's
effect, not a hardcoded tuple index):

1. **`test_target_score_reflects_capability_estimate_for_differentiated_enemy_kinds`**
   - Category: unit
   - Verifies: given two hostiles with *different* `.kind(...)` values (e.g. `"goblin"` vs
     `"dragon"`, both `_ENEMY_DANGER`-known ids with very different danger ratings) at otherwise
     identical HP/distance/group-bias, `target_score()`'s ordering differs from what it would be
     without the capability-driven term — i.e. the sort outcome is provably influenced by
     `CapabilityEstimateService.estimate(...).combat.enemy_type.<kind>`, not purely HP/distance/id.
     Directly satisfies AC1.
   - Location: `tests/unit/combat/test_capability_driven_targeting.py` (new file)

2. **`test_target_score_unaffected_when_all_hostiles_share_the_same_kind`**
   - Category: unit, regression-confirming
   - Verifies: for multiple hostiles sharing the same `.kind(...)` (the shape of every pre-existing
     fixture, per investigation.md Risk 3), the capability-driven term is constant across candidates
     and the pre-existing HP/distance/group-bias ordering decides the outcome unchanged — directly
     substantiates why the existing regression suite is expected to keep passing.
   - Location: `tests/unit/combat/test_capability_driven_targeting.py`

3. **`test_target_score_capability_estimate_derived_from_acting_entitys_own_stats`**
   - Category: unit
   - Verifies: two otherwise-identical acting entities with different `combat.atk`/`combat.hp`
     facing the same single hostile kind produce different capability-driven scoring contributions —
     confirms the estimate is read from the *entity itself* (the one making the tactical decision),
     not from the hostile, consistent with `CapabilityEstimateService.estimate(entity, ...)`'s
     signature.
   - Location: `tests/unit/combat/test_capability_driven_targeting.py`

4. **`test_target_score_does_not_mutate_entity_self_model`**
   - Category: architecture guard
   - Verifies: calling `evaluate_entity_intent()` for an entity with multiple, differently-kinded
     hostiles present does not change `entity.self_model.capabilities.estimates` (still
     empty/unchanged before and after) — confirms the ad-hoc `CapabilityEstimateService.estimate()`
     call is local and read-only, never written back to durable entity state (CLAUDE.md durable-state
     rule, AC3's "stays read-only" requirement).
   - Location: `tests/unit/combat/test_capability_driven_targeting.py`

5. **`test_comb254_legality_filter_still_runs_after_capability_scored_sort`**
   - Category: unit, architecture guard (AC4)
   - Verifies: with hostiles ordered such that the capability-driven top-of-sort candidate is
     positioned illegally (e.g. out of range/LoS) while a lower-priority-by-score candidate is
     legal, `evaluate_entity_intent()` still selects the *legal* candidate for the actual
     attack/pursuit decision — proving `LegalityServiceV2.verify_attack_legality()`
     (`tactical.py:433-443`, COMB-254) still runs unchanged and is not bypassed by the re-scored
     sort. Directly satisfies AC4 and guards SOC-185/COMB-254.
   - Location: `tests/unit/combat/test_capability_driven_targeting.py`

6. **`test_target_score_reads_only_entity_owned_and_hostile_kind_data`**
   - Category: unit, architecture guard (information-opacity boundary)
   - Verifies: the capability-driven contribution changes only in response to the acting entity's
     own `combat`/`stamina`/`identity` fields and the candidate hostile's `kind` — not any unrelated
     `state`-level field the entity has no access to (mirrors the analogous guard the adventure
     scoring precedent added, `test_capability_confidence_reads_only_entity_owned_fields`).
   - Location: `tests/unit/combat/test_capability_driven_targeting.py`

7. **`test_target_score_capability_signal_is_deterministic`**
   - Category: unit, determinism guard
   - Verifies: calling `target_score()`/`evaluate_entity_intent()` twice with identical inputs
     (same entity, same hostiles, same tick) produces an identical sort outcome and identical
     resulting `EntityUpdate`.
   - Location: `tests/unit/combat/test_capability_driven_targeting.py`

8. **`test_capability_estimate_service_unit_tests_unchanged`** — not a new test to write; instead a
   Verify-time diff check that `tests/unit/cognition/test_phase2_capability_estimate_service.py` and
   `src/cognition/capability_estimate.py` are byte-identical to their pre-ticket state, satisfying
   AC3's "existing ... unit tests pass unchanged" literally, not just "still green."

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/combat/ tests/unit/tactical/ tests/unit/movement/test_tactical_movement.py tests/unit/movement/test_mob_leashing.py -v
.venv/bin/python3 -m pytest tests/unit/cognition/test_phase2_capability_estimate_service.py tests/unit/cognition/test_phase2_self_model_phase.py -v
.venv/bin/python3 -m pytest tests/unit/social/test_domain_7_social.py tests/unit/core/test_read_only_guard.py -v
.venv/bin/python3 -m pytest tests/integration/combat/test_relation_combat_integration.py tests/integration/strategic/test_occupation_change_reachability.py tests/integration/scenarios/test_phase2_self_model_scenarios.py -v
```

Never `pytest tests/` — scoped to combat/tactical, capability estimation, and self-model phase
domains, matching the precedent ticket's scoping pattern.

## Anti-Drift Test Guards

- **`test_target_score_does_not_mutate_entity_self_model`** (New Test 4) directly guards against the
  new ad-hoc call silently drifting into writing back to `entity.self_model.capabilities` — which
  would falsely imply the upstream "never populated" gap was fixed when it wasn't (mirrors the
  precedent's identical guard).
- **`test_comb254_legality_filter_still_runs_after_capability_scored_sort`** (New Test 5) is the
  primary guard against the highest-risk regression class for this ticket: the capability signal
  reordering candidates in a way that silently bypasses or weakens the post-sort legality filter,
  which would violate both COMB-254 and SOC-185 (both `P0`, `verified`).
- **`test_target_score_unaffected_when_all_hostiles_share_the_same_kind`** (New Test 2) is the
  concrete, evidence-backed explanation for why the full existing regression suite (all of which
  uses uniform hostile `kind`s) is expected to stay green — if this test starts failing, it signals
  the new term was implemented as more than an additive/conditional signal (e.g. it started reading
  something other than `h.kind`/entity stats), a genuine scope-creep or implementation-drift signal.
- Existing `tests/unit/cognition/test_phase2_capability_estimate_service.py` running **unchanged**
  (byte-diff confirmed at Verify, not just green) is the primary guard for AC3.
- Existing `tests/unit/cognition/test_phase2_self_model_phase.py` continuing to show
  `capability_context` defaulting to `None` at the `apply()`/production level guards against
  silently introducing upstream `SelfModelUpdatePhase` wiring without an explicit Plan decision
  (Out of Scope per the ticket).
- **`test_target_selection_contract.py` running unchanged** guards `select_best_target()` staying
  untouched — a distinct, easily-conflated method this ticket must not modify.
- A new parity ledger entry's `test_path` (see investigation.md "Docs Requiring Update") should list
  the new `tests/unit/combat/test_capability_driven_targeting.py` file in the same commit that adds
  the entry — a parity entry added without a real, passing `test_path` is itself a drift signal
  Verify should catch, especially given COMB-254/SOC-185's own pre-existing `test_path: null` gap
  should not be repeated for the new entry.
