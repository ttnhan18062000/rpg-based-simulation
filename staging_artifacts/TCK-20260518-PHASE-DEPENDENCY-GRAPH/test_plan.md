# Test Plan - Phase Dependency Graph (Milestone 16)

## Unit Tests (`tests/unit/optimization/test_phase_dependency_graph.py`)
- Verify all 17 phases are correctly registered with precise input/output domains.
- Verify `must_run_every_tick` phases always return `True` for `should_run_phase`.
- Verify `force_full_scan` forces execution of all phases.
- Verify cadence checking correctly prevents execution on quiet ticks.
- Verify optional phases skip when their required input dirty domains are completely empty.

## Integration Parity Tests (`tests/integration/optimization/test_phase_skip_parity.py`)
- Run a 50-tick multi-entity simulation scenario with dynamic phase skipping enabled.
- Run the identical scenario with dynamic phase skipping disabled (or forcing full scan).
- Assert 100% exact hash parity across all ticks and metric counters confirming non-zero skipped phase counts.

## Regression Suite
- Run `pytest tests/perf/test_optimization_proof_report.py`.
- Run `pytest tests/api/test_rest_parity.py`.
