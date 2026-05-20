import os
import json
import pytest
from pathlib import Path
from src.cli.entry import _build_parser, _run_warehouse
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.observability.reporting.run_set_repository import RunSetArtifactRepository, SweepSummary, RunIndexRecord
from src.observability.sweeper import RunSetManifest
from src.observability.warehouse.adapters import LocalWarehouseAdapter

def test_warehouse_ingest_run_dry_run_success(tmp_path):
    """Verify that a local adapter dry-run executes successfully and registers all rows from files."""
    # 1. Setup temp run repo inside temporary directory
    run_id = "test_run_123"
    base_dir = tmp_path / "runs"
    run_repo = RunArtifactRepository(base_dir=str(base_dir))
    
    manifest = RunManifest(
        run_id=run_id,
        scenario_name="hero_solo",
        scenario_type="solo",
        seed=123,
        observability_mode="LIGHT",
        started_at="2026-05-20T11:00:00Z",
        ticks_requested=10,
        ticks_completed=10,
        status="COMPLETED"
    )
    run_repo.create_run(run_id, manifest)
    
    # Write some events
    events_path = run_repo.resolve_path(run_id, "events")
    with open(events_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "tick": 1,
            "event_type": "move",
            "event_category": "movement",
            "severity": "INFO",
            "message": "Hero moved",
            "payload": {"x": 10, "y": 20}
        }) + "\n")
        f.write(json.dumps({
            "tick": 2,
            "event_type": "attack",
            "event_category": "combat",
            "severity": "WARNING",
            "message": "Hero attacked",
            "payload": {"damage": 5}
        }) + "\n")

    # Write anomalies list
    anomalies_path = run_repo.resolve_path(run_id, "anomalies")
    with open(anomalies_path, "w", encoding="utf-8") as f:
        json.dump([
            {
                "rule_id": "rule_001",
                "severity": "WARNING",
                "domain": "combat",
                "tick_start": 2,
                "tick_end": 2,
                "affected_entity_count": 1,
                "message": "High combat activity",
                "evidence": {}
            }
        ], f)

    # 2. Execute LocalWarehouseAdapter dry-run ingestion
    adapter = LocalWarehouseAdapter(run_repo=run_repo)
    result = adapter.ingest_run(run_id, dry_run=True)
    
    assert result.status == "DRY_RUN"
    assert result.run_id == run_id
    assert result.records_ingested["runs"] == 1
    assert result.records_ingested["events"] == 2
    assert result.records_ingested["anomalies"] == 1
    assert len(result.errors) == 0

def test_warehouse_ingest_sweep_dry_run_success(tmp_path):
    """Verify that a local adapter sweep dry-run processes multi-run sweeps successfully."""
    sweep_id = "test_sweep_abc"
    child_run_id = "sweep_run_1"
    run_sets_dir = tmp_path / "run_sets"
    runs_dir = tmp_path / "runs"
    
    sweep_repo = RunSetArtifactRepository(base_dir=str(run_sets_dir))
    run_repo = RunArtifactRepository(base_dir=str(runs_dir))

    # Create sweep manifest
    manifest = RunSetManifest(
        sweep_id=sweep_id,
        scenario_name="sweep_scenario",
        scenario_type="sweep",
        started_at="2026-05-20T11:00:00Z",
        ticks_requested=5,
        run_ids=[child_run_id],
        seed_by_run_id={child_run_id: 1}
    )
    sweep_repo.create_sweep(sweep_id, manifest)
    
    # Create child run manifest
    child_manifest = RunManifest(
        run_id=child_run_id,
        scenario_name="sweep_scenario",
        scenario_type="sweep",
        seed=1,
        observability_mode="LIGHT",
        started_at="2026-05-20T11:00:00Z",
        ticks_requested=5,
        ticks_completed=5,
        status="COMPLETED"
    )
    run_repo.create_run(child_run_id, child_manifest)

    # Create run index and summary
    run_index = RunIndexRecord(
        sweep_id=sweep_id,
        run_id=child_run_id,
        seed=1,
        scenario_name="sweep_scenario",
        scenario_type="sweep",
        status="COMPLETED",
        ticks_completed=5,
        health_score=100.0,
        critical_count=0,
        warning_count=0,
        hard_law_violation_count=0,
        artifact_path=str(runs_dir / child_run_id)
    )
    sweep_repo.write_run_index(sweep_id, [run_index])
    
    sweep_summary = SweepSummary(
        sweep_id=sweep_id,
        scenario_name="sweep_scenario",
        scenario_type="sweep",
        total_runs=1,
        completed_runs=1,
        failed_runs=0,
        average_health_score=100.0,
        critical_run_count=0,
        warning_run_count=0
    )
    sweep_repo.write_sweep_summary(sweep_id, sweep_summary)

    # Execute LocalWarehouseAdapter dry-run ingestion
    adapter = LocalWarehouseAdapter(run_repo=run_repo, sweep_repo=sweep_repo)
    result = adapter.ingest_sweep(sweep_id, dry_run=True)
    
    assert result.status == "DRY_RUN"
    assert result.sweep_id == sweep_id
    assert result.records_ingested["sweeps"] == 1
    assert result.records_ingested["runs"] == 1
    assert len(result.errors) == 0

def test_warehouse_cli_parser_routing():
    """Verify that argparse parses the subcommands and flags correctly."""
    parser = _build_parser()
    
    args = parser.parse_args(["warehouse", "ingest-run", "run_123", "--dry-run"])
    assert args.command == "warehouse"
    assert args.warehouse_command == "ingest-run"
    assert args.run_id == "run_123"
    assert args.dry_run is True

    args_sweep = parser.parse_args(["warehouse", "ingest-sweep", "sweep_789"])
    assert args_sweep.command == "warehouse"
    assert args_sweep.warehouse_command == "ingest-sweep"
    assert args_sweep.sweep_id == "sweep_789"
    assert args_sweep.dry_run is False
