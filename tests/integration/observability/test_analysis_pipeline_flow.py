from __future__ import annotations
import os
import json
import pytest
import shutil

from src.observability.events import SimulationEvent
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.observability.reporting.metric_recorder import MetricWindowRecord
from src.observability.anomaly import AnalysisPipeline

@pytest.fixture
def clean_integration_runs(tmp_path):
    base_dir = tmp_path / "runs"
    base_dir.mkdir()
    repo = RunArtifactRepository(str(base_dir))
    yield repo
    if base_dir.exists():
        shutil.rmtree(base_dir)

def test_pipeline_end_to_end_completed_run(clean_integration_runs):
    repo = clean_integration_runs
    run_id = "test_e2e_completed"
    
    manifest = RunManifest(
        run_id=run_id,
        scenario_name="e2e-scen",
        scenario_type="E2E_TEST",
        seed=42,
        observability_mode="LIGHT",
        started_at="2026-05-19T12:00:00Z",
        ticks_requested=200,
        ticks_completed=200,
        status="COMPLETED"
    )
    repo.create_run(run_id, manifest)
    
    # 1. Write synthetic events
    events_path = repo.resolve_path(run_id, "events")
    events = [
        SimulationEvent(
            event_type="InvariantViolation", event_category="hard_law", tick=25,
            severity="CRITICAL", source_system="hard_law_monitor", message="Breached gold limit",
            entity_id=5, payload={"gold": -10}
        )
    ]
    with open(events_path, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(ev.model_dump_json() + "\n")
            
    # 2. Write synthetic metrics
    metrics_path = os.path.join(repo.base_dir, run_id, "metric_windows.jsonl")
    w1 = MetricWindowRecord(
        run_id=run_id, window_start_tick=1, window_end_tick=100, ticks_observed=100,
        alive_entities_avg=5.5, active_entities_avg=6.0, gold_total_avg=1000.0,
        tick_compute_ms_avg=5.0, tick_compute_ms_p95=8.0,
        memory_rss_bytes_avg=100 * 1024 * 1024, memory_rss_bytes_max=120 * 1024 * 1024,
        hard_law_violation_count=1, event_count=1, anomaly_candidate_count=0
    )
    with open(metrics_path, "w", encoding="utf-8") as f:
        f.write(w1.model_dump_json() + "\n")
        
    # 3. Execute AnalysisPipeline
    pipeline = AnalysisPipeline(repo=repo)
    result = pipeline.run(run_id)
    
    # Assertions
    assert result.status == "COMPLETED"
    assert result.anomaly_count == 1
    assert result.critical_count == 1
    assert result.warning_count == 0
    assert result.health_score == 60.0  # 100 - 40
    
    # Verify outputs are written
    assert os.path.exists(result.output_paths["anomalies"])
    assert os.path.exists(result.output_paths["anomaly_summary"])
    assert os.path.exists(result.output_paths["report_json"])
    assert os.path.exists(result.output_paths["report_md"])
    
    # Verify manifest is updated to ANALYZED
    updated_manifest = repo.read_manifest(run_id)
    assert updated_manifest.status == "ANALYZED"
    
    # Verify contents of report markdown
    with open(result.output_paths["report_md"], "r", encoding="utf-8") as f:
        report_md = f.read()
        assert "Simulation Run Observatory Report — test_e2e_completed" in report_md
        assert "Deterministic Health Score" in report_md
        assert "60.0/100" in report_md
        assert "Hard Law Violation detected: Breached gold limit" in report_md

def test_pipeline_end_to_end_partial_run(clean_integration_runs):
    repo = clean_integration_runs
    run_id = "test_e2e_partial"
    
    manifest = RunManifest(
        run_id=run_id,
        scenario_name="e2e-scen-partial",
        scenario_type="E2E_TEST",
        seed=42,
        observability_mode="LIGHT",
        started_at="2026-05-19T12:00:00Z",
        ticks_requested=200,
        ticks_completed=50,
        status="RUNNING"  # Incomplete
    )
    repo.create_run(run_id, manifest)
    
    pipeline = AnalysisPipeline(repo=repo)
    
    # Rejects by default
    res_default = pipeline.run(run_id)
    assert res_default.status == "FAILED"
    assert "Cannot analyze incomplete run" in res_default.errors[0]
    
    # Allows with allow_partial=True
    res_partial = pipeline.run(run_id, allow_partial=True)
    assert res_partial.status == "COMPLETED"
    
    # Verify partial warning is prepended to the report_md file
    report_md_path = repo.resolve_path(run_id, "report_md")
    assert os.path.exists(report_md_path)
    with open(report_md_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "PARTIAL RUN ANALYSIS" in content
        assert "CAUTION" in content
