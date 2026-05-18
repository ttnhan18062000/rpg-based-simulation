import pytest
from unittest.mock import MagicMock
from src_legacy.core.models.enums import Faction, EntityRole
from src_legacy.ai.beliefs import BeliefService
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.aspects.mind import BeliefRecord, ThreatEstimate

@pytest.fixture
def actor():
    return Entity(id=1, kind="hero", faction=0)

@pytest.fixture
def observed():
    # A monster with a class (e.g. Boss)
    monster = Entity(id=2, kind="monster", faction=Faction.GOBLIN_HORDE)
    monster.identity.role = EntityRole.MOB
    if hasattr(monster.progression, "hero_class"):
        monster.progression.hero_class = "WARRIOR"
    return monster

def test_belief_refresh_captures_apparent_state(actor, observed):
    # 1. Fresh observation
    belief = BeliefService.refresh_belief_from_observation(actor, observed, 100)
    
    assert belief.entity_id == 2
    assert belief.last_seen_tick == 100
    assert belief.confidence == 1.0
    assert belief.apparent_faction == "GOBLIN_HORDE"
    assert belief.apparent_role == "MOB"
    
    # Check apparent_class if supported by the entity
    if hasattr(observed.progression, "hero_class"):
        assert belief.apparent_class == "WARRIOR"

def test_belief_decay_lifecycle(actor, observed):
    belief = BeliefService.refresh_belief_from_observation(actor, observed, 100)
    belief.visible_injury = 0.4
    
    actor.mind.perception.entity_memory[observed.id] = belief
    
    up = BeliefService.decay_stale_beliefs(actor, 105)
    b1 = up.entity_memory[observed.id]
    assert pytest.approx(b1.confidence) == 0.9
    assert b1.stale_ticks == 5
    assert b1.visible_injury == 0.4 # Not blurred yet
    
    actor.mind.perception.entity_memory[observed.id] = b1
    up2 = BeliefService.decay_stale_beliefs(actor, 126)
    b2 = up2.entity_memory[observed.id]
    assert b2.confidence < 0.5
    assert b2.visible_injury == -1.0 # Blurred/Unknown

def test_threat_estimation_logic(actor, observed):
    observed.combat.hp = 100
    observed.combat.max_hp = 100
    observed.progression.level = 10
    actor.progression.level = 5
    
    belief = BeliefService.refresh_belief_from_observation(actor, observed, 100)
    assert belief.threat.overall > 0.0
    assert belief.threat.confidence == 1.0 # Fresh observation
    
    actor.mind.perception.entity_memory[observed.id] = belief
    
    up = BeliefService.decay_stale_beliefs(actor, 150)
    b1 = up.entity_memory[observed.id]
    assert b1.threat.confidence < 1.0

