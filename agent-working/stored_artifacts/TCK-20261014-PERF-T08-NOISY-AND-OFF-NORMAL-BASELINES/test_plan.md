---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES
date: 2026-10-15
tags: [performance, benchmarking]
---

# Test plan: TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES

Scoped to `tests/tools/perf*`, `tests/unit/perf`, `tests/perf` non-slow, plus the docs/frontmatter checks; no full suite.

- **P1/P1b host-state capture (unit, written and passing):** the probe is a positive ms value for any iteration count including 0; the note carries `probe a -> b ms` only for runs that have one;  a `/proc/stat` + `/proc/cpuinfo` reader parses a fixture; missing or unreadable files give `None` fields and never fail the run (same rule as the monitoring tools); the values land in `runN.meta.json` and the promotion note.
- **P2 spread rule (unit, NOT written: waits for the written policy):** 5 runs, middle-3 spread computed correctly; ties; exactly 15.0 % passes, 15.1 % does not; fewer than 5 runs falls back to the 3-run rule; the median run (not the mean) is the promoted one.
- **P3 window (unit, written and passing):** `combat_10_local` spec carries 100 sampled ticks and the tick count reaches `protocol.measured_ticks`; `TRIPWIRE_SCENARIOS` is unchanged (a pin test on the two RunSpecs so a later edit is visible).
- **Lifecycle (existing tests):** `baseline_lifecycle.py check` over `tests/perf/baselines` still passes; no promoted file changes without a `promote` call; `LEGACY_TRIPWIRE_REFERENCES` shrinks only by records actually promoted.
- **AC4:** a test that `build_mixed_state(entity_count=200)` still returns 140 entities (the docstring claim is pinned), same entity ids and positions as before the docstring edit.
- **Architecture:** read-only analysis path mutates no state; the paths guard tests (`*guard*`) pass before any push; docs frontmatter valid; `make knowledge-index-update` after docs edits.
- **Measured part (after the gate):** not a test; evidence is the per-run table in the ledger and the candidate files under `reports/perf/` (git-ignored).
