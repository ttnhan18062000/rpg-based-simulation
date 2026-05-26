"""
Integration test — Domain Analysis Flow

Validates the full Phase 8 domain analysis pipeline:
- AnalysisContext creation from synthetic events + anomalies
- DomainAnalyzerRegistry running all four standard analyzers
- Results contain expected findings for synthetic fault conditions
- Missing signals gracefully skipped, not failed
- Result to_dict() serializes all findings
"""
import pytest

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.domain.base import (
    DomainAnalyzerRegistry, DomainAnalysisStatus
)
from src.observability.anomaly.rules import Anomaly
from src.observability.events import SimulationEvent


# ── Helpers ───────────────────────────────────────────────────────────────────

def _movement_event(eid, tick, end_pos):
    return SimulationEvent(
        event_type="movement",
        event_category="movement",
        tick=tick,
        source_system="locomotion_system",
        message=f"Entity {eid} moved",
        entity_id=eid,
        payload={"end_pos": list(end_pos)},
        run_id="int-test"
    )


def _economy_event(eid, tick):
    return SimulationEvent(
        event_type="gold_transaction",
        event_category="economy",
        tick=tick,
        source_system="economy_system",
        message=f"Entity {eid} transacted",
        entity_id=eid,
        payload={"amount": 5.0, "transaction_kind": "harvest"},
        run_id="int-test"
    )


def _quest_event(eid, tick, quest_id, status):
    return SimulationEvent(
        event_type="quest_event",
        event_category="quest",
        tick=tick,
        source_system="quest_system",
        message=f"Entity {eid} quest {quest_id} → {status}",
        entity_id=eid,
        payload={"quest_id": quest_id, "status": status},
        run_id="int-test"
    )


def _stuck_anomaly(eid, pos):
    return Anomaly(
        rule_name="NavigationStuckRule",
        severity="ERROR",
        entity_id=eid,
        tick_detected=100,
        message=f"Entity {eid} stuck",
        context={"position": str(pos), "stuck_duration_ticks": 60}
    )


def _governor_anomaly():
    return Anomaly(
        rule_name="GovernorDegradedLive",
        severity="WARNING",
        tick_detected=50,
        message="Governor degraded",
        context={"current_mode": "DEGRADED", "sustained_ticks": 10}
    )


# ── Integration tests ─────────────────────────────────────────────────────────

class TestDomainAnalysisFlow:

    def test_all_four_analyzers_run(self):
        events = [
            _movement_event(1, 10, (1, 1)),
            _economy_event(1, 20),
            _quest_event(1, 30, "q1", "started"),
        ]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events)
        reg = DomainAnalyzerRegistry.default()
        results = reg.run_all(ctx)

        domain_ids = [r.domain_id for r in results]
        assert "movement" in domain_ids
        assert "economy" in domain_ids
        assert "quest" in domain_ids
        assert "runtime" in domain_ids

    def test_stuck_events_produce_movement_finding(self):
        events = [_movement_event(i, 10, (i, i)) for i in range(1, 6)]
        anomalies = [_stuck_anomaly(i, (i, i)) for i in range(1, 6)]
        ctx = AnalysisContext(run_id="test", scenario_type="resource_economy", events=events, anomalies=anomalies)

        reg = DomainAnalyzerRegistry.default()
        results = reg.run_all(ctx)

        movement_result = next(r for r in results if r.domain_id == "movement")
        assert movement_result.status == DomainAnalysisStatus.FINDINGS_FOUND
        assert any("Stuck" in f.title for f in movement_result.findings)

    def test_economy_freeze_produces_economy_finding(self):
        events = [
            _economy_event(1, 5),
            _economy_event(1, 10),
            # 200-tick gap
            _economy_event(1, 210),
        ]
        ctx = AnalysisContext(run_id="test", scenario_type="resource_economy", events=events)

        reg = DomainAnalyzerRegistry.default()
        results = reg.run_all(ctx)

        economy_result = next(r for r in results if r.domain_id == "economy")
        assert economy_result.status == DomainAnalysisStatus.FINDINGS_FOUND
        assert any("Freeze" in f.title for f in economy_result.findings)

    def test_missing_signals_cause_skipped_not_failed(self):
        # Only movement events — no economy or quest
        events = [_movement_event(1, 10, (0, 0))]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events)

        reg = DomainAnalyzerRegistry.default()
        results = reg.run_all(ctx)

        economy_result = next(r for r in results if r.domain_id == "economy")
        quest_result = next(r for r in results if r.domain_id == "quest")

        assert economy_result.status == DomainAnalysisStatus.SKIPPED_MISSING_SIGNAL
        assert quest_result.status == DomainAnalysisStatus.SKIPPED_MISSING_SIGNAL

        # Movement should still have run
        movement_result = next(r for r in results if r.domain_id == "movement")
        assert movement_result.status in (DomainAnalysisStatus.PASSED, DomainAnalysisStatus.FINDINGS_FOUND)

    def test_governor_pressure_produces_runtime_finding(self):
        anomalies = [_governor_anomaly() for _ in range(5)]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", anomalies=anomalies)

        reg = DomainAnalyzerRegistry.default()
        results = reg.run_all(ctx)

        runtime_result = next(r for r in results if r.domain_id == "runtime")
        assert runtime_result.status == DomainAnalysisStatus.FINDINGS_FOUND
        assert any("Governor" in f.title for f in runtime_result.findings)

    def test_all_results_serialize_to_dict(self):
        events = [_movement_event(1, 10, (0, 0)), _economy_event(1, 20)]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events)

        reg = DomainAnalyzerRegistry.default()
        results = reg.run_all(ctx)

        for result in results:
            d = result.to_dict()
            assert "domain_id" in d
            assert "status" in d
            assert "findings" in d
            assert "analyzer_runtime_ms" in d

    def test_clean_run_all_passed_or_skipped(self):
        events = [
            _movement_event(1, 10, (1, 1)),
            _movement_event(1, 20, (2, 2)),
            _economy_event(1, 10),
            _economy_event(1, 20),
            _quest_event(1, 10, "q1", "started"),
            _quest_event(1, 50, "q1", "completed"),
        ]
        ctx = AnalysisContext(run_id="test", scenario_type="mixed_sandbox", events=events)

        reg = DomainAnalyzerRegistry.default()
        results = reg.run_all(ctx)

        for result in results:
            assert result.status in (
                DomainAnalysisStatus.PASSED,
                DomainAnalysisStatus.SKIPPED_MISSING_SIGNAL,
                DomainAnalysisStatus.FINDINGS_FOUND,
            )
            # No analyzer should fail
            assert result.status != DomainAnalysisStatus.FAILED
