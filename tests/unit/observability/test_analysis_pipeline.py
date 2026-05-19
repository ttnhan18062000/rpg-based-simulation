from __future__ import annotations
import os
import json
import pytest
import shutil
from typing import List

from src.observability.events import SimulationEvent
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.observability.reporting.metric_recorder import MetricWindowRecord
from src.observability.anomaly import (
    AnalysisPipeline, AnalysisInputLoader, AnalysisContext,
    AnalyzerRegistry, BaseAnalyzer, Anomaly, BasicRuntimeAnalyzer
)

@pytest.fixture
def clean_pipeline_runs(tmp_path):
    base_dir = tmp_path / "runs"
    base_dir.mkdir()
    repo = RunArtifactRepository(str(base_dir))
    yield repo
    if base_dir.exists():
        shutil.rmtree(base_dir)

def test_loader_completed_run(clean_pipeline_runs):
    repo = clean_pipeline_runs
    run_id = "test_completed_run"
    
    manifest = RunManifest(
        run_id=run_id,
        scenario_name="test-scen",
        scenario_type="TEST",
        seed=123,
        observability_mode="LIGHT",
        started_at="now",
        ticks_requested=10,
        ticks_completed=10,
        status="COMPLETED"
    )
    repo.create_run(run_id, manifest)
    
    # Write empty jsonl files to avoid load errors
    with open(repo.resolve_path(run_id, "events"), "w", encoding="utf-8") as f:
        pass
    with open(os.path.join(repo.base_dir, run_id, "metric_windows.jsonl"), "w", encoding="utf-8") as f:
        pass
        
    loader = AnalysisInputLoader(repo)
    context = loader.load(run_id)
    
    assert context.run_id == run_id
    assert context.observability_mode == "LIGHT"
    assert context.scenario_type == "TEST"
    assert len(context.events) == 0

def test_loader_missing_manifest(clean_pipeline_runs):
    repo = clean_pipeline_runs
    loader = AnalysisInputLoader(repo)
    with pytest.raises(FileNotFoundError):
        loader.load("non_existent_run")

def test_loader_partial_run_refused_by_default(clean_pipeline_runs):
    repo = clean_pipeline_runs
    run_id = "test_partial_run"
    
    manifest = RunManifest(
        run_id=run_id,
        scenario_name="test-scen",
        scenario_type="TEST",
        seed=123,
        observability_mode="LIGHT",
        started_at="now",
        ticks_requested=10,
        ticks_completed=5,
        status="RUNNING"
    )
    repo.create_run(run_id, manifest)
    
    loader = AnalysisInputLoader(repo)
    with pytest.raises(ValueError, match="Cannot analyze incomplete run"):
        loader.load(run_id)

def test_loader_partial_run_allowed_explicitly(clean_pipeline_runs):
    repo = clean_pipeline_runs
    run_id = "test_partial_run_allowed"
    
    manifest = RunManifest(
        run_id=run_id,
        scenario_name="test-scen",
        scenario_type="TEST",
        seed=123,
        observability_mode="LIGHT",
        started_at="now",
        ticks_requested=10,
        ticks_completed=5,
        status="RUNNING"
    )
    repo.create_run(run_id, manifest)
    
    loader = AnalysisInputLoader(repo)
    context = loader.load(run_id, allow_partial=True)
    assert context.run_id == run_id
    assert context.run_manifest.status == "RUNNING"

def test_analyzer_registry_preserves_order_and_handles_errors():
    class DummyAnalyzer1(BaseAnalyzer):
        def analyze(self, context: AnalysisContext) -> List[Anomaly]:
            return [Anomaly(rule_name="DummyRule1", severity="WARNING", tick_detected=1, message="d1")]
            
    class DummyAnalyzer2(BaseAnalyzer):
        def analyze(self, context: AnalysisContext) -> List[Anomaly]:
            raise RuntimeError("Dummy Failure")
            
    class DummyAnalyzer3(BaseAnalyzer):
        def analyze(self, context: AnalysisContext) -> List[Anomaly]:
            return [Anomaly(rule_name="DummyRule3", severity="ERROR", tick_detected=2, message="d3")]

    registry = AnalyzerRegistry()
    registry._analyzers = [DummyAnalyzer1(), DummyAnalyzer2(), DummyAnalyzer3()]
    
    # Create empty synthetic context
    manifest = RunManifest(
        run_id="test", scenario_name="s", scenario_type="t", seed=1, observability_mode="OFF",
        started_at="now", ticks_requested=1, ticks_completed=1, status="COMPLETED"
    )
    context = AnalysisContext(
        run_id="test", run_manifest=manifest, events=[], metric_windows=[],
        hard_law_violations=[], observability_mode="OFF", scenario_type="t"
    )
    
    anomalies, errors = registry.run_all(context)
    
    # Assert stable order of successful evaluations is preserved
    assert len(anomalies) == 2
    assert anomalies[0].rule_name == "DummyRule1"
    assert anomalies[1].rule_name == "DummyRule3"
    
    # Assert grace failure containment
    assert len(errors) == 1
    assert "DummyAnalyzer2 failed: Dummy Failure" in errors[0]

def test_basic_runtime_analyzer_scans_metrics():
    manifest = RunManifest(
        run_id="test", scenario_name="s", scenario_type="t", seed=1, observability_mode="LIGHT",
        started_at="now", ticks_requested=1, ticks_completed=1, status="COMPLETED"
    )
    
    # Mock window exceeding CPU threshold (>50ms), memory threshold (>2GB), and queue (>80%)
    w1 = MetricWindowRecord(
        run_id="test", window_start_tick=1, window_end_tick=100, ticks_observed=100,
        alive_entities_avg=10, active_entities_avg=10, gold_total_avg=100,
        tick_compute_ms_avg=55.0, tick_compute_ms_p95=60.0,
        memory_rss_bytes_avg=2.5 * 1024 * 1024 * 1024, memory_rss_bytes_max=2.6 * 1024 * 1024 * 1024,
        hard_law_violation_count=0, event_count=0, anomaly_candidate_count=0,
        queue_utilization_avg=0.85
    )
    
    context = AnalysisContext(
        run_id="test", run_manifest=manifest, events=[], metric_windows=[w1],
        hard_law_violations=[], observability_mode="LIGHT", scenario_type="t"
    )
    
    analyzer = BasicRuntimeAnalyzer()
    anomalies = analyzer.analyze(context)
    
    assert len(anomalies) == 3
    rules = [a.rule_name for a in anomalies]
    assert "HighCPULatencyRule" in rules
    assert "MemoryRSSLeakRule" in rules
    assert "HighQueueSaturationRule" in rules
