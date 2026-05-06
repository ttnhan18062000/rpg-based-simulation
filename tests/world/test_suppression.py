import pytest
from src.core.state import AuthoritativeState, RegionState
from src.engine.legality import LegalityServiceV2
from src.core.builder import V2EntityBuilder

def test_action_suppression():
    # Region with suppression active
    region = RegionState(
        id="reg_1", name="R1", bounds=(0,0,10,10),
        suppression_active=True
    )
    # Actor inside the region
    actor = V2EntityBuilder(entity_id=1).identity(role=0).location(5.0, 5.0).build()
    
    state = AuthoritativeState(tick=0, seed=1, entities={1: actor}, regions={"reg_1": region})
    
    # Try to RECRUIT (should be suppressed)
    legal, reason = LegalityServiceV2.verify_action_legality(actor, "RECRUIT", state)
    assert not legal
    assert reason == "REGIONAL_SUPPRESSION"
    
    # Try to MOVE (should be legal)
    legal, reason = LegalityServiceV2.verify_action_legality(actor, "MOVE", state)
    assert legal

def test_action_legality_outside_suppressed_region():
    # Region with suppression active
    region = RegionState(
        id="reg_1", name="R1", bounds=(0,0,10,10),
        suppression_active=True
    )
    # Actor OUTSIDE the region
    actor = V2EntityBuilder(entity_id=1).identity(role=0).location(50.0, 50.0).build()
    
    state = AuthoritativeState(tick=0, seed=1, entities={1: actor}, regions={"reg_1": region})
    
    # Try to RECRUIT (should be legal outside)
    legal, reason = LegalityServiceV2.verify_action_legality(actor, "RECRUIT", state)
    assert legal
