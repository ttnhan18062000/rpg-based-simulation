import pytest
from dataclasses import replace
from src.core.enums import ReasonCode
from src.core.state import (
    AuthoritativeState, EntityState, InteractionComponent, InventoryComponent, 
    GroundItemState, CorpseState, ItemStack, IdentityComponent, EntityRole,
    NavigationComponent, CombatComponent
)
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, InventoryUpdate
from src.engine.interaction import InteractionSystem
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.movement_modes import MovementMode
from src.core.items import ItemRegistry
from src.core.builder import V2EntityBuilder

def test_ground_item_pickup_parity():
    """Verify that InteractionSystem can pick up ground items."""
    state = AuthoritativeState(tick=1, seed=42)
    # Target must be set for _route_interaction_intent to trigger
    entity = (V2EntityBuilder(1)
              .location(0.0, 0.0)
              .navigation(target=(0.0, 0.0))
              .combat(readiness=100.0)
              .build())
    state = replace(state, entities={1: entity})
    
    ground_item = GroundItemState(id=100, item_id="iron_ore", quantity=1, position=(0.0, 0.0))
    state = replace(state, ground_items={100: ground_item})
    
    # 1. Propose interaction
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=10.0))
    })
    
    # 2. Route intent
    update = AuthoritativeApplyPipeline._route_interaction_intent(state, update)
    ent_upd = update.entity_updates[1]
    assert ent_upd.interaction is not None
    assert ent_upd.interaction.target_node_id == 100
    
    # 3. Refine via Pipeline
    refined_update = AuthoritativeApplyPipeline.refine(state, update)
    
    # 4. Verify results
    ent_upd = refined_update.entity_updates[1]
    assert ent_upd.inventory is not None
    assert len(ent_upd.inventory.items_add) == 1
    assert ent_upd.inventory.items_add[0].item_id == "iron_ore"
    assert 100 in refined_update.ground_items_remove

def test_corpse_looting_parity():
    """Verify that InteractionSystem can loot corpses."""
    state = AuthoritativeState(tick=1, seed=42)
    entity = (V2EntityBuilder(1)
              .location(1.0, 1.0)
              .navigation(target=(1.0, 1.0))
              .combat(readiness=100.0)
              .build())
    state = replace(state, entities={1: entity})
    
    corpse = CorpseState(
        id=200, items=[ItemStack("gold_coin", 50)], position=(1.0, 1.0),
        original_entity_id=999, decay_tick=100
    )
    state = replace(state, corpses={200: corpse})
    
    # 1. Propose interaction
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=10.0))
    })
    
    # 2. Route intent
    update = AuthoritativeApplyPipeline._route_interaction_intent(state, update)
    assert update.entity_updates[1].interaction.target_node_id == 200
    
    # 3. Refine via Pipeline
    refined_update = AuthoritativeApplyPipeline.refine(state, update)
    
    # 4. Verify results
    ent_upd = refined_update.entity_updates[1]
    assert ent_upd.inventory is not None
    assert len(ent_upd.inventory.items_add) == 1
    assert ent_upd.inventory.items_add[0].item_id == "gold_coin"
    assert 200 in refined_update.corpses_remove

def test_movement_sidestepping_parity():
    """Verify that MovementSystem can sidestep blocked tiles."""
    from src.engine.movement import MovementSystem
    state = AuthoritativeState(tick=1, seed=42)
    
    # Mover at (0,0), Target at (1,0)
    mover = V2EntityBuilder(1).location(0.0, 0.0).combat(readiness=100.0).build()
    state = replace(state, entities={**state.entities, 1: mover})
    
    # Blocker at (1,0)
    blocker = V2EntityBuilder(2).location(1.0, 0.0).combat(readiness=100.0).build()
    state = replace(state, entities={**state.entities, 2: blocker})
    
    # Call resolve_move
    updates = MovementSystem.resolve_move(state, mover, (1.0, 0.0))
    
    # Should sidestep to (0,1) or (0,-1)
    new_pos = updates[1].new_position
    assert new_pos in [(0.0, 1.0), (0.0, -1.0)]

def test_movement_yielding_parity():
    """Verify that MovementSystem can force lower priority entities to yield."""
    from src.engine.movement import MovementSystem
    state = AuthoritativeState(tick=1, seed=42)
    
    # Hero (High Priority) at (0,0), Target at (1,0)
    hero = (V2EntityBuilder(1)
            .location(0.0, 0.0)
            .identity(role=EntityRole.HERO)
            .combat(readiness=100.0)
            .build())
    state = replace(state, entities={**state.entities, 1: hero})
    
    # Monster (Lower Priority) at (1,0)
    monster = (V2EntityBuilder(2)
               .location(1.0, 0.0)
               .identity(role=EntityRole.MONSTER)
               .combat(readiness=100.0)
               .build())
    state = replace(state, entities={**state.entities, 2: monster})
    
    # BLOCK sidestepping tiles to force yielding
    state.terrain[(0, 1)] = "WALL"
    state.terrain[(0, -1)] = "WALL"
    
    # Call resolve_move
    updates = MovementSystem.resolve_move(state, hero, (1.0, 0.0))
    
    # Hero should take (1,0)
    assert updates[1].new_position == (1.0, 0.0)
    # Monster should have a new position (yielded)
    assert 2 in updates
    assert updates[2].new_position != (1.0, 0.0)
    assert updates[2].navigation.failure_reason == ReasonCode.YIELDING
