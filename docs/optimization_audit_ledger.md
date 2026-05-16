# Optimization Audit Ledger

This ledger tracks performance issues, optimizations, and proofs for the RPG Engine V2.

| Issue ID | Description | Source Area | Test Proof | Status | Proof Type |
| --- | --- | --- | --- | --- | --- |
| RISK-001 | Profiler timing accuracy | `src/perf/bench_harness.py` | `tests/perf/test_profiler_integrity.py` | PROVEN | Characterization |
| RISK-002 | Frame pacing interference | `src/engine/kernel.py` | `tests/perf/test_profiler_integrity.py` | PROVEN | Characterization |
| RISK-003 | DirtySet lifecycle completeness | `src/core/dirty.py` | `tests/perf/test_dirty_set_integrity.py` | PROVEN | Audit |
| RISK-004 | Replay benchmark isolation | `src/perf/bench_harness.py` | `tests/perf/test_profiler_integrity.py` | PROVEN | Characterization |
| RISK-005 | Local/Concurrent Parity | `src/engine/executor` | `tests/integration/executor` | NOT PROVEN | Differential |

## Audit Log

### 2026-05-15: Fix DirtySet Lifecycle Correctness (TCK-20260515-PERF-M2)
- Implemented robust `DirtySet` tracking for movement, combat, and world objects.
- Integrated `AuthoritativeState.validate_dirty_set` for O(N) leak detection in audit mode.
- Hardened `AuthoritativeApplyPipeline` to perform incremental `DirtySet` refreshes.
- Verified integrity via `tests/perf/test_dirty_set_integrity.py`.

### 2026-05-15: Fix Benchmark / Profiler Truth (TCK-20260515-PERF-M1)
- Isolated compute cost from frame pacing and replay overhead.
- Validated phase accounting and status recording at tick end.
- Added `tests/perf/test_profiler_integrity.py` to ensure measurement correctness.
- Standardized benchmark result schema (Compute TPS vs Wall-Clock TPS).

### 2026-05-15: Initial Baseline Freeze (TCK-20260515-PERF-BASELINE)
- Established baseline for semantic and performance metrics.
- All subsequent optimizations must be compared against this baseline.
