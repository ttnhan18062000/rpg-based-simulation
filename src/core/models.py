"""Core data models: Vector2, Stats, Entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.core.enums import AIState, DamageType, Element, EnemyTier, EntityRole, TraitType
from src.core.faction import Faction

if TYPE_CHECKING:
    from src.core.attributes import Attributes, AttributeCaps
    from src.core.classes import SkillInstance
    from src.core.effects import StatusEffect
    from src.core.quests import Quest


@dataclass(frozen=True, slots=True)
class Vector2:
    """Immutable 2D integer coordinate."""

    x: int = 0
    y: int = 0

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(self.x - other.x, self.y - other.y)

    def manhattan(self, other: Vector2) -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def __repr__(self) -> str:
        return f"({self.x}, {self.y})"


# Direction offsets mapped to Direction enum values
DIRECTION_OFFSETS: dict[int, Vector2] = {
    0: Vector2(0, -1),  # NORTH
    1: Vector2(1, 0),   # EAST
    2: Vector2(0, 1),   # SOUTH
    3: Vector2(-1, 0),  # WEST
}


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
    # Values > 1.0 = weakness, < 1.0 = resistance, 0.0 = immune
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
    fame: int = 0           # NEW: Hero prestige
    stamina: int = 50
    max_stamina: int = 50

    # --- Secondary / non-combat ---
    vision_range: int = 6       # Effective vision (base + PER derived)
    loot_bonus: float = 1.0     # Loot drop chance multiplier
    trade_bonus: float = 1.0    # Buy discount / sell markup
    interaction_speed: float = 1.0  # Harvest/craft/interact speed mult
    rest_efficiency: float = 1.0    # Regen speed multiplier
    hp_regen: float = 1.0       # HP per rest tick
    cooldown_reduction: float = 1.0  # Skill cooldown mult (lower=faster)

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


@dataclass(slots=True)
class Entity:
    """A simulation entity — character, generator, or any world actor."""

    id: int
    kind: str
    pos: Vector2
    display_name: str = ""
    death_count: int = 0
    generation: int = 1
    hero_familiarity: dict[int, float] = field(default_factory=dict)
    stats: Stats = field(default_factory=Stats)
    ai_state: AIState = AIState.IDLE
    faction: Faction = Faction.HERO_GUILD
    role: EntityRole = EntityRole.MOB
    next_act_at: float = 0.0
    memory: dict[int, Vector2] = field(default_factory=dict)
    home_pos: Vector2 | None = None
    leash_radius: int = 0
    chase_ticks: int = 0
    tier: int = EnemyTier.BASIC
    inventory: Inventory | None = None
    terrain_memory: dict[tuple[int, int], int] = field(default_factory=dict)
    entity_memory: list[dict] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    effects: list[StatusEffect] = field(default_factory=list)
    loot_progress: int = 0
    known_recipes: list[str] = field(default_factory=list)
    craft_target: str | None = None
    # RPG attributes
    attributes: Attributes | None = None
    attribute_caps: AttributeCaps | None = None
    # Class & skills
    hero_class: int = 0                 # HeroClass enum value (0 = NONE)
    skills: list[SkillInstance] = field(default_factory=list)
    class_mastery: float = 0.0          # 0.0 to 100.0
    # Progression Depth (epic-18)
    veterancy_points: int = 0
    veterancy_rank: int = 0  # VeterancyRank.GREEN
    # Heuristics (epic-18 phase G/C)
    boredom_multipliers: dict[str, float] = field(default_factory=dict)
    consecutive_idle_ticks: int = 0
    talents: list[str] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)  # NEW: Hero titles
    is_world_boss: bool = False                      # NEW: Boss flag
    weakness: str = ""
    # Quests
    quests: list[Quest] = field(default_factory=list)
    # Traits (Rimworld-style discrete personality traits)
    traits: list[int] = field(default_factory=list)  # list of TraitType values
    # Home storage (heroes only)
    home_storage: HomeStorage | None = None
    # Last AI action reason (for goals display)
    last_reason: str = ""
    # Engagement lock: ticks spent adjacent to a hostile (for anti-kite)
    engaged_ticks: int = 0
    # Region (epic-15)
    region_id: str = ""
    difficulty_tier: int = 1
    current_region_id: str = ""  # Tracks which region the entity is currently standing in
    combat_target_id: int | None = None  # Current combat target for visualization
    # Aggro / threat system (epic-05 F3)
    threat_table: dict[int, float] = field(default_factory=dict)  # attacker_id → threat score
    # A* path cache (epic-09)
    cached_path: list | None = field(default=None, repr=False)
    cached_path_target: object | None = field(default=None, repr=False)

    @property
    def alive(self) -> bool:
        return self.stats.alive

    # -- effect helpers --

    def _effect_mult(self, attr: str) -> float:
        """Aggregate multiplicative modifier from all active effects."""
        m = 1.0
        for eff in self.effects:
            m *= getattr(eff, attr, 1.0)
        return m

    def has_effect(self, effect_type: int) -> bool:
        return any(e.effect_type == effect_type for e in self.effects)

    def remove_effects_by_type(self, effect_type: int) -> None:
        self.effects = [e for e in self.effects if e.effect_type != effect_type]

    # -- effective stats (equipment + effects) --
    
    def _veterancy_mult(self, stat: str) -> float:
        """Multiplier based on veterancy rank (0=Green to 4=Legend)."""
        if self.veterancy_rank == 0:  # GREEN
            return 1.0
        elif self.veterancy_rank == 1:  # BLOODED
            if stat in ("atk", "def"): return 1.03
            return 1.0
        elif self.veterancy_rank == 2:  # VETERAN
            if stat in ("atk", "def"): return 1.06
            if stat == "hp": return 1.05
            return 1.0
        elif self.veterancy_rank == 3:  # ELITE
            if stat in ("atk", "def", "hp"): return 1.10
            if stat == "spd": return 1.05
            return 1.0
        else:  # LEGEND
            return 1.15

    def effective_atk(self) -> int:
        """ATK including equipment bonuses, effects, and veterancy."""
        base = self.stats.atk
        if self.inventory:
            base += int(self.inventory.equipment_bonus("atk_bonus"))
        return max(int(base * self._effect_mult("atk_mult") * self._veterancy_mult("atk")), 1)

    def effective_def(self) -> int:
        """DEF including equipment bonuses, effects, and veterancy."""
        base = self.stats.def_
        if self.inventory:
            base += int(self.inventory.equipment_bonus("def_bonus"))
        return max(int(base * self._effect_mult("def_mult") * self._veterancy_mult("def")), 0)

    def effective_spd(self) -> int:
        """SPD including equipment bonuses, effects, and veterancy."""
        base = self.stats.spd
        if self.inventory:
            base += int(self.inventory.equipment_bonus("spd_bonus"))
        return max(int(base * self._effect_mult("spd_mult") * self._veterancy_mult("spd")), 1)

    def effective_crit_rate(self) -> float:
        """Crit rate including equipment bonuses and status effects."""
        base = self.stats.crit_rate
        if self.inventory:
            base += float(self.inventory.equipment_bonus("crit_rate_bonus"))
        return min(base * self._effect_mult("crit_mult"), 1.0)

    def effective_evasion(self) -> float:
        """Evasion including equipment bonuses and status effects."""
        base = self.stats.evasion
        if self.inventory:
            base += float(self.inventory.equipment_bonus("evasion_bonus"))
        return min(base * self._effect_mult("evasion_mult"), 0.75)

    def effective_max_hp(self) -> int:
        """Max HP including equipment bonuses and veterancy."""
        base = self.stats.max_hp
        if self.inventory:
            base += int(self.inventory.equipment_bonus("max_hp_bonus"))
        return max(int(base * self._veterancy_mult("hp")), 1)

    def effective_matk(self) -> int:
        """MATK including equipment bonuses and status effects."""
        base = self.stats.matk
        if self.inventory:
            base += int(self.inventory.equipment_bonus("matk_bonus"))
        return max(int(base * self._effect_mult("matk_mult")), 0)

    def effective_mdef(self) -> int:
        """MDEF including equipment bonuses and status effects."""
        base = self.stats.mdef
        if self.inventory:
            base += int(self.inventory.equipment_bonus("mdef_bonus"))
        return max(int(base * self._effect_mult("mdef_mult")), 0)

    def elemental_vulnerability(self, element: int) -> float:
        """Get vulnerability multiplier for an element. >1 = weak, <1 = resist."""
        if element == Element.NONE:
            return 1.0
        return self.stats.elem_vuln.get(element, 1.0)

    def has_trait(self, trait: int) -> bool:
        """Check if entity has a specific TraitType."""
        return trait in self.traits

    def copy(self) -> Entity:
        """Deep copy for snapshot generation."""
        return Entity(
            id=self.id,
            kind=self.kind,
            pos=self.pos,
            stats=self.stats.copy(),
            ai_state=self.ai_state,
            faction=self.faction,
            role=self.role,
            next_act_at=self.next_act_at,
            memory=dict(self.memory),
            home_pos=self.home_pos,
            leash_radius=self.leash_radius,
            chase_ticks=self.chase_ticks,
            tier=self.tier,
            inventory=self.inventory.copy() if self.inventory else None,
            terrain_memory=dict(self.terrain_memory),
            entity_memory=[dict(em) for em in self.entity_memory],
            goals=list(self.goals),
            last_reason=self.last_reason,
            engaged_ticks=self.engaged_ticks,
            effects=[e.copy() for e in self.effects],
            loot_progress=self.loot_progress,
            known_recipes=list(self.known_recipes),
            craft_target=self.craft_target,
            attributes=self.attributes.copy() if self.attributes else None,
            attribute_caps=self.attribute_caps.copy() if self.attribute_caps else None,
            hero_class=self.hero_class,
            skills=[s.copy() for s in self.skills],
            class_mastery=self.class_mastery,
            quests=[q.copy() for q in self.quests],
            traits=list(self.traits),
            home_storage=self.home_storage.copy() if self.home_storage else None,
            combat_target_id=self.combat_target_id,
            threat_table=dict(self.threat_table),
        )

@dataclass(slots=True)
class Inventory:
    """Mutable item container with slot and weight limits."""
    items: list[str] = field(default_factory=list)
    max_slots: int = 8
    max_weight: float = 20.0
    weapon: str | None = None
    armor: str | None = None
    accessory: str | None = None

    @property
    def current_weight(self) -> float:
        total = 0.0
        from src.core.item_registry import ITEM_REGISTRY
        for iid in self.items:
            t = ITEM_REGISTRY.get(iid)
            if t: total += t.weight
        for slot_id in (self.weapon, self.armor, self.accessory):
            if slot_id:
                t = ITEM_REGISTRY.get(slot_id)
                if t: total += t.weight
        return total

    @property
    def used_slots(self) -> int: return len(self.items)
    
    def can_add(self, item_id: str) -> bool:
        if self.used_slots >= self.max_slots: return False
        from src.core.item_registry import ITEM_REGISTRY
        t = ITEM_REGISTRY.get(item_id)
        if t is None: return False
        return self.current_weight + t.weight <= self.max_weight

    def add_item(self, item_id: str) -> bool:
        if not self.can_add(item_id): return False
        self.items.append(item_id)
        return True

    def remove_item(self, item_id: str) -> bool:
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False

    def equip(self, item_id: str) -> bool:
        from src.core.item_registry import ITEM_REGISTRY
        from src.core.items import ItemType
        t = ITEM_REGISTRY.get(item_id)
        if t is None or item_id not in self.items: return False
        if t.item_type == ItemType.WEAPON:
            if self.weapon: self.items.append(self.weapon)
            self.weapon = item_id
        elif t.item_type == ItemType.ARMOR:
            if self.armor: self.items.append(self.armor)
            self.armor = item_id
        elif t.item_type == ItemType.ACCESSORY:
            if self.accessory: self.items.append(self.accessory)
            self.accessory = item_id
        else: return False
        self.items.remove(item_id)
        return True

    def auto_equip_best(self, item_id: str) -> bool:
        from src.core.item_registry import ITEM_REGISTRY
        from src.core.items import ItemType, _item_power
        t = ITEM_REGISTRY.get(item_id)
        if t is None or item_id not in self.items: return False
        if t.item_type not in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY): return False
        if t.item_type == ItemType.WEAPON: current_id = self.weapon
        elif t.item_type == ItemType.ARMOR: current_id = self.armor
        else: current_id = self.accessory
        if current_id is None: return self.equip(item_id)
        current_t = ITEM_REGISTRY.get(current_id)
        if current_t is None or _item_power(t) > _item_power(current_t):
            return self.equip(item_id)
        return False

    def copy(self) -> Inventory:
        return Inventory(items=list(self.items), max_slots=self.max_slots, max_weight=self.max_weight, weapon=self.weapon, armor=self.armor, accessory=self.accessory)

    def equipment_bonus(self, stat: str) -> int | float:
        total = 0
        from src.core.items import ITEM_REGISTRY
        for slot_id in (self.weapon, self.armor, self.accessory):
            if slot_id:
                t = ITEM_REGISTRY.get(slot_id)
                if t: total += getattr(t, stat, 0)
        return total

    def get_all_item_ids(self) -> list[str]:
        result = list(self.items)
        if self.weapon: result.append(self.weapon)
        if self.armor: result.append(self.armor)
        if self.accessory: result.append(self.accessory)
        return result


@dataclass(slots=True)
class HomeStorage:
    """Large persistent storage at the hero's home building."""
    items: list[str] = field(default_factory=list)
    max_slots: int = 30
    level: int = 0  # upgrade tier (0, 1, 2)

    def copy(self) -> HomeStorage:
        return HomeStorage(
            items=list(self.items),
            max_slots=self.max_slots,
            level=self.level,
        )


@dataclass(slots=True)
class TreasureChest:
    """A respawning treasure chest placed in the world."""
    chest_id: int
    pos: Vector2
    tier: int = 1
    looted: bool = False
    respawn_at: int = -1
    guard_entity_id: int | None = None

    def copy(self) -> TreasureChest:
        return TreasureChest(
            chest_id=self.chest_id,
            pos=self.pos,
            tier=self.tier,
            looted=self.looted,
            respawn_at=self.respawn_at,
            guard_entity_id=self.guard_entity_id,
        )
