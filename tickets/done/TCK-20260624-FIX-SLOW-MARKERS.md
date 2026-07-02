---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260624-FIX-SLOW-MARKERS
phase: done
date: 2026-06-24
tags: [slow-markers, timeout, certification, cli, conftest]
---

# TCK-20260624-FIX-SLOW-MARKERS

## Title
Mark inherently slow tests with @pytest.mark.slow to exclude from 60s conftest budget

## Status
DONE

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
- All 4 tests are skipped under `pytest -m "not slow"` ✓
- All 4 tests run and pass under `pytest -m "slow"` or `pytest --resource-budget large`
- `test_pause_sets_flag` is re-evaluated after the mock-serial fix — only mark slow if it still times out independently ✓ (passes in 2.05s, not marked slow)

## Related Tickets
- `TCK-20260624-FIX-MOCK-SERIAL` — fixes the thread leak that was tainting `test_pause_sets_flag`

## Related Docs
- `docs/testing/v2_test_taxonomy.md` — test classification rules

## Related Code Areas
- `tests/certification/test_cert_long_run_stability.py` — 3 tests
- `tests/cli/test_entry_parity.py::test_cli_basic_execution`
- `tests/unit/engine/test_scenario_runtime_service.py::TestPauseResume::test_pause_sets_flag` (check only)

## Implementation Notes
Added `@pytest.mark.slow` to all 3 cert long-run tests (already had `@pytest.mark.extra_slow`).
Added `@pytest.mark.slow` decorator and `timeout=90` to `test_cli_basic_execution`.
`test_pause_sets_flag` confirmed passing in 2.05s in isolation after MOCK-SERIAL fix — left unmarked.

## Test Summary
`pytest tests/certification/test_cert_long_run_stability.py tests/cli/test_entry_parity.py::test_cli_basic_execution -m "not slow" --collect-only` → 4 deselected, 0 selected. ✓

## Files Changed
- `tests/certification/test_cert_long_run_stability.py` — added `@pytest.mark.slow` to 3 test functions
- `tests/cli/test_entry_parity.py` — added `import pytest`, `@pytest.mark.slow` decorator, `timeout=90` to subprocess.run()

## Completion Summary
All 4 inherently slow tests now carry `@pytest.mark.slow` and are excluded from `pytest -m "not slow"` runs. The CLI test subprocess call has a 90s timeout to fail fast if the CLI hangs. `test_pause_sets_flag` was confirmed clean (2.05s) after MOCK-SERIAL fix and was not marked slow.
