---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P1F-ABANDONMENT-TYPE
phase: done
date: 2026-06-27
tags: [p1, type-safety, abandonment, dataclass, enum, commitment]
---

# TCK-20260627-P1F-ABANDONMENT-TYPE

## Title
Replace `AbandonmentEvaluator` untyped dict return with `AbandonmentClassification` dataclass

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P1

## Request Summary
`AbandonmentEvaluator.evaluate_abandonment()` in `src/domains/commitment/abandonment.py` returns `Dict[str, Any]` carrying mechanical fields `is_betrayal` (bool) and `penalty` (float). A key rename silently breaks callers with no type error. This must be replaced with a typed dataclass. Source: D12 F2, Priority 9/15.

## Scope
- Define `AbandonmentCategory` enum: `SURVIVAL / GREEDY_DESERTION / VOLUNTARY_QUIT`.
- Define `AbandonmentClassification` dataclass with fields: `is_betrayal: bool`, `penalty: float`, `category: AbandonmentCategory`.
- Update `AbandonmentEvaluator.evaluate_abandonment()` return type and all callers.
- Add parity test that `evaluate_abandonment()` returns an `AbandonmentClassification` instance.

## Out of Scope
- Changes to abandonment scoring logic / values.
- Other untyped dicts in the commitment domain.

## Acceptance Criteria
- [x] `AbandonmentCategory` enum and `AbandonmentClassification` dataclass defined in `src/domains/commitment/abandonment.py`.
- [x] `evaluate_abandonment()` annotated to return `AbandonmentClassification`.
- [x] All callers updated — no `Dict[str, Any]` remains at the call sites.
- [x] Parity test: `isinstance(result, AbandonmentClassification)` asserted.
- [x] Existing type-check gate passes (7/7 tests GREEN).

## Related Tickets
- TCK-20260627-P2I-WORKFLOW-TYPES (related typing clean-up sprint)
- TCK-20260627-P2J-PATCHES-TYPE (related typing clean-up sprint)

## Related Docs
- `docs/audits/D12_pattern_consistency.md` F2
- `docs/parity_ledger/social_narrative.yaml` — entry SOC-ABAND-TYPE-01 added

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-D12/` — pattern audit investigation
- `stored_artifacts/TCK-20260627-P1F-ABANDONMENT-TYPE/` — staging artifacts

## Related Code Areas
- `src/domains/commitment/abandonment.py` (primary)
- `tests/unit/domains/commitment/test_phase15_abandonment_evaluator.py`
- `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`

## Assumptions / Open Questions
- Mapping from `reason` string to `AbandonmentCategory` was 1-to-1; confirmed before implementing.
- Only two caller files outside `reviews/` (generated exports, not updated manually).

## Implementation Notes
- `AbandonmentCategory(str, Enum)` — str mixin allows direct string comparison if needed.
- `AbandonmentClassification(frozen=True)` — immutable, safe to return from static evaluator.
- `reviews/src_export.py` and `reviews/test_export.py` are generated artifacts; not manually updated.

## Test Summary
7/7 tests pass: `pytest tests/unit/domains/commitment/ tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`

## Files Changed
- `src/domains/commitment/abandonment.py`
- `tests/unit/domains/commitment/test_phase15_abandonment_evaluator.py`
- `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`
- `docs/parity_ledger/social_narrative.yaml` (entry SOC-ABAND-TYPE-01 appended)

## Completion Summary
Replaced `Dict[str, Any]` return from `AbandonmentEvaluator.evaluate_abandonment()` with a typed
`AbandonmentClassification` frozen dataclass. Added `AbandonmentCategory(str, Enum)` with three
members mapping 1-to-1 to the existing `reason` string values. Updated both test callers from dict
subscript access to attribute access. Added parity test `test_evaluate_abandonment_returns_typed_classification`
covering all three branches with `isinstance` and `.category` assertions. Parity ledger entry
SOC-ABAND-TYPE-01 added to `social_narrative.yaml`. 7/7 tests GREEN.
