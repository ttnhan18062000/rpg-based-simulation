---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-ADVENTURE-GOAL-SCORER
artifact_type: test_plan
tags: [cognition, adventure]
---

# Test Plan — TCK-20260811-ADVENTURE-GOAL-SCORER

## Regression Surface

Existing tests that must keep passing, grouped by category. This ticket adds a new registered
`GoalScorer` (System B, tier 5) and a new materialization branch in
`intelligence.py::evaluate_strategic_intent()` — the regression surface is therefore the whole
goal-competition path plus the adventure domain's own currently-passing tests (since
`AdventureGoalScorer.score()` replicates, but must not alter, `AdventureDecisionService.decide()`,
`AdventureRouteGenerator.generate()`, and opportunity assembly).

**Unit**
- `tests/unit/strategic/test_expanded_goals.py` — all 7 tests, especially
  `test_deterministic_tie_breaking` (sort-key convention this ticket's AC6 test extends) and
  `test_integration_strategic_project_selection` (end-to-end `evaluate_strategic_intent` shape
  this ticket's new materialization test mirrors).
- `tests/unit/strategic/test_score_normalization.py` — all 5 tests (STRAT-186/STRAT-005/006
  cross-system normalization; the `_ADVENTURE_ROUTE_SCORE_MAX`/`_GOAL_UTILITY_SCORE_MAX`
  constants this ticket's own normalization formula reuses must not be redefined or perturbed).
- `tests/unit/strategic/test_enum_drift.py` — `test_goal_registry_strict_validation` and
  `test_all_registered_scorers_are_canonical` (confirms `GoalKind.ADVENTURE_ROUTE` registers
  cleanly and `GoalRegistry`'s strict-validation/canonical-membership invariants still hold with
  an 11th member; no exact-count assertion exists today so this file does not need editing, only
  passing).
- `tests/unit/strategic/test_interruption_resistance.py` — `_make_entity` fixture is imported
  directly by `test_score_normalization.py` and will be reused by this ticket's new
  materialization test; its own tests must keep passing unmodified.
- `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py` — `decide()`'s
  existing behavior (signature, `DEFER_WITH_REASON` empty-candidates path,
  `RouteToProjectMapper.map_to_states()` internal call) must be provably unchanged, since
  `AdventureGoalScorer.score()` calls it as-is.
- `tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py` — boundary/edge
  cases for route generation and decision; `AdventureRouteGenerator.generate()` is called
  unchanged from the new scorer.

**Integration**
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` —
  `AdventureDecisionPhase` stays fully wired and unmodified (Out of Scope); this suite proves
  the new scorer did not disturb the existing pipeline-phase path.
- `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py` — end-to-end
  adventure scenario coverage, unaffected by an unwired new scorer.

**Arena-combat**
- None applicable — this ticket does not touch `src/domains/combat_engagement/` or combat
  resolution. `CombatEngageScorer`/`CombatRetreatScorer` are exercised only incidentally, via
  `test_expanded_goals.py`'s existing tests (already listed above under Unit), not as a
  dedicated arena-combat regression concern.

**Performance (informational, not gated by this ticket)**
- `tests/perf/test_phase3_adventure_decision_budget.py` — not required to be re-run by this
  ticket's Test phase (perf budget is scoped to the wired `AdventureDecisionPhase` path, which
  this ticket does not touch), but flagged here since it shares the same `decide()`/`generate()`
  call surface; worth a spot-check if CI time allows.

## New Tests Required

Per the ticket's 6 Acceptance Criteria (`tickets/inprogress/TCK-20260811-ADVENTURE-GOAL-SCORER.md`):

### AC1 — `GoalKind.ADVENTURE_ROUTE` exists; `AdventureGoalScorer` registered

- **`test_goal_kind_adventure_route_is_registered_member`**
  Category: unit
  Verifies: `GoalKind.ADVENTURE_ROUTE` is a real enum member (`GoalKind("adventure_route")` — or
  whatever value AC6 settles on — does not raise), and
  `GoalRegistry._scorers[GoalKind.ADVENTURE_ROUTE]` is an instance of `AdventureGoalScorer`
  after `src.ai.goals` is imported (mirrors `test_enum_drift.py`'s
  `test_all_registered_scorers_are_canonical` pattern: `isinstance(kind, GoalKind)` plus
  `isinstance(scorer, GoalScorer)`).
  Location: `tests/unit/ai/goals/test_adventure_goal_scorer.py` (new file; new directory
  `tests/unit/ai/goals/` — no `__init__.py`-requiring package exists there today, confirmed by
  `ls` returning "No such file or directory"; create as a plain pytest-discoverable directory
  matching `tests/unit/strategic/`'s and `tests/unit/domains/adventure/`'s existing layout).

- **`test_adventure_goal_scorer_implements_goal_scorer_protocol`**
  Category: unit
  Verifies: `AdventureGoalScorer().score(entity, state)` returns a `GoalScore` instance (protocol
  conformance — mirrors how `test_expanded_goals.py`'s individual scorer tests each call
  `scorer.score(entity, base_state)` directly rather than only through the registry).
  Location: `tests/unit/ai/goals/test_adventure_goal_scorer.py`

### AC2 — normalization formula; `raw_score=2.9` → `utility==100.0` exactly; metadata populated

- **`test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact`**
  Category: unit
  Verifies (parametrized, worked arithmetic in the docstring/comments, matching
  `test_score_normalization.py`'s style of showing the formula inline rather than asserting a
  bare number):
  - `raw_score=2.9` → `utility == 100.0` exactly (AC2's literal claim; formula-identity, not an
    empirical claim about real route scores — per investigation.md Risk #6, do not conflate the
    two in the test's own framing/docstring).
  - `raw_score=1.45` → `utility == 50.0` (midpoint sanity check).
  - `raw_score=0.0` → `utility == 0.0`.
  Achieved by mocking/monkeypatching `AdventureDecisionService.decide()` (or the opportunity/
  generate chain feeding it) to return a controlled `AdventureRouteOption`/`AdventureDecisionResult`
  with a known `selected.score`, so the raw score is pinned rather than emergent from a real
  scenario — isolates the normalization arithmetic from route-generation nondeterminism.
  Location: `tests/unit/ai/goals/test_adventure_goal_scorer.py`

- **`test_adventure_goal_scorer_metadata_carries_route_family_and_raw_score`**
  Category: unit
  Verifies: `GoalScore.metadata["route_family"]` equals the winning `RouteFamily` member (or its
  `.value`) and `GoalScore.metadata["raw_score"]` equals the unnormalized `selected.score` — the
  two keys AC3's materialization branch consumes. This is the first real test of `metadata` ever
  being populated by a scorer (investigation.md confirms no existing scorer does this today), so
  assert the dict shape exactly (`set(score.metadata.keys()) >= {"route_family", "raw_score"}`)
  rather than just truthiness.
  Location: `tests/unit/ai/goals/test_adventure_goal_scorer.py`

### AC3 / AC4 — materialization branch uses `metadata["raw_score"]`, never `best_candidate.utility`

This is the ticket's single highest-value regression test (Anti-Drift Hazards, investigation.md).
It must exercise the **new** `intelligence.py` materialization branch end-to-end, not just the
scorer in isolation — the defect class being guarded against
(`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`'s sibling) only manifests at the
point a `GoalKind.ADVENTURE_ROUTE` winner is turned into a `ProjectState` via
`RouteToProjectMapper.map_to_states(score=...)`.

**Added by plan.md's revision (not in this section originally):** a third test,
`test_form_party_materialized_objective_is_tactically_resolvable_not_a_stall`, guards the
architecture-reviewer's Risk #1 "wins but stalls" finding — see the AC5 section below for its
full description. Also located in `tests/unit/strategic/test_adventure_route_materialization.py`.

- **`test_adventure_route_winner_materializes_with_raw_score_not_utility`**
  Category: integration
  Verifies, with concrete worked arithmetic in the docstring (mirroring
  `test_locked_system_a_current_now_reachable_by_system_b_candidate_fix_confirmed`'s style):
  Force an entity/state where `AdventureGoalScorer` is the clear tier-5 winner (e.g. monkeypatch
  `AdventureDecisionService.decide()` to return a fixed high-confidence route with
  `raw_score=2.0`, so `utility = (2.0/2.9)*100.0 ≈ 68.97`), run
  `StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)` end-to-end,
  and assert the resulting `ProjectState.score == 2.0` (the raw score) — **not** `≈68.97` (the
  utility). Explicitly assert `project.score != best_candidate_utility_expected` as a negative
  check, since a regression back to `best_candidate.utility` would still produce *a* number, just
  the wrong-scale one (the same silent-failure shape as the sibling ticket's bug).
  Also assert `project.kind` is the real mapped `ProjectKind` (via `RouteToProjectMapper`), not
  `GoalKind.ADVENTURE_ROUTE` itself — confirming materialization actually ran the mapper rather
  than falling through to the generic `best_candidate.kind` construction at
  `intelligence.py:1409` (which would produce a `GoalKind`-typed project, wrong for this branch).
  Location: `tests/unit/strategic/test_adventure_route_materialization.py` (new file — judgment
  call: this test exercises the *new* `intelligence.py` materialization branch itself, a
  different concern from `test_score_normalization.py`'s existing scope, which is strictly
  `evaluate_project_switch()`'s lock-bypass normalization and does not touch materialization at
  all. A new file co-located in `tests/unit/strategic/` follows that directory's existing
  granularity — one file per mechanism under test, e.g. `test_score_normalization.py` vs.
  `test_expanded_goals.py` vs. `test_enum_drift.py` — rather than overloading
  `test_score_normalization.py` with a mechanism it doesn't otherwise cover.)

- **`test_adventure_route_winner_preserves_none_none_handling_for_defer_family`**
  Category: integration
  Verifies: if the winning candidate's `metadata["route_family"]` is somehow
  `RouteFamily.DEFER_WITH_REASON` (defensive case — should not normally reach materialization
  since AC5 makes `DEFER_WITH_REASON` score 0/target-None and thus never clear the tier-5 floor,
  but the materialization branch's own `(None, None)` handling per `map_to_states()` must still
  be a no-op rather than raise or construct a garbage project if reached). Asserts no
  `StrategicUpdate.projects_add_or_update` entry is produced for this case.
  Location: `tests/unit/strategic/test_adventure_route_materialization.py`

### AC5 — ineligible entities / `DEFER_WITH_REASON` never clear the tier-5 floor

- **`test_adventure_goal_scorer_ineligible_entity_returns_zero_utility_no_target`**
  Category: unit
  Verifies: for an entity that fails `_supports_adventure_routing()` (imported from
  `src.domains.adventure.phase`, per investigation.md's reuse-by-import requirement), `score()`
  returns `GoalScore(kind=GoalKind.ADVENTURE_ROUTE, utility=0.0, target_id=None)` without calling
  `AdventureDecisionService.decide()` at all (assert via mock/spy that `decide()` was never
  invoked — mirrors `GuildNeedScorer`'s early-return-before-expensive-work shape cited in
  investigation.md as the closest structural precedent).
  Location: `tests/unit/ai/goals/test_adventure_goal_scorer.py`

- **`test_adventure_goal_scorer_defer_with_reason_returns_zero_utility_no_target`**
  Category: unit
  Verifies: when the replicated opportunities → generate → decide chain resolves to a
  `DEFER_WITH_REASON` result (e.g. by forcing empty opportunities/candidates), `score()` returns
  `utility=0.0` and `target_id=None`/`target_pos=None` — confirming this candidate can never
  clear `intelligence.py:1373`'s floor gate (`utility < 20.0` alone already excludes it, target
  check is belt-and-suspenders).
  Location: `tests/unit/ai/goals/test_adventure_goal_scorer.py`

- **RESOLVED by plan.md (supersedes the placeholder originally specified here).** Risk #1 was
  decided as (a) synthesize a placeholder `target_id` paired with a REAL, resolvable
  `target_pos`, via a new `AdventureGoalScorer._resolve_placeholder_target_pos()` method
  (nearest inn else `town_center` for forced `RECOVER`; `town_center` for forced
  `ASK_INFORMATION`; nearest real ally position else the entity's own position for
  `FORM_PARTY`). This was revised once by an architecture-reviewer pass after the plan's
  original version synthesized `target_id` alone (leaving `target_pos=None`, which cleared the
  tier-5 floor gate but left the committed project impossible for
  `TacticalDecisionSystem._resolve_target_position()` to ever resolve into navigation — a "wins
  but stalls forever" defect). See plan.md's "Unresolved Questions Now Resolved" section for the
  full worked justification. The tests actually implemented (replacing this placeholder) are:
  - `test_form_party_winner_has_non_null_target_id_and_resolvable_target_pos` — asserts both
    `score.target_id == f"adventure:{RouteFamily.FORM_PARTY.value}"` and
    `score.target_pos == <the known ally position>`.
  - `test_forced_recover_winner_target_pos_resolves_to_inn_or_town_center` — two-branch: with an
    `inn` building present, `target_pos` resolves to its position; with none present, `target_pos`
    resolves to `state.town_center`.
  - `test_forced_ask_information_winner_target_pos_resolves_to_town_center` — asserts
    `target_pos == state.town_center`.
  - `test_form_party_target_pos_falls_back_to_entity_own_position_when_no_ally_candidates` —
    defensive case: no eligible ally candidates in `state.entities`, asserts
    `target_pos == entity.navigation.position` (never `None`).
  Location (all four): `tests/unit/ai/goals/test_adventure_goal_scorer.py`

  Additionally, `tests/unit/strategic/test_adventure_route_materialization.py` adds
  `test_form_party_materialized_objective_is_tactically_resolvable_not_a_stall`, proving the fix
  end-to-end (not just at the scorer-output level): it runs
  `StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)`, then calls
  `TacticalDecisionSystem._resolve_target_position()` directly on the materialized
  `ObjectiveState` and asserts real resolution succeeds, plus a negative check reconstructing the
  original (rejected) `target_position=None` version and confirming it would have resolved to
  `(None, None, None)` — explicitly demonstrating the stall failure mode the fix prevents.

### AC6 — deliberate tie-break string value, not arbitrary

- **`test_adventure_route_kind_value_sorts_after_all_existing_goal_kinds`**
  Category: unit
  Verifies concretely (per investigation.md Risk #5's recommendation): the chosen
  `GoalKind.ADVENTURE_ROUTE.value` string sorts **after** all 10 existing `GoalKind` values in
  ascending lexicographic order, so it never wins an exact-utility tie against any of them under
  `modified_scores.sort(key=lambda x: (-x.utility, x.kind))` (`intelligence.py:1369`).
  ```python
  def test_adventure_route_kind_value_sorts_after_all_existing_goal_kinds():
      existing_values = [
          GoalKind.HARVESTING.value, GoalKind.FATIGUE.value, GoalKind.HUNGER.value,
          GoalKind.SOCIAL.value, GoalKind.TOWN_RETURN.value, GoalKind.COMBAT_ENGAGE.value,
          GoalKind.COMBAT_RETREAT.value, GoalKind.RECOVER.value, GoalKind.RESOLVE_BLOCKER.value,
          GoalKind.GUILD.value,
      ]
      for v in existing_values:
          assert GoalKind.ADVENTURE_ROUTE.value > v, (
              f"GoalKind.ADVENTURE_ROUTE.value={GoalKind.ADVENTURE_ROUTE.value!r} must sort "
              f"after {v!r} so an exact-utility tie never lets adventure routing win over "
              f"existing survival/urgency-tier scorers (investigation.md Risk #5)."
          )
      # town_return is today's alphabetical maximum among the 10 existing values -- pin that
      # assumption explicitly so this test fails loudly if a future ticket adds an 11th/12th
      # existing GoalKind whose value would also need checking here.
      assert max(existing_values) == GoalKind.TOWN_RETURN.value
  ```
  Also verify a live sort with an actual tie:
  ```python
  def test_adventure_route_loses_exact_utility_tie_against_existing_kind():
      scores = [
          GoalScore(kind=GoalKind.ADVENTURE_ROUTE, utility=50.0, target_id="t", target_pos=(0, 0)),
          GoalScore(kind=GoalKind.RECOVER, utility=50.0, target_id="t", target_pos=(0, 0)),
      ]
      scores.sort(key=lambda x: (-x.utility, x.kind))
      assert scores[0].kind == GoalKind.RECOVER  # recover (survival-urgency) wins the tie
  ```
  Location: `tests/unit/ai/goals/test_adventure_goal_scorer.py` (mirrors
  `test_expanded_goals.py::test_deterministic_tie_breaking`'s existing pattern of constructing
  `GoalScore`s directly and sorting, rather than going through the full registry).

## Scoped Pytest Commands

```
pytest tests/unit/ai/goals/ tests/unit/strategic/test_expanded_goals.py tests/unit/strategic/test_score_normalization.py tests/unit/strategic/test_enum_drift.py tests/unit/strategic/test_adventure_route_materialization.py tests/unit/domains/adventure/ tests/integration/domains/adventure/ -v
```

Never `pytest tests/`. This scopes to: the new scorer's own unit tests, the goal-competition/
normalization regression surface, `GoalRegistry` enum-validation invariants, the new
materialization-branch test, and the adventure-domain tests confirming `decide()`/`generate()`
remain unchanged.

If Implement also touches `tests/unit/strategic/test_interruption_resistance.py` (only if
`_make_entity` needs a new kwarg for these tests — not expected, but flag if so), add it to the
command above.

## Anti-Drift Test Guards

- **`test_adventure_route_winner_materializes_with_raw_score_not_utility`**'s negative assertion
  (`project.score != <utility value>`) specifically catches the single highest-value regression
  this ticket must not introduce (AC3/AC4, Anti-Drift Hazards) — a silent scale-mismatch bug of
  the exact class already fixed once in
  `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`.
- **`test_adventure_goal_scorer_ineligible_entity_returns_zero_utility_no_target`**'s
  spy-assertion that `decide()` was never called guards against a future edit accidentally
  running the (relatively expensive) opportunities→generate→decide chain for entities that
  should short-circuit — a performance/correctness drift the design doc's `GuildNeedScorer`
  precedent exists specifically to prevent.
- **`test_adventure_route_kind_value_sorts_after_all_existing_goal_kinds`** guards against a
  future ticket silently adding a new `GoalKind` member with a value that re-introduces a tie-win
  against `ADVENTURE_ROUTE` (or against a future edit changing `ADVENTURE_ROUTE`'s own value) —
  fails loudly rather than requiring someone to notice a subtle sort-order regression.
- **`test_adventure_route_winner_preserves_none_none_handling_for_defer_family`** guards the
  shared `RouteToProjectMapper.map_to_states()` `(None, None)` contract (investigation.md,
  confirmed already correctly structured) against this ticket's new call site accidentally
  assuming a non-`None` mapper result and raising or constructing a garbage `ProjectState`.
- Running `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py` and
  `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` as part of the
  regression surface (not skipped) guards against the highest-likelihood scope-creep hazard
  flagged in investigation.md's Anti-Drift Hazards: accidentally modifying `phase.py`,
  `service.py`, or `generator.py` while building the replicated opportunities→generate→decide
  sequence inside `score()`, instead of calling them unchanged.
- The placeholder test for Risk #1 (`test_form_party_winner_has_non_null_target_id_after_plan_
  resolves_risk_1`) is an explicit anti-drift guard against a different failure mode: silently
  assuming a resolution to an open architectural question during Implement without it being
  recorded in `plan.md` first. Its presence in the suite (even skipped) forces the resolution to
  be visible rather than quietly baked into scorer code with no test coverage either way.
