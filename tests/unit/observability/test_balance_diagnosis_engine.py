"""
Unit tests — BalanceDiagnosisEngine (M45)

Validates all four balance dimensions:
- ACTIVITY: absent required signals
- LIVENESS: quests that never resolve
- DOMINANCE: faction kill-share skew
- RUNTIME_STABILITY: governor + drop incidents
"""
import pytest

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.balance.engine import BalanceDiagnosisEngine
from src.observability.understanding.balance.models import BalanceDimension
from src.observability.understanding.expectations.models import ScenarioExpectationPack
from src.observability.anomaly.rules import Anomaly
from src.observability.events import SimulationEvent


def _make_event(category, event_type, tick=10, entity_id=None, payload=None):
    return SimulationEvent(
        event_type=event_type,
        event_category=category,
        tick=tick,
        source_system="test_system",
        message="test event",
        entity_id=entity_id,
        payload=payload or {},
        run_id="test"
    )


def _anomaly(rule_name, context=None):
    return Anomaly(
        rule_name=rule_name,
        severity="WARNING",
        tick_detected=10,
        message="test",
        context=context or {}
    )


class TestBalanceDiagnosisEngine:

    def test_activity_missing_signal_produces_finding(self):
        pack = ScenarioExpectationPack(
            scenario_type="combat_heavy",
            version="1.0",
            required_signals=["combat"]
        )
        ctx = AnalysisContext(
            run_id="test", scenario_type="combat_heavy",
            events=[], expectation_pack=pack
        )
        engine = BalanceDiagnosisEngine()
        summary = engine.diagnose(ctx)

        activity_findings = summary.findings_by_dimension(BalanceDimension.ACTIVITY)
        assert len(activity_findings) >= 1
        assert "combat" in activity_findings[0].summary.lower()

    def test_activity_no_finding_when_no_pack(self):
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox")
        summary = BalanceDiagnosisEngine().diagnose(ctx)
        assert summary.findings_by_dimension(BalanceDimension.ACTIVITY) == []

    def test_liveness_finding_on_unresolved_quests(self):
        events = [
            _make_event("quest", "quest_event", tick=10, entity_id=1, payload={"quest_id": f"q{i}", "status": "started"})
            for i in range(1, 6)
        ] + [
            _make_event("quest", "quest_event", tick=50, entity_id=1, payload={"quest_id": "q1", "status": "completed"})
        ]
        # Only 1 of 5 resolved → 80% non-resolution
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events)
        summary = BalanceDiagnosisEngine().diagnose(ctx)
        liveness = summary.findings_by_dimension(BalanceDimension.LIVENESS)
        assert len(liveness) >= 1
        assert "never resolved" in liveness[0].summary.lower()

    def test_liveness_no_finding_when_all_quests_complete(self):
        events = []
        for i in range(1, 4):
            events.append(_make_event("quest", "quest_event", tick=10, entity_id=1,
                                      payload={"quest_id": f"q{i}", "status": "started"}))
            events.append(_make_event("quest", "quest_event", tick=50, entity_id=1,
                                      payload={"quest_id": f"q{i}", "status": "completed"}))
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events)
        summary = BalanceDiagnosisEngine().diagnose(ctx)
        assert summary.findings_by_dimension(BalanceDimension.LIVENESS) == []

    def test_dominance_finding_on_faction_skew(self):
        events = [
            _make_event("combat", "combat_kill", tick=i, payload={"killer_faction": "faction_A"})
            for i in range(1, 20)
        ] + [
            _make_event("combat", "combat_kill", tick=20 + i, payload={"killer_faction": "faction_B"})
            for i in range(1, 3)  # tiny minority
        ]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events)
        summary = BalanceDiagnosisEngine().diagnose(ctx)
        dominance = summary.findings_by_dimension(BalanceDimension.DOMINANCE)
        assert len(dominance) >= 1
        assert "faction_A" in dominance[0].summary

    def test_dominance_skipped_when_no_kill_events(self):
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=[])
        summary = BalanceDiagnosisEngine().diagnose(ctx)
        assert summary.findings_by_dimension(BalanceDimension.DOMINANCE) == []

    def test_runtime_finding_on_sustained_governor_pressure(self):
        anomalies = [
            _anomaly("GovernorDegradedLive", {"current_mode": "DEGRADED", "sustained_ticks": 10})
            for _ in range(6)
        ]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", anomalies=anomalies)
        summary = BalanceDiagnosisEngine().diagnose(ctx)
        rt = summary.findings_by_dimension(BalanceDimension.RUNTIME_STABILITY)
        assert len(rt) >= 1

    def test_is_balanced_when_no_findings(self):
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox")
        summary = BalanceDiagnosisEngine().diagnose(ctx)
        assert summary.is_balanced() is True

    def test_to_dict_serializes(self):
        anomalies = [
            _anomaly("GovernorDegradedLive", {"current_mode": "DEGRADED"})
            for _ in range(6)
        ]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", anomalies=anomalies)
        summary = BalanceDiagnosisEngine().diagnose(ctx)
        d = summary.to_dict()
        assert "run_id" in d
        assert "findings" in d
        assert "is_balanced" in d
