import pytest
from src.core.state import EntityState
from src.domains.perception.salience import WorldSignal
from src.domains.perception.phase import PerceptionUpdatePhase

def test_phase_updates_perception_model():
    entity = EntityState(id=1, kind="HERO")
    signals = [
        WorldSignal("node_1", "healing_resource", (1.0, 1.0), 0.9),
    ]

    phase = PerceptionUpdatePhase()
    updated = phase.run([entity], signals, tick=5)

    assert len(updated) == 1
    new_entity = updated[0]
    perception = new_entity.cognition.subjective.perception
    assert perception.last_updated_tick == 5
    assert "node_1" in perception.perceived_resources
