import pytest
from src.observability.events import SimulationEvent
from src.observability.reporting.artifact_repository import RunManifest
from src.observability.reporting.metric_recorder import MetricWindowRecord
from src.observability.anomaly.pipeline import AnalysisContext
from src.observability.anomaly.rules_engine import AnomalyRecord
from src.observability.anomaly.triage import EvidenceBuilder

@pytest.fixture
def base_context():
    manifest = RunManifest(
        run_id="test_run", ticks_completed=100, status="COMPLETED",
        scenario_name="test_scenario", scenario_type="mixed_sandbox",
        seed=42, observability_mode="LIGHT", started_at="2026-05-19T00:00:00Z",
        ticks_requested=100
    )
    events = [
        SimulationEvent(
            tick=12, event_category="movement", event_type="NavigationStuck",
            entity_id=10, message="Stuck moving", source_system="movement_system",
            payload={"x": 5, "y": 6}
        ),
        SimulationEvent(
            tick=15, event_category="quest", event_type="QuestStarted",
            entity_id=10, message="Quest initiated", source_system="quest_system",
            quest_id="quest_99"
        )
    ]
    metric_windows = [
        MetricWindowRecord(
            run_id="test_run", window_start_tick=0, window_end_tick=10, ticks_observed=10,
            alive_entities_avg=1.0, active_entities_avg=1.0, gold_total_avg=0.0,
            tick_compute_ms_avg=1.0, tick_compute_ms_p95=2.0, memory_rss_bytes_avg=1024.0,
            memory_rss_bytes_max=2048.0, hard_law_violation_count=0, event_count=5,
            anomaly_candidate_count=0, governor_mode_dominant="DEGRADED"
        )
    ]
    violations = [
        {"tick": 5, "entity_id": 10, "message": "Authoritative sovereignty breach", "region_id": "region_x"}
    ]
    return AnalysisContext(
        run_id="test_run",
        run_manifest=manifest,
        events=events,
        metric_windows=metric_windows,
        hard_law_violations=violations,
        observability_mode="LIGHT",
        scenario_type="mixed_sandbox"
    )

def test_evidence_builder_hard_law(base_context):
    anomaly = AnomalyRecord(
        rule_id="HardLawViolationDetected",
        severity="CRITICAL",
        domain="system",
        message="Invariant violation occurred",
        tick_start=0,
        tick_end=10,
        affected_entity_ids=[10]
    )
    evidence = EvidenceBuilder.build_evidence(anomaly, base_context)
    
    assert evidence["source_artifact"] == "hard_law_violations.jsonl"
    assert evidence["tick_range"] == [0, 10]
    assert evidence["affected_ids"]["entities"] == [10]
    assert len(evidence["details"]["violations"]) == 1
    assert evidence["details"]["violations"][0]["message"] == "Authoritative sovereignty breach"

def test_evidence_builder_navigation_stuck(base_context):
    anomaly = AnomalyRecord(
        rule_id="NavigationStuckBasic",
        severity="WARNING",
        domain="movement",
        message="Entity 10 is stuck",
        tick_start=10,
        tick_end=20,
        affected_entity_ids=[10]
    )
    evidence = EvidenceBuilder.build_evidence(anomaly, base_context)

    assert evidence["source_artifact"] == "simulation_events.jsonl"
    assert len(evidence["details"]["stuck_events"]) == 1
    assert evidence["details"]["stuck_events"][0]["entity_id"] == 10
    assert evidence["details"]["stuck_events"][0]["message"] == "Stuck moving"

def test_evidence_builder_quest_stalled(base_context):
    anomaly = AnomalyRecord(
        rule_id="QuestStalledBasic",
        severity="WARNING",
        domain="quest",
        message="Quest stalled",
        tick_start=10,
        tick_end=20,
        affected_quest_ids=["quest_99"]
    )
    evidence = EvidenceBuilder.build_evidence(anomaly, base_context)

    assert evidence["source_artifact"] == "simulation_events.jsonl"
    assert len(evidence["details"]["quest_events"]) == 1
    assert evidence["details"]["quest_events"][0]["quest_id"] == "quest_99"

def test_evidence_builder_resource_production(base_context):
    anomaly = AnomalyRecord(
        rule_id="ResourceProductionZero",
        severity="ERROR",
        domain="economy",
        message="Production froze",
        tick_start=0,
        tick_end=10
    )
    evidence = EvidenceBuilder.build_evidence(anomaly, base_context)

    assert evidence["source_artifact"] == "metric_windows.jsonl"
    assert len(evidence["details"]["metric_windows"]) == 1
    assert evidence["details"]["metric_windows"][0]["gold_total_avg"] == 0.0

def test_evidence_builder_governor_degraded(base_context):
    anomaly = AnomalyRecord(
        rule_id="GovernorDegradedTooLong",
        severity="WARNING",
        domain="system",
        message="Governor degraded too long",
        tick_start=0,
        tick_end=10
    )
    evidence = EvidenceBuilder.build_evidence(anomaly, base_context)

    assert evidence["source_artifact"] == "metric_windows.jsonl"
    assert len(evidence["details"]["metric_windows"]) == 1
    assert evidence["details"]["metric_windows"][0]["governor_mode_dominant"] == "DEGRADED"
