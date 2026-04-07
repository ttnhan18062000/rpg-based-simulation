"""EntityBuilder — fluent API for constructing Entity instances.

Refactored for AOA Stabilization:
- Direct population of Entity aspects (Identity, Spatial, Combat, Progression, Mind, Inventory).
- Supports full fluent API required by the test suite.
- Removed legacy Stats/StatsProxy dependencies.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any

from src.core.models.vectors import Vector2
from src.core.models.enums import AIState, EntityRole, Domain, Archetype
from src.core.gameplay.faction import Faction
from src.core.entities.entity import Entity
from src.core.aspects.identity import IdentityAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.aspects.combat import CombatAspect
from src.core.aspects.progression import ProgressionAspect
from src.core.aspects.inventory import InventoryAspect
from src.core.aspects.mind import MindAspect
from src.core.aspects.interaction import InteractionAspect
from src.core.gameplay.attributes import Attributes, AttributeCaps, recalc_derived_stats
from src.core.gameplay.classes import CLASS_DEFS, RACE_SKILLS, SkillInstance, available_class_skills, SKILL_DEFS

if TYPE_CHECKING:
    from src.platform.rng import DeterministicRNG

logger = logging.getLogger(__name__)

class EntityBuilder:
    """Fluent builder for Entity construction using AOA aspects."""

    def __init__(self, rng: DeterministicRNG, entity_id: int, tick: int = 0) -> None:
        self._rng = rng
        self._eid = entity_id
        self._tick = tick
        self._archetype: Archetype | None = None

        # Default data for aspects
        self._kind: str = "unknown"
        self._display_name: str = ""
        self._pos: Vector2 = Vector2(0, 0)
        self._home_pos: Vector2 | None = None
        self._leash_radius: int = 0
        self._ai_state: AIState = AIState.WANDER
        self._faction: Faction = Faction.HERO_GUILD
        self._role: EntityRole = EntityRole.MOB
        self._tier: int = 0
        self._generation: int = 1
        # Initialize _is_world_boss
        self._is_world_boss: bool = False
        self._difficulty_tier: int = 1
        
        # Combat stats
        self._hp: float = 20.0
        self._atk: int = 5
        self._def: int = 0
        self._spd: int = 10
        self._luck: int = 0
        self._crit_rate: float = 0.05
        self._crit_dmg: float = 1.5
        self._evasion: float = 0.0
        
        # Progression
        self._level: int = 1
        self._xp_to_next: int = 100
        self._gold: float = 0.0
        self._fame: int = 0
        self._hero_class: int = 0
        self._stamina: float = 20.0
        
        # Attributes
        self._attrs: Attributes | None = None
        self._caps: AttributeCaps | None = None
        
        # Skills & Inventory
        self._skills: list[SkillInstance] = []
        self._inventory: InventoryAspect | None = None
        self._traits: list[int] = []
        
        # Personality (RPG Traits) [PHASE 1]
        self._aggression: float | None = None
        self._greed: float | None = None
        self._caution: float | None = None
        self._loyalty: float | None = None
        self._ambition: float | None = None
        self._curiosity: float | None = None

    def kind(self, k: str) -> EntityBuilder:
        self._kind = k
        if k == "hero": self._stamina = 50.0
        return self

    def role(self, r: EntityRole) -> EntityBuilder:
        self._role = r
        return self

    def leash(self, radius: int) -> EntityBuilder:
        self._leash_radius = radius
        return self

    def at(self, pos: Vector2) -> EntityBuilder:
        self._pos = pos
        return self

    def home(self, pos: Vector2 | None) -> EntityBuilder:
        self._home_pos = pos
        return self

    def ai_state(self, state: AIState) -> EntityBuilder:
        self._ai_state = state
        return self

    def faction(self, f: Faction) -> EntityBuilder:
        self._faction = f
        return self

    def tier(self, t: int) -> EntityBuilder:
        self._tier = t
        return self

    def difficulty_tier(self, t: int) -> EntityBuilder:
        self._difficulty_tier = t
        return self

    def with_base_stats(self, hp: float = 20.0, atk: int = 5, def_: int = 0, spd: int = 10,
                        luck: int = 0, crit_rate: float = 0.05, crit_dmg: float = 1.5,
                        evasion: float = 0.0, level: int = 1, xp_to_next: int = 100, gold: float = 0.0) -> EntityBuilder:
        self._hp = hp
        self._atk = atk
        self._def = def_
        self._spd = spd
        self._luck = luck
        self._crit_rate = crit_rate
        self._crit_dmg = crit_dmg
        self._evasion = evasion
        self._level = level
        self._xp_to_next = xp_to_next
        self._gold = gold
        return self

    def with_randomized_stats(self) -> EntityBuilder:
        eid = self._eid
        self._hp += self._rng.next_int(Domain.SPAWN, eid, self._tick + 2, 0, 15)
        self._atk += self._rng.next_int(Domain.SPAWN, eid, self._tick + 3, 0, 4)
        return self

    def with_hero_class(self, hero_class: int) -> EntityBuilder:
        self._hero_class = int(hero_class)
        cdef = CLASS_DEFS.get(hero_class)
        if cdef:
            eid = self._eid
            rng = self._rng
            tick = self._tick
            # Base 5 + class bonus + rng(0,2)
            self._attrs = Attributes(
                str_=5 + cdef.str_bonus + rng.next_int(Domain.SPAWN, eid, tick + 10, 0, 2),
                agi=5 + cdef.agi_bonus + rng.next_int(Domain.SPAWN, eid, tick + 11, 0, 2),
                vit=5 + cdef.vit_bonus + rng.next_int(Domain.SPAWN, eid, tick + 12, 0, 2),
                int_=5 + cdef.int_bonus + rng.next_int(Domain.SPAWN, eid, tick + 13, 0, 2),
                spi=5 + cdef.spi_bonus + rng.next_int(Domain.SPAWN, eid, tick + 16, 0, 2),
                wis=5 + cdef.wis_bonus + rng.next_int(Domain.SPAWN, eid, tick + 14, 0, 2),
                end=5 + cdef.end_bonus + rng.next_int(Domain.SPAWN, eid, tick + 15, 0, 2),
                per=5 + cdef.per_bonus + rng.next_int(Domain.SPAWN, eid, tick + 17, 0, 2),
                cha=5 + cdef.cha_bonus + rng.next_int(Domain.SPAWN, eid, tick + 18, 0, 2),
            )
            self._caps = AttributeCaps(
                str_cap=15 + cdef.str_cap_bonus, agi_cap=15 + cdef.agi_cap_bonus,
                vit_cap=15 + cdef.vit_cap_bonus, int_cap=15 + cdef.int_cap_bonus,
                spi_cap=15 + cdef.spi_cap_bonus, wis_cap=15 + cdef.wis_cap_bonus,
                end_cap=15 + cdef.end_cap_bonus, per_cap=15 + cdef.per_cap_bonus,
                cha_cap=15 + cdef.cha_cap_bonus,
            )
        return self

    def with_attributes(self, **kwargs) -> EntityBuilder:
        """Manually set specific attribute values."""
        if self._attrs is None:
            self._attrs = Attributes()
        for k, v in kwargs.items():
            # Handle keywords likely to be passed in tests
            key = k
            if key == "str": key = "str_"
            if key == "int": key = "int_"
            if hasattr(self._attrs, key):
                setattr(self._attrs, key, int(v))
        return self

    def with_caps(self, **kwargs) -> EntityBuilder:
        """Manually set specific attribute cap values."""
        if self._caps is None:
            self._caps = AttributeCaps()
        for k, v in kwargs.items():
            key = k
            if not key.endswith("_cap"):
                key = f"{key}_cap"
            if hasattr(self._caps, key):
                setattr(self._caps, key, int(v))
        return self

    def with_mob_class(self, mob_class: int) -> EntityBuilder:
        return self.with_hero_class(mob_class)

    def with_identity(self, display_name: str = "", generation: int = 1) -> EntityBuilder:
        self._display_name = display_name
        self._generation = generation
        return self

    def with_mob_attributes(self, attr_base: int, tier: int) -> EntityBuilder:
        eid = self._eid
        rng = self._rng
        tick = self._tick
        self._attrs = Attributes(
            str_=max(1, attr_base + rng.next_int(Domain.SPAWN, eid, tick + 20, 0, 3)),
            agi=max(1, attr_base + rng.next_int(Domain.SPAWN, eid, tick + 21, 0, 3)),
            vit=max(1, attr_base + rng.next_int(Domain.SPAWN, eid, tick + 22, 0, 3)),
        )
        self._caps = AttributeCaps(str_cap=15 + tier * 5, agi_cap=15 + tier * 5)
        return self

    def with_race_attributes(self, attr_base: int, tier: int, r_str: int = 0, r_agi: int = 0, r_vit: int = 0,
                             r_spi: int = 0, r_per: int = 0, r_cha: int = 0) -> EntityBuilder:
        eid = self._eid
        rng = self._rng
        tick = self._tick
        self._attrs = Attributes(
            str_=max(1, attr_base + r_str + rng.next_int(Domain.SPAWN, eid, tick + 20, 0, 3)),
            agi=max(1, attr_base + r_agi + rng.next_int(Domain.SPAWN, eid, tick + 21, 0, 3)),
            vit=max(1, attr_base + r_vit + rng.next_int(Domain.SPAWN, eid, tick + 22, 0, 3)),
            spi=max(0, r_spi),
            per=max(0, r_per),
            cha=max(0, r_cha),
        )
        self._caps = AttributeCaps(str_cap=15 + tier * 5, agi_cap=15 + tier * 5)
        return self

    def with_race_skills(self, race: str) -> EntityBuilder:
        for sid in RACE_SKILLS.get(race, []):
            if sid in SKILL_DEFS: self._skills.append(SkillInstance(skill_id=sid))
        return self

    def with_class_skills(self, hero_class: int, level: int = 1) -> EntityBuilder:
        for sid in available_class_skills(hero_class, level):
            self._skills.append(SkillInstance(skill_id=sid))
        return self

    def with_inventory(self, max_slots: int = 10, max_weight: float = 50.0,
                        weapon: str | None = None, armor: str | None = None, accessory: str | None = None) -> EntityBuilder:
        self._inventory = InventoryAspect(
            max_slots=max_slots, max_weight=max_weight,
            weapon=weapon, armor=armor, accessory=accessory
        )
        return self

    def with_starting_items(self, items: list[str]) -> EntityBuilder:
        if self._inventory: self._inventory.items.extend(items)
        return self

    def with_existing_inventory(self, inv: Any) -> EntityBuilder:
        # Compatibility with legacy Inventory class if passed
        if hasattr(inv, "items"):
            self._inventory = InventoryAspect(
                items=list(inv.items), max_slots=inv.max_slots, max_weight=inv.max_weight,
                weapon=getattr(inv, "weapon", None), armor=getattr(inv, "armor", None)
            )
        return self

    def with_equipment(self, weapon: str | None = None, armor: str | None = None) -> EntityBuilder:
        if self._inventory:
            if weapon: self._inventory.weapon = weapon
            if armor: self._inventory.armor = armor
        return self

    def with_traits(self, race_prefix: str = "", trait_ids: list[str | int] | None = None) -> EntityBuilder:
        from src.core.entities.traits import assign_traits
        if trait_ids:
            from src.core.models.enums import TraitType
            self._traits = []
            for tid in trait_ids:
                if isinstance(tid, str):
                    upper_tid = tid.upper()
                    if hasattr(TraitType, upper_tid):
                        self._traits.append(TraitType[upper_tid])
                elif isinstance(tid, int):
                    try:
                        self._traits.append(TraitType(tid))
                    except ValueError:
                        logger.warning("Invalid TraitType integer: %d", tid)
        else:
            self._traits = assign_traits(self._rng, Domain.SPAWN, self._eid, self._tick, race_prefix=race_prefix)
        return self

    def with_archetype(self, arch: Archetype) -> EntityBuilder:
        self._archetype = arch
        return self

    def with_talents(self, race: str = "") -> EntityBuilder:
        # AOA MindAspect for now handles behavior, talents might be traits
        return self

    def with_personality(self, aggression: float | None = None, greed: float | None = None, 
                         caution: float | None = None, loyalty: float | None = None, 
                         ambition: float | None = None, curiosity: float | None = None) -> EntityBuilder:
        """Manually set RPG personality traits."""
        if aggression is not None: self._aggression = aggression
        if greed is not None: self._greed = greed
        if caution is not None: self._caution = caution
        if loyalty is not None: self._loyalty = loyalty
        if ambition is not None: self._ambition = ambition
        if curiosity is not None: self._curiosity = curiosity
        return self

    def with_home_storage(self) -> EntityBuilder:
        # AOA Entity doesn't have home_storage yet, but we'll accept the call
        return self

    def is_world_boss(self, boss: bool) -> EntityBuilder:
        self._is_world_boss = boss
        return self

    def _apply_archetype_to_personality(self, entity: Entity, mind: MindAspect):
        """Seeds personality traits based on the Identity archetype."""
        arch = entity.identity.archetype
        pers = mind.decision.personality
        pers.archetype = arch.name if hasattr(arch, "name") else str(arch)
        
        if arch == Archetype.BALANCED:
            pass # Default 0.5 for all
        elif arch == Archetype.CAUTIOUS_OPPORTUNIST:
            pers.caution, pers.greed, pers.aggression = 0.8, 0.7, 0.3
        elif arch == Archetype.GLORY_SEEKER:
            pers.ambition, pers.aggression, pers.caution = 0.9, 0.8, 0.2
        elif arch == Archetype.HONORABLE_DEFENDER:
            pers.loyalty, pers.caution, pers.aggression = 0.9, 0.6, 0.4
        elif arch == Archetype.GREEDY_SCAVENGER:
            pers.greed, pers.curiosity, pers.caution = 0.9, 0.7, 0.4
        elif arch == Archetype.BLOODTHIRSTY_SLAYER:
            pers.aggression, pers.ambition, pers.loyalty = 0.9, 0.7, 0.1
        elif arch == Archetype.COWARDLY_SURVIVOR:
            pers.caution, pers.aggression, pers.loyalty = 0.95, 0.1, 0.2

    def _seed_initial_motives(self, entity: Entity, mind: MindAspect):
        """Seeds 1-2 long-term motives based on archetype and role."""
        from src.core.aspects.mind import PersonalMotive
        arch = entity.identity.archetype
        
        motives = []
        if arch == Archetype.GREEDY_SCAVENGER:
            motives.append(PersonalMotive(motive_id="init_wealth", kind="build_wealth", priority=2.0))
        elif arch == Archetype.BLOODTHIRSTY_SLAYER:
            motives.append(PersonalMotive(motive_id="init_strength", kind="prove_strength", priority=2.5))
        elif arch == Archetype.HONORABLE_DEFENDER:
            motives.append(PersonalMotive(motive_id="init_faction", kind="serve_faction", priority=2.0))
        elif arch == Archetype.COWARDLY_SURVIVOR:
            motives.append(PersonalMotive(motive_id="init_safety", kind="seek_safety", priority=3.0))
        else:
            # Default for balanced/others
            if entity.kind == "hero":
                motives.append(PersonalMotive(motive_id="init_explore", kind="explore", priority=1.5))
            else:
                motives.append(PersonalMotive(motive_id="init_safety", kind="seek_safety", priority=1.0))
        
        mind.decision.motives = motives

    def build(self) -> Entity:
        entity = Entity(id=self._eid, kind=self._kind, next_act_at=float(self._tick))
        entity.identity = IdentityAspect(
            display_name=self._display_name or self._kind,
            faction=self._faction,
            role=self._role,
            tier=self._tier,
            difficulty_tier=self._difficulty_tier,
            generation=self._generation,
            traits=self._traits,
            is_world_boss=self._is_world_boss,
            archetype=self._archetype or Archetype.BALANCED
        )
        
        # Initialize Personality & Motives [PHASE 1]
        mind = MindAspect()
        entity.mind = mind
        
        # Apply Archetype Bias to Personality
        self._apply_archetype_to_personality(entity, mind)
        
        # Override with manual values if provided
        pers = mind.decision.personality
        if self._aggression is not None: pers.aggression = self._aggression
        if self._greed is not None: pers.greed = self._greed
        if self._caution is not None: pers.caution = self._caution
        if self._loyalty is not None: pers.loyalty = self._loyalty
        if self._ambition is not None: pers.ambition = self._ambition
        if self._curiosity is not None: pers.curiosity = self._curiosity
        
        # Seed Initial Motives
        self._seed_initial_motives(entity, mind)

        entity.spatial = SpatialAspect(
            pos=self._pos,
            home_pos=self._home_pos,
            leash_radius=self._leash_radius,
            difficulty_tier=self._difficulty_tier
        )
        entity.combat = CombatAspect(
            hp=self._hp,
            max_hp=self._hp,
            atk_base=self._atk,
            def_base=self._def,
            spd_base=self._spd,
            luck=self._luck,
            crit_rate=self._crit_rate,
            crit_dmg=self._crit_dmg,
            evasion=self._evasion
        )
        entity.progression = ProgressionAspect(level=self._level, xp_to_next=self._xp_to_next, gold=self._gold, fame=self._fame, hero_class=self._hero_class, stamina=self._stamina, max_stamina=self._stamina, skills=self._skills, attributes=self._attrs or Attributes(), attribute_caps=self._caps or AttributeCaps())
        entity.mind = mind
        entity.mind.decision.ai_state = self._ai_state
        entity.interaction = InteractionAspect()
        if self._inventory: entity.inventory = self._inventory
        
        recalc_derived_stats(entity, entity.progression.attributes)
        # Ensure built entity starts at full health/stamina after attribute derivation
        entity.combat.hp = entity.combat.max_hp
        entity.progression.stamina = entity.progression.max_stamina
        
        entity.model_post_init(None)
        return entity
