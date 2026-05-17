# PerfRegressionGate Plan

## Proposed Changes

### 1. `src/perf/regression_gate.py`
- Define `MissingBaselineError(Exception)`
- Define dataclass `PerfBaseline`:
  - `scenario_id: str`
  - `p95_tick_compute_ms: float`
  - `p99_tick_compute_ms: float`
  - `peak_rss_mb: float`
  - `memory_delta_mb: float`
  - `compute_tps: float`
  - `raw_entity_updates: int = 0`
  - `compacted_entity_updates: int = 0`
  - `phase_p95_ms: Dict[str, float] = Field(default_factory=dict)`
- Define dataclass `PerfResult`:
  - Same fields plus `wall_clock_tps: float = 0.0`
  - Factory/classmethod `from_bench_dict(data: dict)` to seamlessly bridge with `BenchHarness` output.
- Define dataclass `PerfGateResult`:
  - `passed: bool`
  - `reasons: List[str]`
  - `warnings: List[str]`
- Implement `PerfRegressionGate`:
  - `__init__(ci_mode: bool = True, tolerance_percent: float = 10.0, mem_tolerance_percent: float = 15.0)`
  - `compare(baseline: Optional[PerfBaseline], current: PerfResult) -> PerfGateResult`
  - Enforce CI baseline checking.
  - Enforce compute metrics comparison while explicitly ignoring `wall_clock_tps`.
  - Enforce phase-level p95 checks.
  - Enforce memory regression checks.

### 2. `tests/unit/perf/test_perf_regression_gate.py`
- Implement unit tests covering all acceptance criteria as outlined in `perf_test_plan.md`:
  - `test_perf_gate_passes_within_threshold`
  - `test_perf_gate_fails_when_p95_regresses_too_much`
  - `test_perf_gate_fails_when_phase_regresses_too_much`
  - `test_perf_gate_fails_when_memory_regresses_too_much`
  - `test_perf_gate_ignores_wall_clock_tps_for_compute_regression`
  - `test_missing_baseline_fails_in_ci_mode`
  - `test_missing_baseline_warns_or_skips_in_local_mode`

## Verification
- Execute `pytest tests/unit/perf/test_perf_regression_gate.py`
- Ensure 100% test pass rate and total adherence to acceptance criteria.
