import os
import pytest
from src.observability.reporting.run_set_repository import RunSetArtifactRepository, RunIndexRecord, SweepSummary
from src.observability.sweeper import RunSetManifest


def test_repository_paths_and_create(tmp_path):
    repo = RunSetArtifactRepository(base_dir=str(tmp_path))
    sweep_id = "test_sweep_uuid"

    manifest = RunSetManifest(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        started_at="2026-05-20T00:00:00Z",
        ticks_requested=10
    )

    repo.create_sweep(sweep_id, manifest)
    
    assert os.path.exists(tmp_path / sweep_id)
    assert os.path.exists(tmp_path / sweep_id / "run_set_manifest.json")

    # Re-reading list of sweeps
    sweeps = repo.list_sweeps()
    assert sweep_id in sweeps
    assert sweeps[sweep_id].scenario_name == "idle"


def test_write_and_read_run_index(tmp_path):
    repo = RunSetArtifactRepository(base_dir=str(tmp_path))
    sweep_id = "sweep_run_index"

    records = [
        RunIndexRecord(
            sweep_id=sweep_id,
            run_id="run_1",
            seed=42,
            scenario_name="idle",
            scenario_type="sandbox",
            status="COMPLETED",
            ticks_completed=10,
            health_score=95.5,
            critical_count=0,
            warning_count=1,
            hard_law_violation_count=0,
            artifact_path="data/run_sets/sweep_run_index/runs/run_1"
        ),
        RunIndexRecord(
            sweep_id=sweep_id,
            run_id="run_2",
            seed=43,
            scenario_name="idle",
            scenario_type="sandbox",
            status="FAILED",
            ticks_completed=2,
            health_score=0.0,
            critical_count=1,
            warning_count=0,
            hard_law_violation_count=1,
            artifact_path="data/run_sets/sweep_run_index/runs/run_2"
        )
    ]

    repo.write_run_index(sweep_id, records)

    index_file = tmp_path / sweep_id / "run_index.jsonl"
    assert os.path.exists(index_file)

    # Read back and verify
    read_records = repo.read_run_index(sweep_id)
    assert len(read_records) == 2
    assert read_records[0].run_id == "run_1"
    assert read_records[0].health_score == 95.5
    assert read_records[1].run_id == "run_2"
    assert read_records[1].status == "FAILED"


def test_write_and_read_sweep_summary(tmp_path):
    repo = RunSetArtifactRepository(base_dir=str(tmp_path))
    sweep_id = "sweep_summary_test"

    summary = SweepSummary(
        sweep_id=sweep_id,
        scenario_name="combat",
        scenario_type="arena",
        total_runs=5,
        completed_runs=4,
        failed_runs=1,
        average_health_score=85.2,
        critical_run_count=1,
        warning_run_count=2,
        worst_run_id="run_3",
        best_run_id="run_1",
        most_common_anomaly_rule_ids={"rule_stall": 3, "rule_invariant": 1}
    )

    repo.write_sweep_summary(sweep_id, summary)

    summary_file = tmp_path / sweep_id / "sweep_summary.json"
    assert os.path.exists(summary_file)

    # Read back
    read_summary = repo.read_sweep_summary(sweep_id)
    assert read_summary.sweep_id == sweep_id
    assert read_summary.average_health_score == 85.2
    assert read_summary.most_common_anomaly_rule_ids == {"rule_stall": 3, "rule_invariant": 1}
