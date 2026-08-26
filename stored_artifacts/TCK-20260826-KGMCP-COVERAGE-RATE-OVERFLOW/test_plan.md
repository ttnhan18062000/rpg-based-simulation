---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW
artifact_type: test_plan
tags: [observability, debugging, data-quality]
---

# Test Plan — TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW

## Normal flow
- `test_compute_kgmcp_cache_efficiency_metrics_coverage_rate_window_matched_via_all_tools`: 5
  all-time cache events vs 1 period-scoped search call (uncorrected: >100%) vs 10 all-time search
  calls (corrected: 50%) — proves the reconciliation.
- `test_compute_retro_metrics_threads_all_tools_into_coverage_denominator`: same scenario through
  `compute_retro_metrics()`.
- `test_generate_kgmcp_coverage_uses_all_tools_denominator_not_period_scoped_tools`: same scenario
  through the full `generate()` Markdown render — asserts "50.0%" present, "500.0%" absent.

## Edge cases
- `test_compute_kgmcp_cache_efficiency_metrics_coverage_rate_never_capped_even_when_over_one`: a
  genuinely-uncapped all-time-vs-all-time ratio (5 events / 1 search call = 500%) must still
  render its real raw value, not be clamped.
- Backward compatibility: every pre-existing direct-call test in `test_generate_retro.py` (160
  tests) omits `all_tools` entirely — full suite re-run confirms zero regressions.

## Failure modes
- `search_calls_total == 0` (all-time or period-scoped) → `coverage_rate` stays `None`
  (pre-existing `if search_calls_total else None` guard, untouched).

## Regression paths
- `tests/tools/test_generate_retro.py` — full file, 164 passed (160 pre-existing + 4 new).
- `tests/tools/test_agent_ops_dashboard_stats.py` — full file, 19 passed (confirms the JSON API
  path, which does not pass `all_tools`, is unaffected).
