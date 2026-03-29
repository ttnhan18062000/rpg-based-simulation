from __future__ import annotations
from typing import Any
from pydantic import Field
from src.core.models.base import Aspect
from src.core.models.enums import Element

class CombatAspect(Aspect):
    """Aspect handling health, attack power, defense, and elemental vulnerabilities."""
    hp: int = 20
    max_hp: int = 20
    atk: int = 5
    def_: int = 0
    spd: int = 10
    luck: int = 0
    crit_rate: float = 0.05
    crit_dmg: float = 1.5
    evasion: float = 0.0

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
    
    # Secondary stats (moved from legacy Stats)
    vision_range: int = 6
    loot_bonus: float = 1.0
    trade_bonus: float = 1.0
    interaction_speed: float = 1.0
    rest_efficiency: float = 1.0
    cooldown_reduction: float = 1.0
    
    # State & Targeting
    effects: list[Any] = Field(default_factory=list)
    combat_target_id: int | None = None
    loot_progress: int = 0

    @property
    def alive(self) -> bool:
        return self.hp > 0

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

    # --- Legacy Stats Compatibility ---
    # These properties delegate to other aspects on the entity
    
    @property
    def level(self) -> int: 
        if not self._entity: return 1
        return self.entity.progression.level
    @level.setter
    def level(self, val: int): 
        if self._entity: self.entity.progression.level = val

    @property
    def xp(self) -> int: 
        if not self._entity: return 0
        return self.entity.progression.xp
    @xp.setter
    def xp(self, val: int): 
        if self._entity: self.entity.progression.xp = val

    @property
    def xp_to_next(self) -> int: 
        if not self._entity: return 100
        return self.entity.progression.xp_to_next
    @xp_to_next.setter
    def xp_to_next(self, val: int): 
        if self._entity: self.entity.progression.xp_to_next = val

    @property
    def gold(self) -> int: 
        if not self._entity: return 0
        return self.entity.progression.gold
    @gold.setter
    def gold(self, val: int): 
        if self._entity: self.entity.progression.gold = val

    @property
    def stamina(self) -> int: 
        if not self._entity: return 100
        return self.entity.progression.stamina
    @stamina.setter
    def stamina(self, val: int): 
        if self._entity: self.entity.progression.stamina = val

    @property
    def max_stamina(self) -> int: 
        if not self._entity: return 100
        return self.entity.progression.max_stamina
    @max_stamina.setter
    def max_stamina(self, val: int): 
        if self._entity: self.entity.progression.max_stamina = val

    @property
    def fame(self) -> int: 
        if not self._entity: return 0
        return self.entity.progression.fame
    @fame.setter
    def fame(self, val: int): 
        if self._entity: self.entity.progression.fame = val

    @property
    def chase_ticks(self) -> int:
        if not self._entity: return 0
        return self.entity.mind.chase_ticks
    @chase_ticks.setter
    def chase_ticks(self, val: int):
        if self._entity: self.entity.mind.chase_ticks = val

    @property
    def engaged_ticks(self) -> int:
        if not self._entity: return 0
        return self.entity.mind.engaged_ticks
    @engaged_ticks.setter
    def engaged_ticks(self, val: int):
        if self._entity: self.entity.mind.engaged_ticks = val
