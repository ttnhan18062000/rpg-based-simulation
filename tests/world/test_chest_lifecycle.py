import pytest
from src.core.state import AuthoritativeState, EntityState, ChestState, InteractionComponent, ItemStack, CombatComponent
from src.systems.chest_system import ChestSystem
from src.engine.pipeline import AuthoritativeApplyPipeline

from src.core.builder import V2EntityBuilder

def test_chest_looting():
    # Setup entity looting
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .location(5, 5)
        .interaction(target_node_id=1, progress=9.0)
        .identity(properties={"interaction_kind": "chest"})
        .build())
    
    # Setup chest
    chest = ChestState(
        id=1, position=(5, 5),
        items=[ItemStack("gold_coin", 100)],
        respawn_tick=1000
    )
    
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        chests={1: chest}
    )
    
    update = ChestSystem.update(state)
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Verify inventory gain
    ent_upd = refined.entity_updates[1]
    assert ent_upd.inventory.items_add[0].item_id == "gold_coin"
    assert ent_upd.interaction.reset == True
    
    # Verify chest cooldown
    chest_upd = update.chest_updates[1]
    assert chest_upd.items_set == []
    assert chest_upd.cooldown_set == 1000

def test_chest_respawn():
    # Setup chest in cooldown
    chest = ChestState(
        id=2, position=(10, 10),
        items=[],
        cooldown_remaining=1
    )
    
    state = AuthoritativeState(
        tick=100, seed=42,
        chests={2: chest}
    )
    
    update = ChestSystem.update(state)
    
    # Verify cooldown decrement
    chest_upd = update.chest_updates[2]
    assert chest_upd.cooldown_set == 0 # 1 - 1
