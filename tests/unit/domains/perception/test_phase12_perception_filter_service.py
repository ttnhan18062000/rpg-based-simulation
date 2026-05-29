import pytest
from src.core.state import EntityState
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
