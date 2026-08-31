---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260824-TOWN-CENTER-POINTER-FIX
artifact_type: test_plan
tags: [world, determinism]
---

# Test Plan — TCK-20260824-TOWN-CENTER-POINTER-FIX

## Regression Surface

Existing tests that must keep passing, grouped by domain (found via
`grep -rln "town_center" tests/` plus the direct callers of every changed function):

**World compilation / generation (unit)**
- `tests/unit/worldbuilding/test_world_compiler.py` — no existing `town_center` assertions
  (confirmed by grep); must keep passing unmodified except for new additions.
- `tests/unit/worldgeneration/test_generator.py` — covers `WorldProceduralGenerator`'s own
  town-region carving (`+/-15` bounds); this ticket does not touch the generator, only the
  compiler, so these must be untouched.
- `tests/unit/worldassembly/test_assembly.py`, `tests/unit/worldassembly/test_corpus_diversity.py`
  — module-composition region-merge paths, including multi-settlement compositions.
- `tests/integration/worldassembly/test_e2e_smoke.py`,
  `tests/integration/worldassembly/test_real_content_world_compositions.py` — exercises real
  composition YAMLs including `urban_political.yaml` (two town-type regions).

**Navigation / movement (unit)**
- `tests/unit/movement/test_flow_field_navigation.py` — `test_flow_field_long_distance` (currently
  passes for the wrong reason — `town_center` coincidentally equals `ANCHORS["TOWN"][0]`; must
  still pass after the fix, since the two values will remain equal in that test's own setup) and
  `test_local_navigation_fallback`.
- `tests/perf/test_lod.py` — `DeterministicScheduler.select_work()`'s `focus_points` usage.

**Strategic / tactical (unit + integration)**
- `tests/unit/strategic/test_expanded_goals.py` — `TownScorer`/`RecoverScorer`/
  `ResolveBlockerScorer` goal-scoring and `test_town_return_project_now_produces_real_navigation`
  (constructs `AuthoritativeState` directly with explicit `town_center=(0.0,0.0)` — unaffected by
  the `WorldCompiler` fix, must still pass unmodified).
- `tests/unit/tactical/test_objective_pursuit_coverage.py` — `_resolve_target_position()`'s
  `target_position` fallback tests (STRAT-249's regression suite) — this ticket does not change
  `_resolve_target_position()`, must be untouched.
- `tests/unit/strategic/test_opportunities.py`, `tests/unit/strategic/test_interruption_resistance.py`,
  `tests/unit/strategic/test_committed_intention_materialization.py`,
  `tests/unit/strategic/test_cognition_immediate_fixes.py`,
  `tests/unit/strategic/test_threat_resolved_lock_release.py`,
  `tests/unit/strategic/test_fused_strategic_pass_routing_family.py`,
  `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py` — general strategic
  pass regression surface touched indirectly by `intelligence.py` changes.
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` — `AdventureGoalScorer`'s `RECOVER`/
  `ASK_INFORMATION` families reading `state.town_center` directly.

**Town / world services (unit)**
- `tests/unit/world/test_home_storage.py` — constructs `town_center=(0,0)` explicitly; unaffected
  by the compiler fix, must stay passing unmodified.
- `tests/unit/world/test_town_building_contract.py` — same, `town_center=(0,0)` explicit
  construction.

**Worker protocol / engine (unit)**
- `tests/unit/kernel/test_executor_parity.py`, `tests/integration/kernel/test_worker_determinism.py`,
  `tests/integration/kernel/test_authoritative_outcome_truth.py` — `WorkerPacket` construction and
  parity; must confirm removing (or repurposing) `WorkerPacket.town_center` does not break any
  `WorkerPacket(...)` construction call site or `ProtocolValidator` check
  (`src/core/protocol_validator.py`).
- `tests/unit/core/test_engine_integrity.py` — general `AuthoritativeState` field integrity checks.

**Determinism / fingerprint**
- `src/engine/checkpoint.py`'s canonical-data serialization includes `town_center` — any test
  asserting a fixed state-hash/fingerprint for a fixture world (search
  `tests/` for `StateFingerprinter`/`state_hash` assertions against a compiled-not-hand-built state)
  must be checked for drift once `town_center` stops being `(0.0, 0.0)` for real compiled worlds.

**Behavioral regression baseline**
- `tests/regression/test_behavioral_5k.py` against `tests/regression/baseline_5k.json` — uses
  `urban_political.yaml` among other compositions; must be spot-checked (not blindly re-baselined)
  since `town_center` was never previously read by anything visible in recorded baseline outputs
  per investigation.md Item 7, but the new field value itself changes state, so RNG-sequence drift
  risk is zero (no new RNG draws) while output-field drift risk needs confirmation.
- `tests/simulation_quality/test_grade_regression.py` against
  `tests/simulation_quality/fixtures/grade_anchors.json` — same caution.

## New Tests Required

Per acceptance criteria:

1. **`WorldCompiler.compile()` sets a real `town_center`**
   - Test name: `test_compile_sets_real_town_center_from_town_region`
   - Category: unit
   - Verifies: compiling a `WorldSpec` with one `type="town"` region produces
     `AuthoritativeState.town_center != (0.0, 0.0)` and equal to the chosen derivation rule's
     expected value (e.g. the town region's bounds centroid) — not left at the dataclass default.
   - Location: `tests/unit/worldbuilding/test_world_compiler.py`

2. **`WorldCompiler.compile()` multi-town-region derivation is deterministic and documented**
   - Test name: `test_compile_town_center_derivation_with_multiple_town_regions`
   - Category: unit
   - Verifies: compiling a `WorldSpec` with two `type="town"` regions (mirroring
     `urban_political.yaml`'s real shape) produces a `town_center` value matching whatever
     derivation rule the Plan phase settles on (first-region-by-declaration-order, or documents
     `town_center` as deprecated in favor of a lookup — test asserts whichever design was chosen,
     not left unassertable).
   - Location: `tests/unit/worldbuilding/test_world_compiler.py`

3. **`FlowFieldService.get_flow_direction(target_kind='TOWN', ...)` uses the real town location**
   - Test name: `test_get_flow_direction_town_uses_real_town_center_not_hardcoded_anchor`
   - Category: unit
   - Verifies: with `state.town_center` set to a position distinct from both hardcoded legacy
     anchors `(100,100)` and `(200,50)` (e.g. `(300.0, 300.0)`), `get_flow_direction` returns a
     direction vector pointing toward the real `town_center`, not toward either hardcoded anchor —
     the case the existing `test_flow_field_long_distance` cannot distinguish (per
     investigation.md's Item 3 finding).
   - Location: `tests/unit/movement/test_flow_field_navigation.py`

4. **`WorkerPacket.town_center` resolved — dead-state removal or real-consumer test**
   - Test name: `test_worker_packet_has_no_dead_town_center_field` (if removed) OR
     `test_worker_packet_town_center_has_real_consumer` (if wired to a real use)
   - Category: unit / architecture guard
   - Verifies: whichever resolution the Plan phase chooses — either `WorkerPacket` no longer
     declares `town_center` (and every construction site/test fixture is updated), or a concrete,
     newly-added consumer actually reads `packet.town_center` and the test proves the value flows
     end-to-end from `executor.py`'s packet construction into that consumer's decision.
   - Location: `tests/unit/kernel/test_worker_protocol.py` (create if it doesn't exist) or
     `tests/architecture/` if framed as an architecture guard against reintroducing dead state.

5. **`StrategicRedirectionSystem.enforce()` picks the nearest town tile to the requesting entity**
   - Test name: `test_redirection_enforce_targets_nearest_town_tile_not_arbitrary_sort`
   - Category: unit
   - Verifies: with `town_tiles` spanning two distinct town regions (e.g. one cluster near
     `(10,10)`, one near `(70,70)`), an entity near `(70,70)` carrying items gets redirected to a
     tile in the near cluster, not the globally-lowest-sorted tile from the far cluster (the current
     bug's observable symptom).
   - Location: `tests/unit/strategic/test_redirection.py` (create if it doesn't exist, else the
     existing redirection test file)

6. **`StrategicIntelligenceSystem`'s routine-blocker pass picks the nearest town tile**
   - Test name: `test_routine_blocker_pass_targets_nearest_town_tile_not_arbitrary_iter`
   - Category: unit
   - Verifies: same shape as test 5, but for `intelligence.py`'s `next(iter(state.town_tiles))`
     fallback — confirms it now also computes nearest-to-entity rather than arbitrary set-iteration
     order.
   - Location: `tests/unit/strategic/test_expanded_goals.py` or a dedicated
     `tests/unit/strategic/test_intelligence_routine_blockers.py`

7. **Anti-regression: nearest-tile fix does not change single-town-world behavior**
   - Test name: `test_redirection_and_routine_blocker_single_town_world_unaffected`
   - Category: unit (anti-drift guard)
   - Verifies: for a world with exactly one town region (the common case today), the nearest-tile
     computation produces the same target as before the fix — proving the fix is additive/correct
     for the dominant existing case, not just the new multi-town case.
   - Location: same files as tests 5/6

8. **End-to-end: real compiled world produces working town-return navigation**
   - Test name: `test_town_return_navigates_to_real_compiled_town_center` (integration,
     unmocked pipeline, mirroring `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`'s own
     `test_town_return_project_now_produces_real_navigation` but starting from a real
     `WorldCompiler.compile()` output instead of a hand-built `AuthoritativeState`)
   - Category: integration
   - Verifies: `WorldCompiler.compile()` → `TownScorer`/`evaluate_strategic_intent()` →
     `TacticalDecisionSystem.evaluate_entity_intent()` produces a `NavigationUpdate` toward the
     real compiled town location, not `(0.0, 0.0)` by coincidence.
   - Location: `tests/unit/strategic/test_expanded_goals.py` or
     `tests/integration/worldassembly/` (whichever the Implement phase judges closer to the
     existing precedent test)

## Scoped Pytest Commands

```
# World compilation / generation
pytest tests/unit/worldbuilding/test_world_compiler.py tests/unit/worldgeneration/ tests/unit/worldassembly/ -v

# Navigation / movement
pytest tests/unit/movement/ tests/perf/test_lod.py -v

# Strategic / tactical
pytest tests/unit/strategic/ tests/unit/tactical/ tests/unit/ai/goals/ -v

# Town / world services
pytest tests/unit/world/test_home_storage.py tests/unit/world/test_town_building_contract.py -v

# Worker protocol / kernel
pytest tests/unit/kernel/ tests/integration/kernel/ tests/unit/core/test_engine_integrity.py -v

# World assembly integration (multi-town composition path)
pytest tests/integration/worldassembly/ -v

# Behavioral regression baseline (spot-check, not blind re-run — inspect diffs manually)
pytest tests/regression/test_behavioral_5k.py tests/simulation_quality/test_grade_regression.py -v
```

Never `pytest tests/` — always scoped to the domains above, per project testing rules.

## Anti-Drift Test Guards

- **`test_redirection_and_routine_blocker_single_town_world_unaffected`** (test 7 above) —
  guards against the nearest-tile fix silently changing behavior for the dominant single-town case
  while fixing the multi-town case.
- **A dedicated architecture-guard test asserting `WorkerPacket`'s field set has no unread fields**
  (or, minimally, a test that fails if `town_center` is re-added to `WorkerPacket` without a real
  consumer) — prevents the dead-duplicate-state pattern from silently reappearing.
- **`test_get_flow_direction_town_uses_real_town_center_not_hardcoded_anchor`** must use a
  `town_center` value distinct from *both* `ANCHORS["TOWN"]` entries (`(100,100)` and `(200,50)`) —
  a value matching either would mask the fix the same way the existing test currently does.
- **Behavioral baseline spot-check** (`baseline_5k.json`, `grade_anchors.json`) — must be diffed
  field-by-field after the fix, not treated as "no RNG draws changed so nothing changed"; the new
  `town_center` value itself is new observable state even though it triggers no new RNG consumption.
- **`urban_political.yaml`-based integration test** (`test_real_content_world_compositions.py`) must
  keep passing with the multi-town derivation rule the Plan phase chooses — this is the one real
  fixture that actually exercises the two-town-region path end-to-end, so it is the load-bearing
  guard against a derivation rule that only works for single-town worlds.
