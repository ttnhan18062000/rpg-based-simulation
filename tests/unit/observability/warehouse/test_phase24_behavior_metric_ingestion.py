from __future__ import annotations
import os
import json
import shutil
import pytest
from src.observability.warehouse.adapters import LocalWarehouseAdapter
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.observability.behavior.behavior_metric_window import BehaviorMetricWindow


@pytest.fixture
def temp_run_repository():
    base_dir = "tests/warehouse_run_repo_test"
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    repo = RunArtifactRepository(base_dir=base_dir)
    yield repo
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)


def test_behavior_metric_window_warehouse_ingestion(temp_run_repository):
    repo = temp_run_repository
    run_id = "run_phase24_ingest_test"
    
    # 1. Create a run with manifest
    manifest = RunManifest(
        run_id=run_id,
        scenario_name="test_scenario",
        scenario_type="test_type",
        seed=42,
        observability_mode="NORMAL",
        started_at="2026-05-29T18:00:00Z",
        ticks_requested=100,
        ticks_completed=100
    )
    repo.create_run(run_id, manifest)

    # 2. Write behavior metric windows
    run_dir = os.path.join(repo.base_dir, run_id)
    behavior_metrics_path = os.path.join(run_dir, "behavior_metric_windows.jsonl")
    
    window = BehaviorMetricWindow(
        run_id=run_id,
        window_start_tick=0,
        window_end_tick=10,
        behavior_counts={"combat/engage": 5},
        route_family_counts={"safe": 2}
    )
    
    with open(behavior_metrics_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(window.to_dict()) + "\n")

    # 3. Dry-run ingest run through warehouse adapter
    adapter = LocalWarehouseAdapter(run_repo=repo)
    result = adapter.ingest_run(run_id=run_id, dry_run=True)

    assert result.status == "DRY_RUN"
    assert result.records_ingested["runs"] == 1
    assert result.records_ingested["behavior_metrics"] == 1
    assert len(result.errors) == 0


def test_old_run_without_behavior_metrics_still_loads(temp_run_repository):
    repo = temp_run_repository
    run_id = "run_phase24_old_test"
    
    # Create old run manifest with no behavior metrics
    manifest = RunManifest(
        run_id=run_id,
        scenario_name="old_scenario",
        scenario_type="old_type",
        seed=11,
        observability_mode="NORMAL",
        started_at="2026-05-29T18:00:00Z",
        ticks_requested=50,
        ticks_completed=50
    )
    repo.create_run(run_id, manifest)

    # Dry-run ingest
    adapter = LocalWarehouseAdapter(run_repo=repo)
    result = adapter.ingest_run(run_id=run_id, dry_run=True)

    assert result.status == "DRY_RUN"
    assert result.records_ingested["runs"] == 1
    assert result.records_ingested["behavior_metrics"] == 0
    assert len(result.errors) == 0
