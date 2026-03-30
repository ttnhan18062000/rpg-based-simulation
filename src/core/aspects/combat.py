from __future__ import annotations
from typing import Any
from pydantic import Field
from src.core.models.base import Aspect
from src.core.models.enums import Element

class CombatAspect(Aspect):
    """Aspect handling health, attack power, defense, and elemental vulnerabilities."""
    hp: int = 20
    max_hp: int = 20
    # Base Stats
    atk_base: int = Field(default=5, alias="atk")
    def_base: int = Field(default=0, alias="def_")
    spd_base: int = Field(default=10, alias="spd")
    
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
    
    # Introspection: recent combat traces (ring buffer)
    traces: list[dict] = Field(default_factory=list)

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

