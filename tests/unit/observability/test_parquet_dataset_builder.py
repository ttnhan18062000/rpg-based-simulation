# Compliance IDs: OBS-055, OBS-056
from __future__ import annotations

import os
import json
import shutil
import tempfile
import pytest
from src.observability.analytics.dataset import AnalyticsDatasetBuilder

@pytest.fixture
def mock_sweep_dir():
    sweep_dir = tempfile.mkdtemp()
    
    # Write mock run index
    index_records = [
        {
            "sweep_id": "test_sweep_abc", "run_id": "run_001", "seed": 42,
            "scenario_name": "Grid Combat", "scenario_type": "combat", "status": "COMPLETED",
            "ticks_completed": 100, "health_score": 95.0, "critical_count": 0, "warning_count": 1,
            "hard_law_violation_count": 0, "artifact_path": "runs/run_001"
        },
        {
            "sweep_id": "test_sweep_abc", "run_id": "run_002", "seed": 43,
            "scenario_name": "Grid Combat", "scenario_type": "combat", "status": "COMPLETED",
            "ticks_completed": 100, "health_score": 80.0, "critical_count": 1, "warning_count": 2,
            "hard_law_violation_count": 1, "artifact_path": "runs/run_002"
        }
    ]
    with open(os.path.join(sweep_dir, "run_index.jsonl"), "w", encoding="utf-8") as f:
        for rec in index_records:
            f.write(json.dumps(rec) + "\n")

    # Create directories for run_001 and run_002
    runs_dir = os.path.join(sweep_dir, "runs")
    os.makedirs(runs_dir)

    for rid, seed in [("run_001", 42), ("run_002", 43)]:
        run_path = os.path.join(runs_dir, rid)
        os.makedirs(run_path)

        # 1. Run Manifest
        m = {
            "run_id": rid, "scenario_name": "Grid Combat", "scenario_type": "combat",
            "seed": seed, "status": "COMPLETED", "ticks_completed": 100,
            "started_at": "2026-05-20T12:00:00Z", "ended_at": "2026-05-20T12:01:00Z",
            "health_score": 95.0 if rid == "run_001" else 80.0,
            "critical_count": 0 if rid == "run_001" else 1,
            "warning_count": 1 if rid == "run_001" else 2
        }
        with open(os.path.join(run_path, "run_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(m, f)

        # 2. Metric Windows
        metrics = [
            {
                "run_id": rid, "window_start_tick": 1, "window_end_tick": 50,
                "tick_compute_ms_avg": 1.8, "tick_compute_ms_p95": 2.5, "memory_rss_bytes_avg": 500000.0,
                "memory_rss_bytes_max": 800000.0, "alive_entities_avg": 10.0, "gold_total_avg": 200.0,
                "event_count": 30, "hard_law_violation_count": 0
            },
            {
                "run_id": rid, "window_start_tick": 51, "window_end_tick": 100,
                "tick_compute_ms_avg": 2.1, "tick_compute_ms_p95": 3.0, "memory_rss_bytes_avg": 600000.0,
                "memory_rss_bytes_max": 900000.0, "alive_entities_avg": 9.0, "gold_total_avg": 400.0,
                "event_count": 35, "hard_law_violation_count": 0 if rid == "run_001" else 1
            }
        ]
        with open(os.path.join(run_path, "metric_windows.jsonl"), "w", encoding="utf-8") as f:
            for mw in metrics:
                f.write(json.dumps(mw) + "\n")

        # 3. Anomalies
        anomalies = [
            {
                "rule_name": "NavigationStuckRule", "severity": "WARNING", "tick_detected": 15,
                "message": "Entity 3 stuck", "context": {"domain": "simulation", "run_id": rid}
            }
        ]
        with open(os.path.join(run_path, "anomalies.json"), "w", encoding="utf-8") as f:
            json.dump(anomalies, f)

        # 4. Simulation Events
        events = [
            {"run_id": rid, "tick": 1, "event_type": "init", "event_category": "lifecycle", "severity": "INFO", "message": "Init complete", "payload": {}},
            {"run_id": rid, "tick": 50, "event_type": "combat_damage", "event_category": "combat", "severity": "INFO", "message": "Damage", "payload": {"val": 10}}
        ]
        with open(os.path.join(run_path, "simulation_events.jsonl"), "w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev) + "\n")

    yield sweep_dir
    shutil.rmtree(sweep_dir)


def test_analytics_dataset_builder_full(mock_sweep_dir):
    base_analytics = tempfile.mkdtemp()
    builder = AnalyticsDatasetBuilder(base_analytics_dir=base_analytics)
    
    if not builder.enabled:
        pytest.skip("pyarrow is not installed in test environment.")

    dataset_id = "unit_test_dataset"
    try:
        manifest = builder.build_dataset(
            sweep_id="test_sweep_abc",
            source_sweep_dir=mock_sweep_dir,
            dataset_id=dataset_id
        )

        assert manifest.dataset_id == dataset_id
        assert manifest.source_sweep_id == "test_sweep_abc"
        
        # Verify compiled Parquet outputs
        dest_dir = os.path.join(base_analytics, dataset_id)
        assert os.path.exists(os.path.join(dest_dir, "dataset_manifest.json"))
        
        # Verify record counts
        assert manifest.record_counts["runs"] == 2
        assert manifest.record_counts["metric_windows"] == 4  # 2 per run
        assert manifest.record_counts["anomalies"] == 2       # 1 per run
        assert manifest.record_counts["simulation_events"] == 4 # 2 per run

        # Let's read consolidated tables and verify content merges
        import pyarrow.parquet as pq
        
        # Verify runs
        runs_tbl = pq.read_table(os.path.join(dest_dir, "runs.parquet"))
        assert runs_tbl.num_rows == 2
        assert set(runs_tbl.column("run_id").to_pylist()) == {"run_001", "run_002"}

        # Verify metric windows
        mw_tbl = pq.read_table(os.path.join(dest_dir, "metric_windows.parquet"))
        assert mw_tbl.num_rows == 4

        # Verify anomalies
        anom_tbl = pq.read_table(os.path.join(dest_dir, "anomalies.parquet"))
        assert anom_tbl.num_rows == 2

        # Verify events
        ev_tbl = pq.read_table(os.path.join(dest_dir, "simulation_events.parquet"))
        assert ev_tbl.num_rows == 4
        
    finally:
        shutil.rmtree(base_analytics)
