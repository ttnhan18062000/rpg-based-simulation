# Compliance IDs: PROG-107
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, ItemStack, EquipSlot, EquipmentComponent
from src.core.updates import IdentityUpdate, RewardUpdate, InventoryUpdate, EquipmentUpdate, StateUpdate, EntityUpdate
from src.progression.leveling import LevelingService
from src.engine.evolution import EvolutionSystem
from src.systems.crafting import CraftingSystem
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole

@pytest.fixture
def base_hero():
    return (V2EntityBuilder(1)
            .location(0, 0)
            .identity(role=EntityRole.HERO)
            .build())

def test_xp_separation_full_inventory(base_hero):
    # Setup: Hero with full inventory
    # V2 builder default max_slots is 16
    builder = (V2EntityBuilder(1)
               .location(0, 0)
               .identity(role=EntityRole.HERO)
               .inventory(items=[ItemStack(item_id="iron_ore", quantity=1)] * 16))
    entity = builder.build()
    
    # Reward update with XP
    reward = RewardUpdate(xp_gain=100)
    
    # We use EvolutionSystem to evaluate the update
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=42)
    upd = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, reward=reward)})
    
    final_upd = EvolutionSystem.evaluate(state, upd)
    
    # Check if level up happened (100 XP is enough for level 2)
    ent_upd = final_upd.entity_updates[1]
    assert ent_upd.identity.evolution_level_set == 2
    assert ent_upd.identity.unspent_ap_delta == 5
    assert "power_strike" in ent_upd.identity.learned_skills

def test_durability_decay_combat(base_hero):
    # Setup: Hero with a sword
    builder = (V2EntityBuilder(1)
               .location(0, 0)
               .identity(role=EntityRole.HERO))
    attacker = builder.build()
    # Patch equipment directly as builder doesn't have a specific method for durability yet
    attacker = replace(attacker, 
        equipment=replace(attacker.equipment, 
            slots={EquipSlot.MAIN_HAND: "iron_sword"}, 
            durability={EquipSlot.MAIN_HAND: 100.0}
        )
    )
    
    defender = V2EntityBuilder(2).location(1, 1).build()
    
    from src.engine.combat import CombatResolutionSystem
    att_dur, def_dur = CombatResolutionSystem._get_durability_decay(attacker, defender)
    
    assert att_dur.durability_delta[EquipSlot.MAIN_HAND] == -1.0
    assert def_dur is None # Defender has no armor

def test_crafting_gates(base_hero):
    # Setup: Hero knows iron_sword recipe but has no materials
    entity = (V2EntityBuilder(1)
              .location(0, 0)
              .identity(role=EntityRole.HERO)
              .build())
    # Patch recipe knowledge
    entity = replace(entity, identity=replace(entity.identity, known_recipes={"iron_sword"}))
    
    # Attempt to craft
    inv_upd, reason = CraftingSystem.craft(entity, "iron_sword", 100)
    assert inv_upd is None
    assert "INSUFFICIENT_MATERIAL" in reason

def test_crafting_success(base_hero):
    # Setup: Hero has materials and knows recipe
    entity = (V2EntityBuilder(1)
              .location(0, 0)
              .identity(role=EntityRole.HERO)
              .inventory(gold=100, items=[ItemStack(item_id="iron_ore", quantity=5), ItemStack(item_id="wood", quantity=2)])
              .build())
    # Patch recipe knowledge
    entity = replace(entity, identity=replace(entity.identity, known_recipes={"iron_sword"}))
    
    # Attempt to craft
    inv_upd, reason = CraftingSystem.craft(entity, "iron_sword", 100)
    assert reason == "SUCCESS"
    assert inv_upd.gold_delta == -50
    assert any(s.item_id == "iron_sword" for s in inv_upd.items_add)
    assert len(inv_upd.items_remove) == 2

def test_stat_derivation_broken_gear(base_hero):
    # Setup: Hero with broken sword
    # iron_sword usually gives ATK bonus (e.g. 10)
    # Base hero attributes (STR=5) -> ATK=10 + 2.5 = 12
    entity = (V2EntityBuilder(1)
              .location(0, 0)
              .identity(role=EntityRole.HERO)
              .build())
    entity = replace(entity, 
        equipment=replace(entity.equipment, 
            slots={EquipSlot.MAIN_HAND: "iron_sword"}, 
            durability={EquipSlot.MAIN_HAND: 0.0}
        )
    )
    
    stats = LevelingService.recalculate_combat_stats(entity.attributes, entity.equipment)
    
    # Base ATK is 10 + (strength * 0.5) = 10 + (5 * 0.5) = 12
    # If sword was broken, it should not contribute.
    assert stats["atk"] == 12 
