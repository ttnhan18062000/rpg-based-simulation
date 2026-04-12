# Walkthrough - Log Rotation Mechanism

I have implemented an automated log rotation mechanism for simulation artifacts generated during regression tests and stress runs. This ensures the `logs/` directory remains clean and manageable.

## Changes Made

### Configuration
-   Updated [config.py](file:///home/vboxuser/Work/rpg-based-simulation/src/config.py) to include `max_regression_runs: int = 10`. This defines the authoritative limit for artifact retention per output directory.

### Core Logic
-   Enhanced [headless_regression_runner.py](file:///home/vboxuser/Work/rpg-based-simulation/src/testing/headless_regression_runner.py):
    -   Added a `_rotate_logs` method that identifies artifact directories (prefixed with `run_`).
    -   Implemented chronological pruning based on directory creation time (`ctime`).
    -   Integrated rotation into the simulation lifecycle (called automatically at the start of every run).

### Tooling Integration
-   Updated [test_harness.py](file:///home/vboxuser/Work/rpg-based-simulation/scripts/test_harness.py) to support a new `--max-runs` CLI argument, allowing users to override the default retention policy during manual stress tests.

## Verification Results

### Integration Test
I created and executed a dedicated test script (`tests/integration/test_log_rotation.py`) that performed the following:
1.  Initialized a runner with `max_runs=2`.
2.  Executed 3 consecutive simulation runs.
3.  Verified that strictly 2 directories remained in the target folder.

**Result**: `Log rotation verification passed!`

### Manual Verification
I performed a sequence of 3 runs using the `test_harness.py` script with `--max-runs 2`:
```bash
python3 scripts/test_harness.py --seed 1 --ticks 1 --outdir logs/test_harness_rotation --max-runs 2
...
ls logs/test_harness_rotation
# Output: run_2_1776014366  run_3_1776014368
```
The oldest run (seed 1) was correctly pruned.

## Conclusion
The simulation engine now maintains a lean footprint during large-scale testing and automated CI/CD pipelines. The default limit of 10 runs provides sufficient history for debugging recent failures without overwhelming the workspace.
