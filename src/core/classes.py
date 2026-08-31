from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set

@dataclass(frozen=True)
class ClassDefinition:
    id: str
    name: str
    base_hp: int
    base_atk: int
    base_def: int
    starting_skills: List[str] = field(default_factory=list)
    starting_gear: Dict[str, str] = field(default_factory=dict) # SlotID -> ItemID

CLASS_REGISTRY: Dict[str, ClassDefinition] = {
    "NOVICE": ClassDefinition(
        id="NOVICE",
        name="Novice",
        base_hp=100,
        base_atk=10,
        base_def=5,
        starting_skills=[]
    ),
    "WARRIOR": ClassDefinition(
        id="WARRIOR",
        name="Warrior",
        base_hp=150,
        base_atk=15,
        base_def=10,
        starting_skills=["power_strike"],
        starting_gear={"MAIN_HAND": "iron_sword", "TORSO": "leather_armor"}
    ),
    "MAGE": ClassDefinition(
        id="MAGE",
        name="Mage",
        base_hp=80,
        base_atk=20,
        base_def=2,
        starting_skills=["fireball"],
        starting_gear={"MAIN_HAND": "wooden_staff"}
    ),
    "ROGUE": ClassDefinition(
        id="ROGUE",
        name="Rogue",
        base_hp=100,
        base_atk=12,
        base_def=5,
        starting_skills=["swift_reflexes"],
        starting_gear={"MAIN_HAND": "iron_dagger"}
    ),
}

@dataclass(frozen=True)
class ClassTierOption:
    tier_id: str
    name: str
    attribute_bonuses: Dict[str, int] = field(default_factory=dict)

CLASS_TIER_REGISTRY: Dict[str, List[ClassTierOption]] = {
    "WARRIOR": [
        ClassTierOption(tier_id="WARRIOR_CHAMPION", name="Champion",
                         attribute_bonuses={"strength": 4, "vitality": 2}),
        ClassTierOption(tier_id="WARRIOR_GUARDIAN", name="Guardian",
                         attribute_bonuses={"vitality": 4, "endurance": 3}),
    ],
    "MAGE": [
        ClassTierOption(tier_id="MAGE_ARCHMAGE", name="Archmage",
                         attribute_bonuses={"intelligence": 4, "spirit": 2}),
        ClassTierOption(tier_id="MAGE_STORMWEAVER", name="Stormweaver",
                         attribute_bonuses={"spirit": 4, "wisdom": 3}),
    ],
}
