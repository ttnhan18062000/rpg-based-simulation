# Test Plan — TCK-20260627-P2I-WORKFLOW-TYPES

## Scope

Regression: existing lab workflow tests must pass unchanged.
Type check: `mypy src/lab/workflows.py src/lab/results.py` must report no errors in return positions.

## Test Execution

```bash
pytest tests/unit/lab/ tests/unit/lab_agent/ tests/integration/lab/ tests/integration/lab_agent/ -m "not slow" -x
mypy src/lab/results.py src/lab/workflows.py --ignore-missing-imports --warn-return-any 2>&1 | tail -20
```

## Coverage Required

| Area | Test |
|---|---|
| TypedDicts importable | `from src.lab.results import GenerateSimulationSetupResult` succeeds |
| Existing lab tests pass | `pytest tests/unit/lab/ -m "not slow"` |
| Existing agent guard tests pass | `pytest tests/unit/lab_agent/` |
| Integration e2e passes | `pytest tests/integration/lab_agent/ -m "not slow"` |
| mypy no errors on changed files | `mypy src/lab/results.py src/lab/workflows.py` passes |

## Notes

- TypedDicts are dict subclasses at runtime — no caller logic changes needed.
- Callers using `result["status"]` and `result.get("reason", "")` remain valid.
