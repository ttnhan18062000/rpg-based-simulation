"""
Unit tests — EconomyDomainAnalyzer

Validates:
- Gold circulation freeze produces finding
- Resource node crowding produces finding
- Missing economy events → SKIPPED
- Clean active economy → PASSED
"""
import pytest

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.domain.economy import EconomyDomainAnalyzer
from src.observability.understanding.domain.base import DomainAnalysisStatus
from src.observability.anomaly.rules import Anomaly
from src.observability.events import SimulationEvent


def _make_economy_event(entity_id: int, tick: int, amount: float = 10.0) -> SimulationEvent:
    return SimulationEvent(
        event_type="gold_transaction",
        event_category="economy",
        tick=tick,
        source_system="economy_system",
        message=f"Entity {entity_id} transacted {amount} gold",
        entity_id=entity_id,
        payload={"amount": amount, "transaction_kind": "harvest"},
        run_id="test-run"
    )


def _make_crowding_anomaly(node_id: str, entity_count: int, tick: int) -> Anomaly:
    return Anomaly(
        rule_name="ResourceNodeCrowdingRule",
        severity="WARNING",
        entity_id=None,
        tick_detected=tick,
        message=f"Node {node_id} crowded by {entity_count} entities",
        context={"node_id": node_id, "entities_count": entity_count}
    )


class TestEconomyDomainAnalyzer:

    def test_no_economy_events_produces_skipped(self):
        ctx = AnalysisContext(run_id="test", scenario_type="resource_economy")
        result = EconomyDomainAnalyzer().analyze(ctx)
        assert result.status == DomainAnalysisStatus.SKIPPED_MISSING_SIGNAL

    def test_gold_stagnation_produces_finding(self):
        # Events early in run, then nothing for a long gap
        events = [
            _make_economy_event(1, tick=5),
            _make_economy_event(2, tick=10),
            # Gap of 150 ticks
            _make_economy_event(1, tick=160),
        ]
        ctx = AnalysisContext(run_id="test", scenario_type="resource_economy", events=events)
        result = EconomyDomainAnalyzer().analyze(ctx)

        assert result.status == DomainAnalysisStatus.FINDINGS_FOUND
        stagnation = next(f for f in result.findings if "Freeze" in f.title)
        assert "150" in stagnation.summary or 150 == int(stagnation.evidence[0].split(": ")[1].split(" ")[0])

    def test_no_stagnation_in_active_economy(self):
        # Events every 10 ticks — no long gap
        events = [_make_economy_event(i % 5 + 1, tick=i * 10) for i in range(1, 10)]
        ctx = AnalysisContext(run_id="test", scenario_type="resource_economy", events=events)
        result = EconomyDomainAnalyzer().analyze(ctx)
        assert result.status == DomainAnalysisStatus.PASSED

    def test_crowding_anomalies_produce_finding(self):
        events = [_make_economy_event(1, tick=1)]
        anomalies = [
            _make_crowding_anomaly("node_A", 6, 50),
            _make_crowding_anomaly("node_A", 7, 60),
            _make_crowding_anomaly("node_B", 5, 70),
        ]
        ctx = AnalysisContext(run_id="test", scenario_type="resource_economy", events=events, anomalies=anomalies)
        result = EconomyDomainAnalyzer().analyze(ctx)

        crowding = next(f for f in result.findings if "Crowding" in f.title)
        assert "node_A" in crowding.affected_resources or "node_B" in crowding.affected_resources
        assert len(crowding.evidence) > 0

    def test_finding_serializes_to_dict(self):
        events = [_make_economy_event(1, tick=5), _make_economy_event(1, tick=200)]
        ctx = AnalysisContext(run_id="test", scenario_type="resource_economy", events=events)
        result = EconomyDomainAnalyzer().analyze(ctx)
        if result.findings:
            d = result.findings[0].to_dict()
            assert "finding_id" in d
            assert "evidence" in d
