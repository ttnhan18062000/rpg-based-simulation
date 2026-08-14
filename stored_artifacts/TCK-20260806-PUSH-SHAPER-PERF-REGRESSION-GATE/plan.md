---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE
artifact_type: plan
tags: [observability, performance, simulation-quality]
---

# plan.md — TCK-20260806-PUSH-SHAPER-PERF-REGRESSION-GATE

## Ordered Steps

1. Add `_run_mode_inprocess_with_shaper_flag(monkeypatch, shapers_on: bool) -> ModeResult` to
   `tests/perf/test_simq_isolation_overhead.py`, reusing `_build_state()` +
   `dataclasses.replace(state, feature_flags={...})` to pin `ENABLE_PUSH_EVENT_SHAPERS` explicitly
   under the `inprocess` SimQ mode.
   - Files: `tests/perf/test_simq_isolation_overhead.py`
2. Add `test_push_shaper_registry_overhead_benchmark` (`@pytest.mark.slow`) producing raw
   measurement output, mirroring `test_three_mode_engine_overhead_benchmark`'s shape.
   - Files: `tests/perf/test_simq_isolation_overhead.py`
3. Add `test_push_shaper_registry_overhead_within_regression_band` (`@pytest.mark.slow`) — the
   actual standing gate, mirroring `test_inprocess_simq_overhead_within_regression_band`'s
   band-tolerance shape.
   - Files: `tests/perf/test_simq_isolation_overhead.py`
4. Run both new tests twice (convergence check, same discipline as the file's own existing
   doc-recorded measurement) to get real numbers, not a guessed threshold.
   - No file changes; produces the numbers step 5 documents.
5. Document the new gate in `docs/performance/simq_isolation_overhead.md` — method, committed
   2-run table, locked threshold, CI-wiring confirmation (no new Makefile/CI target needed, since
   this file's existing tests already reach CI only via the broad `pytest tests/ -m "slow or
   extra_slow"` sweep in `.github/workflows/test.yml`'s `slow` job).
   - Files: `docs/performance/simq_isolation_overhead.md`

## Files to Change

- `tests/perf/test_simq_isolation_overhead.py` (new helper + 2 new tests)
- `docs/performance/simq_isolation_overhead.md` (new section)

## Scope Guards

- Do NOT touch the existing 3 tests or their `_run_mode_*` helpers.
- Do NOT add a new Makefile/CI target — confirmed unnecessary (step 5's investigation).
- Do NOT touch `src/observability/event_shapers.py` or any shaper logic — this ticket is
  test-infrastructure only.

## Dependency Map

Steps 1→2→3 are strictly sequential (each depends on the previous existing). Step 4 depends on all
of 1-3 landing. Step 5 depends on step 4's real numbers.

## Acceptance Criteria Map

- AC "real, running ON vs OFF test at standard scale" → steps 1-2
- AC "locked regression-guard threshold from real data" → steps 3-4
- AC "wired into same CI/Makefile path" → step 5 (confirmed already true, documented not built)
- AC "docs/performance/simq_isolation_overhead.md documents the gate" → step 5
- AC "scoped pytest run passes" → step 4's own run + final Test phase
