# Implementation Plan - HeadlessRunner Log Rotation

I propose implementing an automated log rotation mechanism within the `HeadlessRunner` to prevent the `logs/` directory from being cluttered with hundreds of stale simulation artifacts.

## User Review Required

> [!NOTE]
> By default, the system will keep only the **10 most recent runs** in any given output directory (e.g., `logs/tests/regression` or `logs/harness`). This limit will be configurable in the `SimulationConfig`.

## Proposed Changes

### [Component] Core Infrastructure

#### [MODIFY] [config.py](file:///home/vboxuser/Work/rpg-based-simulation/src/config.py)
- Add `max_regression_runs: int = 10` to the `SimulationConfig` class.

#### [MODIFY] [headless_regression_runner.py](file:///home/vboxuser/Work/rpg-based-simulation/src/testing/headless_regression_runner.py)
- Update `HeadlessRunner.__init__` to accept an optional `max_runs` parameter (defaulting to 10).
- Implement `_rotate_logs(self)`:
    - Lists all subdirectories in `self.output_root` starting with `run_`.
    - Sorts them by name (which includes a timestamp) or creation time.
    - Deletes oldest directories if the total count exceeds `self.max_runs`.
- Call `_rotate_logs()` at the start or end of the `run()` method.

### [Component] Testing & Tooling

#### [MODIFY] [test_harness.py](file:///home/vboxuser/Work/rpg-based-simulation/scripts/test_harness.py)
- Update `run_harness` to initialize `HeadlessRunner` with the rotation limit if provided via CLI.

## Verification Plan

### Automated Tests
- Create a temporary integration test `tests/integration/test_log_rotation.py`:
    - Initialize `HeadlessRunner` with `max_runs=2`.
    - Execute `run()` three times.
    - Verify that only exactly 2 directories exist in the output root.

### Manual Verification
- Run `python scripts/test_harness.py --seed 42 --ticks 1` multiple times and observe the `logs/harness` directory.
