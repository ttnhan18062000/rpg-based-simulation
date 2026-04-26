from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict

class SkillKind(Enum):
    ACTIVE = auto()
    PASSIVE = auto()

class SkillCategory(Enum):
    PHYSICAL = auto()
    MAGICAL = auto()
    ELEMENTAL = auto()

@dataclass(frozen=True)
class SkillDefinition:
    id: str
    name: str
    kind: SkillKind
    power: float
    cost: int
    cooldown: int
    description: str
    category: SkillCategory = SkillCategory.PHYSICAL

SKILL_REGISTRY: Dict[str, SkillDefinition] = {
    "power_strike": SkillDefinition(
        id="power_strike",
        name="Power Strike",
        kind=SkillKind.ACTIVE,
        power=1.5,
        cost=10,
        cooldown=3,
        description="A heavy blow dealing 150% damage.",
        category=SkillCategory.PHYSICAL
    ),
    "fireball": SkillDefinition(
        id="fireball",
        name="Fireball",
        kind=SkillKind.ACTIVE,
        power=2.0,
        cost=25,
        cooldown=5,
        description="Launch a ball of fire dealing 200% magic damage.",
        category=SkillCategory.MAGICAL
    ),
    "swift_reflexes": SkillDefinition(
        id="swift_reflexes",
        name="Swift Reflexes",
        kind=SkillKind.PASSIVE,
        power=0.1, # +10% evasion
        cost=0,
        cooldown=0,
        description="Increases evasion by 10%.",
        category=SkillCategory.PHYSICAL # Evasion is physical/agility
    ),
}
