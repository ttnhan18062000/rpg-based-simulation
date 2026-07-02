# Test Plan — D06 Long-Run Simulation Health

## Observation Targets
- `metric_windows.jsonl`: alive_avg, active_avg, rejections (cumulative), sim_events count, quests_active — across all 1,000 ticks
- `run_manifest.json`: outcome, governor_state, final_state_hash, total_ticks
- `simulation_events.jsonl`: event count and last event tick

## Pass Thresholds
- Run completes: LifecycleOutcome.SUCCESS
- Governor: stays NORMAL for full run (no THROTTLE or EMERGENCY)
- Compute: avg tick ms < 50ms throughout (performance contract)
- No hard law violations

## Degradation Signals to Watch
- Tick compute trending upward across quartiles (memory/CPU creep)
- Alive entity count falling toward 0 by tick 1,000
- Zero behavioral events after tick 200 (still broken despite RC fixes)
- Rejection rate accelerating (unbounded cascade)
