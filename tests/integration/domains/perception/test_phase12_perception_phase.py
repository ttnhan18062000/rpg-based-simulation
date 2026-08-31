import dataclasses

import pytest
from src.core.state import EntityState
from src.cognition.self_model_phase import SelfModelUpdatePhase
from src.domains.perception.salience import WorldSignal
from src.domains.perception.phase import PerceptionUpdatePhase
from src.domains.perception.service import AttentionFocusService

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


def test_attention_focus_reads_real_self_model_dominant_need():
    # Force low health so SelfAssessmentService/NeedInterpretationService
    # produce a genuine dominant_need == "healing" via the real writer path.
    entity = EntityState(id=1, kind="HERO")
    entity = dataclasses.replace(
        entity, combat=dataclasses.replace(entity.combat, hp=15, max_hp=100)
    )

    new_bundle = SelfModelUpdatePhase.run(entity=entity, tick=1)
    entity = dataclasses.replace(entity, self_model=new_bundle)

    assert entity.self_model.needs.dominant_need == "healing"

    focus = AttentionFocusService.get_attention_focus(entity)
    assert "healing_resource" in focus
    assert "healer" in focus
    assert "safe_place" in focus
