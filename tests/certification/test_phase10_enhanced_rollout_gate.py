# TDD certification tests for Rollout Gate in Phase 10
import pytest
import os
import json
from scripts.phase10_enhanced_rollout_gate import RolloutGate

@pytest.fixture
def temp_report_file(tmp_path):
    report_data = {
        "avg_tick_ms": 4.5,
        "deterministic": True,
        "semantic_scorecard": {"combat": 85, "coop": 90},
        "forbidden_behaviors": [],
        "hard_law_violations": [],
        "dropped_critical_traces": 0,
        "memory_caps_respected": True
    }
    file_path = tmp_path / "test_rollout_report.json"
    with open(file_path, "w") as f:
        json.dump(report_data, f)
    return str(file_path)

def test_rollout_gate_rejects_missing_reports():
    gate = RolloutGate(report_path="nonexistent_report.json")
    res, reason = gate.validate()
    assert not res
    assert "Missing report" in reason

def test_rollout_gate_rejects_performance_regression(tmp_path):
    report_data = {
        "avg_tick_ms": 55.0, # Exceeds budget threshold e.g. 50.0
        "deterministic": True,
        "semantic_scorecard": {"combat": 85, "coop": 90},
        "forbidden_behaviors": [],
        "hard_law_violations": [],
        "dropped_critical_traces": 0,
        "memory_caps_respected": True
    }
    file_path = tmp_path / "regressed_report.json"
    with open(file_path, "w") as f:
        json.dump(report_data, f)
        
    gate = RolloutGate(report_path=str(file_path), budget_ms=25.0)
    res, reason = gate.validate()
    assert not res
    assert "performance regression" in reason.lower()

def test_rollout_gate_rejects_forbidden_behavior(tmp_path):
    report_data = {
        "avg_tick_ms": 4.5,
        "deterministic": True,
        "semantic_scorecard": {"combat": 85, "coop": 90},
        "forbidden_behaviors": ["stuck_loop_detected"],
        "hard_law_violations": [],
        "dropped_critical_traces": 0,
        "memory_caps_respected": True
    }
    file_path = tmp_path / "forbidden_report.json"
    with open(file_path, "w") as f:
        json.dump(report_data, f)
        
    gate = RolloutGate(report_path=str(file_path))
    res, reason = gate.validate()
    assert not res
    assert "forbidden behavior" in reason.lower()

def test_rollout_gate_rejects_determinism_failure(tmp_path):
    report_data = {
        "avg_tick_ms": 4.5,
        "deterministic": False,
        "semantic_scorecard": {"combat": 85, "coop": 90},
        "forbidden_behaviors": [],
        "hard_law_violations": [],
        "dropped_critical_traces": 0,
        "memory_caps_respected": True
    }
    file_path = tmp_path / "nondet_report.json"
    with open(file_path, "w") as f:
        json.dump(report_data, f)
        
    gate = RolloutGate(report_path=str(file_path))
    res, reason = gate.validate()
    assert not res
    assert "determinism failure" in reason.lower()

def test_rollout_gate_accepts_valid_bundle(temp_report_file):
    gate = RolloutGate(report_path=temp_report_file, budget_ms=10.0)
    res, reason = gate.validate()
    assert res
    assert "Rollout is safe" in reason

def test_rollout_gate_uses_bounded_language(temp_report_file):
    gate = RolloutGate(report_path=temp_report_file)
    res, reason = gate.validate()
    # Ensure no absolute certainty claims are made
    assert "absolutely certain" not in reason.lower()
    assert "100% verified" not in reason.lower()
