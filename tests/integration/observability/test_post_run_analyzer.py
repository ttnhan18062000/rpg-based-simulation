from __future__ import annotations
import os
import shutil
import pytest
from src.observability.events import SimulationEvent
from src.observability.anomaly.post_run_analyzer import PostRunAnomalyAnalyzer

@pytest.fixture
def run_dir(tmp_path):
    path = tmp_path / "test_run_dir"
    path.mkdir()
    yield str(path)
    if path.exists():
        shutil.rmtree(path)

def test_post_run_anomaly_analyzer(run_dir):
    # 1. Write synthetic events JSONL
    jsonl_path = os.path.join(run_dir, "simulation_events.jsonl")
    events = [
        # Hard law violation event
        SimulationEvent(
            event_type="InvariantViolation", event_category="hard_law", tick=5,
            severity="CRITICAL", source_system="hard_law_monitor", message="Breached gold limit",
            entity_id=1, payload={"gold": -5}
        ),
        # Normal movement event
        SimulationEvent(
            event_type="movement", event_category="movement", tick=6,
            severity="INFO", source_system="locomotion_system", message="moved",
            entity_id=1, payload={"end_pos": (20.0, 30.0)}
        )
    ]
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(ev.model_dump_json() + "\n")

    # 2. Run Analyzer
    analyzer = PostRunAnomalyAnalyzer()
    anomalies = analyzer.analyze(run_dir)

    # Assertions
    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "HardLawViolationRule"
    assert anomalies[0].severity == "CRITICAL"
    assert anomalies[0].entity_id == 1

    # Check generated files
    assert os.path.exists(os.path.join(run_dir, "anomalies.json"))
    assert os.path.exists(os.path.join(run_dir, "anomaly_summary.md"))

    with open(os.path.join(run_dir, "anomalies.json"), "r") as f:
        data = f.read()
        assert "HardLawViolationRule" in data

    with open(os.path.join(run_dir, "anomaly_summary.md"), "r") as f:
        summary = f.read()
        assert "Severity Dashboard" in summary
        assert "CRITICAL" in summary
