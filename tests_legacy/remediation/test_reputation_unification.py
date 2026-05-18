
import pytest
from src_legacy.core.entities.entity_builder import EntityBuilder
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.core.models.enums import Archetype, Faction
from src_legacy.core.logic.reputation_service import ReputationService
from src_legacy.core.models.world_state import WorldState
from src_legacy.platform.spatial_hash import SpatialHash
from src_legacy.core.world.grid import Grid

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
    
    # 1. Verify entity.reputation shim exists and delegates to identity.reputation
    assert entity.reputation is entity.identity.reputation
    
    # 2. Verify IdentityAspect.reputation is present
    assert entity.identity.reputation is not None
    assert entity.identity.reputation.trustworthiness == 0.0
    
    # 3. Verify ReputationService uses IdentityAspect
    from src_legacy.actions.base import ReputationUpdate
    ReputationService.apply_update(entity, ReputationUpdate(trustworthiness_delta=0.5))
    assert entity.identity.reputation.trustworthiness == 0.5
