import pytest
from dataclasses import replace
from src.core.state import EntityState, IdentityComponent, InventoryComponent, StrategicComponent, CombatComponent, AttributeComponent, EquipmentComponent, NavigationComponent, TaskComponent, StaminaComponent, BiologicalComponent, LifecycleComponent, AptitudeComponent, InteractionComponent, ItemStack, EquipSlot
from src.core.updates import IdentityUpdate, RewardUpdate, InventoryUpdate, EquipmentUpdate
from src.progression.leveling import LevelingService
from src.engine.evolution import EvolutionSystem
from src.systems.crafting import CraftingSystem
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate

@pytest.fixture
def base_hero():
    return EntityState(
        id=1,
        kind="hero",
        position=(0, 0),
        identity=IdentityComponent(role=0), # HERO
        strategic=StrategicComponent(),
        combat=CombatComponent(),
        inventory=InventoryComponent(),
        attributes=AttributeComponent(),
        interaction=InteractionComponent(),
        navigation=NavigationComponent(),
        task=TaskComponent(),
        stamina=StaminaComponent(),
        biological=BiologicalComponent(),
        lifecycle=LifecycleComponent(),
        aptitude=AptitudeComponent()
    )

def test_xp_separation_full_inventory(base_hero):
    # Setup: Hero with full inventory
    inv = InventoryComponent(items=[ItemStack(item_id="iron_ore", quantity=1)] * 16)
    entity = replace(base_hero, inventory=inv)
    
    # Reward update with XP and items
    reward = RewardUpdate(xp_gain=100)
    # Simulated item rejection wouldn't happen in EvolutionSystem, 
    # but we want to prove XP is processed by apply_update.
    
    # We use EvolutionSystem to evaluate the update
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=42)
    upd = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, reward=reward)})
    
    final_upd = EvolutionSystem.evaluate(state, upd)
    
    # Check if level up happened (100 XP is enough for level 2: 100 * (1 ** 1.5) = 100)
    ent_upd = final_upd.entity_updates[1]
    assert ent_upd.identity.evolution_level_set == 2
    assert ent_upd.identity.unspent_ap_delta == 5
    assert "power_strike" in ent_upd.identity.learned_skills

def test_durability_decay_combat(base_hero):
    # Setup: Hero with a sword
    equip = EquipmentComponent(slots={EquipSlot.MAIN_HAND: "iron_sword"}, durability={EquipSlot.MAIN_HAND: 100.0})
    attacker = replace(base_hero, equipment=equip)
    defender = replace(base_hero, id=2)
    
    from src.engine.combat import CombatResolutionSystem
    att_dur, def_dur = CombatResolutionSystem._get_durability_decay(attacker, defender)
    
    assert att_dur.durability_delta[EquipSlot.MAIN_HAND] == -1.0
    assert def_dur is None # Defender has no armor

def test_crafting_gates(base_hero):
    # Setup: Hero knows iron_sword recipe but has no materials
    identity = replace(base_hero.identity, known_recipes={"iron_sword"})
    entity = replace(base_hero, identity=identity)
    
    # Attempt to craft
    inv_upd, reason = CraftingSystem.craft(entity, "iron_sword", 100)
    assert inv_upd is None
    assert "INSUFFICIENT_MATERIAL" in reason

def test_crafting_success(base_hero):
    # Setup: Hero has materials and knows recipe
    identity = replace(base_hero.identity, known_recipes={"iron_sword"})
    inv = InventoryComponent(items=[ItemStack(item_id="iron_ore", quantity=5), ItemStack(item_id="wood", quantity=2)], gold=100)
    entity = replace(base_hero, identity=identity, inventory=inv)
    
    # Attempt to craft
    inv_upd, reason = CraftingSystem.craft(entity, "iron_sword", 100)
    assert reason == "SUCCESS"
    assert inv_upd.gold_delta == -50
    assert any(s.item_id == "iron_sword" for s in inv_upd.items_add)
    assert len(inv_upd.items_remove) == 2

def test_stat_derivation_broken_gear(base_hero):
    # Setup: Hero with broken sword
    # iron_sword usually gives ATK bonus (e.g. 10)
    # We need to check what iron_sword gives in ItemRegistry
    from src.core.items import ItemRegistry
    
    equip = EquipmentComponent(slots={EquipSlot.MAIN_HAND: "iron_sword"}, durability={EquipSlot.MAIN_HAND: 0.0})
    entity = replace(base_hero, equipment=equip)
    
    stats = LevelingService.recalculate_combat_stats(entity.attributes, entity.equipment)
    
    # Base ATK is 10 + (strength * 0.5) = 10 + (5 * 0.5) = 12
    # If sword was NOT broken, it would be 12 + sword_atk
    assert stats["atk"] == 12 
