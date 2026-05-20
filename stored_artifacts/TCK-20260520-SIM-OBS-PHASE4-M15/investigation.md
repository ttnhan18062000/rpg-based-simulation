# Investigation - Milestone 15: Scenario Run Matrix and Sweeper

## Findings

1. **Scenario Spawning**:
   - `src/perf/scenarios.py` provides `SCENARIO_BUILDERS`, which maps scenario keys (`idle`, `movement`, `resource`, `combat`, `strategic`, `mixed`, `metropolis`) to functions building `AuthoritativeState`.
   - Each builder function expects `(entity_count=..., seed=...)` (or custom count flags) and returns an initial mutable `AuthoritativeState` that we can feed directly into `Kernel`.

2. **Kernel Initialization**:
   - The `Kernel` takes `profile`, `state`, `rng` (a `DeterministicRNG` initialized with the run's seed), and optional overrides.
   - If `ObservabilityMode` is not `OFF`, the Kernel instantiates a `RunArtifactRepository` and generates isolated directory spaces under `data/runs/<run_id>/`.
   - We must make sure that `ObservabilityConfig.set_override_mode(...)` is explicitly set to ensure observability metrics and events are generated.

3. **Replay & Metrics Generation**:
   - The `Kernel.tick_once()` and `Kernel.shutdown()` flows write standard `metric_windows.jsonl`, `events`, and `manifest.json` files seamlessly.
   - For sequential sweeps, we will configure each run to execute synchronously under the desired `run_id` without risking cross-run file pollution.
