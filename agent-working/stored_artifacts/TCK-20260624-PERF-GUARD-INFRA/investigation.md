---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260624-PERF-GUARD-INFRA
date: 2026-06-24
---

# Investigation: TCK-20260624-PERF-GUARD-INFRA

## Existing perf infrastructure

### tests/perf/conftest.py
Contains two existing fixtures:
- `perf_harness` — returns a `BenchHarness` factory using `PERF_PROFILES`
- `perf_reporter` (autouse) — logs results to `reports/perf/` for tests marked `perf`
- `perf_report_dir` — returns the `reports/perf/` path

No `perf_budget` fixture exists yet. The new fixture must be added without removing or breaking the existing fixtures.

### tests/perf/ test structure
Tests currently hardcode thresholds as ad-hoc literals (e.g., `assert t_delta_ms < 15.0`). No shared baseline or tolerance model.

### tests/unit/perf/
Already exists with 5 test files. Has `__init__.py`. New unit tests go in a new file `test_perf_guard.py`.

### docs/testing/
The file is named `test_taxonomy.md` (not `v2_test_taxonomy.md`). Must update `test_taxonomy.md`.

### Makefile
- Uses tabs for indentation
- Section `# ── Testing ──` around line 142
- Uses pattern: `target: ## comment\n\tcommand`
- `.PHONY` list on line 1 (must add `perf-measure`)

### Platform
Linux-only confirmed. `/proc/self/statm` is acceptable.

## Key findings
1. `perf_baselines.json` starts empty — `FIX-PERF-BUDGETS` will populate entries
2. The fixture must `pytest.fail` (not skip) on missing baseline entries
3. `perf_guard.py measure` uses a `PerfMeasurePlugin` approach — hooks `pytest_runtest_call` for per-test wall-clock + RSS delta
4. `tolerance_pct` is per-test in baseline, not global
5. Hardware class via `PERF_HARDWARE_CLASS` env var — informational only in this pass
