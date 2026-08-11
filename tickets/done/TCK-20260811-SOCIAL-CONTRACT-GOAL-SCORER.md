---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER
phase: done
date: 2026-08-11
tags: [social, cognition]
---

# TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER

## Title
Generalize GoalScorer-wrapper pattern to social-contract acceptance (contracts.py)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Apply the same wrapper pattern used for adventure to src/systems/social_systems/contracts.py:187 (SocialContractGoalScorer), which today unconditionally overwrites current_project_id without going through the arbiter. Part of the design's Goal #4 (generalizing the wrapper pattern to the other confirmed arbiter-bypass sites); a natural follow-on now that the pattern is established.

## Scope
- New GoalKind member (e.g. SOCIAL_CONTRACT) added to src/core/strategic.py
- New SocialContractGoalScorer (GoalScorer) delegating to ContractService's existing unchanged internal contract-acceptance logic, producing a GoalScore with raw score in metadata (never utility) per the wrapper pattern
- ContractService.accept_contract() no longer sets current_project_id_set directly; the resulting GoalScore must clear evaluate_project_switch()'s comparison to become current_project_id
- Materialized ProjectState.kind uses a real ProjectKind enum member, respecting _score_scale_max's enum-identity classification (not string value)
- tests/unit/strategic/test_strategic_social_contracts.py::test_accepted_contract_spawns_project_and_objective rewritten as a scorer-output assertion (not just extended)

## Out of Scope
- events.py / RegionStabilizationGoalScorer -- structurally independent bypass site with different data shapes, covered by TCK-20260811-REGION-STABILIZATION-GOAL-SCORER
- AdventureGoalScorer and its own materialization path -- TCK-20260811-ADVENTURE-GOAL-SCORER's job; this ticket follows the same pattern but is a separate materialization path

## Acceptance Criteria
- [x] ContractService.accept_contract() no longer sets current_project_id_set directly
- [x] Accepting a contract produces a GoalScore (via new SocialContractGoalScorer) that must clear evaluate_project_switch()'s comparison to become current_project_id
- [x] An entity with a high-lock current project + a newly-accepted low-urgency contract keeps its current project (the contract does not win)
- [x] An entity with no current project, or a contract that legitimately outscores the lock, does switch
- [x] Materialized ProjectState.kind uses a real ProjectKind enum member
- [x] Follows raw-score/normalized-utility separation: metadata["raw_score"], never utility, goes into ProjectState.score
- [x] docs/mechanics and the relevant parity ledger entry updated in the same session -- `docs/mechanics/04_strategic_cognition.md` (Document-Update phase) and `docs/parity_ledger/strategic_cognition.yaml` (STRAT-254) / `docs/parity_ledger/social_narrative.yaml` (SOC-208) (Architecture-Verify round 1 finding + fix, independently re-verified in round 2 and by the Parity phase, which also added `docs/guidelines/intentional_divergences.md` §2.42)

## Related Tickets
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
- TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS

## Related Docs
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/social_systems/contracts.py
- src/ai/goals/base.py
- src/core/strategic.py
- src/systems/strategic_systems/intelligence.py
- src/ai/goals/scorers.py

## Assumptions / Open Questions
- This is a real behavior change: today accepting a contract ALWAYS wins the project slot; post-migration it competes and can lose -- this is the explicit point, not a regression
- Needs empirical validation of normalization constants (not assumable by formula alone)
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns / Goal #4)

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER/plan.md` Steps 1-8
(Steps 9-10 -- docs/parity and the full regression run -- are this pass's Step 10 test run only;
docs/parity is explicitly deferred to a separate Document-Update/Parity phase per the task's own
instructions).

- Step 1: Added `GoalKind.SOCIAL_CONTRACT = "social_contract"` to `src/core/strategic.py`,
  immediately after `ADVENTURE_ROUTE`, deliberately not `"z_"`-prefixed (Design Decision #5).
- Step 2: Added `ContractService.get_project_mapping()` (RECRUITMENT -> COMBAT, LOAN -> SOCIAL,
  both REACH_LOCATION; None for PROTECTION/MERCHANT/POSITION_SWAP) and simplified
  `accept_contract()` down to only the `transition_contract()` call -- no more inline
  `ProjectState`/`ObjectiveState` construction or `current_project_id_set` write (Design
  Decision #7's duplicate-project hazard).
- Step 3: Created `src/ai/goals/social_contract_scorer.py` with `SocialContractGoalScorer`,
  implementing the raw-score formula exactly as specified (trust/urgency/value/risk_weight,
  clamped to [0.0, 2.9]), the highest-raw-score-wins/contract-id-ascending-tiebreak reduction,
  and the `target_pos` counterparty-position resolution fix (Design Decision #8).
- Step 4: Registered the scorer in `src/ai/goals/__init__.py`.
- Step 5: Added the `elif best_candidate.kind == GoalKind.SOCIAL_CONTRACT:` materialization
  branch in `intelligence.py`'s `evaluate_strategic_intent()`, using
  `best_candidate.metadata.get("raw_score", 0.0)` for `ProjectState.score` (never `.utility`),
  tick-suffixed ids (Design Decision #10), and `lock_until_tick=current_tick+50`.
- Steps 6-8: New test files `tests/unit/ai/goals/test_social_contract_goal_scorer.py` (9 tests)
  and `tests/unit/strategic/test_social_contract_materialization.py` (8 tests); rewrote
  `test_accepted_contract_spawns_project_and_objective` in
  `tests/unit/strategic/test_strategic_social_contracts.py` as a 3-step scorer-output assertion
  (accept_contract -> scorer -> full arbitration), per the ticket's Scope wording.

Deviation from test_plan.md (not a plan.md deviation -- plan.md's own Anti-Drift Notes required
this): added a standalone `test_accept_contract_no_longer_sets_current_project_id_directly` in
`tests/unit/social/test_contract_lifecycle.py` (co-located with the existing
`test_contract_lifecycle_acceptance`) asserting both `current_project_id_set is None` AND
`projects_add_or_update == []`, per plan.md's Anti-Drift Notes explicit instruction ("Implement
must add this assertion even though test_plan.md's own wording only mentions the
current_project_id_set check"). The rewritten `test_strategic_social_contracts.py` test also
exercises this same assertion as its first step (harmless overlap, not exact duplication --
different fixture/entity).

Two of the AC5/AC6 integration tests required arithmetic not spelled out verbatim in
plan.md/test_plan.md and were hand-derived during Implement (documented in each test's own
docstring): (1) the retention test needed the entity's HP below the 80% `_threat_resolved()`
early-release threshold, otherwise `evaluate_project_switch()`'s lock-bypass gate is
unconditionally skipped for a full-HP, no-hostile-nearby entity (a real, previously undocumented
interaction between the SOCIAL_CONTRACT branch and STRAT-236's threat-resolved early release --
not a bug, just an interaction not spelled out in plan.md). (2) The interruption test needed a
low `interruption_resistance` (0.01, mirroring `test_score_normalization.py`'s own pattern for
`ProjectKind`-typed candidates), because a contract-originated candidate's raw score is capped
at 2.9 and can never clear `evaluate_project_switch()`'s final raw
`candidate.score > effective_current_score` check against a current holding the DEFAULT
retention_margin (9.0) -- this is a structural consequence of Design Decision #2 (sharing the
2.9-ceiling scale with ADVENTURE_ROUTE), not something this ticket needed to fix, but it meant
the original test design in test_plan.md's own worked-arithmetic sketch (reusing the same
locked-current values as the retention test) would never have actually switched. Both are
disclosed here and in the test docstrings, not silently patched.

## Test Summary
Ran exactly the test_plan.md-specified scoped command:
```
pytest tests/unit/ai/goals/ tests/unit/strategic/test_expanded_goals.py tests/unit/strategic/test_score_normalization.py tests/unit/strategic/test_enum_drift.py tests/unit/strategic/test_adventure_route_materialization.py tests/unit/strategic/test_social_contract_materialization.py tests/unit/strategic/test_strategic_social_contracts.py tests/unit/strategic/test_interruption_resistance.py tests/unit/social/ -v
```
Result: **259 passed, 0 failed** (includes 18 new tests: 9 in
`test_social_contract_goal_scorer.py`, 8 in `test_social_contract_materialization.py`, 1 new
standalone AC1 guard in `test_contract_lifecycle.py`; plus the rewritten
`test_accepted_contract_spawns_project_and_objective`). No pre-existing test in the regression
surface required an edit to keep passing (confirming no unintended scope creep, per Step 10's own
verify note). `graphify update .` run after all `src/` edits.

## Files Changed
- `src/core/strategic.py` (added `GoalKind.SOCIAL_CONTRACT`)
- `src/systems/social_systems/contracts.py` (added `get_project_mapping()`; simplified
  `accept_contract()`)
- `src/ai/goals/social_contract_scorer.py` (new file: `SocialContractGoalScorer`)
- `src/ai/goals/__init__.py` (registered the new scorer)
- `src/systems/strategic_systems/intelligence.py` (added the `SOCIAL_CONTRACT` materialization
  branch in `evaluate_strategic_intent()`)
- `tests/unit/ai/goals/test_social_contract_goal_scorer.py` (new file)
- `tests/unit/strategic/test_social_contract_materialization.py` (new file)
- `tests/unit/strategic/test_strategic_social_contracts.py` (rewrote
  `test_accepted_contract_spawns_project_and_objective`)
- `tests/unit/social/test_contract_lifecycle.py` (added
  `test_accept_contract_no_longer_sets_current_project_id_directly`)
- `docs/mechanics/04_strategic_cognition.md` (Document-Update: §6.6 third-consumer paragraph for
  `_ADVENTURE_ROUTE_SCORE_MAX`; §2 "Generalized Bypass" clarifying footnote)
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`
  (Document-Update: "Future Extension Patterns" marked done, Post-landing note, component diagram
  updated to move `contracts.py:187` out of the `BYPASS` subgraph)
- `docs/parity_ledger/strategic_cognition.yaml` (Architecture-Verify round-1 finding, fixed
  directly: new `STRAT-254` entry per plan.md Step 9's specification, re-verified by
  Architecture-Verify round 2 and independently re-confirmed by the Parity phase)
- `docs/parity_ledger/social_narrative.yaml` (same pass: `SOC-208`'s `v2_evidence`/`proof_type`/
  `test_path` updated, `status`/`text` left unchanged per plan.md Step 9)
- `docs/guidelines/intentional_divergences.md` (Parity phase: new §2.42 disclosing the
  accept-always-wins-to-arbitrated-competition intentional behavior change, Rationale class
  Enforced)

## Completion Summary
Implemented Steps 1-8 of the approved plan: `GoalKind.SOCIAL_CONTRACT` was added, a new
`SocialContractGoalScorer` was created and registered scanning ACTIVE RECRUITMENT/LOAN contracts
and reducing multiple simultaneous candidates to one raw-scored winner, `accept_contract()` was
simplified to only the status transition (removing the direct `current_project_id_set` write and
the entire inline project/objective construction to avoid a duplicate-project bandwidth hazard),
and a new materialization branch in `evaluate_strategic_intent()` now builds the real
`ProjectState`/`ObjectiveState` from `metadata["raw_score"]` (never `.utility`) through the
existing `evaluate_project_switch()` arbiter. All 7 acceptance criteria are satisfied and covered
by 18 new/rewritten tests plus the full specified regression suite (259 passed, 0 failed).

Architecture-Verify ran 2 rounds: round 1 returned NEEDS_CHANGES for a real gap -- the
Document-Update-phase docs (`04_strategic_cognition.md`, the design doc) cited a parity-ledger
entry `STRAT-254` as "recorded" before it actually existed, a false citation. Fixed directly by
adding the real `STRAT-254` entry to `strategic_cognition.yaml` and updating `SOC-208` in
`social_narrative.yaml`, both per plan.md Step 9's exact specification; round 2 independently
re-verified both entries' file:line citations and all 8 associated tests, then APPROVED. The
subsequent Parity phase re-confirmed both entries correct and found one further gap of its own:
the intentional accept-always-wins-to-arbitrated-competition behavior change (explicit design
point, not a regression, per this ticket's own Assumptions) had no corresponding entry in
`docs/guidelines/intentional_divergences.md` despite the established convention (mirroring
§2.40/§2.41's sibling entries in this same epic) -- fixed by adding §2.42.
