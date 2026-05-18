# Investigation: Production Latency & GC Spikes

## Objective
Analyze the root cause of p95 latency spikes at 10,000 entity scale and calibrate production profiles.

## Findings

### 1. Latency Baseline (No GC Management)
Using `scratch/stress_10k.py` on CLASS_B hardware:
- **1,000 entities**: 8ms AVG | 14ms P95
- **2,000 entities**: 18ms AVG | 23ms P95
- **5,000 entities**: 55ms AVG | 235ms P95 (Budget Failure: 50ms)
- **10,000 entities**: 125ms AVG | 407ms P95 (Budget Failure: 250ms)

### 2. Incremental GC Optimization
Implementing `gc.collect(0)` at the end of every tick (shallow collection of Generation 0) yielded significant improvements:
- **1,000 entities**: 5ms AVG (-37%) | 8ms P95 (-42%)
- **2,000 entities**: 13ms AVG (-27%) | 17ms P95 (-26%)
- **5,000 entities**: 37ms AVG (-32%) | 166ms P95 (-29%)

### 3. Profile Calibration
Based on measurements, the following budgets are proposed for CLASS_B hardware:
- **PROD_DEFAULT (2k)**: 50ms (Sustains 20 FPS)
- **PROD_LARGE (5k)**: 100ms (Sustains 10 FPS)
- **PROD_STRESS (10k)**: 500ms (Sustains 2 FPS)

## Recommendations
1.  **Inject GC Tuning**: Call `gc.collect(0)` in `Kernel.tick_once` frame-pacing window.
2.  **Update Profiles**: Sync `src/config/profiles.py` with measured reality.
3.  **Entity Pooling (Future)**: Consider pooling `EntityUpdate` and `CombatUpdate` objects to further reduce allocation pressure.
