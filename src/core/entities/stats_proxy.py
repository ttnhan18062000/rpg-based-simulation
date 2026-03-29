from __future__ import annotations
from typing import TYPE_CHECKING, Any
from src.core.models.enums import Element

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

class StatsProxy:
    """Entry point for effective stats. Partitioned by Domain/Aspect."""
    __slots__ = ("combat", "progression")

    def __init__(self, entity: Entity) -> None:
        self.combat = StatsProxyCombat(entity)
        self.progression = StatsProxyProgression(entity)

    # --- Top-Level Shims for Legacy Compatibility ---
    @property
    def hp(self) -> int: return self.combat.hp
    @hp.setter
    def hp(self, v: int): self.combat.hp = v

    @property
    def max_hp(self) -> int: return self.combat.max_hp
    @max_hp.setter
    def max_hp(self, v: int): self.combat.max_hp = v

    @property
    def atk(self) -> int: return self.combat.atk
    @atk.setter
    def atk(self, v: int): self.combat.atk = v

    @property
    def def_(self) -> int: return self.combat.def_
    @def_.setter
    def def_(self, v: int): self.combat.def_ = v

    @property
    def spd(self) -> int: return self.combat.spd
    @spd.setter
    def spd(self, v: int): self.combat.spd = v

    @property
    def vision_range(self) -> int: return self.combat.vision_range
    @vision_range.setter
    def vision_range(self, v: int): self.combat.vision_range = v

    @property
    def level(self) -> int: return self.progression.level
    @level.setter
    def level(self, v: int): self.progression.level = v

    @property
    def gold(self) -> int: return self.progression.gold
    @gold.setter
    def gold(self, v: int): self.progression.gold = v

    @property
    def xp(self) -> int: return self.progression.xp
    @xp.setter
    def xp(self, v: int): self.progression.xp = v

    @property
    def xp_to_next(self) -> int: return self.progression.xp_to_next
    @xp_to_next.setter
    def xp_to_next(self, v: int): self.progression.xp_to_next = v

    @property
    def fame(self) -> int: return self.progression.fame
    @fame.setter
    def fame(self, v: int): self.progression.fame = v

    @property
    def stamina(self) -> int: return self.progression.stamina
    @stamina.setter
    def stamina(self, v: int): self.progression.stamina = v

    @property
    def max_stamina(self) -> int: return self.progression.max_stamina
    @max_stamina.setter
    def max_stamina(self, v: int): self.progression.max_stamina = v

    @property
    def matk(self) -> int: return self.combat.matk
    @matk.setter
    def matk(self, v: int): self.combat.matk = v

    @property
    def mdef(self) -> int: return self.combat.mdef
    @mdef.setter
    def mdef(self, v: int): self.combat.mdef = v

    @property
    def luck(self) -> int: return self.combat.luck
    @luck.setter
    def luck(self, v: int): self.combat.luck = v

    @property
    def crit_rate(self) -> float: return self.combat.crit_rate
    @crit_rate.setter
    def crit_rate(self, v: float): self.combat.crit_rate = v

    @property
    def crit_dmg(self) -> float: return self.combat.crit_dmg
    @crit_dmg.setter
    def crit_dmg(self, v: float): self.combat.crit_dmg = v

    @property
    def evasion(self) -> float: return self.combat.evasion
    @evasion.setter
    def evasion(self, v: float): self.combat.evasion = v

    @property
    def hp_regen(self) -> float: return self.combat.hp_regen
    @hp_regen.setter
    def hp_regen(self, v: float): self.combat.hp_regen = v

    @property
    def loot_bonus(self) -> float: return self.combat.loot_bonus
    @loot_bonus.setter
    def loot_bonus(self, v: float): self.combat.loot_bonus = v

    @property
    def trade_bonus(self) -> float: return self.combat.trade_bonus
    @trade_bonus.setter
    def trade_bonus(self, v: float): self.combat.trade_bonus = v

    @property
    def interaction_speed(self) -> float: return self.combat.interaction_speed
    @interaction_speed.setter
    def interaction_speed(self, v: float): self.combat.interaction_speed = v

    @property
    def rest_efficiency(self) -> float: return self.combat.rest_efficiency
    @rest_efficiency.setter
    def rest_efficiency(self, v: float): self.combat.rest_efficiency = v

    @property
    def cooldown_reduction(self) -> float: return self.combat.cooldown_reduction
    @cooldown_reduction.setter
    def cooldown_reduction(self, v: float): self.combat.cooldown_reduction = v

    @property
    def stamina_ratio(self) -> float: return self.progression.stamina_ratio
    @property
    def xp_ratio(self) -> float: return self.progression.xp_ratio

    # --- Primary Attributes Shims ---
    @property
    def str(self) -> int: return self.progression.str
    @str.setter
    def str(self, v: int): self.progression.str = v

    @property
    def agi(self) -> int: return self.progression.agi
    @agi.setter
    def agi(self, v: int): self.progression.agi = v

    @property
    def vit(self) -> int: return self.progression.vit
    @vit.setter
    def vit(self, v: int): self.progression.vit = v

    @property
    def int(self) -> int: return self.progression.int
    @int.setter
    def int(self, v: int): self.progression.int = v

    @property
    def spi(self) -> int: return self.progression.spi
    @spi.setter
    def spi(self, v: int): self.progression.spi = v

    @property
    def wis(self) -> int: return self.progression.wis
    @wis.setter
    def wis(self, v: int): self.progression.wis = v

    @property
    def end(self) -> int: return self.progression.end
    @end.setter
    def end(self, v: int): self.progression.end = v

    @property
    def per(self) -> int: return self.progression.per
    @per.setter
    def per(self, v: int): self.progression.per = v

    @property
    def cha(self) -> int: return self.progression.cha
    @cha.setter
    def cha(self, v: int): self.progression.cha = v

class StatsProxyCombat:
    """Effective stats for Combat domain."""
    __slots__ = ("_entity",)
    def __init__(self, entity: Entity) -> None:
        self._entity = entity

    @property
    def atk(self) -> int:
        ent = self._entity
        base = ent.combat.atk
        if hasattr(ent, "inventory_aspect") and ent.inventory_aspect:
            base += int(ent.inventory_aspect.equipment_bonus("atk_bonus"))
        mult = self._effect_mult("atk_mult") * self._veterancy_mult("atk") * self._bravery_mult("atk")
        return max(int(base * mult), 1)

    @atk.setter
    def atk(self, value: int) -> None:
        self._entity.combat.atk = value

    @property
    def def_(self) -> int:
        ent = self._entity
        base = ent.combat.def_
        if hasattr(ent, "inventory_aspect") and ent.inventory_aspect:
            base += int(ent.inventory_aspect.equipment_bonus("def_bonus"))
        mult = self._effect_mult("def_mult") * self._veterancy_mult("def") * self._bravery_mult("def")
        return max(int(base * mult), 0)

    @def_.setter
    def def_(self, value: int) -> None:
        self._entity.combat.def_ = value

    @property
    def spd(self) -> int:
        ent = self._entity
        base = ent.combat.spd
        if hasattr(ent, "inventory_aspect") and ent.inventory_aspect:
            base += int(ent.inventory_aspect.equipment_bonus("spd_bonus"))
        mult = self._effect_mult("spd_mult") * self._veterancy_mult("spd") * self._bravery_mult("spd")
        return max(int(base * mult), 1)

    @spd.setter
    def spd(self, value: int) -> None:
        self._entity.combat.spd = value

    @property
    def max_hp(self) -> int:
        ent = self._entity
        base = ent.combat.max_hp
        if hasattr(ent, "inventory_aspect") and ent.inventory_aspect:
            base += int(ent.inventory_aspect.equipment_bonus("hp_bonus"))
        mult = self._effect_mult("max_hp_mult") * self._veterancy_mult("hp")
        return max(int(base * mult), 1)
    @property
    def mdef(self) -> int: return self._entity.combat.mdef
    @mdef.setter
    def mdef(self, v: int): self._entity.combat.mdef = v

    @property
    def matk(self) -> int: return self._entity.combat.matk
    @matk.setter
    def matk(self, v: int): self._entity.combat.matk = v

    @property
    def luck(self) -> int: return self._entity.combat.luck
    @luck.setter
    def luck(self, v: int): self._entity.combat.luck = v

    @property
    def crit_rate(self) -> float: return self._entity.combat.crit_rate
    @crit_rate.setter
    def crit_rate(self, v: float): self._entity.combat.crit_rate = v

    @property
    def crit_dmg(self) -> float: return self._entity.combat.crit_dmg
    @crit_dmg.setter
    def crit_dmg(self, v: float): self._entity.combat.crit_dmg = v

    @property
    def evasion(self) -> float: return self._entity.combat.evasion
    @evasion.setter
    def evasion(self, v: float): self._entity.combat.evasion = v

    @property
    def hp_regen(self) -> float: return self._entity.combat.hp_regen
    @hp_regen.setter
    def hp_regen(self, v: float): self._entity.combat.hp_regen = v

    @max_hp.setter
    def max_hp(self, value: int) -> None:
        self._entity.combat.max_hp = value

    @property
    def hp(self) -> int: return self._entity.combat.hp
    @hp.setter
    def hp(self, value: int): self._entity.combat.hp = value
    
    @property
    def hp_ratio(self) -> float: return self._entity.combat.hp_ratio

    @property
    def vision_range(self) -> int: return self._entity.combat.vision_range
    @vision_range.setter
    def vision_range(self, v: int): self._entity.combat.vision_range = v

    @property
    def loot_bonus(self) -> float: return self._entity.combat.loot_bonus
    @loot_bonus.setter
    def loot_bonus(self, v: float): self._entity.combat.loot_bonus = v

    @property
    def trade_bonus(self) -> float: return self._entity.combat.trade_bonus
    @trade_bonus.setter
    def trade_bonus(self, v: float): self._entity.combat.trade_bonus = v

    @property
    def interaction_speed(self) -> float: return self._entity.combat.interaction_speed
    @interaction_speed.setter
    def interaction_speed(self, v: float): self._entity.combat.interaction_speed = v

    @property
    def rest_efficiency(self) -> float: return self._entity.combat.rest_efficiency
    @rest_efficiency.setter
    def rest_efficiency(self, v: float): self._entity.combat.rest_efficiency = v

    @property
    def cooldown_reduction(self) -> float: return self._entity.combat.cooldown_reduction
    @cooldown_reduction.setter
    def cooldown_reduction(self, v: float): self._entity.combat.cooldown_reduction = v

    def _effect_mult(self, attr: str) -> float:
        m = 1.0
        for eff in self._entity.combat.effects:
            v = getattr(eff, attr, 1.0)
            if v is not None: m *= v
        return m

    def _veterancy_mult(self, stat: str) -> float:
        rank = self._entity.progression.veterancy_rank
        if rank <= 0: return 1.0
        elif rank == 1: return 1.03 if stat in ("atk", "def") else 1.0
        elif rank == 2:
            if stat in ("atk", "def"): return 1.06
            return 1.05 if stat == "hp" else 1.0
        elif rank == 3:
            if stat in ("atk", "def", "hp"): return 1.10
            return 1.05 if stat == "spd" else 1.0
        return 1.15

    def _bravery_mult(self, stat: str) -> float:
        bravery = self._entity.mind.emotional_state.get("bravery", 0.5)
        if bravery > 0.8:
            if stat in ("atk", "spd"): return 1.1
        elif bravery < 0.3:
            if stat in ("atk", "def", "spd"): return 0.9
        return 1.0

class StatsProxyProgression:
    """Effective stats for Progression domain."""
    __slots__ = ("_entity",)
    def __init__(self, entity: Entity) -> None:
        self._entity = entity

    @property
    def level(self) -> int: return self._entity.progression.level
    @level.setter
    def level(self, v: int): self._entity.progression.level = v

    @property
    def gold(self) -> int: return self._entity.progression.gold
    @gold.setter
    def gold(self, v: int): self._entity.progression.gold = v

    @property
    def xp(self) -> int: return self._entity.progression.xp
    @xp.setter
    def xp(self, v: int): self._entity.progression.xp = v

    @property
    def xp_to_next(self) -> int: return self._entity.progression.xp_to_next
    @xp_to_next.setter
    def xp_to_next(self, v: int): self._entity.progression.xp_to_next = v

    @property
    def fame(self) -> int: return self._entity.progression.fame
    @fame.setter
    def fame(self, v: int): self._entity.progression.fame = v

    @property
    def stamina(self) -> int: return self._entity.progression.stamina
    @stamina.setter
    def stamina(self, v: int): self._entity.progression.stamina = v

    @property
    def max_stamina(self) -> int: return self._entity.progression.max_stamina
    @max_stamina.setter
    def max_stamina(self, v: int): self._entity.progression.max_stamina = v

    @property
    def stamina_ratio(self) -> float: return self._entity.progression.stamina_ratio
    @property
    def xp_ratio(self) -> float: return self._entity.progression.xp_ratio

    @property
    def xp_mult(self) -> float:
        from src.core.gameplay.attributes import derive_xp_multiplier
        attrs = self._entity.progression.attributes
        if not attrs: return 1.0
        return derive_xp_multiplier(attrs.wis, attrs.int_)

    # --- Attributes Shims ---
    @property
    def str(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.str_ if attrs else 5
    @str.setter
    def str(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.str_ = v

    @property
    def agi(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.agi if attrs else 5
    @agi.setter
    def agi(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.agi = v

    @property
    def vit(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.vit if attrs else 5
    @vit.setter
    def vit(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.vit = v

    @property
    def int(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.int_ if attrs else 5
    @int.setter
    def int(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.int_ = v

    @property
    def spi(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.spi if attrs else 5
    @spi.setter
    def spi(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.spi = v

    @property
    def wis(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.wis if attrs else 5
    @wis.setter
    def wis(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.wis = v

    @property
    def end(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.end if attrs else 5
    @end.setter
    def end(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.end = v

    @property
    def per(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.per if attrs else 5
    @per.setter
    def per(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.per = v

    @property
    def cha(self) -> int: 
        attrs = self._entity.progression.attributes
        return attrs.cha if attrs else 5
    @cha.setter
    def cha(self, v: int): 
        attrs = self._entity.progression.attributes
        if attrs: attrs.cha = v
