import pytest
from unittest.mock import MagicMock
from src.ai.beliefs import BeliefService
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.aspects.mind import BeliefRecord, ThreatEstimate

@pytest.fixture
def actor():
    return Entity(id=1, kind="hero", faction="player")

@pytest.fixture
def observed():
    # A monster with a class (e.g. Boss)
    monster = Entity(id=2, kind="monster", faction="mob")
    monster.identity.role = "BOSS"
    if hasattr(monster.progression, "hero_class"):
        monster.progression.hero_class = "WARRIOR"
    return monster

def test_belief_refresh_captures_apparent_state(actor, observed):
    # 1. Fresh observation
    belief = BeliefService.refresh_belief_from_observation(actor, observed, 100)
    
    assert belief.entity_id == 2
    assert belief.last_seen_tick == 100
    assert belief.confidence == 1.0
    assert belief.apparent_faction == "mob"
    assert belief.apparent_role == "BOSS"
    
    # Check apparent_class if supported by the entity
    if hasattr(observed.progression, "hero_class"):
        assert belief.apparent_class == "WARRIOR"

def test_belief_decay_lifecycle(actor, observed):
    belief = BeliefService.refresh_belief_from_observation(actor, observed, 100)
    belief.visible_injury = 0.4
    
    # AOA FIX: refresh_belief_from_observation returns a NEW record.
    # We must store it in the actor's entity_memory for decay to work.
    actor.mind.perception.entity_memory[observed.id] = belief
    
    # 1. Half decay (5 ticks @ 0.02 = 0.1)
    BeliefService.decay_stale_beliefs(actor, 105)
    assert pytest.approx(belief.confidence) == 0.9
    assert belief.stale_ticks == 5
    assert belief.visible_injury == 0.4 # Not blurred yet
    
    # 2. Blur injury (26 ticks @ 0.02 = 0.52 decay -> 0.48 confidence)
    BeliefService.decay_stale_beliefs(actor, 126)
    assert belief.confidence < 0.5
    assert belief.visible_injury == -1.0 # Blurred/Unknown

def test_threat_estimation_logic(actor, observed):
    # Set up some visible stats for threat estimation
    observed.combat.hp = 100
    observed.combat.max_hp = 100
    observed.progression.level = 10
    actor.progression.level = 5
    
    belief = BeliefService.refresh_belief_from_observation(actor, observed, 100)
    
    # Threat estimation usually runs during memory appraisal
    # But we can call the service directly or via brain
    # For now, let's verify that threat exists
    assert belief.threat.overall > 0.0
    assert belief.threat.confidence == 1.0 # Fresh observation
    
    # AOA FIX: Store belief in entity_memory for decay testing
    actor.mind.perception.entity_memory[observed.id] = belief
    
    # Check that threat confidence decays with belief confidence
    BeliefService.decay_stale_beliefs(actor, 150)
    assert belief.threat.confidence < 1.0

