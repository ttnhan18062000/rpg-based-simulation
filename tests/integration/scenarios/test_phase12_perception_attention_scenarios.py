import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, SubjectiveModel, SelfModel
from src.core.self_model import NeedInterpretationComponent
from src.domains.perception.salience import WorldSignal
from src.domains.perception.phase import PerceptionUpdatePhase

def test_injured_entity_notices_healing_first():
    # Setup entity with dominant_need == "healing"
    entity = EntityState(id=1, kind="HERO")
    needs = NeedInterpretationComponent(dominant_need="healing")
    self_model = SelfModel(needs=needs)
    subjective = SubjectiveModel(self=self_model)
    entity = replace(entity, cognition=CognitionModel(subjective=subjective))

    signals = [
        # Clue gets standard salience score
        WorldSignal("clue_1", "clue", (1.0, 1.0), 0.5),
        # Herb gets high salience due to healing need attention focus tag match
        WorldSignal("herb_1", "healing_resource", (1.0, 1.0), 0.5),
    ]

    phase = PerceptionUpdatePhase()
    updated_entities = phase.run([entity], signals, tick=1)
    perception = updated_entities[0].cognition.subjective.perception

    # Healing resource should have higher salience due to AttentionFocus bonus
    herb_salience = perception.perceived_resources["herb_1"].salience
    clue_salience = perception.perceived_opportunities["clue_1"].salience
    assert herb_salience > clue_salience
