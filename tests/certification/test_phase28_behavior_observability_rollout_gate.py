import json
import pytest
from scripts.behavior_observability_rollout_gate import BehaviorObservabilityRolloutGate

@pytest.fixture
def temp_report_file(tmp_path):
    report = {
        "overhead_percent": 1.5,
        "deterministic": True,
        "runtime_profiling_works": True,
        "queue_nonblocking": True,
        "worker_isolated": True,
        "postrun_deferred": True,
        "behavior_artifacts_optional": True,
        "critical_events_dropped": False
    }
    path = tmp_path / "behavior_report.json"
    with open(path, "w") as f:
        json.dump(report, f)
    return path

def test_rollout_gate_accepts_valid_report(temp_report_file):
    gate = BehaviorObservabilityRolloutGate(str(temp_report_file))
    res, reason = gate.validate()
    assert res is True
    assert "safe for production" in reason

def test_rollout_gate_rejects_excessive_observability_overhead(temp_report_file):
    with open(temp_report_file, "r") as f:
        data = json.load(f)
    data["overhead_percent"] = 5.5
    with open(temp_report_file, "w") as f:
        json.dump(data, f)
        
    gate = BehaviorObservabilityRolloutGate(str(temp_report_file), max_overhead_percent=3.0)
    res, reason = gate.validate()
    assert res is False
    assert "overhead too high" in reason

def test_rollout_gate_rejects_determinism_failure(temp_report_file):
    with open(temp_report_file, "r") as f:
        data = json.load(f)
    data["deterministic"] = False
    with open(temp_report_file, "w") as f:
        json.dump(data, f)
        
    gate = BehaviorObservabilityRolloutGate(str(temp_report_file))
    res, reason = gate.validate()
    assert res is False
    assert "determinism mismatch" in reason
