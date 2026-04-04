from __future__ import annotations
from typing import Any, TYPE_CHECKING, Union
from pydantic import Field, ConfigDict, model_validator
from src.core.models.base import Aspect, SimulationModel
from src.core.models.enums import Element

from src.core.models.combat import CombatTraceRecord, CombatTraceDetails
from src.core.models.types import TargetUnion

if TYPE_CHECKING:
    from src.actions.base import CombatTraceUpdate
    from src.core.effects import StatusEffect

class CombatAspect(Aspect):
    """Aspect handling health, attack power, defense, and elemental vulnerabilities. [AOA STABILIZATION]
    
    Pillar 1: Domain-Driven Separation. Combat state is isolated here
    to ensure clear mutation boundaries and deterministic resolution.
    """
    model_config = ConfigDict(extra='forbid')
    
    @model_validator(mode='before')
    @classmethod
    def _map_legacy_stats(cls, data: Any) -> Any:
        """AOA Stabilization: Maps legacy 'atk' / 'def_' / 'spd' labels to authoritative 'base' fields."""
        if not isinstance(data, dict):
            return data
            
        # Re-mapping (Legacy Shim)
        if "atk" in data and "atk_base" not in data:
            data["atk_base"] = data.pop("atk")
        if "def_" in data and "def_base" not in data:
            data["def_base"] = data.pop("def_")
        if "spd" in data and "spd_base" not in data:
            data["spd_base"] = data.pop("spd")
            
        if "max_hp" in data and "max_hp_base" not in data:
            data["max_hp_base"] = data.pop("max_hp")
        if "matk" in data and "matk_base" not in data:
            data["matk_base"] = data.pop("matk")
        if "mdef" in data and "mdef_base" not in data:
            data["mdef_base"] = data.pop("mdef")
            
        return data

    hp: int = 20
    max_hp_base: int = 20
    
    @property
    def max_hp(self) -> int:
        mult = 1.0
        for eff in self.effects:
            mult *= getattr(eff, "max_hp_mult", 1.0)
        return int(self.max_hp_base * mult)

    @max_hp.setter
    def max_hp(self, value: int) -> None:
        self.max_hp_base = value
    # Base Stats
    atk_base: int = 5
    def_base: int = 0
    spd_base: int = 10
    
    luck: int = 0
    crit_rate: float = 0.05
    crit_dmg: float = 1.5
    evasion: float = 0.0

    @property
    def _bravery_mult(self) -> float:
        """AOA Stabilization Shim: Legacy emotional impact on stats."""
        # We look up the parent entity's mind aspect
        # In AOA, aspects should ideally be decoupled, but for legacy test compatibility
        # we allow this back-reference or assume the property is only called when attached.
        if not hasattr(self, "_entity") or not self._entity or not self._entity.mind:
            return 1.0
        bravery = self._entity.mind.emotion.bravery
        if bravery > 0.8: return 1.1
        if bravery < 0.3: return 0.9
        return 1.0

    @property
    def atk(self) -> int:
        mult = self._bravery_mult
        for eff in self.effects:
            mult *= getattr(eff, "atk_mult", 1.0)
        return int(self.atk_base * mult)

    @property
    def def_(self) -> int:
        mult = self._bravery_mult
        for eff in self.effects:
            mult *= getattr(eff, "def_mult", 1.0)
        return int(self.def_base * mult)

    @property
    def spd(self) -> int:
        mult = self._bravery_mult
        for eff in self.effects:
            mult *= getattr(eff, "spd_mult", 1.0)
        return int(self.spd_base * mult)

    # Magic combat
    matk_base: int = 5
    mdef_base: int = 0

    @property
    def matk(self) -> int:
        mult = self._bravery_mult
        for eff in self.effects:
            mult *= getattr(eff, "matk_mult", 1.0)
        return int(self.matk_base * mult)
    
    @matk.setter
    def matk(self, value: int) -> None:
        self.matk_base = value

    @property
    def mdef(self) -> int:
        mult = self._bravery_mult
        for eff in self.effects:
            mult *= getattr(eff, "mdef_mult", 1.0)
        return int(self.mdef_base * mult)
    
    @mdef.setter
    def mdef(self, value: int) -> None:
        self.mdef_base = value

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
    effects: list["StatusEffect"] = Field(default_factory=list)
    combat_target_id: TargetUnion = Field(default=None)
    
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

    def validate(self) -> None:
        """Enforce HP clamping and attribute bounds."""
        # 1. HP Clamping
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        if self.hp < 0:
            self.hp = 0
            
        # 2. Base Attribute Bounds
        self.atk_base = max(1, self.atk_base)
        self.def_base = max(0, self.def_base)
        self.spd_base = max(1, self.spd_base)
        self.max_hp_base = max(1, self.max_hp_base)
        self.matk_base = max(0, self.matk_base)
        self.mdef_base = max(0, self.mdef_base)

    @property
    def hp_ratio(self) -> float:
        if self.max_hp <= 0:
            return 0.0
        return max(0.0, min(1.0, self.hp / self.max_hp))

    def copy_stats(self) -> "CombatAspect":
        """Equivalent to the old Stats.copy()."""
        return CombatAspect(**self.model_dump())



# Rebuild Model to finalize Pydantic setup
# AOA Final Convergence: Restore eager model_rebuild now that circular 
# dependency is broken.
from src.core.effects import StatusEffect
CombatAspect.model_rebuild()
