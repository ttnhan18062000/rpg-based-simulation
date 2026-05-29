import pytest
from src.core.cognition import (
    PerceptionModel,
    PerceivedEntity,
    PerceivedResource,
    PerceivedService,
    PerceivedThreat,
    PerceivedOpportunity,
    IgnoredSignal
)

def test_perception_model_defaults_are_empty():
    m = PerceptionModel()
    assert len(m.attention_focus) == 0
    assert len(m.perceived_entities) == 0
    assert len(m.perceived_resources) == 0
    assert len(m.perceived_services) == 0
    assert len(m.perceived_threats) == 0
    assert len(m.perceived_opportunities) == 0
    assert len(m.ignored_signals) == 0

def test_perceived_entity_has_confidence_and_salience():
    pe = PerceivedEntity(entity_id=42, kind="HERO", position=(1.2, 3.4), salience=0.8)
    assert pe.entity_id == 42
    assert pe.salience == 0.8
    assert pe.confidence == 1.0

def test_ignored_signal_can_be_recorded():
    sig = IgnoredSignal(signal_id="sig_1", reason="capacity_limit", tick=123)
    assert sig.signal_id == "sig_1"
    assert sig.reason == "capacity_limit"
    assert sig.tick == 123
