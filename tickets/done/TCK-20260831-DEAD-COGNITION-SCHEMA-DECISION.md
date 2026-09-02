---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION
phase: done
date: 2026-08-31
tags: [cognition]
---

# TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION

## Title
Decide keep-or-cut for the dead SelfModel cognition schema wrapper

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Prune or finish the dead cognition schema. core/cognition.py's SelfModel is a genuinely dead wrapper that re-wraps self_model.py's own component classes, with zero production constructions anywhere. AttentionFocusService already reads a path (entity.cognition.subjective.self.needs.dominant_need) that nothing ever writes — currently masked only because ENABLE_SELF_MODEL_COGNITION defaults OFF, and this bug will start firing silently the moment that flag flips on, so it must be fixed as part of this decision, not left for later.

## Scope
- Make and record an explicit keep-or-cut decision scoped to SelfModel/SubjectiveModel.self specifically (not the whole cognition.py file, since PerceptionModel/EmotionalModel/TemporalModel are genuinely live sibling fields), in docs/architecture/cognition_domain_ownership.md or a new ADR.
- If cut: remove SelfModel, repoint cognition_accessors.py's get_self_awareness/get_need_interpretation/get_capability_estimate to entity.self_model.*, and repoint AttentionFocusService to read the real self_model path, proven by a test using the real SelfModelUpdatePhase path (not a hand-built cognition.py shell).
- If kept: add a real writer so entity.cognition.subjective.self.needs.dominant_need is actually populated, and add an ownership row for it in cognition_domain_ownership.md.
- Resolve and record the idea 22 and idea 24 open questions using investigation evidence: idea 22 (Relationship Roles, shipped in M1) is confirmed unrelated/moot; idea 24 (Personal Economy) is confirmed informed-but-not-blocked by a separate not-yet-filed MotivationModel.values foundation ticket.

## Out of Scope
- PerceptionModel, EmotionalModel, and TemporalModel fields in cognition.py — genuinely written by real pipeline phases, not part of this decision's scope.
- Filing the separate MotivationModel.values foundation ticket that idea 24 actually depends on.

## Acceptance Criteria
- [x] Ticket records an explicit keep-or-cut decision scoped to SelfModel/SubjectiveModel.self specifically (not the whole file), persisted in docs/architecture/cognition_domain_ownership.md or a new ADR.
- [x] If cut: SelfModel is removed, cognition_accessors.py's get_self_awareness/get_need_interpretation/get_capability_estimate are repointed to entity.self_model.*, and AttentionFocusService is repointed to read the real self_model path, proven by a test using the real SelfModelUpdatePhase path (not a hand-built cognition.py shell).
- [ ] If kept: a real writer is added so the path is actually populated, and cognition_domain_ownership.md gains a row naming its owner. (N/A — decision was CUT, not keep.)
- [x] Idea 22/24 open question is answered with the evidence above, recorded in the ticket, not left open.

## Related Tickets
- TCK-20260824-RELATIONSHIP-ROLE-FIELD
- TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK
- TCK-20260824-WIRE-ORPHANED-MECHANISMS

## Related Docs
- docs/architecture/cognition_domain_ownership.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/cognition.py
- src/core/self_model.py
- src/core/cognition_accessors.py
- src/domains/perception/service.py
- src/cognition/self_model_phase.py
- src/engine/pipeline.py

## Assumptions / Open Questions
- **Decision: CUT.** `core/cognition.py::SelfModel`/`SubjectiveModel.self` are removed. They had
  zero production constructions anywhere in `src/`; the real self-model system
  (`entity.self_model`, `SelfModelBundle`, `src/core/self_model.py`) is already wired via
  `SelfModelUpdatePhase` (gated by `ENABLE_SELF_MODEL_COGNITION`) and has 6+ real consumers.
  Adding a second writer for the `cognition.py` copy would create an unreconciled durable-state
  duplication. Recorded in `docs/architecture/cognition_domain_ownership.md`'s new `## Decisions`
  section.
- **Idea 22 (`TCK-20260824-RELATIONSHIP-ROLE-FIELD`) — confirmed unrelated/moot.** It shipped
  against `SocialBond.role` in `src/core/models/social.py`, a different module and data model from
  `cognition.py`'s `RelationshipModel` (`EntityState.social` vs.
  `EntityState.cognition.relationships`).
- **Idea 24 (`TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`) — confirmed informed-not-blocked.** Its
  own scoping work is complete, but its deferred implementation ACs remain blocked on a separate,
  not-yet-filed `MotivationModel.values` foundation ticket — unrelated to `SelfModel`
  specifically.
- **Disclosed follow-up gap (not silently expanded into this ticket).** `PerceptionUpdatePhase`
  (and therefore the entire `PerceptionFilterService`/`AttentionFocusService`/
  `SignalSalienceEvaluator` chain) has zero call sites in `AuthoritativeApplyPipeline.refine()` —
  it does not run in production at all, independent of any feature flag. This is a separate,
  materially larger orphan-phase-wiring gap discovered during this ticket's investigation, out of
  scope for this keep/cut decision. Disclosed in `docs/simulation/domains/perception_contract.md`
  (a one-sentence note after the "Authoritative status" line). Recommend filing a new ticket to
  either wire `PerceptionUpdatePhase` into the pipeline or leave it explicitly documented as
  intentionally-not-yet-wired.

## Implementation Notes
Followed `staging_artifacts/TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION/plan.md` Steps 1-13 in
order:
- Step 1: Removed `SelfModel` dataclass and the `self` field from `SubjectiveModel` in
  `src/core/cognition.py`; dropped its now-unused `SelfAwarenessComponent`/
  `NeedInterpretationComponent`/`CapabilityEstimateComponent` imports. `RecoveryState` was kept
  untouched (it has an independent consumer, `RecoveryReadinessService`, outside `SelfModel`).
- Step 2: Repointed `cognition_accessors.py`'s `get_self_awareness`/`get_need_interpretation`/
  `get_capability_estimate` to `entity.self_model.self_awareness`/`.needs`/`.capabilities`.
- Step 3: Repointed `AttentionFocusService.get_attention_focus()` to
  `entity.self_model.needs.dominant_need`.
- Steps 4-5, 7: Rewrote `tests/unit/entity/test_phase11_cognition_model_schema.py`,
  `tests/unit/domains/perception/test_phase12_attention_focus_service.py`,
  `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py`, and
  `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py` off the dead
  hand-built `cognition.py::SelfModel(...)` shell, onto real `entity.self_model`
  (`SelfModelBundle`) construction. `test_phase16_...`'s `test_near_death_prevents_immediate_retry`
  was simplified to call `RecoveryReadinessService` directly against a standalone `RecoveryState`
  value, since it was never actually read back from `entity` for any other purpose.
- Step 6: Added `test_attention_focus_reads_real_self_model_dominant_need` to
  `tests/integration/domains/perception/test_phase12_perception_phase.py`, exercising the real
  `SelfModelUpdatePhase.run()` writer (low-health entity → genuine `dominant_need == "healing"`)
  and then `AttentionFocusService.get_attention_focus()` — proof via the real writer path, not a
  hand-built shell.
- Step 8: Added `test_self_model_cognition_wrapper_deleted_and_not_reintroduced` to
  `tests/integrity/test_logic_guards.py`, modeled on the file's existing
  `test_evolution_service_deleted_and_not_reintroduced` precedent.
- Step 9: Updated `docs/simulation/domains/perception_contract.md`'s Inputs table row to
  `entity.self_model.needs.dominant_need`, and added the disclosure sentence after the
  "Authoritative status" line noting `PerceptionUpdatePhase` has zero pipeline call sites today.
- Step 10: Added a `## Decisions` section to `docs/architecture/cognition_domain_ownership.md`
  recording the CUT decision.
- Step 11: Added `tests/tools/test_cognition_domain_ownership_decision.py` guarding that doc
  content.
- Step 12: Added parity ledger entry `STRAT-261` to `docs/parity_ledger/strategic_cognition.yaml`
  via `tools/parity_ledger_writer.py`'s schema-validating `write_entry()` (not raw Edit), which
  also rebuilt the derived parity index in-process.
- Step 13: this section plus the Assumptions/Open Questions resolution above.

**Deviation from plan (recorded in `staging_artifacts/.../plan.md`'s Deviations section too):**
Step 7 named a third file, `tests/unit/domains/perception/test_phase17_decision_trace_scenarios.py`,
as a possible `SelfModel`-importing file to check. That path does not exist; the actual file is
`tests/integration/scenarios/test_phase17_decision_trace_scenarios.py`, which imports `SelfModel`
but never constructs it — the dead import was dropped per the plan's own fallback instruction for
that case ("if it only imports the type without constructing it, drop the dead import").

## Test Summary
Ran (via `.venv/bin/python3 -m pytest`, since bare `python3` lacks `pydantic` in this sandbox):
- `tests/unit/entity/test_phase11_cognition_model_schema.py`
- `tests/unit/domains/perception/test_phase12_attention_focus_service.py`
- `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py`
- `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py`
- `tests/integration/domains/perception/test_phase12_perception_phase.py`
- `tests/integrity/test_logic_guards.py`
- `tests/tools/test_cognition_domain_ownership_decision.py`

All 24 passed (2 pre-existing xfails, unrelated to this ticket). Also ran a broader scoped sweep,
`pytest tests/ -k "cognition or self_model or attention or perception or recovery" -m "not slow"`:
441 passed, 1 skipped, 3 failed. The 3 failures (`tests/cli/test_cognition_cli.py`) are a
pre-existing sandbox-environment issue unrelated to this change — those tests subprocess-invoke
bare `python3 -m src ...`, which lacks `pydantic` in this sandbox (the venv used to run pytest
itself is not what the subprocess invokes); confirmed by `git stash`-ing all changes and
re-running the same file, which fails identically on the pre-change tree. Also ran
`tests/tools/test_parity_index.py` (40 passed) and `tests/tools/test_parity_index_baseline.py`
(15 passed) to confirm the new `STRAT-261` entry didn't drift the parity-index baseline.

## Files Changed
- `src/core/cognition.py`
- `src/core/cognition_accessors.py`
- `src/domains/perception/service.py`
- `tests/unit/entity/test_phase11_cognition_model_schema.py`
- `tests/unit/domains/perception/test_phase12_attention_focus_service.py`
- `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py`
- `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py`
- `tests/integration/scenarios/test_phase17_decision_trace_scenarios.py`
- `tests/integration/domains/perception/test_phase12_perception_phase.py`
- `tests/integrity/test_logic_guards.py`
- `tests/tools/test_cognition_domain_ownership_decision.py` (new)
- `docs/simulation/domains/perception_contract.md`
- `docs/architecture/cognition_domain_ownership.md`
- `docs/parity_ledger/strategic_cognition.yaml`
- `staging_artifacts/TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION/plan.md` (Deviations section)
- `staging_artifacts/TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION/investigation.md`,
  `staging_artifacts/TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION/test_plan.md` (pre-existing from
  this run's own Investigate/Plan phases; unchanged by Implement)
- `tickets/inprogress/TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION.md` (this file)

## Completion Summary
Cut the dead `core/cognition.py::SelfModel`/`SubjectiveModel.self` wrapper (zero production
constructions anywhere) and repointed its three readers — `cognition_accessors.py`'s
`get_self_awareness`/`get_need_interpretation`/`get_capability_estimate` and
`AttentionFocusService.get_attention_focus()` — to the real, already-wired `entity.self_model.*`
path (`SelfModelBundle`, written by `SelfModelUpdatePhase`). Rewrote every test that hand-built the
dead `cognition.py::SelfModel(...)` shell to build `entity.self_model` directly instead, and added
a new integration test that proves the `AttentionFocusService` repoint via the real
`SelfModelUpdatePhase.run()` writer path. Recorded the CUT decision in
`docs/architecture/cognition_domain_ownership.md`, added parity ledger entry `STRAT-261`, added a
reintroduction guard test, and resolved both open questions (idea 22 confirmed unrelated/moot,
idea 24 confirmed informed-not-blocked) plus disclosed the separately-scoped
`PerceptionUpdatePhase` pipeline-wiring gap found during investigation, without expanding into
fixing it.
