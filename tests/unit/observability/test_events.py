"""Unit tests for new SimulationEvent subclasses added by
TCK-20260824-GRIEF-NEMESIS-REACHABILITY (AC2).

Follows the LegendaryArrivalEvent/KnownTraitorSpottedEvent/OldDebtCollectedEvent
pattern (src/observability/events.py) — fixed event_type/event_category/source_system,
auto-generated message when not supplied.
"""
from __future__ import annotations

from src.observability.events import (
    SimulationEvent,
    GriefUrgencyTriggeredEvent,
    NemesisRelationFormedEvent,
    GRIEF_URGENCY_TRIGGERED,
    NEMESIS_RELATION_FORMED,
)


class TestGriefUrgencyTriggeredEvent:
    def test_is_simulation_event_subclass(self):
        assert issubclass(GriefUrgencyTriggeredEvent, SimulationEvent)

    def test_fixed_fields(self):
        evt = GriefUrgencyTriggeredEvent(
            tick=5, entity_id=1, dead_ally_id=42, urgency=0.56,
        )
        assert evt.event_type == GRIEF_URGENCY_TRIGGERED == "grief_urgency_triggered"
        assert evt.event_category == "social"
        assert evt.severity == "INFO"
        assert evt.dead_ally_id == 42
        assert evt.urgency == 0.56

    def test_default_source_system_is_event_extractor(self):
        """source_system defaults to 'event_extractor' — matches the mid-tick emission
        point (Step 4). CampaignOrchestrator's episode-boundary emission point (Step 6)
        overrides it to 'campaign_orchestrator'."""
        evt = GriefUrgencyTriggeredEvent(tick=1, entity_id=1, dead_ally_id=2, urgency=0.5)
        assert evt.source_system == "event_extractor"

    def test_source_system_overridable(self):
        evt = GriefUrgencyTriggeredEvent(
            tick=1, entity_id=1, dead_ally_id=2, urgency=0.5,
            source_system="campaign_orchestrator",
        )
        assert evt.source_system == "campaign_orchestrator"

    def test_auto_generated_message(self):
        evt = GriefUrgencyTriggeredEvent(tick=1, entity_id=7, dead_ally_id=9, urgency=0.42)
        assert "7" in evt.message
        assert "9" in evt.message

    def test_explicit_message_not_overwritten(self):
        evt = GriefUrgencyTriggeredEvent(
            tick=1, entity_id=1, dead_ally_id=2, urgency=0.5, message="custom",
        )
        assert evt.message == "custom"


class TestNemesisRelationFormedEvent:
    def test_is_simulation_event_subclass(self):
        assert issubclass(NemesisRelationFormedEvent, SimulationEvent)

    def test_fixed_fields(self):
        evt = NemesisRelationFormedEvent(
            tick=5, entity_id=1, antagonist_id=99, strength=0.8,
        )
        assert evt.event_type == NEMESIS_RELATION_FORMED == "nemesis_relation_formed"
        assert evt.event_category == "social"
        assert evt.severity == "INFO"
        assert evt.source_system == "campaign_orchestrator"
        assert evt.antagonist_id == 99
        assert evt.strength == 0.8

    def test_auto_generated_message(self):
        evt = NemesisRelationFormedEvent(tick=1, entity_id=3, antagonist_id=8, strength=0.4)
        assert "3" in evt.message
        assert "8" in evt.message

    def test_explicit_message_not_overwritten(self):
        evt = NemesisRelationFormedEvent(
            tick=1, entity_id=1, antagonist_id=2, strength=0.5, message="custom",
        )
        assert evt.message == "custom"
