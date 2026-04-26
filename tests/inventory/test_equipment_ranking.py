import pytest
from src.core.state import EntityState, IdentityComponent, EquipmentComponent, EquipSlot, ItemKind
from src.core.items import ItemDefinition
from src.core.equipment_service import EquipmentService

def test_equipment_ranking_warrior():
    # Setup warrior
    warrior = EntityState(
        id=1, kind="HERO", position=(0,0),
        identity=IdentityComponent(class_id="WARRIOR")
    )
    
    # Gear 1: Light sword (ATK 5)
    light_sword = ItemDefinition(
        id="light_sword", name="Light Sword", kind=ItemKind.WEAPON,
        properties={"atk_bonus": 5}
    )
    
    # Gear 2: Heavy shield (DEF 10)
    heavy_shield = ItemDefinition(
        id="heavy_shield", name="Heavy Shield", kind=ItemKind.ARMOR,
        properties={"def_bonus": 10}
    )
    
    # Warriors value DEF more (1.5x)
    light_score = EquipmentService.get_gear_score(warrior, light_sword)
    heavy_score = EquipmentService.get_gear_score(warrior, heavy_shield)
    
    assert light_score == 5.0
    assert heavy_score == 15.0 # 10 * 1.5

def test_equipment_ranking_mage():
    # Setup mage
    mage = EntityState(
        id=2, kind="HERO", position=(0,0),
        identity=IdentityComponent(class_id="MAGE")
    )
    
    # Gear 1: Wand (ATK 5, INT 5)
    wand = ItemDefinition(
        id="wand", name="Wand", kind=ItemKind.WEAPON,
        properties={"atk_bonus": 5, "int_bonus": 10}
    )
    
    # Mages value INT more (2.0x) and ATK (1.5x)
    score = EquipmentService.get_gear_score(mage, wand)
    # 5 * 1.5 + 10 * 2.0 = 7.5 + 20.0 = 27.5
    assert score == 27.5

def test_should_replace():
    entity = EntityState(
        id=1, kind="HERO", position=(0,0),
        identity=IdentityComponent(class_id="WARRIOR"),
        equipment=EquipmentComponent(slots={EquipSlot.MAIN_HAND: "wooden_club"})
    )
    
    # iron_sword (ATK 10) vs wooden_club (ATK 3)
    assert EquipmentService.should_replace(entity, "iron_sword", EquipSlot.MAIN_HAND) == True
    assert EquipmentService.should_replace(entity, "wooden_club", EquipSlot.MAIN_HAND) == False
