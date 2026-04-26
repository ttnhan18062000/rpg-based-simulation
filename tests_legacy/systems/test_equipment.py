import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, AttributeComponent, CombatComponent, EquipmentComponent, EquipSlot
from src_legacy.core.updates import StateUpdate, EntityUpdate, EquipmentUpdate
from src_legacy.engine.apply import ApplyPath
from src_legacy.progression.leveling import LevelingService

def test_equipment_stat_application():
    """
    Phase 8: Verify that equipping an item authoritatively alters combat stats.
    """
    # 1. Setup Base Entity
    # Using base attributes which should yield specific base combat stats
    attr = AttributeComponent(strength=10, vitality=10) # Base HP = 100 + 20 + 2 = 122, Base ATK = 10 + 5 = 15
    derived = LevelingService.recalculate_combat_stats(attr)
    
    combat = CombatComponent(
        max_hp=derived["max_hp"], hp=derived["max_hp"],
        atk=derived["atk"], def_stat=derived["def_stat"],
        evasion=derived["evasion"]
    )
    
    entity = EntityState(
        id=1, kind="HERO", position=(0.0, 0.0),
        attributes=attr,
        combat=combat,
        equipment=EquipmentComponent()
    )
    
    state = AuthoritativeState(tick=0, seed=0, entities={1: entity})
    
    # 2. Equip "steel_sword" (ATK +12) and "iron_plate" (DEF +8, HP +20)
    # Note: These are defined in src.core.registry.Registry
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                equipment=EquipmentUpdate(
                    slot_updates={
                        EquipSlot.MAIN_HAND: "steel_sword",
                        EquipSlot.TORSO: "iron_plate"
                    }
                )
            )
        }
    )
    
    # 3. Apply Update
    new_state = ApplyPath.apply_generation(state, update, next_tick=1, next_world_time=1)
    
    # 4. Assert
    updated_entity = new_state.entities[1]
    
    assert updated_entity.equipment.slots[EquipSlot.MAIN_HAND] == "steel_sword"
    assert updated_entity.equipment.slots[EquipSlot.TORSO] == "iron_plate"
    
    # Check stats
    # Expected ATK = 15 + 12 = 27
    assert updated_entity.combat.atk == 27
    
    # Expected DEF = 5 + (10 * 0.3) + 8 = 5 + 3 + 8 = 16
    assert updated_entity.combat.def_stat == 16
    
    # Expected Max HP = 122 + 20 = 142
    assert updated_entity.combat.max_hp == 142
