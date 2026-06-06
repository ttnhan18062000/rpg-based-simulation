# TCK-20260529-COG-PHASE17-TRACE

## Title

Derived Views and Decision Trace Contract Domain Implementation

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement Phase 17 to standardize derived view calculations and establish a unified decision-tracing contract and validator to make all complex choices inspectable and readable.

## Scope

- Implement DerivedView builders for combat, adventure, and recovery readiness.
- Implement `DecisionTrace` schemas and considered/rejected option trace elements.
- Implement `DecisionTraceValidator` supporting STRICT/WARN/OFF validation modes.
- Implement `CausalityChainReporter` reconstructing end-to-end chains from perception to outcome.
- Implement unit, integration, and scenario tests under `tests/`.

## Out of Scope

- Storing any dynamic, transient derived view metrics in core state.

## Acceptance Criteria

- Derived views are computed entirely on the fly from current aspects.
- Decision traces capture noticed, known, needed, considered, selected, and expected results.
- Decision traces are validated strictly according to active modes.
- All unit and scenario integration tests verify these requirements and pass cleanly.

## Related Tickets

- `TCK-20260529-COG-PHASE16-EMOTION`

## Related Docs

- `docs/entity/entity_base.md`

## Related Code Areas

- `src/views/` (created)
- `src/observability/` (modified)

## Test Summary

- 4 unit tests verifying views, traces, and validators.
- 2 integration scenario tests verifying combat loss trace details and cooperative betrayal causality.
- All tests pass cleanly.

## Files Changed

- `src/views/readiness.py`
- `src/observability/trace.py`
- `src/observability/validator.py`
- `src/observability/reporter.py`
- `tests/unit/views/test_phase17_derived_readiness_views.py`
- `tests/unit/observability/test_phase17_decision_trace_contract.py`
- `tests/unit/observability/test_phase17_decision_trace_validator.py`
- `tests/unit/observability/test_phase17_causality_chain_reporter.py`
- `tests/integration/scenarios/test_phase17_decision_trace_scenarios.py`
- `docs/entity/entity_base.md`

## Completion Summary

All Phase 17 derived views and decision trace contract logic have been fully implemented and verified with comprehensive unit and scenario-driven integration tests, passing cleanly with zero regressions.
