---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING
artifact_type: test_plan
tags: [cognition, adventure, self-model]
---

# Test Plan — TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING

## Regression Surface

Existing tests that must keep passing, grouped by domain:

**Unit — adventure scoring (`src/domains/adventure/scoring.py` consumers):**
- `tests/unit/domains/adventure/test_phase3_route_scoring.py` — personality bias, greed/sociability weights, determinism, hidden-world-truth guard
- `tests/unit/domains/adventure/test_depletion_scoring.py` — `GATHER_RESOURCE` depletion-fraction multiplier via `resource_nodes`/`target_node_id` (same data path this ticket reuses for the capability key)
- `tests/unit/domains/adventure/test_memory_informed_scoring.py` — sibling ticket's `memory_adjustment` term; must not regress when `confidence_bonus` formula changes
- `tests/unit/domains/adventure/test_scoring_plan_bonus.py` — `plan_advance_bonus` term
- `tests/unit/faction/test_faction_directive_propagation.py` — faction-directive urgency boosts inside `score()`
- `tests/unit/social/test_party_lifecycle.py` — `FORM_PARTY`-related scoring assertions

**Unit — capability estimation (must remain untouched, per AC3):**
- `tests/unit/cognition/test_phase2_capability_estimate_service.py` — combat/travel/gather/craft formulas, `None` context → empty; these exercise `capability_estimate.py` directly and are unaffected by scoring.py-side changes as long as `capability_estimate.py` is not modified.

**Unit — self-model phase (must remain untouched — confirms the "never populated" gap is not silently fixed by this ticket):**
- `tests/unit/cognition/test_phase2_self_model_phase.py` — asserts `capability_context=` behavior at the `run()` level; must still show `capability_context is None` is the default/production behavior after this ticket (i.e. no upstream wiring added under option (b)).

**Integration:**
- `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py` — end-to-end route decision scenarios
- `tests/integration/scenarios/test_entity_differentiation.py` — bravery-quartile / route behavior differentiation
- `tests/integration/scenarios/test_phase2_self_model_scenarios.py` — capability-estimate trace event emission (unit-level, `capability_context` passed explicitly by the test itself)
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` — `AdventureGoalScorer` wrapper call chain (must remain unaffected — no new params through this layer)

**Arena-combat:** None directly — this ticket does not touch combat resolution. If `HUNT_WEAK_ENEMY` mapping is included (per Plan's decision on Risk 1), confirm it has no observable effect on arena-combat suites since the route family remains dead code in `generator.py`.

## New Tests Required

Per acceptance criteria (assumes Plan adopts the recommended option (b), scoped to `GATHER_RESOURCE` + `CRAFT_UPGRADE`; adjust family coverage if Plan decides otherwise):

1. **`test_gather_resource_confidence_reflects_capability_estimate`**
   - Category: unit
   - Verifies: for a `GATHER_RESOURCE` route with `target_node_id` resolving to a `ResourceNodeState`, `confidence_bonus` differs from the flat `route.confidence × 0.15` value and instead reflects `CapabilityEstimateService.estimate(entity, context=CapabilityContext(gather_resources=(node.kind,)))`'s `gather.resource.<kind>` estimate — e.g. entity with the required tool present scores higher than an otherwise-identical entity missing it.
   - Location: `tests/unit/domains/adventure/test_capability_confidence_scoring.py` (new file, following `test_memory_informed_scoring.py`'s naming/structure precedent)

2. **`test_craft_upgrade_confidence_reflects_capability_estimate`**
   - Category: unit
   - Verifies: for a `CRAFT_UPGRADE` route whose `requirements` tuple carries a `Requirement(kind="recipe_known", subject=<recipe_id>)`, `confidence_bonus` reflects the crafting capability estimate (e.g. entity holding required materials scores higher than one missing them) rather than the flat term.
   - Location: `tests/unit/domains/adventure/test_capability_confidence_scoring.py`

3. **`test_capability_confidence_falls_back_to_flat_term_for_unmapped_families`**
   - Category: unit
   - Verifies: for a family with no capability-key mapping (e.g. `RECOVER`, `BUY_UPGRADE`, `ASK_INFORMATION`, `FORM_PARTY`), `confidence_bonus` is unchanged — still exactly `route.confidence × 0.15` — confirming the change is additive/conditional, not a wholesale formula replacement.
   - Location: `tests/unit/domains/adventure/test_capability_confidence_scoring.py`

4. **`test_capability_confidence_extraction_failure_falls_back_safely`**
   - Category: unit, edge case / failure mode
   - Verifies: `CRAFT_UPGRADE` route with malformed/missing `recipe_known` requirement (or `GATHER_RESOURCE` route with `target_node_id=None` / missing entry in `resource_nodes`) does not raise and falls back to the flat `route.confidence × 0.15` term — per Risk 3's recommended defensive-fallback behavior.
   - Location: `tests/unit/domains/adventure/test_capability_confidence_scoring.py`

5. **`test_capability_confidence_does_not_mutate_entity_self_model`**
   - Category: architecture guard
   - Verifies: calling `AdventureRouteScorer.score()` with a `GATHER_RESOURCE`/`CRAFT_UPGRADE` route does not change `entity.self_model.capabilities.estimates` (still empty/unchanged before and after) — confirms the ad-hoc `CapabilityEstimateService.estimate()` call is a local, read-only, throwaway computation, never written back to durable entity state (CLAUDE.md durable-state rule).
   - Location: `tests/unit/domains/adventure/test_capability_confidence_scoring.py`

6. **`test_capability_confidence_reads_only_entity_owned_fields`**
   - Category: architecture guard (information-opacity boundary, mirrors `test_scoring_does_not_use_hidden_world_truth` in `test_phase3_route_scoring.py`)
   - Verifies: the capability-driven `confidence_bonus` computation reads only `entity`-derived data (combat/stamina/inventory/equipment) and the already-existing `resource_nodes`/route-local data — not any new `state`-level omniscient field. Can be structured as: two entities with identical `resource_nodes`/route input but different self-owned stats produce different `confidence_bonus`, while a change to an unrelated/hidden `state` field the entity has no access to does not.
   - Location: `tests/unit/domains/adventure/test_capability_confidence_scoring.py`

7. **`test_capability_confidence_is_deterministic`**
   - Category: unit (determinism guard, mirrors `test_route_scoring_is_deterministic`)
   - Verifies: calling `score()` twice with identical inputs for a capability-mapped route produces an identical `confidence_bonus`/`score`.
   - Location: `tests/unit/domains/adventure/test_capability_confidence_scoring.py`

8. **(Conditional on Plan's Risk-1 decision) `test_hunt_weak_enemy_confidence_capability_mapped_but_dead_code`**
   - Category: unit, explicitly disclosed dead-code coverage
   - Verifies: if Plan decides to include `HUNT_WEAK_ENEMY`/`combat.enemy_type.*`, this test proves the mapping is correct at the unit level while its docstring explicitly states (mirroring `test_memory_informed_scoring.py`'s docstring pattern) that `HUNT_WEAK_ENEMY` has zero observable effect via a live `generate()` → `score()` chain today.
   - Location: `tests/unit/domains/adventure/test_capability_confidence_scoring.py`, only if in scope.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/domains/adventure/ tests/unit/cognition/test_phase2_capability_estimate_service.py tests/unit/cognition/test_phase2_self_model_phase.py -v
.venv/bin/python3 -m pytest tests/unit/ai/goals/test_adventure_goal_scorer.py tests/unit/faction/test_faction_directive_propagation.py tests/unit/social/test_party_lifecycle.py -v
.venv/bin/python3 -m pytest tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py tests/integration/scenarios/test_entity_differentiation.py tests/integration/scenarios/test_phase2_self_model_scenarios.py -v
```

Never `pytest tests/` — scoped to adventure scoring + capability estimation + self-model phase domains, matching the sibling memory-informed ticket's scoping pattern.

## Anti-Drift Test Guards

- **`test_capability_confidence_does_not_mutate_entity_self_model`** (New Test 5) directly guards against option (b) silently drifting into writing back to `entity.self_model.capabilities` — which would falsely imply the upstream "never populated" gap was fixed when it wasn't.
- **`test_capability_confidence_falls_back_to_flat_term_for_unmapped_families`** (New Test 3) guards against scope creep into families with no evidence-backed capability-key source (`BUY_UPGRADE`, `RECOVER`, `ASK_INFORMATION`, `FORM_PARTY`, `TAKE_EASY_QUEST`, `QUEST_OPPORTUNITY`, etc.) silently gaining an ad-hoc, unjustified mapping.
- Existing `test_phase2_capability_estimate_service.py` suite running **unchanged** (no edits to that file, confirmed by diff review at Verify time) is itself the primary guard for AC3.
- Existing `test_phase2_self_model_phase.py` continuing to show `capability_context` defaulting to `None` at the `apply()`/production level guards against silently introducing option (a)-style upstream wiring without an explicit Plan decision.
- **`test_capability_confidence_reads_only_entity_owned_fields`** (New Test 6) guards the information-opacity boundary the whole `scoring.py` module is built on — the same class of guard `test_scoring_does_not_use_hidden_world_truth` already provides for the rest of the file.
- STRAT-227 parity ledger entry's `test_path` should list every new test file added here in the same commit that changes `v2_evidence`/`text` — a lagging parity ledger update on a `verified`/`P1` entry is itself a drift signal Verify should catch.
