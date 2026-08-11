---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER
artifact_type: test_plan
tags: [social, cognition]
---

# Test Plan — TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER

## Regression Surface

This ticket adds a new registered `GoalScorer` (System B, tier 5), a new materialization branch in
`intelligence.py::evaluate_strategic_intent()`, a new `GoalKind` member, and removes a direct
`current_project_id_set` write from `ContractService.accept_contract()`. The regression surface is
therefore the whole goal-competition path, the contract lifecycle's own existing tests, and anything
that reads `ContractService.accept_contract()`'s return shape.

**Unit**
- `tests/unit/strategic/test_strategic_social_contracts.py` — the one test in this file
  (`test_accepted_contract_spawns_project_and_objective`) is the ticket's own named rewrite target
  (see New Tests Required below) — it is not "kept passing unmodified," it is replaced.
- `tests/unit/social/test_contract_lifecycle.py` — `test_contract_lifecycle_acceptance` (line 66-78)
  also calls `ContractService.accept_contract()` but only asserts on
  `update.contracts_add_or_update[0].status`/`.expiry_tick` — never touches
  `current_project_id_set` or `projects_add_or_update`. Confirmed by direct read: **this test must
  keep passing unmodified** and is a real regression guard that the contract-status-transition half
  of `accept_contract()` (unrelated to the bypass) stays intact.
- `tests/unit/social/test_contract_lifecycle.py` — the other 3 tests in this file
  (`test_contract_appraisal_trust`, `test_contract_appraisal_greed`, `test_contract_appraisal_rejection`)
  exercise `SocialAppraisalSystem.appraise_contract` only, untouched by this ticket — must keep passing
  as a guard that appraisal logic (upstream of acceptance) is undisturbed.
- `tests/unit/social/test_contracts.py`, `tests/unit/social/test_social_contracts.py`,
  `tests/unit/social/test_contract_lifecycle_phase7.py` — broader contract-lifecycle regression
  surface; none call `accept_contract()` directly per the ticket's own grep-confirmed caller list, but
  exercise `SocialContractSystem`/`ContractService` methods this ticket's changes sit alongside; run to
  confirm no accidental disturbance.
- `tests/unit/strategic/test_expanded_goals.py` — all 7 tests, especially
  `test_deterministic_tie_breaking` (sort-key convention the new tie-break test extends) and
  `test_integration_strategic_project_selection` (end-to-end `evaluate_strategic_intent` shape the new
  materialization test mirrors).
- `tests/unit/strategic/test_score_normalization.py` — all 5 tests. Must keep passing **unmodified in
  outcome** even if `_score_scale_max`/`_ADVENTURE_ROUTE_SCORE_MAX` end up touched per Plan's
  resolution of investigation.md Risk #1 — these tests are the existing calibration contract for
  `ADVENTURE_ROUTE` and must not silently regress as a side effect of adding a second `ProjectKind`-
  classified system.
- `tests/unit/strategic/test_enum_drift.py` — `test_goal_registry_strict_validation` and
  `test_all_registered_scorers_are_canonical`, confirming `GoalKind.SOCIAL_CONTRACT` registers cleanly
  as a 12th member and `GoalRegistry`'s invariants still hold.
- `tests/unit/strategic/test_interruption_resistance.py` — `_make_entity` fixture is reused by the new
  materialization test (mirrors `test_score_normalization.py`'s own reuse); its own tests must keep
  passing unmodified.
- `tests/unit/strategic/test_adventure_route_materialization.py` — all 4 tests (confirmed file has
  `test_adventure_route_winner_materializes_with_raw_score_not_utility`,
  `test_adventure_route_winner_preserves_none_none_handling_for_defer_family`,
  `test_form_party_materialized_objective_is_tactically_resolvable_not_a_stall`,
  `test_shadow_diff_report_separates_raw_score_from_utility_mismatches`) — must keep passing unmodified
  as proof the new `SOCIAL_CONTRACT` branch is additive (an `elif`, not a restructure of the existing
  `if best_candidate.kind == GoalKind.ADVENTURE_ROUTE:` branch).
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` — confirms `AdventureGoalScorer` itself is
  undisturbed by adding a sibling scorer in the same registry/package.

**Integration**
- None of this ticket's own new code has an existing integration-level suite (no live production
  caller of `accept_contract()` exists — see investigation.md Risk #4). No integration regression
  surface to enumerate beyond confirming the pipeline still constructs (`src/engine/pipeline.py`
  import-time registration of `GoalRegistry` scorers must not raise).

**Arena-combat**
- None applicable — this ticket does not touch `src/domains/combat_engagement/` or combat resolution.
  `CombatEngageScorer`/`CombatRetreatScorer` are exercised only incidentally via
  `test_expanded_goals.py` (already listed under Unit).

## New Tests Required

Per the ticket's 7 Acceptance Criteria
(`tickets/inprogress/TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER.md`):

### AC1 — `ContractService.accept_contract()` no longer sets `current_project_id_set` directly

- **`test_accept_contract_no_longer_sets_current_project_id_directly`**
  Category: unit
  Verifies: calling `ContractService.accept_contract(entity, contract_id, tick)` on a freshly-offered
  RECRUITMENT (or LOAN) contract returns a `StrategicUpdate` whose `current_project_id_set is None`.
  Explicitly a negative assertion — the single highest-value regression guard for this ticket's core
  behavior change (mirrors AC3/AC4's negative-check style in the adventure ticket's own materialization
  test).
  Location: `tests/unit/social/test_contract_lifecycle.py` (co-located with the existing
  `test_contract_lifecycle_acceptance`, same file, same fixtures) **or**
  `tests/unit/strategic/test_strategic_social_contracts.py` if Plan decides the rewritten test in that
  file covers this directly instead of a separate test — avoid duplicating the same assertion in both
  files.

### AC2 — new `SocialContractGoalScorer` produces a `GoalScore` with raw score in metadata (never utility)

- **`test_goal_kind_social_contract_is_registered_member`**
  Category: unit
  Verifies: `GoalKind.SOCIAL_CONTRACT` is a real enum member and
  `GoalRegistry._scorers[GoalKind.SOCIAL_CONTRACT]` is an instance of `SocialContractGoalScorer` after
  `src.ai.goals` is imported (mirrors `test_adventure_goal_scorer.py`'s own registration test).
  Location: `tests/unit/ai/goals/test_social_contract_goal_scorer.py` (new file, same directory
  convention as `test_adventure_goal_scorer.py`).

- **`test_social_contract_goal_scorer_implements_goal_scorer_protocol`**
  Category: unit
  Verifies: `SocialContractGoalScorer().score(entity, state)` returns a `GoalScore` instance for an
  entity with an `ACTIVE` RECRUITMENT contract.
  Location: `tests/unit/ai/goals/test_social_contract_goal_scorer.py`

- **`test_social_contract_goal_scorer_metadata_carries_raw_score_and_contract_identity`**
  Category: unit
  Verifies: `GoalScore.metadata` contains a `"raw_score"` key (distinct from `.utility`) plus enough to
  reconstruct the materialized project (contract id and/or kind) — exact key set to be confirmed
  against plan.md's chosen `metadata` shape; assert `set(score.metadata.keys())` is a superset of
  whatever plan.md specifies, mirroring `test_adventure_goal_scorer.py`'s own
  `test_adventure_goal_scorer_metadata_carries_route_family_and_raw_score` shape-exactness style.
  Location: `tests/unit/ai/goals/test_social_contract_goal_scorer.py`

- **`test_social_contract_goal_scorer_no_active_contracts_returns_zero_utility_no_target`**
  Category: unit
  Verifies: an entity with no contracts, or only `OFFERED`/terminal-status contracts (no `ACTIVE`
  ones), gets `GoalScore(kind=GoalKind.SOCIAL_CONTRACT, utility=0.0, target_id=None)` — mirrors
  `AdventureGoalScorer`'s ineligible-entity early-return shape (investigation.md's cited
  `GuildNeedScorer` precedent).
  Location: `tests/unit/ai/goals/test_social_contract_goal_scorer.py`

- **`test_social_contract_goal_scorer_reduces_multiple_active_contracts_to_one_candidate`**
  Category: unit
  Verifies investigation.md Risk #3 directly: an entity with 2+ simultaneous `ACTIVE` contracts (e.g.
  one LOAN, one RECRUITMENT) produces exactly one `GoalScore` from a single `score()` call, and that
  the winning contract is the one plan.md's reduction rule says should win (e.g. highest raw score) —
  assert on which contract's identity ended up in `metadata`, not just that a score was returned.
  Location: `tests/unit/ai/goals/test_social_contract_goal_scorer.py`

### AC3 — `accept_contract()`'s `GoalScore` clears `evaluate_project_switch()`'s comparison to become `current_project_id`

- **`test_active_contract_wins_arbitration_with_no_current_project`**
  Category: integration (exercises `evaluate_strategic_intent()` end-to-end, not just the scorer)
  Verifies: entity has no current project, one `ACTIVE` RECRUITMENT (or LOAN) contract. Run
  `StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)`. Assert
  `entity.strategic.current_project_id` becomes the materialized contract project's id (via the
  returned `StrategicUpdate.current_project_id_set`), through `evaluate_project_switch()`'s
  unconditional-adopt path (`intelligence.py:985-998`) — confirming AC3's "clear the comparison" claim
  concretely, not just that *a* score was produced.
  Location: `tests/unit/strategic/test_social_contract_materialization.py` (new file, mirrors
  `test_adventure_route_materialization.py`'s own file-per-mechanism granularity).

### AC4 — Materialized `ProjectState.kind` uses a real `ProjectKind` member; raw-score/utility separation preserved

- **`test_social_contract_winner_materializes_with_raw_score_not_utility`**
  Category: integration
  Verifies, with concrete worked arithmetic in the docstring (mirroring
  `test_adventure_route_winner_materializes_with_raw_score_not_utility`'s style): force a
  `SocialContractGoalScorer` win via a fixed, known raw score (monkeypatch or a controlled contract
  fixture), run `evaluate_strategic_intent(..., force=True)` end-to-end, and assert the resulting
  `ProjectState.score` equals the **raw** score, explicitly **not** the normalized utility — plus a
  negative check (`project.score != <utility value>`) for the same silent-regression reason as the
  adventure ticket's own highest-value guard.
  Also assert `project.kind` is a real `ProjectKind` member (`ProjectKind.COMBAT` for RECRUITMENT,
  `ProjectKind.SOCIAL` for LOAN — matching `accept_contract()`'s pre-existing mapping) — **not**
  `GoalKind.SOCIAL_CONTRACT` itself, confirming the new branch actually ran the contract-specific
  mapping rather than falling through to the generic construction at `intelligence.py:1469-1486`
  (which would wrongly produce a `GoalKind`-typed project).
  Location: `tests/unit/strategic/test_social_contract_materialization.py`

- **`test_social_contract_recruitment_maps_to_combat_project_loan_maps_to_social_project`**
  Category: unit or integration (whichever plan.md's mapper shape supports directly)
  Verifies both of `accept_contract()`'s pre-existing kind mappings are preserved exactly by the new
  path: RECRUITMENT → `ProjectKind.COMBAT`, `ObjectiveKind.REACH_LOCATION`, `target=str(source_id)`;
  LOAN → `ProjectKind.SOCIAL`, same objective shape. Direct regression guard for investigation.md's
  "delegating to `ContractService`'s existing unchanged internal contract-acceptance logic" scope
  constraint — this test would fail if Implement accidentally changes either mapping while extracting
  it into a reusable form.
  Location: `tests/unit/strategic/test_social_contract_materialization.py` or co-located with the
  extracted mapping helper's own unit tests, per plan.md's chosen file layout.

- **`test_social_contract_protection_merchant_position_swap_never_spawn_a_project`**
  Category: unit
  Verifies investigation.md's documented pre-existing coverage gap is preserved, not silently widened:
  an `ACTIVE` `PROTECTION`/`MERCHANT`/`POSITION_SWAP` contract produces `GoalScore(utility=0.0,
  target_id=None)` from `SocialContractGoalScorer.score()` (or is simply never considered a
  materializable candidate), exactly matching `accept_contract()`'s existing `if obj:` guard behavior
  for these 3 of 5 `ContractKind` members today.
  Location: `tests/unit/ai/goals/test_social_contract_goal_scorer.py`

### AC5 — high-lock current project + low-urgency contract keeps its project

- **`test_high_lock_current_project_retains_against_low_urgency_contract`**
  Category: integration
  Verifies, with concrete worked arithmetic (mirroring
  `test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate`'s existing style): entity
  has a locked (`lock_until_tick > current_tick`), high-score current project plus a newly-`ACTIVE`,
  deliberately low-raw-score contract. Run `evaluate_strategic_intent(..., force=True)`. Assert
  `entity.strategic.current_project_id` is **unchanged** (still the original locked project) — the
  contract does not win. This is the ticket's single most important behavioral proof, directly named in
  AC5's own wording.
  Location: `tests/unit/strategic/test_social_contract_materialization.py`

### AC6 — no current project, or a contract that legitimately outscores the lock, does switch

- **`test_no_current_project_contract_wins_immediately`**
  Category: integration
  Same setup/mechanism as the AC3 test above — may be the same test if plan.md consolidates them, or a
  distinct one if AC3's test is scoped narrower (arbitration-clearing) vs. this one (end-state
  assertion). Flag for Plan/Implement to de-duplicate deliberately rather than accidentally.
  Location: `tests/unit/strategic/test_social_contract_materialization.py`

- **`test_high_urgency_contract_interrupts_locked_current_project`**
  Category: integration
  Verifies, with concrete worked arithmetic (mirroring
  `test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`'s existing style): a
  locked current project plus a deliberately high-raw-score contract (calibrated per whatever ceiling
  Plan settles on for investigation.md Risk #1) clears both `candidate_pct > normalized_effective_current_pct`
  and the `0.8` urgency floor, and the contract **does** win — `current_project_id` switches to the
  materialized contract project.
  Location: `tests/unit/strategic/test_social_contract_materialization.py`

### AC7 (Materialized `ProjectState.kind` real member) — covered by AC4's tests above; no separate test needed.

### `_score_scale_max` scale-sharing regression guard (investigation.md Risk #1, whichever way Plan resolves it)

- **`test_social_contract_and_adventure_route_share_or_separate_score_scale_as_designed`**
  Category: unit
  Verifies explicitly, by name, whichever resolution Plan records for investigation.md Risk #1: either
  (a) `_score_scale_max(ProjectKind.COMBAT-from-a-contract) == _score_scale_max(ProjectKind.COMBAT-from-
  adventure's-HUNT_WEAK_ENEMY) == _ADVENTURE_ROUTE_SCORE_MAX` (deliberate shared-scale design), or (b) a
  new, distinct constant is returned for contract-originated projects if Plan chose to extend
  `_score_scale_max()`'s classification. This test exists specifically so the resolution is asserted in
  code, not just narrated in plan.md — the same "force the resolution to be visible" discipline the
  adventure ticket applied to its own Risk #1 placeholder test.
  Location: `tests/unit/strategic/test_social_contract_materialization.py` or
  `tests/unit/strategic/test_score_normalization.py`, whichever plan.md designates as the score-scale
  regression home.

### Test rewrite — `test_accepted_contract_spawns_project_and_objective`

Per the ticket's own Scope: "rewritten as a scorer-output assertion (not just extended)." Current test
(`tests/unit/strategic/test_strategic_social_contracts.py:8-36`, full text confirmed by direct read)
asserts directly on `ContractService.accept_contract()`'s return value:
```python
strat_up = ContractService.accept_contract(ent, "c1", tick=100)
assert strat_up.current_project_id_set == "proj_contract_c1"
assert len(strat_up.projects_add_or_update) == 1
proj = strat_up.projects_add_or_update[0]
assert proj.id == "proj_contract_c1"
assert proj.kind == "combat"
assert len(proj.objectives) == 1
assert proj.objectives[0].id == "obj_recruit_c1"
assert proj.objectives[0].target == "2"
```
**Must be rewritten**, not extended, because every one of these assertions describes the exact bypass
behavior AC1 removes (`current_project_id_set` being set directly by `accept_contract()`, and the
project appearing in `accept_contract()`'s own `projects_add_or_update` rather than via the scorer +
materialization branch). The rewrite should assert instead:
1. `ContractService.accept_contract(ent, "c1", tick=100)` returns a `StrategicUpdate` with
   `current_project_id_set is None` (moved to the AC1 test above, or duplicated here per plan.md's
   choice) and the contract's own status transition still correct (`contracts_add_or_update[0].status
   == ContractStatus.ACTIVE`) — the part of the old test that remains true.
2. `SocialContractGoalScorer().score(ent_with_active_contract, state)` produces a `GoalScore` whose
   `metadata["raw_score"]` and contract-identity fields are populated as designed.
3. Running the full `evaluate_strategic_intent()` arbitration on that entity produces the same
   `ProjectState`/`ObjectiveState` shape the old test asserted directly (`proj.kind == ProjectKind.COMBAT`
   — note: the **old** test asserts the bare string `"combat"`, which coincidentally equals
   `ProjectKind.COMBAT.value`; the rewrite should assert `proj.kind == ProjectKind.COMBAT` the enum
   member, not the string, per AC "uses a real `ProjectKind` enum member" — a meaningful upgrade in
   assertion precision, not just a mechanical port).
Location: `tests/unit/strategic/test_strategic_social_contracts.py` (same file, replacing the existing
test body) — do not create a duplicate file; the ticket's own Scope names this exact
file/test.

## Scoped Pytest Commands

```
pytest tests/unit/ai/goals/ tests/unit/strategic/test_expanded_goals.py tests/unit/strategic/test_score_normalization.py tests/unit/strategic/test_enum_drift.py tests/unit/strategic/test_adventure_route_materialization.py tests/unit/strategic/test_social_contract_materialization.py tests/unit/strategic/test_strategic_social_contracts.py tests/unit/strategic/test_interruption_resistance.py tests/unit/social/ -v
```

Never `pytest tests/`. This scopes to: the new scorer's own unit tests (alongside the existing
`AdventureGoalScorer` tests, confirming no cross-scorer interference), the goal-competition/
normalization regression surface, `GoalRegistry` enum-validation invariants, both materialization
branches' tests (adventure's existing one + this ticket's new one), the rewritten
`test_strategic_social_contracts.py`, and the full `tests/unit/social/` contract-lifecycle suite
(appraisal, recruitment, betrayal, party formation via contracts) to catch any accidental disturbance
outside the strategic-cognition layer.

## Anti-Drift Test Guards

- **`test_accept_contract_no_longer_sets_current_project_id_directly`**'s negative assertion is the
  single highest-value regression guard this ticket must not introduce a silent revert of — a future
  edit accidentally reintroducing the direct write would otherwise be invisible until a locked-project
  starvation bug resurfaces in production, exactly the failure mode this whole epic exists to close.
- **`test_social_contract_winner_materializes_with_raw_score_not_utility`**'s negative assertion
  (`project.score != <utility value>`) catches the same silent scale-mismatch regression class already
  fixed once for adventure and flagged here as doubly-important given the shared `_score_scale_max`
  finding.
- **`test_social_contract_protection_merchant_position_swap_never_spawn_a_project`** guards against
  silent scope creep — a future edit "helpfully" widening contract-kind coverage without an explicit
  Plan decision would break this test loudly instead of silently changing behavior for 3 previously-
  inert `ContractKind` members.
- **`test_contract_lifecycle_acceptance`** (existing, `tests/unit/social/test_contract_lifecycle.py`,
  kept passing unmodified) guards that the contract-status-transition half of `accept_contract()` — the
  part genuinely unrelated to the arbiter bypass — is not accidentally broken while removing the
  project-spawn half.
- **`test_adventure_route_winner_materializes_with_raw_score_not_utility`** and the other 3 existing
  tests in `test_adventure_route_materialization.py`, run as part of the regression surface (not
  skipped), guard against the new `elif GoalKind.SOCIAL_CONTRACT:` branch accidentally being written as
  a replacement for, rather than an addition alongside, the existing `ADVENTURE_ROUTE` branch.
- **`test_social_contract_and_adventure_route_share_or_separate_score_scale_as_designed`** is an
  explicit anti-drift guard against investigation.md Risk #1 being silently resolved during Implement
  without the resolution being recorded in plan.md first and asserted in code — same discipline as the
  adventure ticket's own Risk #1 placeholder-test pattern.
