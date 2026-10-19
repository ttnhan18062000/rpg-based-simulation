---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261019-D80B-ENGINE-STOPS-IMPORTING-SIMQ-POST-APPLY-OBSERVER-HOOK
phase: inprogress
date: 2026-10-19
tags: [observability]
---

# TCK-20261019-D80B-ENGINE-STOPS-IMPORTING-SIMQ-POST-APPLY-OBSERVER-HOOK

## Title
The engine stops importing SimQ: a generic post-apply observer hook replaces kernel.py's SimQ hub wiring (D80 B)

## Status
INPROGRESS

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Decision 80 (B). The kernel builds SimQ itself: src/engine/kernel.py:230-272 imports src.simulation_quality (the feed, QualityHub, ScoringWeights, QualityPersistence, build_all_scorers), wires `quality_fn=_hub.on_envelope` into EventRecorder, and stops it and reads the report at about 1148-1167. This is step 1 after baseline v1, under memo row 82.

## Scope
- A typed observer registry that the kernel calls after authoritative apply. The kernel knows no observer types.
- SimQ registers from outside src/engine, at the composition root (API or run harness).
- Move the RunLedger onto the same hook if that fits without changing its output.
- Add an import-linter contract: src.engine must not import src.simulation_quality.

## Out of Scope
- How SimQ reads events (D80 C).
- Any change to scorers or grades (D77).

## Acceptance Criteria
- The final hash is identical to the v1 record on 3 gate worlds x seed 42, with observability ON and OFF.
- The new lint-imports contract passes.
- The SimQ report is unchanged on one calibration run.
- Paired numbers are recorded as their own step (memo row 82).

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (must land first)
- TCK-20261019-D80B-ENGINE-STOPS-IMPORTING-SIMQ-POST-APPLY-OBSERVER-HOOK, TCK-20261019-D80C-SIMQ-READS-THE-LOSSLESS-EVENT-FILE-OFFLINE, TCK-20261019-D80D-UNGRADED-SIMQ-DATA-REVIEW-ON-THE-V1-RECORD (order B, C, D, then D73)
- TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 (testing)

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md rows 77, 80, 82 (82 on rpg-designer-after-v1 ff0a4a9df until it merges)
- docs/plans/systemic_world/v1_disclosure.md (E, Q sections)

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/kernel.py (230-272, 1148-1167)
- src/observability/event_recorder.py (quality_fn)
- src/simulation_quality/
- importlinter config

## Assumptions / Open Questions
- Order and guards per memo row 82 (rpg-designer, user-confirmed 2026-10-19). B, C and D73 may share batch 1 under the PR size rule, each as its own measured step.

## Implementation Notes
- Naming (rpg-planner): the hook is a *run observer* (an envelope sink with a four-stage lifecycle: start, on_envelope, stop_intake, finish); the title keeps "post-apply observer hook". RunLedger and DeathLedger are not moved: they are event producers upstream of SimQ, not sinks.
- Fold the decay-record withdrawal (rpg-v2-decay-record, `ResourceTransactionSystem.resolve_all` in `src/engine/economy.py`) into the post-apply hook: emit once from the applied outcome. (Added on rpg-planner's instruction after the designer accepted V2; the intent-versus-outcome emitter list in TCK-20261019-MEAT-DECAYED-IS-WRITTEN-FROM-THE-APPLIED-OUTCOME-V2 is the starting set for the 80(A) audit, not findings.)

## Test Summary
- Scoped, serial (rpg-d80b e1986db65): tests/unit/engine/test_run_observers.py + tests/simulation_quality + tests/api/test_scenario_runtime_api.py: 568 passed, 85 skipped. lint-imports 18 kept, 0 broken (c16 red on the base tree, green here). mypy gate exit 0.
- A wide mixed batch (tests/api, unit/api, unit/kernel, unit/observability, unit/tools, tests/tools, architecture, unit/core, unit/cli, integration/kernel) showed 8 failures that pass in isolation on both rpg-d80b and the V2 branch (rpg-v2-decay-record): mixed-process ordering/host exposure, not D80B. Names: tests/integration/kernel/test_authoritative_outcome_truth.py::test_replay_sources_from_refined_update; tests/unit/core/test_startup_validation.py::test_aggressive_budget_warning; tests/tools/test_shadow_reviewer_call_site.py::test_architecture_verify_shadow_call_emits_distinct_joinable_event and ::test_security_review_shadow_call_emits_distinct_joinable_event; tests/tools/test_skill_usage_metric.py::test_live_corpus_loads_nonempty and ::test_causes_zero_diff_on_real_corpus; tests/tools/test_verify_referential_integrity.py::test_real_corpus_smoke_run; tests/tools/test_verify_temporal_week_consistency.py::test_real_corpus_smoke_run.
- To do after v1 is recorded: rebase onto v1, rerun the wide batch once (clean, or the same 8 also fail on main), then the hash ON/OFF check (3 worlds x seed 42, 5000t) and the calibrate_simq diff against v1.

## Files Changed

## Completion Summary
