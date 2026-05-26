from __future__ import annotations
import os
import shutil
import pytest
import json
from src.core.lifecycle import ShutdownResult, LifecycleOutcome
from src.observability.reporting.run_report import RunReportGenerator

@pytest.fixture
def run_dir(tmp_path):
    path = tmp_path / "test_cognition_report_dir"
    path.mkdir()
    yield str(path)
    if path.exists():
        shutil.rmtree(path)


def test_cognition_report_generation_with_data(run_dir):
    # 1. Write dummy cognition files
    patterns = [
        {"pattern_id": "P01", "entity_id": 10, "pattern_type": "detour_loop", "severity": "WARNING", "description": "Entity 10 is looping", "tick_detected": 10}
    ]
    with open(os.path.join(run_dir, "cognition_patterns.json"), "w", encoding="utf-8") as f:
        json.dump(patterns, f)

    features = [
        {"tick": 5, "entity_id": 10, "overload_factor": 0.5, "project_switch_count": 0, "detour_delta_count": 0},
        {"tick": 10, "entity_id": 10, "overload_factor": 1.2, "project_switch_count": 1, "detour_delta_count": 1}
    ]
    with open(os.path.join(run_dir, "cognition_features.jsonl"), "w", encoding="utf-8") as f:
        for feat in features:
            f.write(json.dumps(feat) + "\n")

    snapshots = [
        {
            "tick": 10,
            "entity_id": 10,
            "current_project_id": "project_1",
            "current_objective_id": "objective_1",
            "overload_source": "congestion",
            "nodes": [
                {"node_id": "node_1", "kind": "blocker", "label": "Stuck in region", "metadata": {"severity": "high", "resolved": False}},
                {"node_id": "node_2", "kind": "lead", "label": "Alternative route found", "metadata": {"certainty": "high", "tested": True}}
            ]
        }
    ]
    with open(os.path.join(run_dir, "cognition_graph_snapshots.jsonl"), "w", encoding="utf-8") as f:
        for snap in snapshots:
            f.write(json.dumps(snap) + "\n")

    diffs = [
        {
            "tick": 10,
            "entity_id": 10,
            "current_project_changed": True,
            "detour_delta_count": 1,
            "added_nodes": [{"node_id": "node_3"}],
            "removed_nodes": []
        }
    ]
    with open(os.path.join(run_dir, "cognition_graph_diffs.jsonl"), "w", encoding="utf-8") as f:
        for diff in diffs:
            f.write(json.dumps(diff) + "\n")

    # 2. Setup mock shutdown result
    shutdown_res = ShutdownResult(
        final_tick=100,
        final_hash="SHA-256-V2-REPORT",
        replay_outcome=LifecycleOutcome.SUCCESS,
        overall_outcome=LifecycleOutcome.SUCCESS
    )

    # 3. Generate report
    report = RunReportGenerator.generate(
        run_dir,
        shutdown_result=shutdown_res,
        timeline_store=None,
        rule_results=[],
        clusters=[]
    )

    # 4. Assertions on JSON output
    assert "cognition" in report
    sc = report["cognition"]
    assert len(sc["patterns"]) == 1
    assert sc["patterns"][0]["pattern_id"] == "P01"
    assert len(sc["features"]) == 2
    assert len(sc["snapshots"]) == 1
    assert len(sc["diffs"]) == 1

    # 5. Assertions on Markdown output
    report_md_file = os.path.join(run_dir, "run_report.md")
    assert os.path.exists(report_md_file)
    with open(report_md_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Strategic Cognition Evidence" in content
        assert "detour_loop" in content
        assert "Entity 10 is looping" in content
        assert "Recent Strategic Cognition Changes" in content


def test_cognition_report_generation_missing_data(run_dir):
    # Setup mock shutdown result
    shutdown_res = ShutdownResult(
        final_tick=100,
        final_hash="SHA-256-V2-REPORT",
        replay_outcome=LifecycleOutcome.SUCCESS,
        overall_outcome=LifecycleOutcome.SUCCESS
    )

    # Generate report with no cognition files written
    report = RunReportGenerator.generate(
        run_dir,
        shutdown_result=shutdown_res,
        timeline_store=None,
        rule_results=[],
        clusters=[]
    )

    # Assertions on JSON output
    assert "cognition" in report
    sc = report["cognition"]
    assert sc["patterns"] == []
    assert sc["features"] == []
    assert sc["snapshots"] == []
    assert sc["diffs"] == []

    # Assertions on Markdown notice
    report_md_file = os.path.join(run_dir, "run_report.md")
    assert os.path.exists(report_md_file)
    with open(report_md_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Strategic Cognition Evidence" in content
        assert "Strategic cognition data is missing or unavailable for this run" in content
