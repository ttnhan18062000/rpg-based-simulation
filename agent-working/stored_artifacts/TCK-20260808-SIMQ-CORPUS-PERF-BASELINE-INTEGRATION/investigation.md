---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION
artifact_type: investigation
tags: [simulation-quality, world, corpus, performance]
---

# Investigation — TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION

## Docs Requiring Update

- `docs/performance/perf_baseline_policy.md`: document the new corpus-world baseline coverage (Implement phase)

## Correction to the ticket's own "piggyback" framing

The ticket's own Request Summary hoped a `PerfResult` could be captured "alongside" a normal
`calibrate_simq.py` quality run at zero extra engine-run cost. **Not quite true, confirmed by
direct read of `BenchHarness.run_benchmark(scenario_id, initial_state, warmup_ticks=100,
sample_ticks=1000, ...)`** (`src/perf/bench_harness.py:40-54`): it runs its OWN dedicated
warmup+sample tick loop, separate from `calibrate_simq.py`'s own quality-scoring tick loop — not a
shared execution. What IS free is **world content reuse**: `BenchHarness.run_benchmark` accepts
any `AuthoritativeState` directly, and `tools/calibrate_simq.py::_load_world_state(name, seed)`
(line 114) already does exactly `WorldCompiler.compile(spec, seed) -> (AuthoritativeState,
compile_report)` for a named SimQ world. Reusing that function means a perf baseline run needs the
same real, authored world content calibration already uses — no new world/profile authoring,
still a genuinely separate benchmark execution.

Corrected framing carried into Plan/Implement: this is a **second, dedicated benchmark run per
world**, sharing world-content construction with calibration, not a truly free byproduct of a
single run.

## Real integration points confirmed

- `tools/calibrate_simq.py::_load_world_state(world_name, seed) -> (AuthoritativeState | None, compile_report | None)` —
  reused directly, not re-derived.
- `src/perf/bench_harness.py::BenchHarness(profile).run_benchmark(scenario_id, initial_state, ...)` —
  returns a dict; `PerfResult.from_bench_dict(data)` (`src/perf/regression_gate.py`) converts it.
- `PROD_SMALL` (`src/config/profiles.py`) — the `RuntimeProfile` calibration already uses; reused
  for the benchmark's own `BenchHarness(profile=PROD_SMALL)` construction for consistency (not
  `HardwareClass.CLASS_A/B/C` from `tests/perf/`'s own convention — those are perf-test-specific
  profile objects, a different thing from `RuntimeProfile`; confirmed by direct import trace, not
  assumed).

## Second, more significant correction: `PerfRegressionGate`/`PerfBaseline`/`PerfResult` are dead code — never actually consumed

Direct grep for real usage of these 3 dataclasses (`src/perf/regression_gate.py`) across the whole
`tests/`/`src/` tree found **zero real consumers** — the only 2 hits are `test_undisclosed_skill_swap_adaptation.py`
(checks that a skill doc's own TEXT mentions the string "PerfRegressionGate," not actual class
usage) and a comment in `test_perf_tag_test_scoper_wiring.py`. The actual, real, exercised
comparison mechanism — confirmed by reading `tests/perf/test_perf_regression_baseline.py` and a
committed baseline JSON (`tests/perf/baselines/idle_100_local.json`) directly — is simpler and
never goes through the dataclass system at all: the baseline JSON is loaded as a raw dict,
`avg_tick_compute_ms` is compared against `max(5.0, baseline_avg * 1.25)`, done.

**This corrects the premise I gave the user in the prior turn** — `PerfRegressionGate` is a real,
well-designed dataclass system, but describing it as "the" live performance regression mechanism
overstated its actual role; the team's real, currently-exercised path is the simpler ad-hoc
dict-comparison in `test_perf_regression_baseline.py`. Implementation follows the REAL, live
pattern (raw dict, `avg_tick_compute_ms`-style threshold) for the new corpus-world baselines,
matching what's actually exercised — not the disconnected, currently-unused dataclass system.
Disclosed here rather than silently building on dead code and calling it "wired in."

## Scale/cost check

Given the "second dedicated run" reality, only the corpus's largest few worlds get initial
baselines (matches the ticket's own Plan intent) rather than all 79 run_keys — `frontier_extended`
(59 entities per `corpus_registry.yaml`), `frontier_marches` (62 entities), `crowded_frontier` (38
entities) as the first batch. `BenchHarness`'s own default `sample_ticks=1000` is independent of
the SimQ scenario's own `ticks` field (200-1000t) — the benchmark's tick count is its own
parameter, not inherited from the calibration run_key.
