import dataclasses

import pytest
from src.core.state import EntityState
from src.core.cognition import PerceivedEntity
from src.domains.perception.salience import WorldSignal
from src.domains.perception.filter import PerceptionFilterService, PerceptionBudget

def test_filter_keeps_high_salience_signals():
    entity = EntityState(id=1, kind="HERO")
    
    signals = [
        WorldSignal("sig_1", "threat", (1.0, 1.0), 0.8),
        WorldSignal("sig_2", "unrelated", (1.0, 1.0), 0.1),
    ]

    budget = PerceptionBudget(max_perceived=5)
    update = PerceptionFilterService.filter(entity, signals, budget)

    assert "sig_1" in update.perceived_threats
    assert "sig_2" in update.perceived_opportunities
    assert len(update.ignored_signals) == 0

def test_filter_drops_low_salience_signals_when_capacity_full():
    entity = EntityState(id=1, kind="HERO")
    
    signals = [
        WorldSignal("sig_1", "unrelated", (1.0, 1.0), 0.9),
        WorldSignal("sig_2", "unrelated", (1.0, 1.0), 0.8),
        WorldSignal("sig_3", "unrelated", (1.0, 1.0), 0.7),
    ]

    # Limit max perceived to 2
    budget = PerceptionBudget(max_perceived=2)
    update = PerceptionFilterService.filter(entity, signals, budget, tick=10)

    assert len(update.perceived_opportunities) == 2
    assert "sig_3" not in update.perceived_opportunities
    assert len(update.ignored_signals) == 1
    assert update.ignored_signals[0].signal_id == "sig_3"
    assert update.ignored_signals[0].reason == "capacity_limit"

def test_perceived_entity_has_no_item_or_event_fields():
    """Architecture guard (TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY, Answer 3):
    PerceivedEntity's field set stays narrow -- entity_id, kind, position, salience, confidence
    only. Even a fully-wired PerceptionUpdatePhase could not carry combat-death, inheritance, or
    any other item/event content today without a schema change. Guards against a future ticket
    silently widening this record to smuggle in that content without a conscious design
    decision -- not building perception capability itself, per this ticket's Out of Scope.
    """
    field_names = {f.name for f in dataclasses.fields(PerceivedEntity)}
    assert field_names == {"entity_id", "kind", "position", "salience", "confidence"}
