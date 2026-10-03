---
status: active
layer: observability
authority: P0
audience: agent
ticket_id: TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2
artifact_type: test_plan
tags: [observability, engine, simulation-quality, performance]
---

# test_plan.md — TCK-20260806-PUSH-SHADOW-VALIDATION-PERF-PHASE2

## Regression Surface

- `tests/perf/test_simq_isolation_overhead.py` (full file) — existing tests unmodified.
- `tests/unit/observability/`, `tests/unit/kernel/`, `tests/integration/kernel/` — spot-checked
  for continued green, no changes to shaper code this ticket.

## New Tests Required

`tests/perf/test_simq_isolation_overhead.py`: 2 new `@pytest.mark.slow` tests
(`test_phase2_shaper_registry_overhead_benchmark`,
`test_phase2_shaper_registry_overhead_within_regression_band`), mirroring child 1's exact pattern
for the complete Phase 2 registry.

## Scoped Pytest Commands

```
pytest tests/perf/test_simq_isolation_overhead.py -m slow -s -q
pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q
```

## Anti-Drift Test Guards

- The event-stream comparison across 6 worlds is a real-kernel investigation artifact (not a
  committed pytest suite) — the committed regression surface for correctness is each child's own
  unit test file (already in place); this ticket's own committed addition is the performance gate
  only, matching how Phase 1's own Child 4 (Shadow-Validation-Perf) worked.

## Results (this session)

- Event-stream comparison: 6 worlds x 500 ticks, all Phase 2 event types. 5/6 worlds exact
  parity; 1/6 (`urban_political`) showed 6 mismatches, root-caused to the pre-existing,
  already-documented `INFRA-273` mechanism (confirmed via repeated-run variance check, not
  assumed) — not a shaper defect.
- `pytest tests/perf/test_simq_isolation_overhead.py::test_phase2_shaper_registry_overhead_benchmark tests/perf/test_simq_isolation_overhead.py::test_phase2_shaper_registry_overhead_within_regression_band -m slow -s -q`:
  2 passed. `phase2_off=5.880s`, `phase2_on=5.770s`, overhead -0.35% (band 25%).
- `pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q`:
  unchanged at 1045 passed, 6 skipped, 3 deselected (no shaper code touched this ticket).

## GO Verdict

**GO** — see investigation.md's own verdict section for the full reasoning.
