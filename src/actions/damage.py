"""Damage calculation strategy pattern.

Refactored for AOA Stabilization:
- Direct aspect access (combat, progression, attributes).
- Removed legacy StatsProxy dependency.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING
from src.core.models.enums import DamageType

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

@dataclass(slots=True)
class DamageContext:
    """Resolved damage parameters from a calculator."""
    atk_power: int
    def_power: int
    atk_mult: float
    def_mult: float
    train_action: str

class DamageCalculator(ABC):
    """Base class for damage type calculators."""

    @property
    @abstractmethod
    def damage_type(self) -> DamageType:
        """The DamageType this calculator handles."""

    @abstractmethod
    def resolve(self, attacker: Entity, defender: Entity) -> DamageContext:
        """Resolve attack/defense power and multipliers for this damage type."""

class PhysicalDamageCalculator(DamageCalculator):
    @property
    def damage_type(self) -> DamageType:
        return DamageType.PHYSICAL

    def resolve(self, attacker: Entity, defender: Entity) -> DamageContext:
        # Direct Aspect Access
        atk_power = attacker.combat.atk
        def_power = defender.combat.def_

        atk_mult = 1.0
        def_mult = 1.0
        
        # Flanking check
        diff = attacker.spatial.pos - defender.spatial.pos
        facing = defender.spatial.facing
        if (diff.x * facing.x + diff.y * facing.y) < 0:
            atk_mult *= 1.3

        if attacker.progression.attributes:
            atk_mult *= (1.0 + attacker.progression.attributes.str_ * 0.02)
        if defender.progression.attributes:
            def_mult *= (1.0 + defender.progression.attributes.vit * 0.01)

        return DamageContext(
            atk_power=atk_power,
            def_power=def_power,
            atk_mult=atk_mult,
            def_mult=def_mult,
            train_action="attack",
        )

class MagicalDamageCalculator(DamageCalculator):
    @property
    def damage_type(self) -> DamageType:
        return DamageType.MAGICAL

    def resolve(self, attacker: Entity, defender: Entity) -> DamageContext:
        # Direct Aspect Access
        atk_power = attacker.combat.matk
        def_power = defender.combat.mdef

        atk_mult = 1.0
        def_mult = 1.0
        if attacker.progression.attributes:
            atk_mult = 1.0 + attacker.progression.attributes.spi * 0.02
        if defender.progression.attributes:
            def_mult = 1.0 + defender.progression.attributes.wis * 0.01

        return DamageContext(
            atk_power=atk_power,
            def_power=def_power,
            atk_mult=atk_mult,
            def_mult=def_mult,
            train_action="magic_attack",
        )

DAMAGE_CALCULATORS: dict[DamageType, DamageCalculator] = {}
_physical = PhysicalDamageCalculator()
_magical = MagicalDamageCalculator()

DAMAGE_CALCULATORS[DamageType.PHYSICAL] = _physical
DAMAGE_CALCULATORS[DamageType.MAGICAL] = _magical

DEFAULT_CALCULATOR: DamageCalculator = _physical

def get_damage_calculator(damage_type: DamageType) -> DamageCalculator:
    """Look up the calculator for a damage type, falling back to physical."""
    if not isinstance(damage_type, DamageType):
        try:
            damage_type = DamageType(damage_type)
        except ValueError:
            return DEFAULT_CALCULATOR
    return DAMAGE_CALCULATORS.get(damage_type, DEFAULT_CALCULATOR)
