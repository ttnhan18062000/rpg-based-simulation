---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260624-PERF-GUARD-INFRA
date: 2026-06-24
---

# Plan: TCK-20260624-PERF-GUARD-INFRA

## Delivery order

1. `perf_baselines.json` at repo root (empty entries, schema v1)
2. Extend `tests/perf/conftest.py` — add `_snapshot_rss_kb`, `PerfBudget`, `_perf_baselines`, `perf_budget`
3. `tools/perf_guard.py` — `measure` + `show` subcommands with `PerfMeasurePlugin`
4. `Makefile` — add `perf-measure` target + add to `.PHONY`
5. `tests/unit/perf/test_perf_guard.py` — 6 unit tests
6. `docs/testing/test_taxonomy.md` — add "Performance Test Authoring" section

## Constraints
- Do not remove existing fixtures from `tests/perf/conftest.py`
- `perf_guard.py measure` does NOT auto-write `perf_baselines.json` — prints proposed diff only
- `memory_kb: null` → skip memory assertion
- Missing baseline → `pytest.fail` (not skip)
- Linux only for `/proc/self/statm`
