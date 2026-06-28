# Test Plan: TCK-20260627-P1F-ABANDONMENT-TYPE

## Scope

`pytest tests/unit/domains/commitment/ tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py -v`

## Test Cases

### Existing Tests (updated to attribute access)
- `test_abandonment_evaluator` — survival path: `result.is_betrayal is False`, `result.penalty == 0.0`
- `test_abandonment_evaluator` — greedy desertion path: `result.is_betrayal is True`, `result.penalty > 0.5`
- `test_abandoning_party_changes_future_partner_selection` — checks `result.is_betrayal is True`

### New Parity Test (added)
- `test_evaluate_abandonment_returns_typed_classification` in `test_phase15_abandonment_evaluator.py`:
  - Assert `isinstance(result, AbandonmentClassification)` for all three category branches
  - Assert `.category` equals the expected `AbandonmentCategory` member

## Pass Criteria
All tests in the scoped run GREEN. No `Dict[str, Any]` access remains in the test files.
