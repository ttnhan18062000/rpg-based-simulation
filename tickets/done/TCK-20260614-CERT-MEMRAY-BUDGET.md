---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260614-CERT-MEMRAY-BUDGET
phase: done
date: 2026-06-14
tags: [certification, memray, testing, performance, tooling]
---

# TCK-20260614-CERT-MEMRAY-BUDGET

## Title
Add profiling mode script with baseline comparison and Memray-compatible test runner configuration

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
The pytest `--resource-budget large` hook sets `RLIMIT_AS` to 8 GB. Under Memray, virtual address usage differs from RSS, so the pytest process hits `MemoryError` inside its own reporting/cache code even though the real memory pressure came from the application earlier. This misleads diagnosis. The fix is to document and provide a Makefile target (or script) for Memray profiling runs that disables the resource budget, disables the pytest cache provider, and uses short tracebacks.

## Scope
- Add `scripts/profile_memory.py` with `--suite` and `--memray` flags:
  - `--suite certification` — runs only `tests/certification/`
  - `--suite observability` — runs only `tests/unit/observability/`
  - `--suite full` — runs all tests except `tests/perf/`
  - `--memray` — wraps run with `python -m memray run -o memray-<suite>-<timestamp>.bin`
  - Always sets: `--resource-budget off`, `-p no:cacheprovider`, `--tb=short`
  - Saves top allocation stacks to `reports/profiling/<suite>-<timestamp>.txt` when `--memray` used
  - Compares peak RSS against a baseline file `reports/profiling/baseline.json` if it exists; prints delta and warns if regression > 10%
  - `--save-baseline` flag: write current peak RSS to `reports/profiling/baseline.json`
- Add `make memray-profile` target calling `python scripts/profile_memory.py --suite certification --memray`
- Add a comment in `tests/conftest.py` near the `RLIMIT_AS` budget hook (line 31) explaining that profilers may need `--resource-budget off`
- Check for `memray` availability at script start; print clear install instructions if absent
- Do NOT change the default budget (remains `"medium"`)

## Out of Scope
- Fixing the application-level memory issue (TCK-20260614-CERT-SAFE-SERIAL handles that)
- Adding Memray as a required CI step
- Automated regression blocking in CI (manual flag only)
- Changing existing budget values (small/medium/large/off)

## Acceptance Criteria
- `python scripts/profile_memory.py --suite certification` runs the certification suite without hitting `MemoryError` in pytest internals
- `python scripts/profile_memory.py --suite certification --memray` produces a `memray-certification-*.bin` file and a top-stacks report
- `--save-baseline` writes `reports/profiling/baseline.json` with `{"suite": str, "peak_rss_mb": float, "timestamp": str}`
- Subsequent run without `--save-baseline` compares against baseline and prints delta
- `tests/conftest.py` has a one-line comment explaining profiler budget incompatibility at line 31
- Script exits with helpful message if `memray` is not installed
- No existing tests are affected

## Related Tickets
- TCK-20260614-CERT-SAFE-SERIAL (the real fix; this ticket is a tooling supplement)

## Related Docs
- `docs/engine/performance_contract.md`

## Related Stored Artifacts
- `memory_issue.md` (source investigation, section 3.6 and Phase 4)

## Related Code Areas
- `tests/conftest.py:20` — `--resource-budget` addoption registration
- `tests/conftest.py:31` — `pytest_runtest_setup` hook applying RLIMIT_AS
- `tests/conftest.py:40` — budget limit definitions
- `Makefile` (root) — target to add

## Assumptions / Open Questions
- Memray must be installed separately (`pip install memray`) — the target can print a helpful error if not found
- If no `Makefile` exists at root, use `scripts/memray_profile.sh` instead

## Implementation Notes
- Check `which memray` or `python -m memray --version` in the script and exit with a clear message if absent
- The `--resource-budget off` path in conftest: when budget is `"off"`, the hook should `return` without setting any limit — verify this is already implemented or add the guard

## Test Summary
- `tests/unit/cli/test_profile_memory_script.py` (new):
  - `test_script_exits_cleanly_on_missing_memray` (mock memray absent)
  - `test_baseline_write_creates_json_file`
  - `test_baseline_comparison_prints_delta`
  - `test_suite_certification_selects_correct_test_paths`
- Manual verification: run `make memray-profile` with Memray installed; confirm pytest completes without `MemoryError` in its own internals.

## Files Changed
- scripts/profile_memory.py (new — profiling runner with --suite, --memray, --save-baseline flags)
- tests/unit/cli/test_profile_memory_script.py (new — 4 tests)
- tests/unit/cli/__init__.py (new — empty init)
- tests/conftest.py (one-line comment at pytest_runtest_setup about profiler budget incompatibility)
- Makefile (memray-profile target added to .PHONY and profiling section)

## Completion Summary
Added scripts/profile_memory.py with --suite/--memray/--save-baseline flags; added memray-profile Makefile target; added profiler budget comment in conftest.py; 4 tests pass.
