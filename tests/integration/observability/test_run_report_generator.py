from __future__ import annotations
import os
import shutil
import pytest
from src.core.lifecycle import ShutdownResult, LifecycleOutcome
from src.observability.reporting.run_report import RunReportGenerator
from src.observability.events import SimulationEvent
from src.observability.anomaly.post_run_analyzer import PostRunAnomalyAnalyzer

@pytest.fixture
def run_dir(tmp_path):
    path = tmp_path / "test_report_dir"
    path.mkdir()
    yield str(path)
    if path.exists():
        shutil.rmtree(path)

def test_run_report_generator(run_dir):
    # 1. Write synthetic anomalies JSON
    anomalies_path = os.path.join(run_dir, "anomalies.json")
    # We have:
    # - 1 CRITICAL / Hard law violation (deducts 40)
    # - 1 ERROR (deducts 15)
    # - 1 WARNING (deducts 5)
    # Health score should be: 100 - 40 - 15 - 5 = 40.0
    anomalies = [
        {"rule_name": "HardLawViolationRule", "severity": "CRITICAL", "entity_id": 1, "tick_detected": 5, "message": "Law broken"},
        {"rule_name": "NavigationStuckRule", "severity": "ERROR", "entity_id": 1, "tick_detected": 10, "message": "Stuck"},
        {"rule_name": "QuestStalledRule", "severity": "WARNING", "entity_id": 2, "tick_detected": 12, "message": "Stalled"}
    ]
    import json
    with open(anomalies_path, "w") as f:
        json.dump(anomalies, f)

    # 2. Write event logs to allow timeline reconstruction
    jsonl_path = os.path.join(run_dir, "simulation_events.jsonl")
    events = [
        SimulationEvent(
            event_type="spawn", event_category="lifecycle", tick=1,
            severity="INFO", source_system="kernel", message="Spawned", entity_id=1
        ),
        SimulationEvent(
            event_type="movement", event_category="movement", tick=2,
            severity="INFO", source_system="locomotion_system", message="Moved", entity_id=1
        ),
        SimulationEvent(
            event_type="quest_event", event_category="quest", tick=3,
            severity="INFO", source_system="quest_system", message="Started quest", entity_id=2
        )
    ]
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(ev.model_dump_json() + "\n")

    # 3. Create synthetic shutdown result
    shutdown_res = ShutdownResult(
        final_tick=15,
        final_hash="SHA-256-AAAA",
        replay_outcome=LifecycleOutcome.SUCCESS,
        overall_outcome=LifecycleOutcome.SUCCESS
    )

    # 4. Generate report
    report = RunReportGenerator.generate(run_dir, shutdown_result=shutdown_res, timeline_store=None)

    # Assertions
    assert report["metadata"]["health_score"] == 40.0
    assert report["metadata"]["hard_law_violations_count"] == 1
    assert report["metadata"]["errors_count"] == 1
    assert report["metadata"]["warnings_count"] == 1
    assert len(report["flagged_timelines"]) == 2
    assert len(report["flagged_timelines"][1]) == 2
    assert len(report["flagged_timelines"][2]) == 1

    # Check generated files
    assert os.path.exists(os.path.join(run_dir, "run_report.json"))
    assert os.path.exists(os.path.join(run_dir, "run_report.md"))

    with open(os.path.join(run_dir, "run_report.md"), "r") as f:
        report_md = f.read()
        assert "Simulation Run Observatory Report" in report_md
        assert "Deterministic Health Score" in report_md
        assert "Executive Scorecard" in report_md
        assert "Triage Metrics Dashboard" in report_md
        assert "Top Anomaly Breakdowns" in report_md
        assert "Diagnostic Entity Timelines" in report_md
