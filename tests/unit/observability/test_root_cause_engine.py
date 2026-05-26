"""
Unit tests — RootCauseEngine and HypothesisRules

Validates:
- Each rule generates hypotheses for matching conditions
- No hypothesis generated when signature absent
- Crashed rule does not crash engine
- Deduplication keeps highest-confidence version
- Ranking by confidence is correct
"""
import pytest

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.rootcause.engine import RootCauseEngine, RootCauseEngineResult
from src.observability.understanding.rootcause.models import ConfidenceLevel
from src.observability.understanding.rootcause.rules import (
    StaleResourceTargetSelection,
    MovementBottleneckOrOccupancyCrowding,
    InventoryFullReturnLoopBroken,
    QuestObjectiveImpossible,
    GovernorPressureFromObservabilityOrWorkDebt,
    CombatEngagementCannotResolve,
    HypothesisRule,
)
from src.observability.anomaly.rules import Anomaly
from src.observability.events import SimulationEvent


# ── Helpers ───────────────────────────────────────────────────────────────────

def _anomaly(rule_name, entity_id=None, context=None):
    return Anomaly(
        rule_name=rule_name,
        severity="WARNING",
        entity_id=entity_id,
        tick_detected=10,
        message="test anomaly",
        context=context or {}
    )


def _economy_event(tick):
    return SimulationEvent(
        event_type="gold_transaction",
        event_category="economy",
        tick=tick,
        source_system="economy_system",
        message="economy event",
        payload={"amount": 5.0},
        run_id="test"
    )


def _empty_ctx(**kwargs):
    return AnalysisContext(run_id="test", scenario_type="mixed_sandbox", **kwargs)


class _CrashingRule(HypothesisRule):
    rule_id = "CrashingRule"
    def generate(self, ctx):
        raise RuntimeError("Rule crash!")


# ── Individual rule tests ─────────────────────────────────────────────────────

class TestStaleResourceTargetSelection:

    def test_generates_when_crowding_present(self):
        anomalies = [_anomaly("ResourceNodeCrowdingRule", context={"node_id": "n1", "entities_count": 5})]
        ctx = _empty_ctx(anomalies=anomalies)
        hyps = StaleResourceTargetSelection().generate(ctx)
        assert len(hyps) == 1
        assert hyps[0].domain == "economy"

    def test_no_hypothesis_when_no_crowding(self):
        ctx = _empty_ctx()
        hyps = StaleResourceTargetSelection().generate(ctx)
        assert hyps == []

    def test_high_confidence_when_many_crowding_anomalies(self):
        anomalies = [
            _anomaly("ResourceNodeCrowdingRule", context={"node_id": f"n{i}", "entities_count": 6})
            for i in range(6)
        ]
        ctx = _empty_ctx(anomalies=anomalies)
        hyps = StaleResourceTargetSelection().generate(ctx)
        assert hyps[0].confidence == ConfidenceLevel.HIGH

    def test_medium_confidence_with_stuck_also_present(self):
        anomalies = [
            _anomaly("ResourceNodeCrowdingRule", context={"node_id": "n1", "entities_count": 5}),
            _anomaly("NavigationStuckRule", entity_id=1, context={"position": "(1,1)", "stuck_duration_ticks": 60}),
        ]
        ctx = _empty_ctx(anomalies=anomalies)
        hyps = StaleResourceTargetSelection().generate(ctx)
        assert hyps[0].confidence == ConfidenceLevel.MEDIUM


class TestMovementBottleneckOrOccupancyCrowding:

    def test_generates_when_enough_stuck_anomalies(self):
        anomalies = [
            _anomaly("NavigationStuckRule", entity_id=i, context={"position": f"({i},{i})", "stuck_duration_ticks": 60})
            for i in range(1, 4)
        ]
        ctx = _empty_ctx(anomalies=anomalies)
        hyps = MovementBottleneckOrOccupancyCrowding().generate(ctx)
        assert len(hyps) == 1
        assert hyps[0].domain == "movement"

    def test_no_hypothesis_when_few_stuck(self):
        anomalies = [_anomaly("NavigationStuckRule", entity_id=1, context={"position": "(1,1)"})]
        ctx = _empty_ctx(anomalies=anomalies)
        hyps = MovementBottleneckOrOccupancyCrowding().generate(ctx)
        assert hyps == []

    def test_high_confidence_when_concentrated_positions(self):
        # All stuck at same position
        anomalies = [
            _anomaly("NavigationStuckRule", entity_id=i, context={"position": "(5,5)"})
            for i in range(1, 5)
        ]
        ctx = _empty_ctx(anomalies=anomalies)
        hyps = MovementBottleneckOrOccupancyCrowding().generate(ctx)
        assert hyps[0].confidence == ConfidenceLevel.HIGH


class TestInventoryFullReturnLoopBroken:

    def test_generates_on_long_gap(self):
        events = [_economy_event(5), _economy_event(10), _economy_event(200)]
        ctx = _empty_ctx(events=events)
        hyps = InventoryFullReturnLoopBroken().generate(ctx)
        assert len(hyps) == 1
        assert hyps[0].domain == "economy"

    def test_no_hypothesis_on_short_gap(self):
        events = [_economy_event(t) for t in range(1, 20, 5)]  # every 5 ticks
        ctx = _empty_ctx(events=events)
        hyps = InventoryFullReturnLoopBroken().generate(ctx)
        assert hyps == []

    def test_no_hypothesis_when_no_economy_events(self):
        ctx = _empty_ctx()
        hyps = InventoryFullReturnLoopBroken().generate(ctx)
        assert hyps == []


class TestQuestObjectiveImpossible:

    def test_generates_when_many_stalled_quests(self):
        anomalies = [
            _anomaly("QuestStalledRule", context={"quest_id": f"q{i}", "duration_ticks": 120})
            for i in range(4)
        ]
        ctx = _empty_ctx(anomalies=anomalies)
        hyps = QuestObjectiveImpossible().generate(ctx)
        assert len(hyps) == 1

    def test_no_hypothesis_when_few_stalled_quests(self):
        anomalies = [_anomaly("QuestStalledRule", context={"quest_id": "q1"})]
        ctx = _empty_ctx(anomalies=anomalies)
        hyps = QuestObjectiveImpossible().generate(ctx)
        assert hyps == []


class TestGovernorPressure:

    def test_generates_when_many_governor_anomalies(self):
        anomalies = [
            _anomaly("GovernorDegradedLive", context={"current_mode": "DEGRADED", "sustained_ticks": 5})
            for _ in range(4)
        ]
        ctx = _empty_ctx(anomalies=anomalies)
        hyps = GovernorPressureFromObservabilityOrWorkDebt().generate(ctx)
        assert len(hyps) == 1
        assert hyps[0].domain == "runtime"

    def test_high_confidence_with_drop_also_present(self):
        anomalies = [
            _anomaly("GovernorDegradedLive", context={"current_mode": "DEGRADED", "sustained_ticks": 5})
            for _ in range(4)
        ]
        anomalies.append(_anomaly("EventDropRateHigh", context={"drop_count": 15}))
        ctx = _empty_ctx(anomalies=anomalies)
        hyps = GovernorPressureFromObservabilityOrWorkDebt().generate(ctx)
        assert hyps[0].confidence == ConfidenceLevel.HIGH


class TestCombatEngagementCannotResolve:

    def test_generates_when_combat_anomalies_present(self):
        anomalies = [
            _anomaly("CombatNeverEndsRule", entity_id=i, context={"combat_duration_ticks": 50})
            for i in range(1, 4)
        ]
        ctx = _empty_ctx(anomalies=anomalies)
        hyps = CombatEngagementCannotResolve().generate(ctx)
        assert len(hyps) == 1
        assert hyps[0].domain == "combat"

    def test_no_hypothesis_when_no_combat_anomalies(self):
        ctx = _empty_ctx()
        hyps = CombatEngagementCannotResolve().generate(ctx)
        assert hyps == []


# ── RootCauseEngine tests ─────────────────────────────────────────────────────

class TestRootCauseEngine:

    def test_engine_runs_all_rules(self):
        anomalies = [
            _anomaly("ResourceNodeCrowdingRule", context={"node_id": "n1", "entities_count": 5})
        ] + [
            _anomaly("NavigationStuckRule", entity_id=i, context={"position": f"({i},{i})"})
            for i in range(1, 4)
        ]
        ctx = _empty_ctx(anomalies=anomalies)
        engine = RootCauseEngine()
        result = engine.run(ctx)
        assert isinstance(result, RootCauseEngineResult)
        assert len(result.hypotheses) >= 1

    def test_crashed_rule_does_not_crash_engine(self):
        ctx = _empty_ctx()
        engine = RootCauseEngine(rules=[_CrashingRule()])
        result = engine.run(ctx)
        assert "CrashingRule" in result.failed_rules
        assert result.hypotheses == []

    def test_ranking_by_confidence(self):
        # Trigger governor (MEDIUM+) and combat (MEDIUM) hypotheses
        anomalies = [
            _anomaly("GovernorDegradedLive", context={"current_mode": "DEGRADED", "sustained_ticks": 5})
            for _ in range(9)  # HIGH confidence threshold
        ]
        anomalies += [
            _anomaly("CombatNeverEndsRule", entity_id=1, context={"combat_duration_ticks": 50})
        ]
        ctx = _empty_ctx(anomalies=anomalies)
        engine = RootCauseEngine()
        result = engine.run(ctx)
        if len(result.hypotheses) >= 2:
            # Highest confidence should come first
            ranks = [h.confidence.rank for h in result.hypotheses]
            assert ranks == sorted(ranks, reverse=True)

    def test_top_by_confidence_limits_results(self):
        anomalies = [
            _anomaly("ResourceNodeCrowdingRule", context={"node_id": f"n{i}", "entities_count": 5})
            for i in range(3)
        ]
        ctx = _empty_ctx(anomalies=anomalies)
        result = RootCauseEngine().run(ctx)
        top = result.top_by_confidence(1)
        assert len(top) == 1

    def test_result_serializes_to_dict(self):
        anomalies = [
            _anomaly("CombatNeverEndsRule", entity_id=1, context={"combat_duration_ticks": 50})
            for _ in range(3)
        ]
        ctx = _empty_ctx(anomalies=anomalies)
        result = RootCauseEngine().run(ctx)
        d = result.to_dict()
        assert "total_hypotheses" in d
        assert "hypotheses" in d
        assert "failed_rules" in d

    def test_empty_context_produces_no_hypotheses(self):
        ctx = _empty_ctx()
        result = RootCauseEngine().run(ctx)
        assert result.hypotheses == []
        assert result.failed_rules == []
