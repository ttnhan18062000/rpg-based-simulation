# Investigation — TCK-20260628-E-LONGRUN-REGRESSION

## Current Behavior

No 5,000-tick behavioral regression test exists. The closest is:
- `tests/certification/test_cert_long_run_stability.py` — performance/stability (PURE mode,
  metropolis scenario with 1000 entities). Tracks RSS, latency drift, GC — not behavior.
- `tests/integration/kernel/test_long_run_determinism.py` — 1000-tick determinism check only.
- `tests/integration/scenarios/test_balance_regression.py` — 100-tick balance baseline
  (urban_political, seed=42) tracking combat attrition.

None of these guard behavioral metrics (alive_avg, gold economy activation, quest activity)
across long horizon runs.

## Mechanics / Engine Constraints

- `MetricsService.extract_metrics(state)` (`src/engine/metrics.py`) returns a `WorldMetrics`
  snapshot with `alive_entities`, `total_gold`, `quest_status_counts` per tick. No side effects.
- `WorldCompiler.compile(spec, seed) → (AuthoritativeState, dict)` for world setup.
- `Kernel(profile, state, rng).tick_once()` runs one tick (returns None).
- `ENABLE_ADVENTURE_ROUTING` defaults to `FeatureMode.OFF` — must be explicitly set to 1.0
  for economic and quest metrics to be meaningful (matches D06 adventure pipeline behavior).
- `max_replay_buffer_kb=0`, `max_observability_budget_percent=0.0` minimize overhead in test.
- Persistence phase causes ~80-220ms spikes every ~70 ticks (disk I/O); avg tick is ~20ms.
  5000-tick run completes in ~2-5 minutes locally (well under 10-minute AC).

## Parity Ledger Overlap

No direct parity entries — this is a new testing layer. No existing parity entry tracks
behavioral regression harness coverage.

## Prior Work

- D06 (`docs/audits/D06_longrun_health.md`): 1000-tick run metrics for seed=42.
  Established baselines: alive_avg 13-18, gold_avg 0-120, quest_active_count 0.0.
- `TCK-20260513-PERF-CI-GUARD`: 15% threshold performance regression guard.
  Pattern reused: baseline file + threshold comparison + CI gate.

## Risks and Open Questions

- Persistence spikes inflate per-tick time; doesn't affect total behavioral correctness.
- `quest_active_count = 0.0` in D06 1k-tick runs — baseline may be 0.0 at 5k ticks too.
  The `±20%` band uses absolute tolerance when baseline=0 (threshold=0.20).
- Baseline must be regenerated when deliberate behavioral changes are made.

## Anti-Drift Hazards

- Do not measure performance metrics in this test (use cert tests for that).
- Do not run the full test suite in CI fast path.
- Baseline file is the single source of truth — no in-code constants.
