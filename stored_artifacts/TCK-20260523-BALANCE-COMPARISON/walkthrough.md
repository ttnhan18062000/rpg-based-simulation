# Balance Comparison Engine - Walkthrough

We have successfully implemented **Milestone 88 — Balance Comparison Engine** of the Mutation and Balance Lab (Phase 13). This completes the engine's capability to analyze metric differentials, apply safety gates, and generate detailed scorecards with absolute scientific humility.

---

## 1. Key Accomplishments

### A. Balance Comparison Engine and Reports (`src/lab/comparison.py`)
- Created `BalanceComparisonReport` carrying structured telemetry evidence, metamorphic summary, and description.
- Created `BalanceComparisonEngine` evaluating differential checks:
  - **Telemetry Check**: Raises `INSUFFICIENT_DATA` if essential fields like `health_score` are absent from metrics.
  - **Multi-Dimensional Metrics Comparison**: Supports standard metrics comparing improvement and regression directions (e.g. stuck ratios, resource production, combat resolution, runtime performance, memory usage).
  - **Safety Violation Gates**: Strictly classifies the shift as `REGRESSED` if new hard law violations are introduced or if associated metamorphic assertions fail.
  - **Classification decision logic**: Categorizes shifts into `IMPROVED`, `REGRESSED`, `UNCHANGED`, `MIXED`, or `INSUFFICIENT_DATA` cleanly.
  - **Scientific Humility**: Built an engine-level validator to ensure explanations use correlative phrasing ("correlates with", "associated with") and strictly avoid causal assertions ("caused by", "proves that").
  - **Output Generation**: Implemented a `write_reports` utility writing the results to `balance_comparison.json` and a beautifully formatted scorecard table in `balance_comparison.md`.

### B. Core API Namespace Export
- Exported the new components cleanly via the package API in `src/lab/__init__.py`.

---

## 2. Verification

### A. Unit Tests (`tests/unit/lab/test_balance_comparison_engine.py`)
Developed 8 comprehensive unit tests verifying:
- Happy paths for IMPROVED classifications.
- Strict REGRESSED classification on hard law violations.
- MIXED classifications.
- INSUFFICIENT_DATA outputs on missing telemetry.
- Evidence mapping delta calculations.
- Strict enforcement of scientific humility correlative wording.
- Integration with metamorphic validation rules.
- File serialization and scorecard markdown generation.

### Test execution summary:
```text
tests/unit/lab/test_balance_comparison_engine.py::test_variant_with_better_health_score_is_marked_improved PASSED [ 12%]
tests/unit/lab/test_balance_comparison_engine.py::test_variant_with_hard_law_violation_is_marked_regressed PASSED [ 25%]
tests/unit/lab/test_balance_comparison_engine.py::test_mixed_metrics_produce_mixed PASSED [ 37%]
tests/unit/lab/test_balance_comparison_engine.py::test_missing_data_produces_insufficient_data PASSED [ 50%]
tests/unit/lab/test_balance_comparison_engine.py::test_comparison_includes_evidence PASSED [ 62%]
tests/unit/lab/test_balance_comparison_engine.py::test_comparison_does_not_claim_root_cause PASSED [ 75%]
tests/unit/lab/test_balance_comparison_engine.py::test_comparison_fails_when_associated_metamorphic_rule_fails PASSED [ 87%]
tests/unit/lab/test_write_reports_creates_files PASSED [100%]
```

Total lab unit tests executed: **107 passed in 1.73s**
