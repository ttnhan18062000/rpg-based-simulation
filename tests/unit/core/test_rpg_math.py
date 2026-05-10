from dataclasses import replace
import pytest
from src.core.state import (
    EntityState, IdentityComponent, AttributeComponent, 
    EquipmentComponent, EquipSlot, CombatComponent, StaminaComponent,
    WoundState
)
from src.progression.leveling import LevelingService
from src.engine.rpg_depth import SkillScalingService, StaminaService, WoundService

def test_level_up_mechanics():
    identity = IdentityComponent(evolution_level=1, evolution_points=0, unspent_ap=0)
    
    # Gain 100 XP (Level 1 -> 2 requirement is 100 * 1**1.5 = 100)
    update = LevelingService.process_progression(identity, 150)
    
    assert update.evolution_level_set == 2
    assert update.unspent_ap_delta == 5
    assert "power_strike" in update.learned_skills
    # 150 - 100 = 50 remaining XP
    assert update.evolution_points_delta == 50
    
    print("\nSuccessfully verified Level Up mechanics.")

def test_stat_recalculation():
    # Base: Str 10, Vit 10, Agi 10, End 10
    # HP: 100 + 10*2 + 10*0.5 = 125
    # ATK: 10 + 10*0.5 = 15
    # DEF: 5 + 10*0.3 = 8
    # Evasion: 0.05 + 10*0.001 = 0.06
    # Move Cost: 10 + 0 - 1 = 9
    
    attrs = AttributeComponent(strength=10, vitality=10, agility=10, endurance=10)
    
    # 1. Base Stats
    stats = LevelingService.recalculate_combat_stats(attrs)
    assert stats["max_hp"] == 125
    assert stats["atk"] == 15
    assert stats["def_stat"] == 8
    assert stats["evasion"] == pytest.approx(0.06)
    assert stats["move_cost"] == 9.0
    
    # 2. With Gear (Iron Sword + Iron Plate)
    # Iron Sword: Atk +10, Weight 5.0
    # Iron Plate: Def +15, Weight 12.0
    # Total Weight: 17.0
    # HP: 125
    # ATK: 15 + 10 = 25
    # DEF: 8 + 15 = 23
    # Move Cost: 10 + (17/5) - 1 = 10 + 3.4 - 1 = 12.4
    
    equip = EquipmentComponent(slots={
        EquipSlot.MAIN_HAND: "iron_sword",
        EquipSlot.TORSO: "iron_plate"
    })
    
    stats_gear = LevelingService.recalculate_combat_stats(attrs, equipment=equip)
    assert stats_gear["atk"] == 25
    assert stats_gear["def_stat"] == 23
    assert stats_gear["move_cost"] == 12.4
    
    print("\nSuccessfully verified Stat Recalculation (Attributes + Gear).")

def test_encumbrance_scaling():
    attrs = AttributeComponent(agility=10) # -1.0 cost
    
    # 50kg weight -> +10.0 cost
    # Base 10.0 + 10.0 - 1.0 = 19.0
    
    # We need to mock ItemRegistry or use real items
    from src.core.items import ItemRegistry, ItemDefinition, ItemKind
    # Create a heavy item
    heavy_item = ItemDefinition(id="heavy_anvil", name="Anvil", kind=ItemKind.MATERIAL, weight=50.0)
    ItemRegistry._items["heavy_anvil"] = heavy_item
    
    equip = EquipmentComponent(slots={EquipSlot.OFF_HAND: "heavy_anvil"})
    stats = LevelingService.recalculate_combat_stats(attrs, equipment=equip)
    
    assert stats["move_cost"] == 19.0
    print("\nSuccessfully verified Encumbrance scaling.")

def test_stamina_and_wounds():
    stamina = StaminaComponent(current=100.0, max_stamina=100.0)
    
    # Drain move
    cost = StaminaService.drain_move(stamina)
    assert cost == 3.0
    
    # Exhaustion check
    stamina_low = replace(stamina, current=5.0)
    assert StaminaService.is_exhausted(stamina_low)
    assert StaminaService.get_exhaustion_multiplier(stamina_low) == 0.7
    
    # Wound impact
    attrs = AttributeComponent(strength=10, vitality=10, agility=10, endurance=10)
    wound = WoundState(id="w1", kind="SLASH", severity=0.5, tick_inflicted=100, atk_penalty=5, def_penalty=3, max_hp_penalty=20)
    
    # Recompute with wound
    stats = SkillScalingService.get_effective_stats(attrs, wounds=[wound])
    # Base ATK 15 - 5 = 10
    # Base DEF 8 - 3 = 5
    # Base MaxHP 125 - 20 = 105
    assert stats["atk"] == 10
    assert stats["def_stat"] == 5
    assert stats["max_hp"] == 105
    
    print("\nSuccessfully verified Stamina and Wound stat impacts.")
