---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION
phase: open
date: 2026-08-08
tags: [simulation-quality, world, corpus, performance]
---

# TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION

## Title
Wire `PerfRegressionGate`'s committed-baseline system to run against the real SimQ world corpus,
not just synthetic 10-200-entity scenarios — a real performance-tracking gate exists but has never
touched an authored world

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
A 2026-08-08 status discussion asked whether SimQ has a performance-tracking analog. It does:
`src/perf/regression_gate.py` (`PerfBaseline`/`PerfResult`/`PerfRegressionGate`) is a real,
committed-baseline drift-detection system — the same shape as `grade_anchors.json`/
`test_grade_regression.py`, just for performance metrics (`p95`/`p99_tick_compute_ms`,
`peak_rss_mb`, `memory_delta_mb`, `compute_tps`, `phase_p95_ms` breakdown) instead of quality
scores. But its 12 committed baselines (`tests/perf/baselines/*.json`) are ALL synthetic,
ALL small (`combat_10`, `idle_100`, `mixed_200`, `movement_100`, `resource_100`, `strategic_100`,
via `src/perf/scenarios.py`'s raw `State` builders) — none of the 17 real, authored SimQ worlds
have ever gone through this gate. Separately, the large-scale perf tests that DO exist
(`test_perf_metropolis.py`, 1000-5000 entities) bypass the baseline system entirely — hardcoded
inline thresholds (`assert p99 < 500.0`), no historical drift tracking, still on synthetic states.

Real gap: {synthetic state, real SimQ world} × {small/tracked, large/untracked} — only
synthetic-small is properly baseline-tracked; synthetic-large is ad hoc; real-world (any scale) has
never been perf-measured, tracked or not.

## Scope
1. **Investigate**:
   - Confirm exactly what `BenchHarness`/`PerfResult.from_bench_dict()` needs as input (a `State`
     object + tick count) and whether a real, `WorldCompiler`-compiled SimQ world's own `State`
     (already produced during a normal `calibrate_simq.py` run) is directly compatible, or needs
     adaptation.
   - Confirm whether capturing perf metrics can piggyback on an EXISTING calibration run (same
     engine execution, just also recording `tick_ms`/`mem_rss_mb` timing alongside the quality
     scoring) or requires a genuinely separate run — piggybacking is strongly preferred (avoids
     doubling the corpus's own real-engine-run cost).
2. **Plan**: which corpus worlds get baselines first (likely: the existing 17, prioritizing the
   largest few — `frontier_extended`, `frontier_marches` — plus whatever
   `TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION` produces once it lands, if this ticket
   implements after that one) and how `PerfBaseline.scenario_id` should encode a SimQ run_key
   (reuse the same `run_key` string directly, avoiding a second naming scheme).
3. **Implement**:
   - Extend `calibrate_simq.py`/`evaluate_simq.py` to optionally capture and emit a `PerfResult`
     alongside the quality report (flag-gated, off by default — this must never slow down or
     change behavior of the existing routine SimQ calibration path).
   - Commit initial `PerfBaseline` entries for a first batch of corpus worlds.
   - Wire a scoped pytest check (mirroring `test_grade_regression.py`'s own shape) that runs
     `PerfRegressionGate` against the corpus baselines.
4. Register new baselines' existence in `TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY`'s
   registry file, if that ticket has landed by the time this one implements (natural fit: the
   registry becomes the answer to "which worlds have a perf baseline").

## Out of Scope
- Any performance optimization work itself — this ticket only adds measurement/tracking, never
  changes engine behavior to make it faster.
- Retrofitting the ad-hoc `test_perf_metropolis.py`-style large-scale tests into the baseline
  system — worth doing eventually, but a separate concern from wiring the SimQ *world corpus*
  specifically (those tests use synthetic states, not real worlds, and are out of this ticket's
  own "real SimQ corpus" framing).
- Changing `PerfRegressionGate`'s own comparison/threshold logic — reused as-is.

## Acceptance Criteria
- [ ] investigation.md confirms the BenchHarness/PerfResult input compatibility with a real
      compiled SimQ world's `State`, and the piggyback-vs-separate-run feasibility
- [ ] `calibrate_simq.py`/`evaluate_simq.py` can optionally emit a `PerfResult`, flag-gated, no
      change to default behavior
- [ ] At least the corpus's largest few worlds have committed `PerfBaseline` entries
- [ ] A scoped pytest check runs `PerfRegressionGate` against the new corpus baselines
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY (registry this ticket's new baselines get
  recorded into — filed together)
- TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION (the large world this ticket should also baseline
  once it exists)
- TCK-20260518-PERF-REGRESSION-GATE (built the `PerfRegressionGate`/`PerfBaseline`/`PerfResult`
  system this ticket extends — DONE)

## Related Docs
- `docs/engine/performance_contract.md`, `docs/performance/perf_baseline_policy.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/perf/regression_gate.py` (`PerfBaseline`, `PerfResult`, `PerfRegressionGate`)
- `src/perf/bench_harness.py`, `src/perf/scenarios.py`
- `tests/perf/baselines/*.json`
- `tools/calibrate_simq.py`, `tools/evaluate_simq.py`

## Assumptions / Open Questions
- Whether a SimQ world's own tick count (200-1000t, much longer than the synthetic baselines'
  typical short benchmark runs) changes what "p95/p99 tick cost" even means for comparison
  purposes — not assumed; Investigate should confirm the metric stays meaningful over a long run
  vs. a short benchmark window before committing baselines.

## Implementation Notes
Subagent spawn cap (200/200) reached earlier this session — Investigate/Implement/Verify performed
directly.

Two significant corrections to this ticket's own starting premise, found during Investigate and
disclosed rather than silently worked around:

1. **"Piggyback on an existing calibration run" was wrong.** `BenchHarness.run_benchmark()` runs
   its own dedicated warmup+sample tick loop — not a shared execution with `calibrate_simq.py`'s
   own quality-scoring run. What's actually free is real-world-content reuse (via
   `calibrate_simq.py::_load_world_state`), not a truly free perf capture. Corrected in
   investigation.md/plan.md before implementing, rather than building a misleading "piggyback" that
   doesn't match the real API shape.

2. **`PerfRegressionGate`/`PerfBaseline`/`PerfResult` (the system this ticket's own Request Summary
   described as "the real performance regression mechanism") turned out to be dead code — zero
   real consumers anywhere in `tests/`/`src/`.** The actually-live mechanism is
   `tests/perf/test_perf_regression_baseline.py`'s own simpler raw-dict comparison
   (`avg_tick_compute_ms` vs. `max(5.0, baseline_avg * 1.25)`). Corrected the user-facing framing
   from the prior conversation turn (which had described `PerfRegressionGate` as the real system)
   and built against the real, live path instead — added the 3 new corpus-world scenarios directly
   to that file's own `parametrize` list, not a parallel test file with a 3rd comparison mechanism.
   Also caught a real bug from this: my own baseline generator initially used `PROD_SMALL`
   (`src/config/profiles.py`, `calibrate_simq.py`'s own `RuntimeProfile`), which is a DIFFERENT
   profile namespace from what `tests/perf/conftest.py`'s `perf_harness` fixture actually expects
   (`PERF_PROFILES["PERF_512MB_LOCAL"]`, `src/perf/profiles.py`) — caught via a real test run
   failing with `KeyError: 'PROD_SMALL'`, fixed, and both committed baselines regenerated with the
   correct profile before finalizing.

Flagged (not fixed — genuinely out of this ticket's own scope) that `docs/performance/perf_baseline_policy.md`
§3-4 describe an aspirational CI mechanism that matches neither the unused dataclass system nor the
real, live test — a pre-existing, larger doc-accuracy gap, disclosed with a dated correction note
rather than silently left for a reader to discover independently, but not rewritten wholesale here.

## Test Summary
`tests/tools/test_corpus_perf_baseline.py` (new): 3 passed. `tests/perf/test_perf_regression_baseline.py -k simq_corpus -m perf`
(real, slow-marked, live comparison logic reused unchanged): 3 passed — all 3 new corpus-world
scenarios (`frontier_extended`/`frontier_marches`/`crowded_frontier`) benchmark cleanly against
their own freshly-committed baselines.

## Files Changed
- `tools/bench_corpus_world.py` (new)
- `tests/perf/baselines/simq_corpus_{frontier_extended,frontier_marches,crowded_frontier}.json` (new, real benchmark data)
- `tests/tools/test_corpus_perf_baseline.py` (new)
- `tests/perf/test_perf_regression_baseline.py` (3 new parametrize rows + adapter function)
- `docs/performance/perf_baseline_policy.md` (§3 correction note + new §5)

## Completion Summary
Corrected 2 real, significant misunderstandings from this ticket's own starting premise (both
carried over from the prior conversation turn's own framing) rather than building on top of a
wrong assumption — the "piggyback" framing and, more importantly, which perf-comparison mechanism
is actually live. Delivered real, working perf baselines for the corpus's 3 largest worlds using
the genuinely-exercised comparison path, and disclosed (without fixing, correctly out of scope)
the pre-existing doc-vs-reality gap in `perf_baseline_policy.md`'s own CI-guards section. Third of
5 tickets in this batch.
