# TCK-20260415-CORRECTIVE-PLANS

## Title

Execute Remaining Corrective Plan Tasks (strategy_implementation_updated_v2 + intel_capacity_implementation_updated)

## Status

DONE

## Request Summary

Systematically complete all remaining tasks from the two corrective implementation plans.

## Scope

### Batch 1 — Infrastructure Isolation (Cross-Cutting Track Task 1)
- Brokerless import smoke tests for RabbitMQ/Kafka disabled mode

### Batch 2 — Cognition Capacity Derivation Proof (Intel M1 Task 2)
- Deterministic builder tests for personality, trait, archetype, overload inputs

### Batch 3 — Budget Enforcement Proof (Intel M2 Task 1)
- candidate_zone_limit and ally_evaluation_limit capping tests

### Batch 4 — Inspector Smoke Expansion (Strategy M1 Task 1 completion)
- Empty-state, uncertainty-section, contracts/offers/obligations smoke tests

### Batch 5 — Resume & Explainability (Strategy M2)
- Resume-restores-objective test
- Strategic explainability assertions

### Batch 6 — Downstream Feedback Loops (Strategy M5 Task 2 completion)
- False-lead-to-source-weighting test
- Severe-failure-to-reattempt test

### Batch 7 — Cognition Scope Documentation (Strategy M6 Task 2)
- Document included vs excluded cognition domains

### Batch 8 — Replay/Graph Consistency (Cross-Cutting Track Tasks 2-3, Strategy M7)
- Repair stale replay-vs-graph assertion paths
- Truth-surface ownership documentation
- Deepen replay-vs-graph consistency assertions

### Batch 9 — Documentation Integrity (Intel M8)
- End-to-end doc-alignment tests against populated artifacts

## Out of Scope

- New feature development
- Pre-existing test failures unrelated to these plans

## Acceptance Criteria

- All checklist items in both corrective plans are marked done or explicitly descoped
- All new tests pass
- No regressions

## Related Tickets

- TCK-20260415-PIPELINE-IDEMPOTENCY
- TCK-20260414-LEARNING-SOCIAL-CONSEQUENCE

## Implementation Notes

- **Batch 8**: Implemented directive-to-project promotion in `BoundedStrategicAppraisalService` to ensure entity bootstrapping in minimal environments. Synced `ReplayRecorder` with Milestone 2 contracts to resolve consistency assertion failures (`detour_depth_used` parity).
- **Batch 9**: Expanded `docs/bounded_cognition_feature_spec.md` with full Milestone 2 fields and added `tests/ai/test_doc_artifact_integrity.py` to verify documentation vs actual artifacts (Replay/Graph).

## Test Summary

- `tests/e2e/strategy/test_strategic_regression.py`: 5/5 PASSED
- `tests/ai/test_doc_artifact_integrity.py`: 1/1 PASSED

## Files Changed

- `src/ai/strategic_bounded_appraisal.py`
- `src/ai/brain.py`
- `src/utils/replay.py`
- `src/core/logic/cognition_graph_exporter.py`
- `src/testing/assertions.py`
- `docs/bounded_cognition_feature_spec.md`
- `tests/ai/test_doc_artifact_integrity.py`

## Completion Summary

Successfully hardened the strategic cognition pipeline by resolving cross-artifact parity issues and ensuring deterministic entity bootstrapping from directives. The documentation is now strictly aligned with implementation through automated integrity tests.
