---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260624-FIX-SLOW-MARKERS
phase: open
date: 2026-06-24
tags: [slow-markers, timeout, certification, cli, conftest]
---

# TCK-20260624-FIX-SLOW-MARKERS

## Title
Mark inherently slow tests with @pytest.mark.slow to exclude from 60s conftest budget

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
3 tests TimeoutError under the default 60s conftest budget — not because of bugs, but because they spawn subprocesses or run many ticks:

1. `tests/certification/test_cert_long_run_stability.py::test_long_run_pure_stability`
2. `tests/certification/test_cert_long_run_stability.py::test_long_run_runtime_stability`
3. `tests/certification/test_cert_long_run_stability.py::test_long_run_determinism_parity`
4. `tests/cli/test_entry_parity.py::test_cli_basic_execution` — spawns `python3 -m src cli --ticks 20` subprocess with no timeout; conftest alarm fires

Note: `tests/unit/engine/test_scenario_runtime_service.py::TestPauseResume::test_pause_sets_flag` appeared to timeout due to thread leaks from MagicMock tests in the same session — it should clear after `TCK-20260624-FIX-MOCK-SERIAL` is applied. Recheck before marking.

## Scope
- Add `@pytest.mark.slow` (and `@pytest.mark.extra_slow` where appropriate) to the 4 tests above
- Confirm `test_pause_sets_flag` clears after `TCK-20260624-FIX-MOCK-SERIAL` before marking it slow
- For `test_cli_basic_execution`: also add `timeout=90` to the `subprocess.run()` call so it fails fast rather than hanging indefinitely if the CLI hangs

## Out of Scope
- Optimizing the long-run stability tests or the CLI execution time
- Changing conftest budget duration

## Acceptance Criteria
- All 4 tests are skipped under `pytest -m "not slow"`
- All 4 tests run and pass under `pytest -m "slow"` or `pytest --resource-budget large`
- `test_pause_sets_flag` is re-evaluated after the mock-serial fix — only mark slow if it still times out independently

## Related Tickets
- `TCK-20260624-FIX-MOCK-SERIAL` — fixes the thread leak that was tainting `test_pause_sets_flag`

## Related Docs
- `docs/testing/v2_test_taxonomy.md` — test classification rules

## Related Code Areas
- `tests/certification/test_cert_long_run_stability.py` — 3 tests
- `tests/cli/test_entry_parity.py::test_cli_basic_execution`
- `tests/unit/engine/test_scenario_runtime_service.py::TestPauseResume::test_pause_sets_flag` (check only)

## Implementation Notes
Add to each test function:
```python
@pytest.mark.slow
@pytest.mark.extra_slow  # for cert long-run tests that need --resource-budget large
def test_long_run_pure_stability():
    ...
```

For `test_cli_basic_execution` subprocess call:
```python
result = subprocess.run([...], timeout=90, ...)  # fail fast if CLI hangs
```

## Test Summary
Run: `pytest tests/certification/test_cert_long_run_stability.py tests/cli/test_entry_parity.py::test_cli_basic_execution -m "not slow" -v` — expect all 4 deselected.
Run: `pytest tests/certification/test_cert_long_run_stability.py tests/cli/test_entry_parity.py::test_cli_basic_execution -m "slow" -v --resource-budget large` — expect all to pass.

## Files Changed
TBD

## Completion Summary
TBD
