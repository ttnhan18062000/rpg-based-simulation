
import pytest
from src.core.entities.entity_builder import EntityBuilder
from src.platform.rng import DeterministicRNG
from src.core.models.enums import Archetype, Faction
from src.core.logic.reputation_service import ReputationService
from src.core.models.world_state import WorldState
from src.platform.spatial_hash import SpatialHash
from src.core.world.grid import Grid

def test_reputation_unification():
    rng = DeterministicRNG(123)
    world = WorldState(seed=123, grid=Grid(10, 10), spatial_index=SpatialHash(2))
    
    eid = world.allocate_entity_id()
    entity = (EntityBuilder(rng, eid)
              .kind("hero")
              .at((5, 5))
              .faction(Faction.HERO_GUILD)
              .with_archetype(Archetype.BALANCED)
              .build())
    
    # 1. Verify entity.reputation NO LONGER EXISTS or is removed
    with pytest.raises(AttributeError):
        _ = entity.reputation
    
    # 2. Verify IdentityAspect.reputation is present
    assert entity.identity.reputation is not None
    assert entity.identity.reputation.trustworthiness == 0.0
    
    # 3. Verify ReputationService uses IdentityAspect
    from src.actions.base import ReputationUpdate
    ReputationService.apply_update(entity, ReputationUpdate(trustworthiness_delta=0.5))
    assert entity.identity.reputation.trustworthiness == 0.5
