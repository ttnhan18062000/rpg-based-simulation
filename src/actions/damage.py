"""Damage calculation strategy pattern.

Abstract DamageCalculator with concrete subclasses for each damage type.
To add a new damage type (e.g. TRUE, HYBRID):
  1. Create a new DamageCalculator subclass.
  2. Register it in DAMAGE_CALCULATORS.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.models.enums import DamageType

if TYPE_CHECKING:
    from src.core.entities.entity import Entity


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class DamageContext:
    """Resolved damage parameters from a calculator."""
    atk_power: int
    def_power: int
    atk_mult: float
    def_mult: float
    train_action: str


# ---------------------------------------------------------------------------
# Abstract calculator
# ---------------------------------------------------------------------------

class DamageCalculator(ABC):
    """Base class for damage type calculators.

    Subclass and implement:
      - damage_type: the DamageType enum value this handles
      - resolve(): extract atk/def power and attribute multipliers
    """

    @property
    @abstractmethod
    def damage_type(self) -> int:
        """The DamageType this calculator handles."""

    @abstractmethod
    def resolve(self, attacker: Entity, defender: Entity) -> DamageContext:
        """Resolve attack/defense power and multipliers for this damage type."""


# ---------------------------------------------------------------------------
# Physical damage
# ---------------------------------------------------------------------------

class PhysicalDamageCalculator(DamageCalculator):

    @property
    def damage_type(self) -> int:
        return DamageType.PHYSICAL

    def resolve(self, attacker: Entity, defender: Entity) -> DamageContext:
        atk_power = attacker.stats.combat.atk
        def_power = defender.stats.combat.def_

        atk_mult = 1.0
        def_mult = 1.0
        
        # Flanking check (1.3x damage)
        diff = attacker.spatial.pos - defender.spatial.pos
        # Note: dot product < 0 means attacker is in the 180-degree arc BEHIND the defender's facing
        facing = defender.spatial.facing
        if (diff.x * facing.x + diff.y * facing.y) < 0:
            atk_mult *= 1.3
            # We could emit a "Flank!" event here, but resolve() is usually pure.
            # We'll let the system handle the log/emit.

        if attacker.attributes:
            atk_mult *= (1.0 + attacker.attributes.str_ * 0.02)
        if defender.attributes:
            def_mult *= (1.0 + defender.attributes.vit * 0.01)

        return DamageContext(
            atk_power=atk_power,
            def_power=def_power,
            atk_mult=atk_mult,
            def_mult=def_mult,
            train_action="attack",
        )


# ---------------------------------------------------------------------------
# Magical damage
# ---------------------------------------------------------------------------

class MagicalDamageCalculator(DamageCalculator):

    @property
    def damage_type(self) -> int:
        return DamageType.MAGICAL

    def resolve(self, attacker: Entity, defender: Entity) -> DamageContext:
        atk_power = attacker.stats.combat.matk
        def_power = defender.stats.combat.mdef

        atk_mult = 1.0
        def_mult = 1.0
        if attacker.attributes:
            atk_mult = 1.0 + attacker.attributes.spi * 0.02
        if defender.attributes:
            def_mult = 1.0 + defender.attributes.wis * 0.01

        return DamageContext(
            atk_power=atk_power,
            def_power=def_power,
            atk_mult=atk_mult,
            def_mult=def_mult,
            train_action="magic_attack",
        )


# ---------------------------------------------------------------------------
# Registry — maps DamageType -> calculator instance
# ---------------------------------------------------------------------------

DAMAGE_CALCULATORS: dict[int, DamageCalculator] = {}

_physical = PhysicalDamageCalculator()
_magical = MagicalDamageCalculator()

DAMAGE_CALCULATORS[DamageType.PHYSICAL] = _physical
DAMAGE_CALCULATORS[DamageType.MAGICAL] = _magical

# Fallback for unknown types
DEFAULT_CALCULATOR: DamageCalculator = _physical


def get_damage_calculator(damage_type: int) -> DamageCalculator:
    """Look up the calculator for a damage type, falling back to physical."""
    return DAMAGE_CALCULATORS.get(damage_type, DEFAULT_CALCULATOR)
