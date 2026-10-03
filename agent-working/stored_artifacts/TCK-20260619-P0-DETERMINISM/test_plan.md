---
ticket_id: TCK-20260619-P0-DETERMINISM
phase: test_plan
---

# Test Plan — TCK-20260619-P0-DETERMINISM

## Tests Run

### 1. Lint Gate (extended)
- File: `tests/integration/kernel/test_phase2_determinism.py`
- Extended `_scan_for_bare_random()` to assert empty result for all of `src/`
- Result: PASS (27 tests total, 0 failures)

### 2. Determinism Suite
- File: `tests/integration/kernel/test_determinism_suite.py`
- Covers same-seed identical output, different-seed divergence
- Result: PASS (included in the 27 passing tests)

### 3. Replay Determinism
- File: `tests/integration/kernel/test_replay_determinism.py`
- `test_transaction_trace_determinism` — two 1000-tick runs, identical seeds
- Result: PASS

## Acceptance Criteria Verification

| Criterion | Result |
|---|---|
| `grep -r "import random\|random\." src/ --include="*.py"` returns zero outside rng.py | PASS |
| Two runs with identical seeds produce identical event logs | PASS (test_replay_determinism) |
| CI lint step fails if new bare random added | PASS (lint test in test_phase2_determinism.py) |
