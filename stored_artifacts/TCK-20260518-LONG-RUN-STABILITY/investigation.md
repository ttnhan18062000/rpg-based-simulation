# Investigation: Long-Run Stability Certification (Milestone 18)

## 1. Background & Goal
While previous optimization proofs (e.g. `BenchHarness`, `Optimization Proof Suite`) demonstrated massive throughput gains (up to 83x speedups) and p95 latency drops over 1,000 ticks, long-duration simulations (5,000+ ticks) present distinct memory and degradation risks. As entities move, caches (movement plans, spatial indexes, read models) can accumulate stale references or unbounded dictionary entries. Furthermore, short-lived Python objects can promote into Gen 1/2 garbage collection, creating periodic latency spikes.

Milestone 18 requires rigorous certification proving that over a 5,000-tick horizon with 1,000 entities, the engine remains bounded in memory, stable in latency, and strictly deterministic.

## 2. Existing Infrastructure & Reuse Opportunities
- `src/perf/scenarios.py`: Already implements `build_metropolis_state` and `build_mixed_state` capable of generating 1,000 entities with mixed workloads (heroes, monsters, resource nodes, buildings, regions).
- `src/certification/harness.py` & `src/perf/bench_harness.py`: Provide excellent models for sampling memory RSS via `psutil`, timing tick compute ms, and extracting state hashes via `CanonicalStateHasher`.
- `src/engine/kernel.py`: Includes `_metrics` and `status` tracking recent tick compute times and GC invocations.

## 3. Key Technical Challenges
1. **GC Event Tracking**: Python's `gc` module allows inspection of GC counts and stats (`gc.get_stats()`). Tracking collections during long runs proves whether object churn is effectively managed.
2. **Cache Size Inspection**: We need to observe the sizes of `MovementPlanCache` and `ReadModelCache` to verify they don't grow monotonically.
3. **Execution Time**: Running 5,000 ticks on 1,000 entities in sequential/pure mode can take several seconds. We must ensure the test harness is efficient, utilizing optimized state compaction and phase skipping from earlier milestones.
4. **Pure vs. Runtime Mode**: `Pure` mode disables throttling/governor limits to test raw engine stability. `Runtime` mode enables the `PhaseBudgetGovernor` and `ResourceGovernor` to verify adaptive degradation under sustained load.
