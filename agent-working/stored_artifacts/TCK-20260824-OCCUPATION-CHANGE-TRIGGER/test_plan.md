---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260824-OCCUPATION-CHANGE-TRIGGER
artifact_type: test_plan
tags: [combat, economy, social, world]
---

# Test Plan — TCK-20260824-OCCUPATION-CHANGE-TRIGGER

## Regression Surface

### Identity-event tests (AC: "All 4 existing identity-event tests still pass unmodified")
`tests/unit/observability/test_event_extractor_identity.py` contains 8 test functions, not 4 —
the AC's "4" most plausibly refers to the 4 *event types* ENTITY-007 groups as "4 new events" in
`docs/event_ledger/entity.yaml` (`entity_role_changed`, `entity_faction_changed`, `recipe_learned`,
`skill_cooldown_started`), not a literal test-function count. Flagged as a wording ambiguity, not
a blocker — all 8 must pass regardless:
- `test_entity_role_changed_fires_on_real_delta` (line 31) — **most directly exercised by this
  ticket**: currently exercises a hand-constructed role delta; once a real `role_set=` producer
  exists, this test's assertions must still hold for both hand-constructed and pipeline-produced
  deltas.
- `test_entity_faction_changed_fires_on_real_delta` (line 44)
- `test_recipe_learned_fires_on_new_entry` (line 57)
- `test_recipe_learned_does_not_fire_on_removal_or_no_change` (line 70)
- `test_skill_cooldown_started_fires_on_new_or_changed_entry` (line 88)
- `test_no_event_on_zero_delta` (line 101)
- `test_identity_events_suppressed_in_light_and_long_run_modes` (line 114)
- `test_recipe_learned_fires_through_real_kernel_tick_once` (line 129) — precedent for the new
  "real transition through a real `Kernel.tick_once()` run" test this ticket's AC #1 requires.

### The 12 confirmed role-reading consumers — existing tests that must keep passing unmodified
1. `src/world/spawn.py:55` (monster density) — `tests/unit/world/test_spawn_cadence.py`,
   `tests/unit/core/test_engine_integrity.py`
2. `src/engine/occupancy_snapshot.py:33-35` (tile priority) —
   `tests/unit/domains/optimization/test_occupancy_snapshot.py`,
   `tests/unit/domains/optimization/test_cache_invalidation_policy.py`
3. `src/engine/legality.py:504-505` (readiness priority) —
   `tests/unit/combat/test_phase5_combat_legality.py`,
   `tests/unit/combat/test_combat_legality_regression.py`
4. `src/systems/economy_systems/crafting.py:33` (required_role gate) —
   `tests/unit/world/test_economy_contract.py`
5. `src/domains/adventure/scoring.py` (GUARD/SHOPKEEPER/HERO route-scoring boosts) —
   `tests/unit/domains/adventure/test_phase3_route_scoring.py`,
   `tests/unit/domains/adventure/test_memory_informed_scoring.py`,
   `tests/unit/domains/adventure/test_capability_confidence_scoring.py`
6. `src/systems/world_systems/routine.py:130-147` (role utility boost) —
   `tests/unit/strategic/test_role_biasing.py`
7. `src/engine/combat_rewards.py` (MONSTER/HERO reward classification) —
   `tests/unit/combat/test_combat_rewards.py`, `tests/unit/combat/test_combat_reward_trace.py`
8. `src/engine/combat.py` (HERO lethality/rebirth, SLASH/CRUSH kind) — the combat unit suite
   under `tests/unit/combat/` broadly (no single dedicated file isolates lines 136/610-615)
9. `src/engine/military_conflict.py:126-136` (`_find_guard_entities_in_region`) —
   `tests/unit/domains/faction/test_military_conflict_phase.py`,
   `tests/unit/domains/faction/test_siege_ledger.py`,
   `tests/unit/domains/faction/test_war_exhaustion.py`,
   `tests/unit/domains/faction/test_siege_model.py`,
   `tests/unit/domains/faction/test_territory_transfer.py`
10. `src/domains/cooperation/providers.py:52,88` + `evaluators.py:180` (`role == 1` magic number)
    — `tests/unit/domains/cooperation/test_phase7_cooperation_intent_bridge.py`,
    `test_phase7_cooperation_decision_service.py`,
    `test_phase7_party_objective_alignment.py`, `test_phase7_cooperation_learning.py`,
    `test_phase7_cooperation_postures.py`
11. `src/engine/evolution.py:111-112` (HERO check) — no dedicated test file located by targeted
    search; covered only indirectly by the broader progression/evolution suite if at all — a
    genuine coverage gap, not something this ticket needs to fix, but the implementer should
    re-search before assuming coverage exists.
12. `src/world/regional_sovereignty.py:48,82` (HERO tax/debuff) — no dedicated test file located
    by targeted search; same caveat as #11.

### Architecture guard
- `tests/architecture/test_legacy_enum_usage_boundaries.py` (all functions) — must keep passing.
  Any new source file added by this ticket that reads `EntityRole.X` directly (e.g. a new
  `src/ai/goals/occupation_change_scorer.py`) will not fail this test even if left off
  `ALLOWED_MODULES` (it only fails on `FORBIDDEN_MODULES` hits, and reports — does not fail on —
  untracked modules), but should be added to `ALLOWED_MODULES` with a rationale comment to follow
  the established convention (see investigation.md Anti-Drift Hazards).

### Goal-hierarchy pipeline (indirect regression surface — new GoalKind competing in the same pool)
- `tests/unit/strategic/test_score_normalization.py` — tests the `_score_scale_max()`/tier-5
  normalization machinery a new bespoke-materialization `GoalKind` must respect.
- `tests/unit/strategic/test_committed_intention_materialization.py` — tests
  `_COMMITTED_INTENTION_ELIGIBLE_KINDS` gating; must confirm a new `GoalKind.OCCUPATION_CHANGE`
  is correctly *excluded* unless Plan explicitly adds it.
- `tests/unit/strategic/test_strategic_lifecycle.py`, `tests/unit/strategic/test_biological_needs.py`,
  `tests/unit/world/test_anchored_world.py` — broader tier-5 competition/lifecycle tests that a
  new always-competing `GoalScorer` could perturb if its utility function is miscalibrated
  (e.g. if it wins ties it shouldn't, starving other goals).

## New Tests Required

Per AC:

1. **`test_occupation_change_scorer_returns_zero_utility_for_non_eligible_role`**
   Category: unit. Verifies: a `HERO`/`SHOPKEEPER`/`WORKER`/`GUARD`/`MONSTER` entity (i.e. any
   non-entry-level role per whatever Plan decides "entry-level" means) scores `GoalScore(kind=
   GoalKind.OCCUPATION_CHANGE, utility=0.0, ...)` from the new scorer — confirms the trigger does
   not fire for entities already holding a specific occupation.
   Location: `tests/unit/strategic/` (new file, e.g.
   `tests/unit/strategic/test_occupation_change_scorer.py`) or co-located with other goal-scorer
   tests if a closer convention exists (`test_role_biasing.py` is the nearest sibling).

2. **`test_occupation_change_scorer_fires_when_open_slot_and_skill_match`**
   Category: unit. Verifies: an entry-level entity with a matching skill/aptitude and a
   region reporting an open slot for the matched occupation produces a non-zero `GoalScore` with a
   resolvable `target_id`/`target_pos`.
   Location: same file as above.

3. **`test_occupation_change_scorer_does_not_fire_without_open_slot`**
   Category: unit. Verifies: an otherwise-eligible entity in a region with no open slot for any
   role it could match produces `utility=0.0` — proves the "open slot" half of the trigger
   condition is load-bearing, not decorative.
   Location: same file as above.

4. **`test_occupation_change_goal_registered_in_goal_registry`**
   Category: unit / registration smoke test. Verifies: `GoalKind.OCCUPATION_CHANGE` is present
   in `GoalRegistry._scorers` after `src.ai.goals` import (mirrors the existing implicit coverage
   `test_scan_finds_enum_usages_in_known_allowed_module`-style registration smoke tests give other
   subsystems) and that `GoalRegistry.get_all_scores()` includes exactly one `OCCUPATION_CHANGE`
   entry per call.
   Location: `tests/unit/strategic/test_occupation_change_scorer.py` or a `src/ai/goals/`-focused
   test module if one exists (search before creating a duplicate).

5. **`test_occupation_change_materializes_into_project_with_correct_kind`**
   Category: integration. Verifies: when `OCCUPATION_CHANGE` wins the tier-5 competition in
   `StrategicIntelligenceSystem.evaluate_strategic_intent`, the resulting `ProjectState`/
   `ObjectiveState` carry the correct (bespoke or generic, per Plan's decision) `ProjectKind`/
   `ObjectiveKind`, and `_score_scale_max()` classifies the materialized score on the correct
   scale (mirrors `RegionStabilizationGoalScorer`'s own precedent bug class —
   TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG — this test exists specifically to
   catch that regression class recurring a third time).
   Location: `tests/unit/strategic/` (new) or `tests/integration/strategic/` if project
   materialization integration tests already live there — search before creating.

6. **`test_occupation_change_completion_issues_role_set_identity_update`**
   Category: integration. Verifies: once the `OCCUPATION_CHANGE` objective's completion condition
   is met, the resulting `EntityUpdate` carries `identity=IdentityUpdate(role_set=<new role int>)`
   — the actual mechanism-level proof that this ticket's core deliverable exists.
   Location: co-located with wherever the new `CoreActions.execute_*`/completion-check code lives
   (e.g. `tests/unit/engine/domain/test_core_actions.py` if that convention exists, else new).

7. **`test_role_set_applies_through_identity_patch_only`**
   Category: architecture guard. Verifies: given an `EntityUpdate(identity=IdentityUpdate(
   role_set=N))`, `ApplyPath.apply_generation`/`_apply_entity_update` produces an `EntityState`
   whose `identity.role == N`, AND that no other code path (grep-level static check, mirroring
   `test_legacy_enum_usage_boundaries.py`'s scan style) constructs an `IdentityComponent`/
   `EntityState` with a role field outside `IdentityPatch.apply`/`ApplyPath._fast_replace_identity`.
   Directly satisfies CLAUDE.md's "Authoritative application is the only place durable state
   should be committed" architecture-test requirement.
   Location: `tests/architecture/` (new file or added to an existing apply-path guard file if one
   exists — search before creating).

8. **`test_occupation_change_reachable_through_real_kernel_tick_once`**
   Category: integration (end-to-end). Verifies AC #1 directly: construct a world/entity in the
   entry-level role with a matching skill and an open slot, run a real `Kernel.tick_once()` loop
   for enough ticks to reach goal selection → project completion → role commit, and assert
   `entity.identity.role` changed to the expected destination role by the end. Mirrors
   `test_recipe_learned_fires_through_real_kernel_tick_once`'s existing pattern exactly.
   Location: `tests/integration/strategic/` or `tests/integration/` root, following whichever
   convention the closest sibling test uses.

9. **`test_entity_role_changed_event_fires_on_real_occupation_transition`**
   Category: integration. Verifies AC #3: running the same real-`Kernel.tick_once()` scenario as
   test 8 produces a `SimulationEvent(event_type="entity_role_changed", payload={"role": <new>,
   "previous_role": <old>})` — the direct proof that ENTITY-007's ledger note can legitimately be
   updated from `unscored_intentional` to `verified/live`.
   Location: `tests/unit/observability/test_event_extractor_identity.py` (append to the existing
   file — natural home) or a new integration-tier file if the existing file is unit-only by
   convention (it already has one real-kernel test, #129, so appending is likely correct).

10. **`test_cooperation_role_1_magic_number_flagged_not_fixed`** (documentation/regression-lock
    test, optional but recommended): Category: unit. Verifies the disclosed
    `cooperation/providers.py`/`evaluators.py` `role == 1` behavior is exactly what's documented
    (an entity with `role_set` transitioned to `SHOPKEEPER` is treated as a Hireling/Guild
    Merchant for cooperation purposes) — locks in the current (buggy but disclosed, in-scope-to-
    flag-only) behavior so a future fix is a deliberate, visible test change, not a silent
    behavior drift. Location: `tests/unit/domains/cooperation/` (new or appended to an existing
    file).

## Scoped Pytest Commands

```
# Core regression: identity events, goal-hierarchy pipeline, the 12 consumers' existing suites
pytest tests/unit/observability/test_event_extractor_identity.py \
       tests/unit/strategic/ \
       tests/unit/domains/adventure/ \
       tests/unit/domains/cooperation/ \
       tests/unit/domains/faction/ \
       tests/unit/domains/optimization/ \
       tests/unit/world/ \
       tests/unit/combat/ \
       tests/architecture/test_legacy_enum_usage_boundaries.py \
       -m "not slow"

# New/updated integration coverage (real Kernel.tick_once() paths)
pytest tests/integration/strategic/ tests/integration/ -k "occupation or identity or role" -m "not slow"

# Full economy contract regression (crafting required_role gate)
pytest tests/unit/world/test_economy_contract.py -m "not slow"
```

Never `pytest tests/` — scoped to the domains this ticket touches (strategic cognition, adventure,
cooperation, faction/military, optimization/occupancy, economy/crafting, combat rewards/lethality,
observability identity events, and the enum-usage architecture guard) per CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- **Non-target roles must show zero behavior change**: any new test for the `OCCUPATION_CHANGE`
  scorer/action must include an explicit assertion that `HERO`/`MONSTER` entities are entirely
  unaffected (e.g. `HERO`'s combat lethality/reward-classification/adventure-scoring behavior must
  be bit-identical before and after this ticket) — the 12-consumer regression surface above exists
  precisely to catch a role-mutation change silently altering combat/economy/social behavior for
  roles that were never supposed to be reachable through this trigger.
- **`GoalKind.OCCUPATION_CHANGE` must not silently win ties it shouldn't**: a test should assert
  the new `GoalKind`'s string value sorts correctly relative to the existing 13 values under
  `intelligence.py:1495`'s `sort(key=lambda x: (-x.utility, x.kind))` tie-break, matching whatever
  deliberate ordering rationale Plan documents (mirroring `ADVENTURE_ROUTE`'s `"z_"` prefix
  precedent) — an un-tested ordering choice is exactly how the three existing tier-5 goals'
  inline comments explain past near-misses were caught.
- **`_COMMITTED_INTENTION_ELIGIBLE_KINDS` must stay unchanged unless Plan explicitly decides
  otherwise**: a guard assertion (`GoalKind.OCCUPATION_CHANGE not in
  _COMMITTED_INTENTION_ELIGIBLE_KINDS`) belongs in the new test file so an accidental future
  addition doesn't silently enable committed-intention materialization for a goal that was never
  designed for it.
- **The cooperation `role == 1` sites must not be touched by this ticket's diff**: a
  `git diff`-level review check (not necessarily an automated test) confirming
  `src/domains/cooperation/providers.py` and `evaluators.py` are unmodified except possibly for an
  added `# TODO`/comment — the ticket's own scope explicitly says "flag, not fix."
- **`docs/mechanics/04_strategic_cognition.md`'s doc-coverage check**
  (`tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage`) will fail Verify if
  this path is listed under investigation.md's required-bullet format but `git status` shows it
  untouched — the implementer must actually edit this file, not just cite it.
