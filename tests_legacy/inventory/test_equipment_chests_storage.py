import pytest
from src_legacy.core.state import (
    EntityState, AuthoritativeState, InventoryComponent, ItemStack, ChestState, EquipSlot
)
from src_legacy.core.updates import StateUpdate
from src_legacy.core.equipment import EquipmentService
from src_legacy.town.home_storage import HomeStorageAction
from src_legacy.engine.apply import ApplyPath

@pytest.mark.v2_contract
def test_auto_equip_ranking():
    # 1. Setup: Entity with Wood Sword equipped, Iron Sword in inventory
    # wood_sword is not in registry, but iron_sword is. 
    # Let's check ItemRegistry again to be sure.
    # Registry has iron_sword (atk 10).
    # Bread has no atk_bonus.
    
    inventory = InventoryComponent(items=[ItemStack("iron_sword", 1)])
    entity = EntityState(id=1, kind="hero", position=(0,0), inventory=inventory)
    
    # 2. Test Ranking
    iron_power = EquipmentService.rank_item("iron_sword")
    bread_power = EquipmentService.rank_item("bread")
    assert iron_power == 10.0
    assert bread_power == 0.0
    
    # 3. Test Auto-equip
    ent_upd = EquipmentService.auto_equip(entity)
    assert ent_upd is not None
    assert ent_upd.equipment.slot_updates[EquipSlot.MAIN_HAND] == "iron_sword"

@pytest.mark.v2_contract
def test_home_storage_atomicity():
    # 1. Setup: Entity with 1 iron_ore
    inventory = InventoryComponent(items=[ItemStack("iron_ore", 1)])
    entity = EntityState(id=1, kind="hero", position=(0,0), inventory=inventory)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, home_storage={})
    
    # 2. Deposit
    sys_upd = HomeStorageAction.deposit(entity, "iron_ore", 1, state)
    assert sys_upd is not None
    assert 1 in sys_upd.entity_updates
    assert 1 in sys_upd.home_storage_updates
    
    state = ApplyPath.apply_generation(state, sys_upd)
    
    # 3. Verify: Entity empty, Storage has 1
    assert len(state.entities[1].inventory.items) == 0
    assert state.home_storage[1].items[0].item_id == "iron_ore"
    
    # 4. Withdraw
    new_entity = state.entities[1]
    withdraw_upd = HomeStorageAction.withdraw(new_entity, "iron_ore", 1, state)
    assert withdraw_upd is not None
    
    state = ApplyPath.apply_generation(state, withdraw_upd)
    assert state.entities[1].inventory.items[0].item_id == "iron_ore"
    assert len(state.home_storage[1].items) == 0

@pytest.mark.v2_contract
def test_chest_loot_and_apply():
    # 1. Setup: Chest with bread
    chest = ChestState(id=99, position=(0,1), items=[ItemStack("bread", 5)])
    state = AuthoritativeState(tick=1, seed=42, chests={99: chest})
    
    # 2. Manual update (Simulation of looting)
    # We don't have a ChestAction.loot yet, but we test the ApplyPath support
    from src_legacy.core.updates import ChestUpdate
    sys_upd = StateUpdate(
        chest_updates={99: ChestUpdate(chest_id=99, cooldown_set=100, items_set=[])}
    )
    
    state = ApplyPath.apply_generation(state, sys_upd)
    
    # 3. Verify
    assert state.chests[99].cooldown_remaining == 100
    assert len(state.chests[99].items) == 0
