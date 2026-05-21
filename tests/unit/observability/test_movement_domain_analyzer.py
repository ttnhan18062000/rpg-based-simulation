"""
Unit tests — MovementDomainAnalyzer

Validates:
- Stuck events produce a movement finding
- Oscillating entities produce a movement finding
- Missing movement events → SKIPPED
- Clean run produces PASSED
"""
import pytest

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.domain.movement import MovementDomainAnalyzer
from src.observability.understanding.domain.base import DomainAnalysisStatus
from src.observability.anomaly.rules import Anomaly
from src.observability.events import SimulationEvent


def _make_movement_event(entity_id: int, tick: int, start_pos, end_pos) -> SimulationEvent:
    return SimulationEvent(
        event_type="movement",
        event_category="movement",
        tick=tick,
        source_system="locomotion_system",
        message=f"Entity {entity_id} moved",
        entity_id=entity_id,
        payload={"start_pos": list(start_pos), "end_pos": list(end_pos)},
        run_id="test-run"
    )


def _make_stuck_anomaly(entity_id: int, position, stuck_ticks: int) -> Anomaly:
    return Anomaly(
        rule_name="NavigationStuckRule",
        severity="ERROR",
        entity_id=entity_id,
        tick_detected=100,
        message=f"Entity {entity_id} stuck at {position}",
        context={"position": str(position), "stuck_duration_ticks": stuck_ticks}
    )


class TestMovementDomainAnalyzer:

    def test_no_movement_events_produces_skipped(self):
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=[], anomalies=[])
        analyzer = MovementDomainAnalyzer()
        result = analyzer.analyze(ctx)
        assert result.status == DomainAnalysisStatus.SKIPPED_MISSING_SIGNAL

    def test_stuck_entities_produce_finding(self):
        events = [_make_movement_event(1, 10, (0, 0), (1, 1))]
        anomalies = [
            _make_stuck_anomaly(1, (1, 1), 60),
            _make_stuck_anomaly(2, (1, 1), 55),
            _make_stuck_anomaly(3, (2, 2), 70),
        ]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events, anomalies=anomalies)
        analyzer = MovementDomainAnalyzer()
        result = analyzer.analyze(ctx)

        assert result.status == DomainAnalysisStatus.FINDINGS_FOUND
        assert len(result.findings) >= 1
        stuck_finding = next(f for f in result.findings if "Stuck" in f.title)
        assert "3" in stuck_finding.title or 3 == len(stuck_finding.affected_entities)
        assert len(stuck_finding.evidence) > 0
        assert len(stuck_finding.recommended_next_steps) > 0

    def test_single_stuck_entity_produces_warning_not_error(self):
        events = [_make_movement_event(1, 10, (0, 0), (1, 1))]
        anomalies = [_make_stuck_anomaly(1, (1, 1), 60)]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events, anomalies=anomalies)
        result = MovementDomainAnalyzer().analyze(ctx)
        stuck_finding = next(f for f in result.findings if "Stuck" in f.title)
        assert stuck_finding.severity == "WARNING"  # Single entity, not cluster threshold

    def test_many_stuck_entities_produce_error(self):
        events = [_make_movement_event(i, 10, (0, 0), (i, i)) for i in range(1, 6)]
        anomalies = [_make_stuck_anomaly(i, (i, i), 60) for i in range(1, 6)]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events, anomalies=anomalies)
        result = MovementDomainAnalyzer().analyze(ctx)
        stuck_finding = next(f for f in result.findings if "Stuck" in f.title)
        assert stuck_finding.severity == "ERROR"

    def test_oscillating_entities_produce_finding(self):
        # Entity oscillates between (0,0) and (1,1) 6 times
        events = []
        positions = [(0, 0), (1, 1), (0, 0), (1, 1), (0, 0), (1, 1)]
        for i, pos in enumerate(positions):
            events.append(_make_movement_event(42, tick=i * 10 + 1, start_pos=(0, 0), end_pos=pos))

        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events, anomalies=[])
        result = MovementDomainAnalyzer().analyze(ctx)

        oscillation_findings = [f for f in result.findings if "Oscillation" in f.title]
        assert len(oscillation_findings) == 1
        assert 42 in oscillation_findings[0].affected_entities

    def test_clean_run_produces_passed(self):
        events = [
            _make_movement_event(1, 10, (0, 0), (1, 1)),
            _make_movement_event(1, 20, (1, 1), (2, 2)),
            _make_movement_event(1, 30, (2, 2), (3, 3)),
        ]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events, anomalies=[])
        result = MovementDomainAnalyzer().analyze(ctx)
        assert result.status == DomainAnalysisStatus.PASSED
        assert result.findings == []

    def test_finding_includes_suspected_causes(self):
        events = [_make_movement_event(1, 10, (0, 0), (1, 1))]
        anomalies = [_make_stuck_anomaly(1, (1, 1), 60)]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events, anomalies=anomalies)
        result = MovementDomainAnalyzer().analyze(ctx)
        stuck_finding = next(f for f in result.findings if "Stuck" in f.title)
        assert len(stuck_finding.suspected_causes) > 0
