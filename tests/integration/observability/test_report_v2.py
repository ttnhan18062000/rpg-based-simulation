from __future__ import annotations
import os
import shutil
import pytest
import json
from src.core.lifecycle import ShutdownResult, LifecycleOutcome
from src.observability.reporting.run_report import RunReportGenerator
from src.observability.events import SimulationEvent
from src.observability.reporting.metric_recorder import MetricWindowRecord
from src.observability.anomaly.rules_engine import RuleResult, RuleStatus, AnomalyRecord
from src.observability.anomaly.triage import TriageEngine, EvidenceBuilder

@pytest.fixture
def run_dir(tmp_path):
    path = tmp_path / "test_report_v2_dir"
    path.mkdir()
    yield str(path)
    if path.exists():
        shutil.rmtree(path)

def test_report_v2_generation(run_dir):
    # 1. Create simulated events and metric windows
    jsonl_path = os.path.join(run_dir, "simulation_events.jsonl")
    events = [
        SimulationEvent(
            event_type="NavigationStuck", event_category="movement", tick=12,
            severity="WARNING", source_system="movement_system", message="Entity 10 is stuck",
            entity_id=10, region_id="region_a", payload={"x": 5, "y": 6}
        ),
        SimulationEvent(
            event_type="NavigationStuck", event_category="movement", tick=14,
            severity="WARNING", source_system="movement_system", message="Entity 11 is stuck",
            entity_id=11, region_id="region_a", payload={"x": 5, "y": 7}
        )
    ]
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(ev.model_dump_json() + "\n")

    # 2. Formulate rule results
    anomalies = [
        AnomalyRecord(
            rule_id="NavigationStuckBasic",
            severity="WARNING",
            domain="movement",
            message="Navigation stuck basic triggered",
            tick_start=10,
            tick_end=20,
            affected_entity_ids=[10, 11],
            affected_region_ids=["region_a"],
            suggested_causes=["Tile block"]
        )
    ]
    
    # Run evidence enrichment
    from src.observability.anomaly.pipeline import AnalysisContext
    from src.observability.reporting.artifact_repository import RunManifest
    manifest = RunManifest(
        run_id="test_run", ticks_completed=100, status="COMPLETED",
        scenario_name="test_scenario", scenario_type="resource_economy",
        seed=42, observability_mode="LIGHT", started_at="2026-05-19T00:00:00Z",
        ticks_requested=100
    )
    context = AnalysisContext(
        run_id="test_run",
        run_manifest=manifest,
        events=events,
        metric_windows=[],
        hard_law_violations=[],
        observability_mode="LIGHT",
        scenario_type="resource_economy"
    )

    for a in anomalies:
        a.evidence = EvidenceBuilder.build_evidence(a, context)

    rule_results = [
        RuleResult(rule_id="NavigationStuckBasic", status=RuleStatus.FAILED, anomalies=anomalies),
        RuleResult(rule_id="HardLawViolationDetected", status=RuleStatus.PASSED, anomalies=[]),
        RuleResult(rule_id="ResourceProductionZero", status=RuleStatus.SKIPPED_MISSING_SIGNAL, anomalies=[])
    ]

    # Cluster anomalies
    clusters = TriageEngine.cluster_anomalies(anomalies)

    # 3. Create synthetic shutdown result
    shutdown_res = ShutdownResult(
        final_tick=100,
        final_hash="SHA-256-V2-REPORT",
        replay_outcome=LifecycleOutcome.SUCCESS,
        overall_outcome=LifecycleOutcome.SUCCESS
    )

    # 4. Generate report
    report = RunReportGenerator.generate(
        run_dir,
        shutdown_result=shutdown_res,
        timeline_store=None,
        rule_results=rule_results,
        clusters=clusters
    )

    # Assert health score deducts 5 for 1 warning anomaly: 100 - 5 = 95.0
    assert report["metadata"]["health_score"] == 95.0
    assert report["metadata"]["warnings_count"] == 1
    assert len(report["rule_execution"]) == 3
    assert len(report["anomaly_clusters"]) == 1

    # Verify JSON structure
    assert report["rule_execution"][0]["rule_id"] == "NavigationStuckBasic"
    assert report["rule_execution"][0]["status"] == "FAILED"
    assert report["rule_execution"][2]["status"] == "SKIPPED_MISSING_SIGNAL"

    assert report["anomaly_clusters"][0]["rule_id"] == "NavigationStuckBasic"
    assert report["anomaly_clusters"][0]["tick_start"] == 10
    assert report["anomaly_clusters"][0]["tick_end"] == 20
    assert report["anomaly_clusters"][0]["region_id"] == "region_a"
    assert len(report["anomaly_clusters"][0]["evidence_samples"]) == 1

    # Verify report files were saved
    report_json_file = os.path.join(run_dir, "run_report.json")
    report_md_file = os.path.join(run_dir, "run_report.md")
    assert os.path.exists(report_json_file)
    assert os.path.exists(report_md_file)

    # Read md report and assert content
    with open(report_md_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Rule Engine Execution Summary" in content
        assert "Top Anomaly Breakdowns & Clustered Details (Report V2)" in content
        assert "NavigationStuckBasic" in content
        assert "Spacetime Span" in content
        assert "Ticks `10 - 20`" in content
        assert "Troubleshooting Hints" in content
        assert "pathfinding obstacle" in content.lower()
