from __future__ import annotations
from dataclasses import dataclass, field
from src.core.models.enums import Element

@dataclass(slots=True)
class Stats:
    """Mutable combat statistics for an entity."""

    # --- Core combat ---
    hp: int = 20
    max_hp: int = 20
    atk: int = 5
    def_: int = 0
    spd: int = 10
    luck: int = 0
    crit_rate: float = 0.05
    crit_dmg: float = 1.5
    evasion: float = 0.0

    # --- Magic combat ---
    matk: int = 5           # Magic attack power
    mdef: int = 0           # Magic defense

    # --- Elemental vulnerability table ---
    elem_vuln: dict[int, float] = field(default_factory=lambda: {
        Element.FIRE: 1.0,
        Element.ICE: 1.0,
        Element.LIGHTNING: 1.0,
        Element.DARK: 1.0,
        Element.HOLY: 1.0,
    })

    # --- Progression ---
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    gold: int = 0
    fame: int = 0
    stamina: int = 50
    max_stamina: int = 50

    # --- Secondary / non-combat ---
    vision_range: int = 6
    loot_bonus: float = 1.0
    trade_bonus: float = 1.0
    interaction_speed: float = 1.0
    rest_efficiency: float = 1.0
    hp_regen: float = 1.0
    cooldown_reduction: float = 1.0

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def hp_ratio(self) -> float:
        if self.max_hp <= 0:
            return 0.0
        return max(0.0, min(1.0, self.hp / self.max_hp))

    @property
    def stamina_ratio(self) -> float:
        return self.stamina / self.max_stamina if self.max_stamina > 0 else 0.0

    def copy(self) -> Stats:
        return Stats(
            hp=self.hp, max_hp=self.max_hp, atk=self.atk, def_=self.def_,
            spd=self.spd, luck=self.luck, crit_rate=self.crit_rate,
            crit_dmg=self.crit_dmg, evasion=self.evasion,
            matk=self.matk, mdef=self.mdef,
            elem_vuln=dict(self.elem_vuln),
            level=self.level, xp=self.xp, xp_to_next=self.xp_to_next,
            gold=self.gold, fame=self.fame, 
            stamina=self.stamina, max_stamina=self.max_stamina,
            vision_range=self.vision_range, loot_bonus=self.loot_bonus,
            trade_bonus=self.trade_bonus,
            interaction_speed=self.interaction_speed,
            rest_efficiency=self.rest_efficiency,
            hp_regen=self.hp_regen,
            cooldown_reduction=self.cooldown_reduction,
        )
