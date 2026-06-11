---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260523-BALANCE-COMPARISON
artifact_type: test_plan
tags: [balance, comparison]
---

# Balance Comparison Engine - Test Plan

## Unit Tests
File path: `tests/unit/lab/test_balance_comparison_engine.py`

### Test Cases

- **`test_better_health_score_marked_improved`**:
  - Verifies that when compared health score is better and all other metrics are stable or improved, the classification is `IMPROVED`.
- **`test_hard_law_violation_marked_regressed`**:
  - Verifies that if the compared variant contains hard law violations (or increased violations), it is strictly classified as `REGRESSED`.
- **`test_mixed_metrics_produce_mixed`**:
  - Verifies that when some metrics improve (e.g. higher health score) but others worsen (e.g. higher stuck ratio), the outcome is classified as `MIXED`.
- **`test_missing_data_produces_insufficient_data`**:
  - Verifies that if essential fields like `health_score` are missing, it cleanly returns `INSUFFICIENT_DATA`.
- **`test_comparison_includes_evidence`**:
  - Verifies that the returned report contains a detailed `evidence` dictionary mapping compared metric values against baseline metric values.
- **`test_comparison_does_not_claim_root_cause`**:
  - Verifies that the explanation text uses correlative wording and strictly avoids absolute causal statements.
