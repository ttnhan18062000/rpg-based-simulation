---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-BASELINE-GENERATION-FLOW-HEALTH-SCORE-MEAN-IS-99-NOT-100
phase: done
date: 2026-10-20
tags: []
---

# TCK-20261020-BASELINE-GENERATION-FLOW-HEALTH-SCORE-MEAN-IS-99-NOT-100

## Title
test_baseline_generation_and_cli_flow fails on main: one of 5 runs scores health 95, so the mean is 99.0, not 100.0

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/integration/observability/test_baseline_generation_flow.py::test_baseline_generation_and_cli_flow` asserts health_score_dist.mean == 100.0 and got mean 99.0 (min 95). Filed by rpg-planner 2026-10-20; the cause is the wall-clock HighCPULatencyRule WARNING described in TCK-20261010-BASELINE-COMPARISON-FLOW-TEST-WALL-CLOCK-DEPENDENT, which closes it in the same PR.

## Scope
Find which run scores 95 and why; decide defect or intended; answer why CI did not catch it.

## Out of Scope
Changing the health-score formula without a ruling.

## Acceptance Criteria
- [x] The cause is named: the slow first run of the sweep trips HighCPULatencyRule (avg compute > 50 ms), -5 health. It is wall clock, not an engine change.
- [x] The test passes for that reason (fixed tick cost through the existing LiveSignalSource seam); the 100.0 assertion is unchanged.
- [x] The CI-selection question: not a marker or selection gap. A fast CI host keeps the sweep's first run under the 50 ms HighCPULatencyRule limit, so the test passes there and fails only on a slow or loaded host (rpg-planner accepted this reading, 2026-10-20; no new ticket).

## Related Tickets
- TCK-20261010-BASELINE-COMPARISON-FLOW-TEST-WALL-CLOCK-DEPENDENT

## Related Docs
- docs/architecture/simulation_watchdog.md

## Related Stored Artifacts
None.

## Related Code Areas
tests/integration/observability/test_baseline_generation_flow.py

## Assumptions / Open Questions
- Seed-dependence: the slow run is whichever runs first in the process (warm-up), not a particular seed.

## Implementation Notes
- Cause (measured, not assumed): in the sweep the first run's first ticks are slow (seed 1: tick_compute_ms_avg 108.6, p95 199.9; seeds 2 and 3: about 8-9). The metric window feeds BasicRuntimeAnalyzer's HighCPULatencyRule (avg > 50 ms), a WARNING that scores the run 95; the baseline then has health mean 99 / threshold 96, and the compared run's 95 is `Metric envelope degraded: actual 95.0 < baseline threshold 96.0`, so WARNING.
- Fix, test only: `tests/integration/observability/conftest.py` fixture `tick_cost_ms`, a monkeypatch on the existing seam `LiveSignalSource.tick_end_signals` (the one place a measured tick cost becomes PressureSignals) that records a fixed compute cost. No src/ change. The flow tests pin 5 ms; the L55 comparison assertion and the rest of the test are unchanged.
- AC1: `test_a_slow_tick_is_what_trips_the_cpu_latency_rule` injects 59 ms ticks (the figure observed on a loaded VM) and shows every run's average compute is over the 50 ms limit, so the injection is real; the flow test passes on this loaded host, 2 of 2 runs, where it failed before.
- Folded in: TCK-20261020-BASELINE-GENERATION-FLOW-HEALTH-SCORE-MEAN-IS-99-NOT-100 (rpg-planner's sibling). Same cause (the 95 is one HighCPULatencyRule WARNING on the slow first run, so it is wall clock, not an engine change); `test_baseline_generation_and_cli_flow` uses the same fixture and passes with its mean 100.0 assertion unchanged.

## Test Summary
tests/integration/observability/test_baseline_comparison_flow.py and test_baseline_generation_flow.py: 4 passed, twice, on a loaded host. CI read from the PR.

## Files Changed
- tests/integration/observability/conftest.py (new fixture)
- tests/integration/observability/test_baseline_comparison_flow.py
- tests/integration/observability/test_baseline_generation_flow.py

## Completion Summary
The two baseline flow tests no longer depend on the host's tick speed; the cause was a HighCPULatencyRule WARNING on a slow first run.
