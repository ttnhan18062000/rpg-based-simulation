# Test Plan - Milestone 16: Multi-Run Artifact Index

We will verify both repository operations and end-to-end integration flows.

## Unit Tests

### `tests/unit/observability/test_run_set_repository.py`
- Verify that `RunSetArtifactRepository` cleanly creates sweep directory paths, writes manifests, indexes, and summaries, and successfully reads them back.
- Verify `list_sweeps()` scans the directory tree and returns correct active sweep profiles.

### `tests/unit/observability/test_run_index_builder.py`
- Mock standard run directories containing complete vs missing or failed run reports.
- Verify that the indexer parses records accurately, defaulting values properly when reports or anomalies are missing without crashing.

## Integration Tests

### `tests/integration/observability/test_multi_run_index_flow.py`
- Execute a real 2-seed sweep of scenario `"idle"`.
- Assert that upon completion, `run_index.jsonl` and `sweep_summary.json` are automatically generated inside the sweep folder.
- Parse the generated files and assert that the aggregate averages, worst/best run selections, and anomaly rule counters are mathematically correct.
- Verify the CLI `rpg-observe list-sweeps` and `rpg-observe inspect-sweep <sweep_id>` commands print the correct structured outputs.
