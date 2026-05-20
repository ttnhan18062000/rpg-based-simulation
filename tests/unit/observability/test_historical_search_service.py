from __future__ import annotations
import os
import json
import pytest
from datetime import datetime
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.observability.warehouse.adapters import LocalWarehouseAdapter
from src.observability.warehouse.models import (
    RunRecord,
    EventRecord,
    AnomalyRecord,
    MetricWindowRecord,
    HardLawViolationRecord
)

@pytest.fixture
def mock_run_repo(tmp_path):
    # Setup a mock run repository targeting a temp directory
    repo = RunArtifactRepository(base_dir=str(tmp_path))
    
    # 1. Create Run 1 (Completed, healthy)
    manifest1 = RunManifest(
        run_id="run-1",
        scenario_name="scenario-A",
        scenario_type="combat",
        seed=42,
        observability_mode="LIGHT",
        started_at="2026-05-20T10:00:00Z",
        ended_at="2026-05-20T10:05:00Z",
        ticks_requested=100,
        ticks_completed=100,
        status="COMPLETED"
    )
    repo.create_run("run-1", manifest1)
    # Write run_report.json to test health_score parsing
    report_path1 = repo.resolve_path("run-1", "report_json")
    with open(report_path1, "w", encoding="utf-8") as f:
        json.dump({"metadata": {"health_score": 95.0}}, f)
        
    # Write events to run-1
    events_path1 = repo.resolve_path("run-1", "events")
    events1 = [
        {"tick": 5, "event_type": "move", "event_category": "movement", "severity": "INFO", "entity_id": "hero1", "message": "hero1 moved", "timestamp": "2026-05-20T10:01:00Z"},
        {"tick": 12, "event_type": "hit", "event_category": "combat", "severity": "WARNING", "entity_id": "hero1", "message": "hero1 hit", "timestamp": "2026-05-20T10:02:00Z"},
        {"tick": 20, "event_type": "move", "event_category": "movement", "severity": "INFO", "entity_id": "hero2", "message": "hero2 moved", "timestamp": "2026-05-20T10:03:00Z"}
    ]
    with open(events_path1, "w", encoding="utf-8") as f:
        for ev in events1:
            f.write(json.dumps(ev) + "\n")
            
    # Write anomalies to run-1
    anomalies_path1 = repo.resolve_path("run-1", "anomalies")
    anomalies1 = [
        {
            "rule_id": "NavigationStuckLive",
            "severity": "WARNING",
            "domain": "movement",
            "tick_start": 10,
            "tick_end": 15,
            "affected_entity_count": 1,
            "message": "hero1 is stuck in corner",
            "evidence": {"entity_id": "hero1", "cycles_stuck": 5}
        }
    ]
    with open(anomalies_path1, "w", encoding="utf-8") as f:
        json.dump(anomalies1, f)

    # Write metric windows to run-1
    metrics_path1 = os.path.join(str(tmp_path), "run-1", "metric_windows.jsonl")
    metrics1 = [
        {"window_start_tick": 0, "window_end_tick": 10, "tick_compute_ms_avg": 5.2, "tick_compute_ms_p95": 8.1, "memory_rss_bytes_avg": 5000000.0, "memory_rss_bytes_max": 6000000.0, "alive_entities_avg": 2.0, "gold_total_avg": 100.0, "event_count": 5, "hard_law_violation_count": 0},
        {"window_start_tick": 10, "window_end_tick": 20, "tick_compute_ms_avg": 4.8, "tick_compute_ms_p95": 7.5, "memory_rss_bytes_avg": 5500000.0, "memory_rss_bytes_max": 6500000.0, "alive_entities_avg": 2.0, "gold_total_avg": 120.0, "event_count": 8, "hard_law_violation_count": 0}
    ]
    with open(metrics_path1, "w", encoding="utf-8") as f:
        for m in metrics1:
            f.write(json.dumps(m) + "\n")

    # Write violations to run-1
    violations_path1 = repo.resolve_path("run-1", "violations")
    violations1 = [
        {"tick": 12, "violation_type": "RegionalSovereigntyViolation", "severity": "CRITICAL", "actor_id": "hero1", "target_id": "territory_B", "message": "Invading regional sovereignty", "evidence": {"region": "territory_B"}}
    ]
    with open(violations_path1, "w", encoding="utf-8") as f:
        for v in violations1:
            f.write(json.dumps(v) + "\n")

    # 2. Create Run 2 (Failed, degraded health)
    manifest2 = RunManifest(
        run_id="run-2",
        scenario_name="scenario-B",
        scenario_type="combat",
        seed=100,
        observability_mode="FULL",
        started_at="2026-05-20T11:00:00Z",
        ended_at="2026-05-20T11:02:00Z",
        ticks_requested=200,
        ticks_completed=80,
        status="FAILED",
        failure_reason="Deadlock"
    )
    repo.create_run("run-2", manifest2)
    # Write run_report.json to test health_score parsing
    report_path2 = repo.resolve_path("run-2", "report_json")
    with open(report_path2, "w", encoding="utf-8") as f:
        json.dump({"metadata": {"health_score": 40.0}}, f)
        
    return repo


def test_local_query_runs(mock_run_repo):
    adapter = LocalWarehouseAdapter(run_repo=mock_run_repo)
    
    # Check simple list
    runs = adapter.query_runs({})
    assert len(runs) == 2
    # Should default to run_id desc sorting
    assert runs[0].run_id == "run-2"
    assert runs[1].run_id == "run-1"
    
    # Filter by scenario_name
    runs_filtered = adapter.query_runs({"scenario_name": "scenario-A"})
    assert len(runs_filtered) == 1
    assert runs_filtered[0].run_id == "run-1"
    assert runs_filtered[0].health_score == 95.0
    
    # Filter by status
    runs_failed = adapter.query_runs({"status": "FAILED"})
    assert len(runs_failed) == 1
    assert runs_failed[0].run_id == "run-2"
    assert runs_failed[0].health_score == 40.0

    # Test health score sorting asc
    runs_sorted_asc = adapter.query_runs({"sort": "health_score_asc"})
    assert runs_sorted_asc[0].run_id == "run-2"
    assert runs_sorted_asc[1].run_id == "run-1"

    # Test health score sorting desc
    runs_sorted_desc = adapter.query_runs({"sort": "health_score_desc"})
    assert runs_sorted_desc[0].run_id == "run-1"
    assert runs_sorted_desc[1].run_id == "run-2"

    # Test pagination
    runs_paginated = adapter.query_runs({"limit": 1, "offset": 1})
    assert len(runs_paginated) == 1
    assert runs_paginated[0].run_id == "run-1"


def test_local_query_events(mock_run_repo):
    adapter = LocalWarehouseAdapter(run_repo=mock_run_repo)

    # Missing run_id
    assert adapter.query_events({}) == []

    # Path traversal block
    assert adapter.query_events({"run_id": "../run-1"}) == []

    # Simple fetch
    events = adapter.query_events({"run_id": "run-1"})
    assert len(events) == 3
    assert events[0].tick == 5
    assert events[1].tick == 12
    assert events[2].tick == 20

    # Filter by entity_id
    events_entity = adapter.query_events({"run_id": "run-1", "entity_id": "hero1"})
    assert len(events_entity) == 2
    assert all(e.entity_id == "hero1" for e in events_entity)

    # Filter by tick bounds
    events_ticks = adapter.query_events({"run_id": "run-1", "tick_start": 10, "tick_end": 15})
    assert len(events_ticks) == 1
    assert events_ticks[0].tick == 12

    # Filter by severity
    events_severity = adapter.query_events({"run_id": "run-1", "severity": "WARNING"})
    assert len(events_severity) == 1
    assert events_severity[0].event_type == "hit"

    # Pagination
    events_paginated = adapter.query_events({"run_id": "run-1", "limit": 1, "offset": 1})
    assert len(events_paginated) == 1
    assert events_paginated[0].tick == 12


def test_local_query_anomalies(mock_run_repo):
    adapter = LocalWarehouseAdapter(run_repo=mock_run_repo)

    # Fetch
    anomalies = adapter.query_anomalies({"run_id": "run-1"})
    assert len(anomalies) == 1
    assert anomalies[0].rule_id == "NavigationStuckLive"
    assert anomalies[0].tick_start == 10
    assert anomalies[0].affected_entity_count == 1

    # Filter by rule
    assert len(adapter.query_anomalies({"run_id": "run-1", "rule_id": "WrongRule"})) == 0


def test_local_query_metric_windows(mock_run_repo):
    adapter = LocalWarehouseAdapter(run_repo=mock_run_repo)

    metrics = adapter.query_metric_windows({"run_id": "run-1"})
    assert len(metrics) == 2
    assert metrics[0].window_start_tick == 0
    assert metrics[1].window_start_tick == 10
    assert metrics[0].tick_compute_ms_avg == 5.2


def test_local_query_violations(mock_run_repo):
    adapter = LocalWarehouseAdapter(run_repo=mock_run_repo)

    violations = adapter.query_violations({"run_id": "run-1"})
    assert len(violations) == 1
    assert violations[0].violation_type == "RegionalSovereigntyViolation"
    assert violations[0].actor_id == "hero1"
