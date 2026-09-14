"""
tests/unit/domains/combat_engagement/test_memory_store.py

TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

Unit tests for the sanctioned OpponentModel storage write path
(src/domains/combat_engagement/memory_store.py).
"""

from src.core.cognition import CombatMemory
from src.domains.combat_engagement.schema import OpponentModel
from src.domains.combat_engagement.memory_store import (
    MAX_OPPONENT_MODELS_PER_ENTITY,
    compute_salience,
    store_opponent_model,
)


def _model(key, power=20.0, salience=0.0, tick=0):
    return OpponentModel(
        subject_key=key, estimated_power=power, uncertainty=0.4, confidence=0.5,
        last_updated_tick=tick, salience=salience,
    )


def test_upsert_by_key_never_grows_collection():
    memory = CombatMemory()
    memory = store_opponent_model(memory, _model("entity.1", power=20.0))
    memory = store_opponent_model(memory, _model("entity.1", power=25.0))

    assert len(memory.opponent_stats) == 1
    assert memory.opponent_stats["entity.1"].estimated_power == 25.0


def test_bound_enforced_on_new_key_insert():
    memory = CombatMemory()
    for i in range(MAX_OPPONENT_MODELS_PER_ENTITY):
        memory = store_opponent_model(memory, _model(f"entity.{i}", salience=0.5))

    assert len(memory.opponent_stats) == MAX_OPPONENT_MODELS_PER_ENTITY

    memory = store_opponent_model(memory, _model("entity.new", salience=0.5))

    assert len(memory.opponent_stats) == MAX_OPPONENT_MODELS_PER_ENTITY


def test_eviction_is_by_lowest_salience_not_oldest():
    """
    A deliberately-aged, high-salience entry (the frightening early encounter) must survive a
    newer, low-salience insert -- the whole point of not copying causal memory's own oldest-first
    policy (Sec 13.6).
    """
    memory = CombatMemory()
    # Fill to the bound: entry 0 is old but highly salient (the frightening encounter).
    memory = store_opponent_model(memory, _model("entity.scary", salience=0.9, tick=1))
    for i in range(1, MAX_OPPONENT_MODELS_PER_ENTITY):
        memory = store_opponent_model(memory, _model(f"entity.{i}", salience=0.2, tick=100 + i))

    assert len(memory.opponent_stats) == MAX_OPPONENT_MODELS_PER_ENTITY

    # A new, low-salience encounter arrives -- it should evict one of the low-salience entries,
    # never the high-salience "entity.scary".
    memory = store_opponent_model(memory, _model("entity.new_low_salience", salience=0.1, tick=200))

    assert "entity.scary" in memory.opponent_stats
    assert "entity.new_low_salience" in memory.opponent_stats
    assert len(memory.opponent_stats) == MAX_OPPONENT_MODELS_PER_ENTITY


def test_compute_salience_rises_with_surprise_magnitude():
    prior = _model("entity.1", power=20.0)
    small_surprise = compute_salience(prior, updated_estimated_power=22.0)
    large_surprise = compute_salience(prior, updated_estimated_power=80.0)

    assert large_surprise > small_surprise


def test_compute_salience_rises_with_outcome_severity():
    prior = _model("entity.1", power=20.0)
    low_severity = compute_salience(prior, updated_estimated_power=20.0, outcome_severity=0.0)
    high_severity = compute_salience(prior, updated_estimated_power=20.0, outcome_severity=1.0)

    assert high_severity > low_severity


def test_compute_salience_with_no_prior_uses_updated_as_baseline():
    # No prior (first-ever observation) -- surprise is zero by definition, salience comes purely
    # from outcome_severity.
    salience = compute_salience(None, updated_estimated_power=50.0, outcome_severity=0.5)
    assert 0.0 < salience <= 1.0
