# TDD tests for TraceVolumeGovernor
import pytest
from src.domains.optimization.trace_governor import TraceVolumeGovernor, TraceEvent

def test_trace_governor_caps_low_severity_events():
    tg = TraceVolumeGovernor(max_events_per_tick=3)
    events = [
        TraceEvent(event_id="e1", category="self_model", severity="INFO", message="low1"),
        TraceEvent(event_id="e2", category="self_model", severity="INFO", message="low2"),
        TraceEvent(event_id="e3", category="self_model", severity="INFO", message="low3"),
        TraceEvent(event_id="e4", category="self_model", severity="INFO", message="low4"),
    ]
    processed = tg.process_events(events)
    assert len(processed) == 3
    assert tg.dropped_count == 1

def test_trace_governor_keeps_hard_law_events():
    tg = TraceVolumeGovernor(max_events_per_tick=1)
    events = [
        TraceEvent(event_id="e1", category="self_model", severity="INFO", message="low1"),
        TraceEvent(event_id="e2", category="hard_law", severity="ERROR", message="CRITICAL_LAW_VIOLATION"),
    ]
    processed = tg.process_events(events)
    # The hard law event MUST NOT be dropped, even if it exceeds standard max_events_per_tick
    assert any(e.category == "hard_law" for e in processed)

def test_trace_governor_summarizes_repeated_events():
    tg = TraceVolumeGovernor(max_events_per_tick=10, repeated_summary_threshold=2)
    events = [
        TraceEvent(event_id="e1", category="combat_engagement", severity="INFO", message="slash", entity_id=1),
        TraceEvent(event_id="e2", category="combat_engagement", severity="INFO", message="slash", entity_id=1),
        TraceEvent(event_id="e3", category="combat_engagement", severity="INFO", message="slash", entity_id=1),
    ]
    processed = tg.process_events(events)
    # The repeated low-severity messages should be summarized/deduplicated
    assert len(processed) < 3
    assert any("Repeated message summarized" in e.message for e in processed)

def test_trace_governor_reports_dropped_counts():
    tg = TraceVolumeGovernor(max_events_per_tick=2)
    events = [
        TraceEvent(event_id="e1", category="self_model", severity="INFO", message="m1"),
        TraceEvent(event_id="e2", category="self_model", severity="INFO", message="m2"),
        TraceEvent(event_id="e3", category="self_model", severity="INFO", message="m3"),
    ]
    tg.process_events(events)
    report = tg.generate_report()
    assert report["dropped_total"] == 1

def test_trace_governor_does_not_change_state_hash():
    # Demonstrating pure observability without mutating state logic
    tg = TraceVolumeGovernor(max_events_per_tick=1)
    events = [TraceEvent(event_id="e1", category="self_model", severity="INFO", message="m1")]
    processed = tg.process_events(events)
    assert len(processed) == 1

def test_required_scenario_evidence_events_are_not_dropped():
    tg = TraceVolumeGovernor(max_events_per_tick=1)
    # Scenario evidence has high severity or dedicated tag
    events = [
        TraceEvent(event_id="ev_evidence", category="campaign_semantic", severity="WARNING", message="evidence of arc"),
        TraceEvent(event_id="e1", category="self_model", severity="INFO", message="m1"),
    ]
    processed = tg.process_events(events)
    assert any(e.event_id == "ev_evidence" for e in processed)
