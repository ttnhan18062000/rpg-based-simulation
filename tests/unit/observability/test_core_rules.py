import pytest
from src.observability.events import SimulationEvent
from src.observability.reporting.artifact_repository import RunManifest
from src.observability.reporting.metric_recorder import MetricWindowRecord
from src.observability.anomaly.pipeline import AnalysisContext
from src.observability.anomaly.rules_engine import (
    RuleConfig, RuleStatus, HardLawViolationDetected,
    NavigationStuckBasic, QuestStalledBasic, ResourceProductionZero,
    GovernorDegradedTooLong
)

@pytest.fixture
def base_manifest():
    return RunManifest(
        run_id="test_run", ticks_completed=150, status="COMPLETED",
        scenario_name="test_scenario", scenario_type="resource_economy",
        seed=42, observability_mode="LIGHT", started_at="2026-05-19T00:00:00Z",
        ticks_requested=150
    )

def make_event(tick: int, event_type: str, event_category: str = "movement", entity_id: int = 1, payload: dict = None) -> SimulationEvent:
    return SimulationEvent(
        event_type=event_type,
        event_category=event_category,
        tick=tick,
        source_system="test_system",
        message=f"Test message at {tick}",
        entity_id=entity_id,
        payload=payload or {}
    )

def make_window(start: int, end: int, gold: float = 0.0, governor: str = "NORMAL", active: float = 5.0) -> MetricWindowRecord:
    return MetricWindowRecord(
        run_id="test_run",
        window_start_tick=start,
        window_end_tick=end,
        ticks_observed=end - start,
        alive_entities_avg=10.0,
        active_entities_avg=active,
        gold_total_avg=gold,
        tick_compute_ms_avg=1.0,
        tick_compute_ms_p95=2.0,
        memory_rss_bytes_avg=1024.0,
        memory_rss_bytes_max=2048.0,
        hard_law_violation_count=0,
        event_count=5,
        anomaly_candidate_count=0,
        governor_mode_dominant=governor
    )

def test_hard_law_violation_rule(base_manifest):
    rule = HardLawViolationDetected()
    config = RuleConfig()

    # 1. No violation
    ctx_clean = AnalysisContext(
        run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
        events=[], metric_windows=[], hard_law_violations=[], observability_mode="LIGHT"
    )
    res_clean = rule.evaluate(ctx_clean, config)
    assert res_clean.status == RuleStatus.PASSED
    assert not res_clean.anomalies

    # 2. Violation logged in hard_law_violations
    ctx_violation = AnalysisContext(
        run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
        events=[], metric_windows=[],
        hard_law_violations=[{"tick": 42, "entity_id": 101, "message": "Authoritative sovereignty violation"}],
        observability_mode="LIGHT"
    )
    res_violation = rule.evaluate(ctx_violation, config)
    assert res_violation.status == RuleStatus.FAILED
    assert len(res_violation.anomalies) == 1
    assert res_violation.anomalies[0].severity == "CRITICAL"
    assert res_violation.anomalies[0].tick_start == 42
    assert res_violation.anomalies[0].affected_entity_ids == [101]

def test_navigation_stuck_rule(base_manifest):
    rule = NavigationStuckBasic()
    config = RuleConfig(thresholds={"tick_threshold": 30})

    # 1. Negative path (entity moves positions)
    events_clean = [
        make_event(tick=10, event_type="movement", entity_id=202, payload={"end_pos": "A"}),
        make_event(tick=20, event_type="movement", entity_id=202, payload={"end_pos": "B"}),
        make_event(tick=35, event_type="movement", entity_id=202, payload={"end_pos": "C"}),
    ]
    ctx_clean = AnalysisContext(
        run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
        events=events_clean, metric_windows=[], hard_law_violations=[], observability_mode="LIGHT"
    )
    res_clean = rule.evaluate(ctx_clean, config)
    assert res_clean.status == RuleStatus.PASSED

    # 2. Positive path (entity stuck at same position for >= 30 ticks)
    events_stuck = [
        make_event(tick=10, event_type="movement", entity_id=202, payload={"end_pos": "A"}),
        make_event(tick=20, event_type="movement", entity_id=202, payload={"end_pos": "B"}),
        # Stuck starts at tick 20
        make_event(tick=40, event_type="movement", entity_id=202, payload={"end_pos": "B"}),
        make_event(tick=60, event_type="movement", entity_id=202, payload={"end_pos": "B"}),
    ]
    ctx_stuck = AnalysisContext(
        run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
        events=events_stuck, metric_windows=[], hard_law_violations=[], observability_mode="LIGHT"
    )
    res_stuck = rule.evaluate(ctx_stuck, config)
    assert res_stuck.status == RuleStatus.FAILED
    assert len(res_stuck.anomalies) == 1
    assert res_stuck.anomalies[0].tick_start == 20
    assert res_stuck.anomalies[0].tick_end == 60
    assert res_stuck.anomalies[0].affected_entity_ids == [202]

def test_quest_stalled_rule(base_manifest):
    rule = QuestStalledBasic()
    config = RuleConfig(thresholds={"tick_threshold": 50})

    # 1. Quest started and completed within threshold
    events_clean = [
        make_event(tick=10, event_type="quest_event", event_category="quest", entity_id=1, payload={"quest_id": "Q1", "status": "started"}),
        make_event(tick=30, event_type="quest_event", event_category="quest", entity_id=1, payload={"quest_id": "Q1", "status": "completed"}),
    ]
    ctx_clean = AnalysisContext(
        run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
        events=events_clean, metric_windows=[], hard_law_violations=[], observability_mode="LIGHT"
    )
    res_clean = rule.evaluate(ctx_clean, config)
    assert res_clean.status == RuleStatus.PASSED

    # 2. Quest started and stalled at tick 150 (duration: 140 ticks >= 50 threshold)
    events_stalled = [
        make_event(tick=10, event_type="quest_event", event_category="quest", entity_id=1, payload={"quest_id": "Q1", "status": "started"}),
    ]
    ctx_stalled = AnalysisContext(
        run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
        events=events_stalled, metric_windows=[], hard_law_violations=[], observability_mode="LIGHT"
    )
    res_stalled = rule.evaluate(ctx_stalled, config)
    assert res_stalled.status == RuleStatus.FAILED
    assert len(res_stalled.anomalies) == 1
    assert res_stalled.anomalies[0].affected_quest_ids == ["Q1"]
    assert res_stalled.anomalies[0].tick_start == 10
    assert res_stalled.anomalies[0].tick_end == 150  # manifest complete tick

def test_resource_production_zero_rule(base_manifest):
    rule = ResourceProductionZero()
    config = RuleConfig(thresholds={"window_threshold": 2})

    # 1. Missing signal
    ctx_missing = AnalysisContext(
        run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
        events=[], metric_windows=[], hard_law_violations=[], observability_mode="LIGHT"
    )
    res_missing = rule.evaluate(ctx_missing, config)
    assert res_missing.status == RuleStatus.SKIPPED_MISSING_SIGNAL

    # 2. Skipped scenario type
    ctx_mismatched_scenario = AnalysisContext(
        run_id="test_run", run_manifest=base_manifest, scenario_type="combat_arena",
        events=[], metric_windows=[make_window(start=0, end=10, gold=0.0)], hard_law_violations=[],
        observability_mode="LIGHT"
    )
    res_mismatched_scenario = rule.evaluate(ctx_mismatched_scenario, config)
    assert res_mismatched_scenario.status == RuleStatus.SKIPPED_SCENARIO_TYPE

    # 3. Economy freeze (zero resource production for 2 windows)
    windows_stagnant = [
        make_window(start=0, end=10, gold=0.0, active=5.0),
        make_window(start=10, end=20, gold=0.0, active=5.0),
    ]
    ctx_freeze = AnalysisContext(
        run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
        events=[], metric_windows=windows_stagnant, hard_law_violations=[], observability_mode="LIGHT"
    )
    res_freeze = rule.evaluate(ctx_freeze, config)
    assert res_freeze.status == RuleStatus.FAILED
    assert len(res_freeze.anomalies) == 1
    assert res_freeze.anomalies[0].severity == "ERROR"  # active entities > 0
    assert res_freeze.anomalies[0].tick_start == 0
    assert res_freeze.anomalies[0].tick_end == 20

def test_governor_degraded_too_long_rule(base_manifest):
    rule = GovernorDegradedTooLong()
    config = RuleConfig(thresholds={"window_threshold": 2})

    # 1. Missing signal
    ctx_missing = AnalysisContext(
        run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
        events=[], metric_windows=[], hard_law_violations=[], observability_mode="LIGHT"
    )
    assert rule.evaluate(ctx_missing, config).status == RuleStatus.SKIPPED_MISSING_SIGNAL

    # 2. System pressure error (survival/degraded dominant modes for >= 2 windows)
    windows_pressure = [
        make_window(start=0, end=10, gold=10.0, governor="SURVIVAL"),
        make_window(start=10, end=20, gold=10.0, governor="DEGRADED"),
    ]
    ctx_pressure = AnalysisContext(
        run_id="test_run", run_manifest=base_manifest, scenario_type="resource_economy",
        events=[], metric_windows=windows_pressure, hard_law_violations=[], observability_mode="LIGHT"
    )
    res_pressure = rule.evaluate(ctx_pressure, config)
    assert res_pressure.status == RuleStatus.FAILED
    assert len(res_pressure.anomalies) == 1
    assert res_pressure.anomalies[0].severity == "ERROR"
    assert res_pressure.anomalies[0].tick_start == 0
    assert res_pressure.anomalies[0].tick_end == 20
