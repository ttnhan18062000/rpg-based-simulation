
import pytest
from dataclasses import replace
from src.core.state import (
    EntityState, CombatComponent, EquipmentComponent, EquipSlot,
    InventoryComponent, ItemStack, AuthoritativeState, AttributeComponent,
    IdentityComponent
)
from src.core.enums import Faction, EntityRole
from src.core.items import ItemRegistry
from src.core.updates import EntityUpdate, CombatUpdate, EquipmentUpdate, ResourceTransferIntent
from src.engine.combat import CombatResolutionSystem
from src.engine.domain_logic import SimulationDomainLogic
from src.progression.leveling import LevelingService
from src.engine.apply import ApplyPath

def make_entity(eid=1, hp=100, gold=100, slots=None, durability=None, faction=Faction.HERO_GUILD, role=EntityRole.HERO):
    from src.core.builder import V2EntityBuilder
    builder = (V2EntityBuilder(eid)
               .kind("hero")
               .location(0, 0)
               .identity(role=role, faction=faction)
               .combat(hp=hp, max_hp=100, atk=10, def_stat=5, alive=hp > 0)
               .inventory(gold=gold)
               .attributes(strength=10, vitality=10, agility=10, endurance=10)
               .lifecycle(active=True)
               .combat(readiness=100.0))
    
    if slots or durability:
        builder.equipment(slots=slots or {}, durability=durability or {})
        
    return builder.build()

class TestDurabilityDecay:
    def test_weapon_decay_on_attack(self):
        """Attacker's weapon durability should decrease by 1.0 on attack."""
        attacker = make_entity(eid=1, slots={EquipSlot.MAIN_HAND: "steel_sword"}, durability={EquipSlot.MAIN_HAND: 100.0})
        defender = make_entity(eid=2, faction=Faction.MONSTER_HORDE, role=EntityRole.MONSTER)
        
        # Resolve attack
        state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
        combat_up = CombatResolutionSystem.resolve_attack(attacker, defender, state)
        
        assert combat_up.attacker_equipment_upd is not None
        assert combat_up.attacker_equipment_upd.durability_delta[EquipSlot.MAIN_HAND] == -1.0

    def test_armor_decay_on_damage(self):
        """Defender's armor durability should decrease by 0.5 per hit."""
        attacker = make_entity(eid=1)
        defender = make_entity(eid=2, faction=Faction.MONSTER_HORDE, role=EntityRole.MONSTER, slots={
            EquipSlot.TORSO: "iron_plate",
            EquipSlot.HEAD: "iron_helmet"
        }, durability={
            EquipSlot.TORSO: 100.0,
            EquipSlot.HEAD: 100.0
        })
        
        state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
        combat_up = CombatResolutionSystem.resolve_attack(attacker, defender, state)
        
        assert combat_up.equipment_upd is not None
        assert combat_up.equipment_upd.durability_delta[EquipSlot.TORSO] == -0.5
        assert combat_up.equipment_upd.durability_delta[EquipSlot.HEAD] == -0.5

class TestBrokenEquipmentImpact:
    def test_broken_weapon_no_bonus(self):
        """A broken weapon (durability 0) should provide no ATK bonus."""
        # Steel sword gives +5 ATK in registry (assumed)
        # Check ItemRegistry for steel_sword
        sword = ItemRegistry.get("steel_sword")
        atk_bonus = sword.properties.get("atk_bonus", 0)
        
        # Healthy weapon
        hero_ok = make_entity(slots={EquipSlot.MAIN_HAND: "steel_sword"}, durability={EquipSlot.MAIN_HAND: 100.0})
        stats_ok = LevelingService.recalculate_combat_stats(hero_ok.attributes, hero_ok.equipment)
        
        # Broken weapon
        hero_broken = make_entity(slots={EquipSlot.MAIN_HAND: "steel_sword"}, durability={EquipSlot.MAIN_HAND: 0.0})
        stats_broken = LevelingService.recalculate_combat_stats(hero_broken.attributes, hero_broken.equipment)
        
        assert stats_ok["atk"] == stats_broken["atk"] + atk_bonus

    def test_broken_weapon_reverts_range(self):
        """A broken weapon should revert to base range (1)."""
        # Assume steel_sword has range > 1 or check registry
        # For test, let's assume it has range 1.5
        hero_ok = make_entity(slots={EquipSlot.MAIN_HAND: "steel_sword"}, durability={EquipSlot.MAIN_HAND: 100.0})
        # Mock range if needed, or use an item that has range
        # Let's check desert_bow
        bow = ItemRegistry.get("desert_bow")
        if bow and "range" in bow.properties:
            hero_ok = make_entity(slots={EquipSlot.MAIN_HAND: "desert_bow"}, durability={EquipSlot.MAIN_HAND: 100.0})
            stats_ok = LevelingService.recalculate_combat_stats(hero_ok.attributes, hero_ok.equipment)
            
            hero_broken = make_entity(slots={EquipSlot.MAIN_HAND: "desert_bow"}, durability={EquipSlot.MAIN_HAND: 0.0})
            stats_broken = LevelingService.recalculate_combat_stats(hero_broken.attributes, hero_broken.equipment)
            
            assert stats_ok["range"] == bow.properties["range"]
            assert stats_broken["range"] == 1 # Base range

class TestRepairMechanism:
    def test_repair_cost_calculation(self):
        """Repair cost should be (100 - durability) * 0.5."""
        hero = make_entity(gold=100, slots={EquipSlot.MAIN_HAND: "steel_sword"}, durability={EquipSlot.MAIN_HAND: 80.0})
        
        logic = SimulationDomainLogic()
        updates = logic.execute_action(hero, {"action": "REPAIR"}, current_tick=1)
        
        ent_upd = updates[hero.id]
        intent = ent_upd.resource_transfers[0]
        
        # (100 - 80) * 0.5 = 10 gold
        assert intent.gold_delta == -10
        assert intent.gold_cost == 10
        assert intent.equipment_upd.durability_set[EquipSlot.MAIN_HAND] == 100.0

    def test_apply_repair_update(self):
        """Applying a repair update should restore durability."""
        hero = make_entity(durability={EquipSlot.MAIN_HAND: 50.0})
        upd = EntityUpdate(
            entity_id=hero.id,
            equipment=EquipmentUpdate(durability_set={EquipSlot.MAIN_HAND: 100.0})
        )
        
        result = ApplyPath._apply_entity_update(hero, upd)
        assert result.equipment.durability[EquipSlot.MAIN_HAND] == 100.0

class TestCraftingCapacity:
    def test_crafting_succeeds_with_freed_space(self):
        """Crafting should succeed if materials removed make room for output."""
        # Inventory is full but contains iron_ore
        inv = InventoryComponent(
            max_slots=2,
            max_weight=100.0,
            gold=100,
            items=[
                ItemStack("iron_ore", 2),
                ItemStack("wood", 1)
            ]
        )
        hero = make_entity(eid=1, gold=100)
        hero = replace(hero, inventory=inv)
        
        # Recipe for steel_sword: 2 iron_ore, 1 wood, 60 gold
        # It adds 1 item (steel_sword) and removes 2 stacks (iron_ore, wood)
        intent = ResourceTransferIntent(
            source_id="craft_steel_sword",
            source_kind="CRAFTING",
            items_add=[ItemStack("steel_sword", 1)],
            items_remove=[ItemStack("iron_ore", 2), ItemStack("wood", 1)],
            gold_cost=60
        )
        
        from src.core.conservation import ResourceTransactionResolver
        state = AuthoritativeState(tick=1, seed=42, entities={1: hero})
        result = ResourceTransactionResolver.resolve(state, hero, intent)
        
        assert result.accepted, f"Failed: {result.reason}"
        assert len(result.inventory_update.items_add) == 1
        assert len(result.inventory_update.items_remove) == 2
