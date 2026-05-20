# Implementation Plan - Milestone 16: Multi-Run Artifact Index

We will implement the run-set indexer and abstraction layers to compare multiple simulation runs systematically.

## Proposed Changes

### Models & Repositories

#### [NEW] [run_set_repository.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/reporting/run_set_repository.py)
- **`RunIndexRecord`**: Pydantic model representing metadata for one run inside a sweep:
  - `sweep_id`: string
  - `run_id`: string
  - `seed`: int
  - `scenario_name`: string
  - `scenario_type`: string
  - `status`: string
  - `ticks_completed`: int
  - `health_score`: float
  - `critical_count`: int
  - `warning_count`: int
  - `hard_law_violation_count`: int
  - `artifact_path`: string
- **`SweepSummary`**: Pydantic model representing sweep-wide aggregation metrics:
  - `sweep_id`: string
  - `scenario_name`: string
  - `scenario_type`: string
  - `total_runs`: int
  - `completed_runs`: int
  - `failed_runs`: int
  - `average_health_score`: float
  - `critical_run_count`: int  # Runs with health_score < threshold (e.g. 60) or status == "FAILED"
  - `warning_run_count`: int   # Runs with health_score < 90
  - `worst_run_id`: Optional[str]
  - `best_run_id`: Optional[str]
  - `most_common_anomaly_rule_ids`: Dict[str, int]
- **`RunSetArtifactRepository`**: Performs files management inside `data/run_sets/<sweep_id>`:
  - `__init__(base_dir="data/run_sets")`
  - `create_sweep(sweep_id, manifest)`
  - `write_run_index(sweep_id, records: List[RunIndexRecord])`
  - `write_sweep_summary(sweep_id, summary: SweepSummary)`
  - `read_run_index(sweep_id) -> List[RunIndexRecord]`
  - `read_sweep_summary(sweep_id) -> SweepSummary`
  - `list_sweeps() -> Dict[str, RunSetManifest]`

### Sweeper Integration

#### [MODIFY] [sweeper.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/sweeper.py)
- Integrate automatic run indexing and sweep summary generation after sequential execution loops finish.

### CLI Layer

#### [MODIFY] [entry.py](file:///home/vboxuser/Work/rpg-based-simulation/src/cli/entry.py)
- Register:
  - `rpg-observe list-sweeps`
  - `rpg-observe inspect-sweep <sweep_id>`
