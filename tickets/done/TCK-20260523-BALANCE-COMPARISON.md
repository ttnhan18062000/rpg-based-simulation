# TCK-20260523-BALANCE-COMPARISON

## Title

Milestone 88 — Balance Comparison Engine

## Status

DONE

## Request Summary

Implement the `BalanceComparisonEngine` to compare base variant run results against mutated variant run results, classify the shifts, include structured evidence, and explain findings without claiming absolute root cause.

## Scope

- Define core domain classes/models for balance comparison:
  - `BalanceComparisonReport`: Pydantic model for holding comparison results
  - `BalanceComparisonEngine`: Engine executing metric differential analysis
- Support comparison dimensions:
  - `health_score` (higher is better)
  - `critical_anomalies` or `critical_count` (lower is better)
  - `hard_law_violations` or `hard_law_violation_count` (lower is better)
  - `stuck_ratio` or `stuck_entity_ratio` (lower is better)
  - `resource_production` or `resource_production_rate` (higher is better)
  - `quest_completion` (higher is better)
  - `combat_resolution` (higher is better)
  - `runtime_performance` (lower runtime/ticks is better)
  - `memory_usage` (lower is better)
  - `event_volume` (lower or stable is better)
- Support shift classification categories:
  - `IMPROVED`
  - `REGRESSED`
  - `UNCHANGED`
  - `MIXED`
  - `INSUFFICIENT_DATA`
- Ensure scientific humility in explanations (correlation, not absolute root cause).
- Generate `balance_comparison.json` and a structured `balance_comparison.md` report.
- Design unit tests verifying all classification cases.

## Out of Scope

- Mutation Lab Orchestration sweeps (Milestone 89).

## Acceptance Criteria

- Variant with strictly better health score and no regressions is marked `IMPROVED`.
- Variant with hard law violations (or increased violations) is marked `REGRESSED`.
- Mixed metric shifts (e.g. improved health but increased stuck ratio) produce `MIXED`.
- Missing or null essential metric data produces `INSUFFICIENT_DATA`.
- Comparison explicitly includes evidence mapping.
- Explanation avoids causal certainty ("caused by", "proves that") and uses correlative framing.

## Related Tickets

- TCK-20260523-METAMORPHIC-VALIDATION (Done)

## Related Docs

- `lab_phase13.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260523-BALANCE-COMPARISON/`

## Related Code Areas

- `src/lab/comparison.py`
- `tests/unit/lab/test_balance_comparison_engine.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Implemented `src/lab/comparison.py` containing `BalanceComparisonReport` and `BalanceComparisonEngine`.
- Supports 10 comparison dimensions checking both improvement and regression directions.
- Direct regression check flags `REGRESSED` if new hard law violations are introduced or associated metamorphic assertions fail.
- Scientific humility filter replaces any causal certainties with correlative phrasing automatically.
- Writes comprehensive `balance_comparison.json` and scorecard `balance_comparison.md` outputs.

## Test Summary

- Designed 8 comprehensive unit tests covering all shift classifications, evidence mappings, humility filters, and file reporting operations.
- **100% Pass Rate** across 107 unit/integration tests in the `lab` package.

## Files Changed

- `src/lab/__init__.py`
- `src/lab/comparison.py` (New)
- `tests/unit/lab/test_balance_comparison_engine.py` (New)

## Completion Summary

- Milestone 88 is fully implemented, verified, and integrated.
