from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pydantic import Field, ConfigDict
from src.core.models.base import Aspect, SimulationModel
from src.core.models.enums import Element

if TYPE_CHECKING:
    from src.actions.base import CombatTraceDetails

class CombatTraceRecord(SimulationModel):
    """Authoritative record of a combat exchange. [AOA STABILIZATION]"""
    model_config = ConfigDict(extra='forbid')
    
    tick: int
    attacker_id: int
    defender_id: int
    damage: int
    is_crit: bool
    is_evasion: bool
    skill_used: str = "attack"
    details: Any = None # CombatTraceDetails (Deferred)

class CombatAspect(Aspect):
    """Aspect handling health, attack power, defense, and elemental vulnerabilities. [AOA STABILIZATION]
    
    Pillar 1: Domain-Driven Separation. Combat state is isolated here
    to ensure clear mutation boundaries and deterministic resolution.
    """
    model_config = ConfigDict(extra='forbid')
    hp: int = 20
    max_hp: int = 20
    # Base Stats
    atk_base: int = 5
    def_base: int = 0
    spd_base: int = 10
    
    luck: int = 0
    crit_rate: float = 0.05
    crit_dmg: float = 1.5
    evasion: float = 0.0

    @property
    def atk(self) -> int:
        mult = 1.0
        for eff in self.effects:
            mult *= getattr(eff, "atk_mult", 1.0)
        return int(self.atk_base * mult)

    @property
    def def_(self) -> int:
        mult = 1.0
        for eff in self.effects:
            mult *= getattr(eff, "def_mult", 1.0)
        return int(self.def_base * mult)

    @property
    def spd(self) -> int:
        mult = 1.0
        for eff in self.effects:
            mult *= getattr(eff, "spd_mult", 1.0)
        return int(self.spd_base * mult)

    # Magic combat
    matk: int = 5
    mdef: int = 0

    # Elemental vulnerability table
    elem_vuln: dict[int, float] = Field(default_factory=lambda: {
        Element.FIRE: 1.0,
        Element.ICE: 1.0,
        Element.LIGHTNING: 1.0,
        Element.DARK: 1.0,
        Element.HOLY: 1.0,
    })
    
    hp_regen: float = 1.0
    cooldown_reduction: float = 1.0
    
    # State & Targeting
    effects: list[Any] = Field(default_factory=list)
    combat_target_id: int | None = None
    
    # Introspection: recent combat traces (ring buffer) [AOA STABILIZATION]
    traces: list[CombatTraceRecord] = Field(default_factory=list)

    def add_effect(self, effect: Any) -> None:
        """Add a StatusEffect to the entity."""
        self.effects.append(effect)

    def remove_effect(self, identifier: str) -> None:
        """Remove effects by effect_id or source."""
        self.effects = [
            e for e in self.effects 
            if getattr(e, "effect_id", None) != identifier 
            and getattr(e, "source", None) != identifier
        ]

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def elemental_vulnerability(self, elem: Element) -> float:
        """Returns the vulnerability multiplier for a given element."""
        return self.elem_vuln.get(elem, 1.0)

    def model_copy(self, **kwargs) -> CombatAspect:
        """Deep copy collections even on shallow aspect copy."""
        copy_obj = super().model_copy(**kwargs)
        copy_obj.elem_vuln = dict(self.elem_vuln)
        copy_obj.effects = list(self.effects)
        return copy_obj

    @property
    def hp_ratio(self) -> float:
        if self.max_hp <= 0:
            return 0.0
        return max(0.0, min(1.0, self.hp / self.max_hp))

    def copy_stats(self) -> "CombatAspect":
        """Equivalent to the old Stats.copy()."""
        return CombatAspect(**self.model_dump())

