
import pytest
from src.api.presenters.entity_presenter import EntityPresenter
from src.api.presenters.ai_presenter import AIPresenter
from src.core.entities.entity_builder import EntityBuilder
from src.platform.rng import DeterministicRNG
from src.core.models.enums import AIState, Archetype
from src.core.models.vectors import Vector2
from src.core.models.world_state import WorldState
from src.platform.spatial_hash import SpatialHash
from src.core.world.grid import Grid
from src.core.aspects.mind import BeliefRecord

def test_inspection_serialization():
    rng = DeterministicRNG(123)
    world = WorldState(seed=123, grid=Grid(10, 10), spatial_index=SpatialHash(2))
    
    eid = world.allocate_entity_id()
    entity = (EntityBuilder(rng, eid)
              .kind("hero")
              .at(Vector2(5, 5))
              .with_archetype(Archetype.BALANCED)
              .build())
    
    # Add a belief to memory
    belief = BeliefRecord(
        entity_id=999,
        pos=Vector2(10, 10),
        apparent_kind="enemy",
        last_seen_tick=1
    )
    entity.mind.perception.entity_memory[999] = belief
    
    # 1. Test EntityPresenter serialization
    schema = EntityPresenter.to_full_schema(entity, world=world)
    assert schema.entity_memory is not None
    assert len(schema.entity_memory) == 1
    # Verify it's a list of schemas, not just an ID
    mem_entry = schema.entity_memory[0]
    assert mem_entry.entity_id == 999
    assert mem_entry.pos == (10, 10)
    assert mem_entry.last_seen_tick == 1
    # 2. Test AIPresenter explanation distance calculation
    # This checks the fix: distance = self.entity.spatial.pos.manhattan(belief.pos)
    explanation = AIPresenter.get_explanation(entity)
    assert explanation is not None
    # Belief is at (10, 10), entity is at (5, 5). Manhattan distance is 10.
    assert explanation.nearest_enemy_dist == 10.0
    assert explanation.nearest_target_id == 999
    # Note: get_explanation might return "Nothing of note" if distance is > 5 or something, 
    # but the point is it shouldn't CRASH.
    
    # Check distance calculation specifically if we can trigger it
    entity.mind.decision.ai_state = AIState.COMBAT
    explanation = AIPresenter.get_explanation(entity)
    assert explanation.current_state == "combat"
    assert explanation.nearest_target_id == 999
