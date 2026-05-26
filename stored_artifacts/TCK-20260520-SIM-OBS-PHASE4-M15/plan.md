# Implementation Plan - Milestone 15: Scenario Run Matrix and Sweeper

We will implement the foundation of the multi-run simulation analysis: the `ScenarioRunMatrix` and `ScenarioSweeper`.

## Proposed Changes

### Configuration & Models

#### [NEW] [sweeper.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/sweeper.py)
- **`ScenarioSweepConfig`**: Pydantic model validating sweep setup parameters:
  - `sweep_id`: string (auto-generated if empty).
  - `scenario_name`: string (e.g. `"mixed"`, `"idle"`).
  - `scenario_type`: string (e.g. `"resource_economy"`, `"mixed_sandbox"`).
  - `seeds`: non-empty list of integers.
  - `ticks`: positive integer.
  - `observability_mode`: `ObservabilityMode` matching the system definition.
  - `profile_name`: optional string (defaults to `"cli_default"`).
  - `max_parallel_runs`: int >= 1 (defaults to 1).
  - `stop_on_first_critical`: boolean (defaults to `False`).
  - `output_dir`: string (defaults to `"data/run_sets"`).
- **`ScenarioRunSpec`**: Individual run metadata mapping:
  - `run_id`: string.
  - `seed`: int.
  - `ticks`: int.
  - `scenario_name`: string.
  - `scenario_type`: string.
- **`RunSetManifest`**: Tracks summary metadata:
  - `sweep_id`: string.
  - `scenario_name`: string.
  - `scenario_type`: string.
  - `started_at`: ISO format datetime.
  - `ended_at`: ISO format datetime (updated upon complete).
  - `status`: string (`"COMPLETED"`, `"FAILED"`, `"PARTIAL"`).
  - `run_ids`: list of strings.
  - `seed_by_run_id`: dict mapping `run_id -> seed`.
  - `ticks_requested`: int.
  - `completed_count`: int.
  - `failed_count`: int.
  - `artifact_schema_version`: string (defaults to `"1.0"`).
- **`ScenarioSweeper`**: Sequential run sweeper loop.
  - Instantiates regional and entity state from builders inside `SCENARIO_BUILDERS`.
  - Initializes `Kernel` with exact seed RNG, execution mode, and isolated artifact directories.
  - Loops ticks synchronously, updates manifest files atomically, and handles run-level errors cleanly.

### CLI Layer

#### [MODIFY] [entry.py](file:///home/vboxuser/Work/rpg-based-simulation/src/cli/entry.py)
- Registers the command `rpg-observe sweep <sweep_config.json>`.
- Parses sweep config and launches `ScenarioSweeper.run_sweep()`.
