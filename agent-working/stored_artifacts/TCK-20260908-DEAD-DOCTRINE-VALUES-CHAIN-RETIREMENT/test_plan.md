---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT
artifact_type: test_plan
tags: [architecture, strategy]
---

# Test Plan — TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT

## Normal flow
- The 4 dead-code test files are deleted (their subject no longer exists — nothing to test).
- The 4 mixed test files retain their real, unrelated tests unchanged and passing.

## Edge cases
- `test_fame_legend_fact_distinctness.py`'s static guard (checks no file calls
  `compute_bias_multiplier(`) must still pass now that the function is fully gone, not just
  unwired — verifies the guard's own text-search logic doesn't choke on the symbol no longer
  existing anywhere, and doesn't false-positive on my own historical-reference docstrings
  mentioning the deleted class/method by name (required rewording to avoid the literal
  `compute_bias_multiplier(` substring in one docstring).

## Failure modes checked
- Import-time failure: confirmed `python3 -c "import src.core.cognition; import
  src.domains.motivation; ..."` succeeds after all edits, before running the full test suite.
- Dangling type reference: confirmed `MotivationModel`'s remaining fields (`role_fit`, `ambition`,
  `moral`, `named_intention`) and its `to_canonical_dict()` no longer reference the deleted
  classes at all.

## Regression scope
- Focused: `tests/unit/domains/motivation/`, `tests/unit/motivation/`,
  `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py`,
  `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py`,
  `tests/architecture/test_fame_legend_fact_distinctness.py`.
- Broader: `tests/unit/domains/`, `tests/unit/ai/`, `tests/unit/strategic/`, `tests/architecture/`,
  `tests/integration/scenarios/` (excluding `slow`).

## Results
Focused: 13 passed. Broader: 1514 passed, 1 skipped, 0 failed.
