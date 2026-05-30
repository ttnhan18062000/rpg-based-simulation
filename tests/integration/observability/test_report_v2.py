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


def test_provenance_grouping_in_report(run_dir):
    # 1. Create a dummy world.resolved.yaml
    resolved_world_content = {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley_report",
        "name": "Test Valley Report",
        "regions": [
            {"id": "town_square", "bounds": [0, 0, 10, 10], "type": "town"}
        ],
        "factions": [],
        "resources": [],
        "buildings": [],
        "entities": [
            {"id": "citizen_group", "spawn_region": "town_square", "role": "citizen", "faction": "town_council", "count": 1}
        ],
        "topology": {"width": 100, "height": 100, "coordinate_system": "grid"}
    }
    import yaml
    resolved_world_path = os.path.join(run_dir, "world.resolved.yaml")
    with open(resolved_world_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(resolved_world_content, f)

    # 2. Create a dummy run_manifest.json pointing to it
    run_manifest = {
        "run_id": os.path.basename(run_dir),
        "scenario_name": "Test Report",
        "scenario_type": "test",
        "seed": 42,
        "status": "COMPLETED",
        "ticks_requested": 10,
        "started_at": "2026-05-30T12:00:00Z",
        "observability_mode": "full",
        "resolved_world_path": resolved_world_path
    }
    with open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(run_manifest, f)

    # 3. Create provenance manifest sidecar
    provenance_manifest = {
        "manifest_id": "prov_manifest_report",
        "world_id": "test_valley_report",
        "catalog_fingerprint": "catalog_sha256",
        "records": {
            "citizen_group": {
                "source_module": "core_town",
                "recipe_type": "population"
            }
        }
    }
    with open(os.path.join(run_dir, "provenance_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(provenance_manifest, f)

    # 4. Create an anomaly list
    anomalies = [
        {
            "rule_name": "QuestStalledRule",
            "severity": "WARNING",
            "entity_id": 1,  # matches citizen_group
            "tick_detected": 5,
            "message": "Citizen quest stalled"
        }
    ]

    # 5. Generate report
    shutdown_res = ShutdownResult(
        final_tick=10,
        final_hash="SHA-256-PROV",
        replay_outcome=LifecycleOutcome.SUCCESS,
        overall_outcome=LifecycleOutcome.SUCCESS
    )

    report = RunReportGenerator.generate(
        run_dir,
        shutdown_result=shutdown_res,
        timeline_store=None,
        rule_results=[],
        clusters=[],
        anomalies=anomalies
    )

    # 6. Verify provenance groupings are populated
    assert "provenance_grouping" in report
    grouping = report["provenance_grouping"]
    
    assert "by_module" in grouping
    assert "by_profile" in grouping
    assert "by_faction" in grouping
    
    assert "core_town" in grouping["by_module"]
    assert "citizen" in grouping["by_profile"]
    assert "town_council" in grouping["by_faction"]

    # Verify generated markdown report contains the sections and data
    report_md_file = os.path.join(run_dir, "run_report.md")
    assert os.path.exists(report_md_file)
    with open(report_md_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Provenance Source Grouping" in content
        assert "By Source Module" in content
        assert "core_town" in content
        assert "citizen" in content
        assert "town_council" in content
