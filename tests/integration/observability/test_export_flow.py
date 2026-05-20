# Compliance IDs: OBS-050, OBS-055, OBS-058
from __future__ import annotations

import os
import json
import shutil
import tempfile
import pytest
from src.cli.entry import main
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.observability.reporting.run_set_repository import RunSetArtifactRepository, RunIndexRecord
from src.observability.sweeper import RunSetManifest

@pytest.fixture
def mock_repo_data(monkeypatch):
    runs_dir = tempfile.mkdtemp()
    run_sets_dir = tempfile.mkdtemp()
    
    # Temporarily override default paths using monkeypatch
    monkeypatch.setattr(RunArtifactRepository, "__init__", lambda self, base_dir=runs_dir: setattr(self, "base_dir", os.path.abspath(base_dir)))
    monkeypatch.setattr(RunSetArtifactRepository, "__init__", lambda self, base_dir=run_sets_dir: setattr(self, "base_dir", os.path.abspath(base_dir)))
    
    run_repo = RunArtifactRepository()
    run_set_repo = RunSetArtifactRepository()

    # 1. Create a single run
    run_id = "integration_run_01"
    manifest = RunManifest(
        run_id=run_id,
        scenario_name="Combat Arena",
        scenario_type="combat",
        seed=123,
        observability_mode="full",
        started_at="2026-05-20T12:00:00Z",
        ticks_requested=100,
        ticks_completed=100,
        status="COMPLETED"
    )
    run_repo.create_run(run_id, manifest)
    
    # Write some mock events
    with open(run_repo.resolve_path(run_id, "events"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"run_id": run_id, "tick": 1, "event_type": "init", "event_category": "lifecycle", "severity": "INFO", "message": "Go"}) + "\n")
    
    # Write metric windows
    with open(os.path.join(runs_dir, run_id, "metric_windows.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "run_id": run_id, "window_start_tick": 1, "window_end_tick": 100,
            "tick_compute_ms_avg": 1.5, "tick_compute_ms_p95": 2.0, "memory_rss_bytes_avg": 500000.0,
            "memory_rss_bytes_max": 600000.0, "alive_entities_avg": 2.0, "gold_total_avg": 10.0,
            "event_count": 10, "hard_law_violation_count": 0
        }) + "\n")

    # Write anomalies
    with open(run_repo.resolve_path(run_id, "anomalies"), "w", encoding="utf-8") as f:
        json.dump([
            {"rule_name": "QuestStalledRule", "severity": "WARNING", "tick_detected": 50, "message": "Stalled", "context": {"domain": "simulation", "run_id": run_id}}
        ], f)

    # 2. Create a mock scenario sweep
    sweep_id = "integration_sweep_01"
    sweep_dest = os.path.join(run_sets_dir, sweep_id)
    os.makedirs(sweep_dest, exist_ok=True)
    
    # Create runs directory inside sweep
    sweep_runs_dir = os.path.join(sweep_dest, "runs")
    os.makedirs(sweep_runs_dir, exist_ok=True)
    
    # Copy run_01 inside the sweep
    shutil.copytree(os.path.join(runs_dir, run_id), os.path.join(sweep_runs_dir, run_id))

    # Write run_index for sweep
    index_rec = RunIndexRecord(
        sweep_id=sweep_id,
        run_id=run_id,
        seed=123,
        scenario_name="Combat Arena",
        scenario_type="combat",
        status="COMPLETED",
        ticks_completed=100,
        health_score=90.0,
        critical_count=0,
        warning_count=1,
        hard_law_violation_count=0,
        artifact_path=f"runs/{run_id}"
    )
    with open(run_set_repo.resolve_path(sweep_id, "index"), "w", encoding="utf-8") as f:
        f.write(index_rec.model_dump_json() + "\n")

    yield {
        "runs_dir": runs_dir,
        "run_sets_dir": run_sets_dir,
        "run_id": run_id,
        "sweep_id": sweep_id
    }

    shutil.rmtree(runs_dir)
    shutil.rmtree(run_sets_dir)


def test_cli_export_command_success(mock_repo_data, monkeypatch):
    import sys
    
    # Clean output directories if they exist
    exports_dir = "data/exports"
    if os.path.exists(exports_dir):
        shutil.rmtree(exports_dir)

    run_id = mock_repo_data["run_id"]
    test_args = ["rpg-observe", "export", run_id, "--format", "parquet"]
    monkeypatch.setattr(sys, "argv", test_args)

    # We expect clean execution without raising exceptions (or raising SystemExit(0))
    try:
        main()
    except SystemExit as e:
        assert e.code == 0
    
    # Verify exported Parquet file exists
    expected_export_path = os.path.abspath(os.path.join(exports_dir, f"export_{run_id}_parquet"))
    assert os.path.exists(expected_export_path)
    assert os.path.exists(os.path.join(expected_export_path, "simulation_events.parquet"))
    assert os.path.exists(os.path.join(expected_export_path, "metric_windows.parquet"))
    assert os.path.exists(os.path.join(expected_export_path, "anomalies.parquet"))

    # Cleanup exports
    if os.path.exists(exports_dir):
        shutil.rmtree(exports_dir)


def test_cli_export_sweep_and_query_flow(mock_repo_data, monkeypatch):
    import sys
    
    exports_dir = "data/exports"
    analytics_dir = "data/analytics"
    
    for d in [exports_dir, analytics_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)

    sweep_id = mock_repo_data["sweep_id"]
    
    # 1. Export Sweep
    monkeypatch.setattr(sys, "argv", ["rpg-observe", "export-sweep", sweep_id, "--format", "parquet"])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0
    
    expected_sweep_export = os.path.abspath(os.path.join(exports_dir, f"export_{sweep_id}_parquet"))
    assert os.path.exists(expected_sweep_export)

    # 2. Build Dataset
    monkeypatch.setattr(sys, "argv", ["rpg-observe", "build-dataset", sweep_id])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    # Let's inspect base analytics folder to get compiled dataset ID
    dataset_dirs = os.listdir(analytics_dir)
    assert len(dataset_dirs) == 1
    ds_id = dataset_dirs[0]

    # 3. Query Dataset: worst-runs
    monkeypatch.setattr(sys, "argv", ["rpg-observe", "query-dataset", ds_id, "--query", "worst-runs"])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    # 4. Query Dataset: anomaly-summary
    monkeypatch.setattr(sys, "argv", ["rpg-observe", "query-dataset", ds_id, "--query", "anomaly-summary"])
    try:
        main()
    except SystemExit as e:
        assert e.code == 0

    # Cleanup
    for d in [exports_dir, analytics_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
