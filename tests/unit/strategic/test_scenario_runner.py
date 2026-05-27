import os
import pytest
from src.testing.scenario_runner import ScenarioRunner


def test_scenario_spec_loading():
    """Verify that ScenarioRunner loads YAML scenario spec and parses config fields correctly."""
    spec_path = "docs/scenarios/phase1/scenario1_growth.yaml"
    assert os.path.exists(spec_path)
    
    runner = ScenarioRunner(spec_path, output_dir="tmp/reports/phase1")
    assert runner.spec["scenario_id"] == "scenario1_growth"
    assert runner.spec["world_pack"] == "phase1_adventure_seed"
    assert len(runner.spec["actors"]) == 1
    assert "defer_with_reason" in runner.spec["valid_route_families"]


def test_scenario_execution_and_reports():
    """Verify that ScenarioRunner executes and compiles rich diagnostic scorecard reports."""
    spec_path = "docs/scenarios/phase1/scenario1_growth.yaml"
    runner = ScenarioRunner(spec_path, output_dir="tmp/reports/phase1")
    
    scorecard = runner.execute(ticks=10)
    assert scorecard["scenario_id"] == "scenario1_growth"
    assert scorecard["total_ticks"] == 10
    assert scorecard["status"] in ("PASS", "PARTIAL_PASS", "FAIL")
    assert "defer_with_reason" in scorecard["detected_route_families"]
    
    # Assert report files are generated on disk
    scorecard_file = "tmp/reports/phase1/scenario1_growth_scorecard.json"
    trace_file = "tmp/reports/phase1/scenario1_growth_route_trace.jsonl"
    
    assert os.path.exists(scorecard_file)
    assert os.path.exists(trace_file)
