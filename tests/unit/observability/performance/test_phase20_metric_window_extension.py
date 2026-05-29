import json
import pytest
from src.observability.reporting.metric_recorder import MetricWindowRecord

def test_metric_window_record_backward_compatibility():
    # Construct standard schema dictionary corresponding to older version (v1)
    old_data = {
        "run_id": "test_run_compatibility",
        "window_start_tick": 1,
        "window_end_tick": 100,
        "ticks_observed": 100,
        "alive_entities_avg": 10.5,
        "active_entities_avg": 10.5,
        "gold_total_avg": 500.0,
        "tick_compute_ms_avg": 2.5,
        "tick_compute_ms_p95": 5.0,
        "memory_rss_bytes_avg": 1024 * 1024 * 50,
        "memory_rss_bytes_max": 1024 * 1024 * 60,
        "hard_law_violation_count": 0,
        "event_count": 50,
        "anomaly_candidate_count": 0
    }
    
    # Load old data structure into MetricWindowRecord - it should validate and use safe defaults
    record = MetricWindowRecord(**old_data)
    
    assert record.run_id == "test_run_compatibility"
    assert record.ticks_observed == 100
    
    # Assert new Phase 20 extension fields are present with correct default values
    assert record.phase_duration_ms_avg_json is None
    assert record.phase_duration_ms_p95_json is None
    assert record.phase_event_count_json is None
    assert record.phase_budget_status_json is None
    assert record.observability_overhead_ms_avg == 0.0
    assert record.event_emission_ms_avg == 0.0

def test_metric_window_record_serialization_with_timings():
    # Construct complete dictionary with Phase 20 timing extension fields
    extended_data = {
        "run_id": "test_run_extended",
        "window_start_tick": 101,
        "window_end_tick": 200,
        "ticks_observed": 100,
        "alive_entities_avg": 12.0,
        "active_entities_avg": 12.0,
        "gold_total_avg": 750.0,
        "tick_compute_ms_avg": 3.0,
        "tick_compute_ms_p95": 6.5,
        "memory_rss_bytes_avg": 1024 * 1024 * 55,
        "memory_rss_bytes_max": 1024 * 1024 * 65,
        "hard_law_violation_count": 1,
        "event_count": 75,
        "anomaly_candidate_count": 0,
        "phase_duration_ms_avg_json": json.dumps({"combat": 1.25, "movement": 0.85}),
        "phase_duration_ms_p95_json": json.dumps({"combat": 2.5, "movement": 1.5}),
        "observability_overhead_ms_avg": 0.15,
        "event_emission_ms_avg": 0.05
    }
    
    record = MetricWindowRecord(**extended_data)
    
    # Assert model loads correctly
    assert record.run_id == "test_run_extended"
    assert record.observability_overhead_ms_avg == 0.15
    
    # Parse and assert phase timings JSON string
    assert record.phase_duration_ms_avg_json is not None
    avg_timings = json.loads(record.phase_duration_ms_avg_json)
    assert avg_timings["combat"] == 1.25
    assert avg_timings["movement"] == 0.85
    
    # Serialize to JSON and parse back
    json_str = record.model_dump_json()
    deserialized = json.loads(json_str)
    
    assert deserialized["run_id"] == "test_run_extended"
    assert deserialized["observability_overhead_ms_avg"] == 0.15
    assert "combat" in json.loads(deserialized["phase_duration_ms_avg_json"])
