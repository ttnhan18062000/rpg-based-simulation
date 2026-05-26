# Compliance IDs: OBS-050, OBS-051, OBS-052
from __future__ import annotations

import os
import json
import shutil
import tempfile
import pytest
from src.observability.analytics.exporter import (
    JSONLArtifactExporter,
    ParquetArtifactExporter,
    get_exporter,
    ExportJob,
    ExportManager
)

@pytest.fixture
def temp_run_dir():
    temp_dir = tempfile.mkdtemp()
    
    # 1. Create run manifest
    manifest_data = {
        "run_id": "test_run_123",
        "scenario_name": "Test Scenario",
        "scenario_type": "unit_test",
        "seed": 99,
        "status": "COMPLETED",
        "ticks_completed": 150,
        "started_at": "2026-05-20T12:00:00Z",
        "ended_at": "2026-05-20T12:01:00Z"
    }
    with open(os.path.join(temp_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    # 2. Create simulation events
    events = [
        {"run_id": "test_run_123", "tick": 10, "event_type": "spawn", "event_category": "lifecycle", "severity": "INFO", "message": "Hero spawned", "payload": {}},
        {"run_id": "test_run_123", "tick": 20, "event_type": "combat_damage", "event_category": "combat", "severity": "WARNING", "entity_id": 1, "message": "Hit", "payload": {"damage": 15}}
    ]
    with open(os.path.join(temp_dir, "simulation_events.jsonl"), "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    # 3. Create metric windows
    metrics = [
        {
            "run_id": "test_run_123", "window_start_tick": 1, "window_end_tick": 100,
            "tick_compute_ms_avg": 2.5, "tick_compute_ms_p95": 4.1, "memory_rss_bytes_avg": 1000000.0,
            "memory_rss_bytes_max": 2000000.0, "alive_entities_avg": 5.0, "gold_total_avg": 150.0,
            "event_count": 50, "hard_law_violation_count": 0
        }
    ]
    with open(os.path.join(temp_dir, "metric_windows.jsonl"), "w", encoding="utf-8") as f:
        for m in metrics:
            f.write(json.dumps(m) + "\n")

    # 4. Create anomalies
    anomalies = [
        {
            "rule_name": "NavigationStuckRule", "severity": "ERROR", "tick_detected": 45,
            "message": "Entity 1 stuck", "context": {"domain": "simulation", "run_id": "test_run_123"}
        }
    ]
    with open(os.path.join(temp_dir, "anomalies.json"), "w", encoding="utf-8") as f:
        json.dump(anomalies, f)

    yield temp_dir
    shutil.rmtree(temp_dir)


def test_get_exporter_resolution():
    jsonl_exp = get_exporter("jsonl")
    assert isinstance(jsonl_exp, JSONLArtifactExporter)

    parquet_exp = get_exporter("parquet")
    assert isinstance(parquet_exp, ParquetArtifactExporter)

    with pytest.raises(ValueError):
        get_exporter("xml")


def test_jsonl_export_run(temp_run_dir):
    exporter = JSONLArtifactExporter()
    dest_dir = tempfile.mkdtemp()
    try:
        output_files, record_counts, skipped = exporter.export_run(
            run_id="test_run_123",
            source_dir=temp_run_dir,
            dest_dir=dest_dir,
            artifact_types=["simulation_events", "metric_windows", "anomalies", "run_manifest", "hard_law_violations"]
        )

        assert "simulation_events" in output_files
        assert "metric_windows" in output_files
        assert "anomalies" in output_files
        assert "run_manifest" in output_files
        
        # hard_law_violations should be marked as skipped since it's not present in temp_run_dir
        assert "hard_law_violations" in skipped
        assert "hard_law_violations" not in output_files

        assert record_counts["simulation_events"] == 2
        assert record_counts["metric_windows"] == 1
        assert record_counts["anomalies"] == 1

        # Check file content copies
        assert os.path.exists(os.path.join(dest_dir, "simulation_events.jsonl"))
        assert os.path.exists(os.path.join(dest_dir, "metric_windows.jsonl"))
        assert os.path.exists(os.path.join(dest_dir, "anomalies.json"))
        assert os.path.exists(os.path.join(dest_dir, "run_manifest.json"))
    finally:
        shutil.rmtree(dest_dir)


def test_parquet_export_run(temp_run_dir):
    exporter = ParquetArtifactExporter()
    if not exporter.enabled:
        pytest.skip("pyarrow or parquet is not installed in the test environment.")

    dest_dir = tempfile.mkdtemp()
    try:
        output_files, record_counts, skipped = exporter.export_run(
            run_id="test_run_123",
            source_dir=temp_run_dir,
            dest_dir=dest_dir,
            artifact_types=["simulation_events", "metric_windows", "anomalies", "run_manifest", "hard_law_violations"]
        )

        assert "simulation_events" in output_files
        assert "metric_windows" in output_files
        assert "anomalies" in output_files
        assert "run_manifest" in output_files
        assert "hard_law_violations" in skipped

        assert record_counts["simulation_events"] == 2
        assert record_counts["metric_windows"] == 1
        assert record_counts["anomalies"] == 1

        # Check Parquet files
        events_parquet = os.path.join(dest_dir, "simulation_events.parquet")
        assert os.path.exists(events_parquet)

        # Let's read back the Parquet file to verify
        import pyarrow.parquet as pq
        table = pq.read_table(events_parquet)
        assert table.num_rows == 2
        
        # Verify schema names
        col_names = table.schema.names
        assert "run_id" in col_names
        assert "tick" in col_names
        assert "payload_json" in col_names

    finally:
        shutil.rmtree(dest_dir)


def test_export_manager_full_flow(temp_run_dir):
    exports_base = tempfile.mkdtemp()
    manager = ExportManager(base_export_dir=exports_base)
    
    # We will point output_path inside exports_base/export_id
    export_id = "test_job_001"
    output_path = os.path.join(exports_base, export_id, "out")

    job = ExportJob(
        export_id=export_id,
        source_run_id="test_run_123",
        source_path=temp_run_dir,
        output_path=output_path,
        format="jsonl",
        artifact_types=["simulation_events", "run_manifest"]
    )

    try:
        manifest = manager.execute_job(job)
        assert manifest.status == "COMPLETED"
        assert manifest.export_id == export_id
        assert "simulation_events" in manifest.output_files
        assert manifest.record_counts["simulation_events"] == 2

        # Verify manifest file exists on disk
        manifest_file = os.path.join(exports_base, export_id, "export_manifest.json")
        assert os.path.exists(manifest_file)
        with open(manifest_file, "r", encoding="utf-8") as f:
            disk_manifest = json.load(f)
            assert disk_manifest["export_id"] == export_id
            assert disk_manifest["status"] == "COMPLETED"

    finally:
        shutil.rmtree(exports_base)
