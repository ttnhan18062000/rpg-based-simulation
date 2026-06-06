# TCK-20260509-PIPELINE-AUDIT-HARDENING

## Title
Hardening Authoritative Audit Fidelity & Pipeline Determinism

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Resolve regression failures in `test_rejection_audit_aggregation` and ensure pipeline determinism for actor validity.

## Scope
- Implement Phase 0.0 Global Actor Validity check in `AuthoritativeApplyPipeline`.
- Harden rejection accounting to capture detailed action kinds and target IDs.
- Correlate resource transaction rejections with original intents to preserve audit fidelity.

## Out of Scope
- Major architectural changes to the economy or combat systems.
- Rewriting the entire testing suite.

## Acceptance Criteria
- `test_rejection_audit_aggregation` passes with 100% fidelity.
- `GLOBAL_PROPOSAL` rejections are correctly emitted for dead/inactive entities.
- `ATTACK` and `HARVEST` rejections capture correct target IDs and action kinds.

## Related Tickets
- None

## Related Docs
- AGENTS.md
- architecture.md

## Related Stored Artifacts
- None

## Related Code Areas
- src/engine/pipeline.py
- src/engine/economy.py
- src/engine/domain_logic.py

## Implementation Notes
- Resource intents are now retained (not cleared) in `economy.py` to allow Phase 10.0 rejection accounting to access `transfer_kind`.
- `_resolve_actor_validity` is the absolute first step in `refine`.

## Test Summary
- `pytest tests/engine/test_rejection_audit.py` - PASSED
- `pytest tests/world/test_regional_consequences.py` - PASSED

## Files Changed
- src/engine/pipeline.py
- src/engine/economy.py

## Completion Summary
Stabilized the authoritative audit pipeline. All regression tests for rejection aggregation are now passing. Pipeline determinism is hardened with mandatory actor validity checks at the entry point.
