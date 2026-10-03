---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260414-COGNITION-EXPLAINABILITY-HARDENING
phase: done
date: 2026-04-14
tags: [cognition, explainability, hardening]
---

# TCK-20260414-COGNITION-EXPLAINABILITY-HARDENING

## Title
Cognition Derivation Hardening & Strategic Explainability

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Address derivation gaps and explainability proof from `intel_capacity_implementation_updated.md` and `strategy_implementation_updated_v2.md`. Hardened the strategic cognition pipeline with robust bounding and transparent observability.

## Scope
- [x] Expand `CognitionCapacityBuilder` to include personality, traits, and archetype derivation.
- [x] Add enforcement proof for `candidate_zone_limit` and `ally_evaluation_limit`.
- [x] Populate `primary_overload_source` and `last_overload_tick` in `AIPresenter`.
- [x] Implement structured strategic explainability assertions (reasons for project switches/locks).
- [x] Add dedicated strategic inspector smoke coverage for uncertainty and contracts.

## Out of Scope
- Infrastructure isolation (covered in TCK-INFRA).
- Social recruitment consequences (covered in TCK-LEARNING).

## Acceptance Criteria
- [x] Builder tests prove that personality/traits affect cognition.
- [x] Regression tests prove `candidate_zone_limit` is enforced during search.
- [x] API output contains `primary_overload_source`.
- [x] `EntityInspector` renders the new overload metadata clearly.
- [x] Strategic decisions have structurally verifiable reasons.

## Related Tickets
- TCK-20260414-INFRA-REMEDIATION (Parallel)

## Related Docs
- intel_capacity_implementation_updated.md
- strategy_implementation_updated_v2.md

## Related Code Areas
- `src/ai/cognition_capacity.py`
- `src/api/presenters/ai_presenter.py`
- `src/ui/cli/inspector.py`
- `tests/ai/test_cognition_capacity_builder.py`
- `tests/integration/strategy/test_strategic_explainability.py`

## Implementation Notes
- Added robust ID resolution for candidate gathering.
- Implemented margin-based `switch_reason` for strategic pivots.

## Test Summary
- **Unit Tests**: `tests/ai/test_cognition_capacity_builder.py` (verified personality/trait effects).
- **Integration Tests**: `tests/integration/strategy/test_strategic_explainability.py` (verified zone/ally enforcement and overload sources).
- **Manual Verification**: Inspected `EntityInspector` output for overload alerts and switch justifications.

## Files Changed
- `src/ai/cognition_capacity.py`
- `src/ai/brain.py`
- `src/ai/strategic_bounded_appraisal.py`
- `src/ui/cli/inspector.py`
- `tests/integration/strategy/test_strategic_explainability.py`

## Completion Summary
Successfully hardened the strategic cognition pipeline. The system now enforces strict deterministic limits on candidate zones and ally evaluations based on the entity's cognitive profile. Enhanced observability now provides transparent reasons for strategic pivots and identifies the specific stressors (trauma, panic, complexity) causing cognitive overload.
