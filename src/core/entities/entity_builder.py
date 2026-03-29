"""EntityBuilder — fluent API for constructing Entity instances.

Consolidates duplicated spawn logic from __main__.py, engine_manager.py,
and generator.py into a single, chainable builder.

Usage::

    hero = (
        EntityBuilder(rng, world.allocate_entity_id(), tick=0)
        .kind("hero")
        .at(town_center)
        .with_base_stats(hp=50, atk=10, def_=3, spd=10)
        .with_hero_class(HeroClass.WARRIOR)
        .with_faction(Faction.HERO_GUILD)
        .with_inventory(max_slots=20, max_weight=100, weapon="iron_sword", armor="leather_vest")
        .with_starting_items(["small_hp_potion"] * 3)
        .with_traits(race_prefix="hero")
        .build()
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.gameplay.attributes import Attributes, AttributeCaps, recalc_derived_stats
from src.core.gameplay.classes import (
    CLASS_DEFS, RACE_SKILLS, SKILL_DEFS, SkillInstance,
    available_class_skills,
)
from src.core.models.enums import AIState, Domain, EntityRole
from src.core.gameplay.faction import Faction
from src.core.gameplay.items.items import HomeStorage
from src.core.entities.entity import Entity, Stats, Vector2, Inventory
from src.core.entities.traits import assign_traits

if TYPE_CHECKING:
    from src.platform.rng import DeterministicRNG


class EntityBuilder:
    """Fluent builder for Entity construction.

    All ``with_*`` methods return ``self`` for chaining.
    Call ``build()`` to produce the final Entity.
    """

    __slots__ = (
        "_rng", "_eid", "_tick",
        "_kind", "_pos", "_ai_state", "_faction", "_role",
        "_home_pos", "_leash_radius", "_tier",
        "_base_hp", "_base_atk", "_base_def", "_base_spd",
        "_luck", "_crit_rate", "_crit_dmg", "_evasion",
        "_level", "_xp", "_xp_to_next", "_gold",
        "_hero_class", "_class_def",
        "_attrs", "_caps",
        "_skills", "_inventory", "_home_storage", "_traits",
        "_attr_base", "_attr_randomness",
        "_talents", "_weakness",
        "_display_name", "_generation", "_death_count",
        "_fame", "_titles", "_is_world_boss",
    )

    def __init__(
        self,
        rng: DeterministicRNG,
        entity_id: int,
        tick: int = 0,
    ) -> None:
        self._rng = rng
        self._eid = entity_id
        self._tick = tick

        # Defaults
        self._kind: str = "unknown"
        self._pos: Vector2 = Vector2(0, 0)
        self._ai_state: AIState = AIState.WANDER
        self._faction: Faction = Faction.HERO_GUILD
        self._role: EntityRole = EntityRole.MOB
        self._home_pos: Vector2 | None = None
        self._leash_radius: int = 0
        self._tier: int = 0

        self._base_hp: int = 20
        self._base_atk: int = 5
        self._base_def: int = 0
        self._base_spd: int = 10
        self._luck: int = 0
        self._crit_rate: float = 0.05
        self._crit_dmg: float = 1.5
        self._evasion: float = 0.0
        self._level: int = 1
        self._xp: int = 0
        self._xp_to_next: int = 100
        self._gold: int = 0
        self._fame: int = 0
        self._titles: list[str] = []
        self._is_world_boss: bool = False

        self._hero_class: int | None = None
        self._class_def = None
        self._attrs: Attributes | None = None
        self._caps: AttributeCaps | None = None
        self._skills: list[SkillInstance] = []
        self._inventory: Inventory | None = None
        self._home_storage: HomeStorage | None = None
        self._traits: list[int] = []
        self._talents: list[str] | None = None
        self._weakness: str | None = None
        self._display_name: str = ""
        self._generation: int = 1
        self._death_count: int = 0

    # -------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------

    def kind(self, kind_str: str) -> EntityBuilder:
        self._kind = kind_str
        return self

    def with_identity(self, display_name: str = "", generation: int = 1, death_count: int = 0) -> EntityBuilder:
        self._display_name = display_name
        self._generation = generation
        self._death_count = death_count
        return self

    def at(self, pos: Vector2) -> EntityBuilder:
        self._pos = pos
        return self

    def home(self, pos: Vector2 | None) -> EntityBuilder:
        self._home_pos = pos
        return self

    def leash(self, radius: int) -> EntityBuilder:
        self._leash_radius = radius
        return self

    def ai_state(self, state: AIState) -> EntityBuilder:
        self._ai_state = state
        return self

    def faction(self, f: Faction) -> EntityBuilder:
        self._faction = f
        return self

    def role(self, r: EntityRole) -> EntityBuilder:
        self._role = r
        return self

    def tier(self, t: int) -> EntityBuilder:
        self._tier = t
        return self

    def is_world_boss(self, val: bool) -> EntityBuilder:
        self._is_world_boss = val
        return self

    # -------------------------------------------------------------------
    # Base stats
    # -------------------------------------------------------------------

    def with_base_stats(
        self, *,
        hp: int = 20, atk: int = 5, def_: int = 0, spd: int = 10,
        luck: int = 0, crit_rate: float = 0.05, crit_dmg: float = 1.5,
        evasion: float = 0.0, level: int = 1, xp_to_next: int = 100,
        gold: int = 0, fame: int = 0,
    ) -> EntityBuilder:
        self._base_hp = hp
        self._base_atk = atk
        self._base_def = def_
        self._base_spd = spd
        self._luck = luck
        self._crit_rate = crit_rate
        self._crit_dmg = crit_dmg
        self._evasion = evasion
        self._level = level
        self._xp_to_next = xp_to_next
        self._gold = gold
        self._fame = fame
        return self

    def titles(self, t_list: list[str]) -> EntityBuilder:
        self._titles = list(t_list)
        return self

    def with_randomized_stats(self) -> EntityBuilder:
        """Add RNG variance to base stats (typical for hero spawns)."""
        eid = self._eid
        self._base_hp += self._rng.next_int(Domain.SPAWN, eid, self._tick + 2, 0, 15)
        self._base_atk += self._rng.next_int(Domain.SPAWN, eid, self._tick + 3, 0, 4)
        self._base_spd += self._rng.next_int(Domain.SPAWN, eid, self._tick + 4, 0, 3)
        self._base_def += self._rng.next_int(Domain.SPAWN, eid, self._tick + 5, 0, 2)
        return self

    # -------------------------------------------------------------------
    # Hero class + attributes
    # -------------------------------------------------------------------

    def with_attributes(self, **kwargs) -> EntityBuilder:
        """Manually set or override specific attributes."""
        if self._attrs is None:
            self._attrs = Attributes(str_=5, agi=5, vit=5, int_=5, spi=5, wis=5, end=5, per=5, cha=5)
        for k, v in kwargs.items():
            if hasattr(self._attrs, k):
                setattr(self._attrs, k, v)
        return self

    def with_caps(self, **kwargs) -> EntityBuilder:
        """Manually set or override specific attribute caps."""
        if self._caps is None:
            self._caps = AttributeCaps()
        for k, v in kwargs.items():
            if hasattr(self._caps, k):
                setattr(self._caps, k, v)
        return self

    def with_hero_class(self, hero_class) -> EntityBuilder:
        """Set hero class and derive attributes from class definition."""
        self._hero_class = int(hero_class)
        self._class_def = CLASS_DEFS.get(hero_class)
        if self._class_def:
            cdef = self._class_def
            eid = self._eid
            rng = self._rng
            tick = self._tick
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

    def with_mob_class(self, mob_class) -> EntityBuilder:
        """Set mob archetype class."""
        self._hero_class = int(mob_class)
        self._class_def = CLASS_DEFS.get(mob_class)
        return self

    def with_mob_attributes(self, attr_base: int, tier: int) -> EntityBuilder:
        """Generate mob-style attributes scaled by tier + class bonuses."""
        eid = self._eid
        rng = self._rng
        tick = self._tick
        cd = self._class_def
        c_str = cd.str_bonus if cd else 0
        c_agi = cd.agi_bonus if cd else 0
        c_vit = cd.vit_bonus if cd else 0
        c_int = cd.int_bonus if cd else 0
        c_spi = cd.spi_bonus if cd else 0
        c_wis = cd.wis_bonus if cd else 0
        c_end = cd.end_bonus if cd else 0
        c_per = cd.per_bonus if cd else 0
        c_cha = cd.cha_bonus if cd else 0
        self._attrs = Attributes(
            str_=max(1, attr_base + c_str + rng.next_int(Domain.SPAWN, eid, tick + 20, 0, 3)),
            agi=max(1, attr_base + c_agi + rng.next_int(Domain.SPAWN, eid, tick + 21, 0, 3)),
            vit=max(1, attr_base + c_vit + rng.next_int(Domain.SPAWN, eid, tick + 22, 0, 3)),
            int_=max(1, attr_base - 2 + c_int + rng.next_int(Domain.SPAWN, eid, tick + 23, 0, 2)),
            spi=max(1, attr_base - 2 + c_spi + rng.next_int(Domain.SPAWN, eid, tick + 26, 0, 2)),
            wis=max(1, attr_base - 2 + c_wis + rng.next_int(Domain.SPAWN, eid, tick + 24, 0, 2)),
            end=max(1, attr_base + c_end + rng.next_int(Domain.SPAWN, eid, tick + 25, 0, 3)),
            per=max(1, attr_base - 1 + c_per + rng.next_int(Domain.SPAWN, eid, tick + 27, 0, 2)),
            cha=max(1, attr_base - 3 + c_cha + rng.next_int(Domain.SPAWN, eid, tick + 28, 0, 2)),
        )
        cc_str = cd.str_cap_bonus if cd else 0
        cc_agi = cd.agi_cap_bonus if cd else 0
        cc_vit = cd.vit_cap_bonus if cd else 0
        cc_int = cd.int_cap_bonus if cd else 0
        cc_spi = cd.spi_cap_bonus if cd else 0
        cc_wis = cd.wis_cap_bonus if cd else 0
        cc_end = cd.end_cap_bonus if cd else 0
        cc_per = cd.per_cap_bonus if cd else 0
        cc_cha = cd.cha_cap_bonus if cd else 0
        self._caps = AttributeCaps(
            str_cap=15 + tier * 5 + cc_str, agi_cap=15 + tier * 5 + cc_agi,
            vit_cap=15 + tier * 5 + cc_vit, int_cap=10 + tier * 3 + cc_int,
            spi_cap=10 + tier * 3 + cc_spi, wis_cap=10 + tier * 3 + cc_wis,
            end_cap=15 + tier * 5 + cc_end, per_cap=10 + tier * 3 + cc_per,
            cha_cap=8 + tier * 2 + cc_cha,
        )
        return self

    def with_race_attributes(
        self, attr_base: int, tier: int,
        r_str: int = 0, r_agi: int = 0, r_vit: int = 0,
        r_spi: int = 0, r_per: int = 0, r_cha: int = 0,
    ) -> EntityBuilder:
        """Generate race-specific attributes with racial + class modifiers."""
        eid = self._eid
        rng = self._rng
        tick = self._tick
        cd = self._class_def
        c_str = cd.str_bonus if cd else 0
        c_agi = cd.agi_bonus if cd else 0
        c_vit = cd.vit_bonus if cd else 0
        c_int = cd.int_bonus if cd else 0
        c_spi = cd.spi_bonus if cd else 0
        c_wis = cd.wis_bonus if cd else 0
        c_end = cd.end_bonus if cd else 0
        c_per = cd.per_bonus if cd else 0
        c_cha = cd.cha_bonus if cd else 0
        self._attrs = Attributes(
            str_=max(1, attr_base + r_str + c_str + rng.next_int(Domain.SPAWN, eid, tick + 20, 0, 3)),
            agi=max(1, attr_base + r_agi + c_agi + rng.next_int(Domain.SPAWN, eid, tick + 21, 0, 3)),
            vit=max(1, attr_base + r_vit + c_vit + rng.next_int(Domain.SPAWN, eid, tick + 22, 0, 3)),
            int_=max(1, attr_base - 2 + c_int + rng.next_int(Domain.SPAWN, eid, tick + 23, 0, 2)),
            spi=max(1, attr_base - 2 + r_spi + c_spi + rng.next_int(Domain.SPAWN, eid, tick + 26, 0, 2)),
            wis=max(1, attr_base - 2 + c_wis + rng.next_int(Domain.SPAWN, eid, tick + 24, 0, 2)),
            end=max(1, attr_base + c_end + rng.next_int(Domain.SPAWN, eid, tick + 25, 0, 3)),
            per=max(1, attr_base - 1 + r_per + c_per + rng.next_int(Domain.SPAWN, eid, tick + 27, 0, 2)),
            cha=max(1, attr_base - 3 + r_cha + c_cha + rng.next_int(Domain.SPAWN, eid, tick + 28, 0, 2)),
        )
        cc_str = cd.str_cap_bonus if cd else 0
        cc_agi = cd.agi_cap_bonus if cd else 0
        cc_vit = cd.vit_cap_bonus if cd else 0
        cc_int = cd.int_cap_bonus if cd else 0
        cc_spi = cd.spi_cap_bonus if cd else 0
        cc_wis = cd.wis_cap_bonus if cd else 0
        cc_end = cd.end_cap_bonus if cd else 0
        cc_per = cd.per_cap_bonus if cd else 0
        cc_cha = cd.cha_cap_bonus if cd else 0
        self._caps = AttributeCaps(
            str_cap=15 + tier * 5 + cc_str, agi_cap=15 + tier * 5 + cc_agi,
            vit_cap=15 + tier * 5 + cc_vit, int_cap=10 + tier * 3 + cc_int,
            spi_cap=10 + tier * 3 + cc_spi, wis_cap=10 + tier * 3 + cc_wis,
            end_cap=15 + tier * 5 + cc_end, per_cap=10 + tier * 3 + cc_per,
            cha_cap=8 + tier * 2 + cc_cha,
        )
        return self

    # -------------------------------------------------------------------
    # Skills
    # -------------------------------------------------------------------

    def with_race_skills(self, race: str) -> EntityBuilder:
        """Add skills from the race skill table."""
        for sid in RACE_SKILLS.get(race, []):
            if sid in SKILL_DEFS:
                self._skills.append(SkillInstance(skill_id=sid))
        return self

    def with_class_skills(self, hero_class, level: int = 1) -> EntityBuilder:
        """Add class skills available at the given level."""
        for sid in available_class_skills(hero_class, level):
            self._skills.append(SkillInstance(skill_id=sid))
        return self

    # -------------------------------------------------------------------
    # Inventory
    # -------------------------------------------------------------------

    def with_inventory(
        self, *,
        max_slots: int = 10,
        max_weight: int = 50,
        weapon: str | None = None,
        armor: str | None = None,
        accessory: str | None = None,
    ) -> EntityBuilder:
        self._inventory = Inventory(
            items=[], max_slots=max_slots, max_weight=max_weight,
            weapon=weapon, armor=armor, accessory=accessory,
        )
        return self

    def with_starting_items(self, item_ids: list[str]) -> EntityBuilder:
        """Add starting items."""
        if self._inventory:
            for item_id in item_ids:
                self._inventory.add_item(item_id)
        return self

    def with_existing_inventory(self, inv: Inventory) -> EntityBuilder:
        self._inventory = inv
        return self

    def with_equipment(
        self, *,
        weapon: str | None = None,
        armor: str | None = None,
        accessory: str | None = None,
    ) -> EntityBuilder:
        if self._inventory:
            if weapon:
                self._inventory.weapon = weapon
            if armor:
                self._inventory.armor = armor
            if accessory:
                self._inventory.accessory = accessory
        return self

    # -------------------------------------------------------------------
    # Traits + Talents
    # -------------------------------------------------------------------

    def with_home_storage(self, max_slots: int = 30) -> EntityBuilder:
        self._home_storage = HomeStorage(max_slots=max_slots)
        return self

    def with_traits(self, race_prefix: str = "", trait_ids: list[int] | None = None) -> EntityBuilder:
        if trait_ids is not None:
            self._traits = trait_ids
        else:
            self._traits = assign_traits(
                self._rng, Domain.SPAWN, self._eid, self._tick,
                race_prefix=race_prefix,
            )
        return self

    def with_talents(self, race: str = "") -> EntityBuilder:
        """Assign 2 random talents and 1 weakness."""
        race = race or self._kind
        attributes = ["str", "agi", "vit", "int", "spi", "wis", "end", "per", "cha"]
        weights = [1.0] * 9
        if "orc" in race: weights[0] = 5.0; weights[2] = 5.0
        elif "wolf" in race: weights[1] = 5.0; weights[7] = 3.0
        elif "undead" in race: weights[2] = 5.0; weights[4] = 3.0
        
        t1 = self._rng.weighted_choice(Domain.SPAWN, self._eid, self._tick + 30, attributes, weights)
        remaining = [a for a in attributes if a != t1]
        rem_weights = [weights[attributes.index(a)] for a in remaining]
        t2 = self._rng.weighted_choice(Domain.SPAWN, self._eid, self._tick + 31, remaining, rem_weights)
        self._talents = [t1, t2]
        
        remaining_weak = [a for a in attributes if a not in self._talents]
        inv_weights = [1.0 / weights[attributes.index(a)] for a in remaining_weak]
        self._weakness = self._rng.weighted_choice(Domain.SPAWN, self._eid, self._tick + 32, remaining_weak, inv_weights)
        
        return self

    # -------------------------------------------------------------------
    # Build
    # -------------------------------------------------------------------

    def _init_aspects(self) -> dict[str, Any]:
        """Create Aspect instances from builder data."""
        from src.core.aspects.identity import IdentityAspect
        from src.core.aspects.spatial import SpatialAspect
        from src.core.aspects.combat import CombatAspect
        from src.core.aspects.progression import ProgressionAspect
        from src.core.aspects.inventory import InventoryAspect
        from src.core.aspects.mind import MindAspect
        
        stamina = 50 if self._kind == "hero" else 30
        
        combat = CombatAspect(
            hp=self._base_hp, max_hp=self._base_hp,
            atk=self._base_atk, def_=self._base_def, spd=self._base_spd,
            luck=self._luck, crit_rate=self._crit_rate, crit_dmg=self._crit_dmg,
            evasion=self._evasion,
        )
        
        prog = ProgressionAspect(
            level=self._level, xp_to_next=self._xp_to_next,
            gold=self._gold, fame=self._fame,
            stamina=stamina, max_stamina=stamina,
            hero_class=self._hero_class or 0,
            skills=self._skills,
            attributes=self._attrs,
            attribute_caps=self._caps,
            talents=self._talents or [],
        )
        
        if self._attrs:
            from src.core.gameplay.attributes import recalc_derived_stats
            recalc_derived_stats(combat, self._attrs)
            combat.hp = combat.max_hp
        
        # logger already imported or need to add it?
        # Check imports in entity_builder.py
        identity = IdentityAspect(
            display_name=self._display_name or self._kind,
            faction=self._faction,
            role=self._role,
            tier=self._tier,
            traits=list(self._traits),
            is_world_boss=self._is_world_boss,
            death_count=self._death_count,
            generation=self._generation,
        )

        aspects = {
            "identity": identity,
            "spatial": SpatialAspect(
                pos=self._pos,
                region_id="unknown", 
                difficulty_tier=0, 
                home_pos=self._home_pos,
                leash_radius=self._leash_radius,
            ),
            "combat": combat,
            "progression": prog,
            "mind": MindAspect(
                ai_state=self._ai_state,
                next_act_at=self._tick or 0
            ),
        }

        # Only add inventory if configured
        if self._inventory:
            inv_aspect = InventoryAspect()
            inv_aspect.items = list(self._inventory.items)
            inv_aspect.max_slots = self._inventory.max_slots
            inv_aspect.max_weight = self._inventory.max_weight
            inv_aspect.weapon = self._inventory.weapon
            inv_aspect.armor = self._inventory.armor
            inv_aspect.accessory = self._inventory.accessory
            
            aspects["inventory"] = inv_aspect

        return aspects

    def build(self) -> Entity:
        """Construct and return the final Entity."""
        aspects_dict = self._init_aspects()
        
        entity = Entity(
            id=self._eid,
            kind=self._kind,
            aspects=aspects_dict
        )
        
        # Attach aspects to the entity
        for aspect in aspects_dict.values():
            aspect.on_attach(entity)
            
        return entity
