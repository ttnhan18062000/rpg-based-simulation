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

from src.core.attributes import Attributes, AttributeCaps
from src.core.classes import (
    CLASS_DEFS, RACE_SKILLS, SKILL_DEFS, SkillInstance,
    available_class_skills,
)
from src.core.enums import AIState, Domain
from src.core.faction import Faction
from src.core.items import Inventory
from src.core.models import Entity, Stats, Vector2
from src.core.traits import assign_traits

if TYPE_CHECKING:
    from src.systems.rng import DeterministicRNG


class EntityBuilder:
    """Fluent builder for Entity construction.

    All ``with_*`` methods return ``self`` for chaining.
    Call ``build()`` to produce the final Entity.
    """

    __slots__ = (
        "_rng", "_eid", "_tick",
        "_kind", "_pos", "_ai_state", "_faction",
        "_home_pos", "_tier",
        "_base_hp", "_base_atk", "_base_def", "_base_spd",
        "_luck", "_crit_rate", "_crit_dmg", "_evasion",
        "_level", "_xp", "_xp_to_next", "_gold",
        "_hero_class", "_class_def",
        "_attrs", "_caps",
        "_skills", "_inventory", "_traits",
        "_attr_base", "_attr_randomness",
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
        self._home_pos: Vector2 | None = None
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

        self._hero_class: int | None = None
        self._class_def = None
        self._attrs: Attributes | None = None
        self._caps: AttributeCaps | None = None
        self._skills: list[SkillInstance] = []
        self._inventory: Inventory | None = None
        self._traits: list[int] = []

    # -------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------

    def kind(self, kind: str) -> EntityBuilder:
        self._kind = kind
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

    # -------------------------------------------------------------------
    # Base stats
    # -------------------------------------------------------------------

    def with_base_stats(
        self, *,
        hp: int = 20, atk: int = 5, def_: int = 0, spd: int = 10,
        luck: int = 0, crit_rate: float = 0.05, crit_dmg: float = 1.5,
        evasion: float = 0.0, level: int = 1, xp_to_next: int = 100,
        gold: int = 0,
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

    def with_mob_attributes(self, attr_base: int, tier: int) -> EntityBuilder:
        """Generate mob-style attributes scaled by tier."""
        eid = self._eid
        rng = self._rng
        tick = self._tick
        self._attrs = Attributes(
            str_=attr_base + rng.next_int(Domain.SPAWN, eid, tick + 20, 0, 3),
            agi=attr_base + rng.next_int(Domain.SPAWN, eid, tick + 21, 0, 3),
            vit=attr_base + rng.next_int(Domain.SPAWN, eid, tick + 22, 0, 3),
            int_=max(1, attr_base - 2 + rng.next_int(Domain.SPAWN, eid, tick + 23, 0, 2)),
            spi=max(1, attr_base - 2 + rng.next_int(Domain.SPAWN, eid, tick + 26, 0, 2)),
            wis=max(1, attr_base - 2 + rng.next_int(Domain.SPAWN, eid, tick + 24, 0, 2)),
            end=attr_base + rng.next_int(Domain.SPAWN, eid, tick + 25, 0, 3),
            per=max(1, attr_base - 1 + rng.next_int(Domain.SPAWN, eid, tick + 27, 0, 2)),
            cha=max(1, attr_base - 3 + rng.next_int(Domain.SPAWN, eid, tick + 28, 0, 2)),
        )
        self._caps = AttributeCaps(
            str_cap=15 + tier * 5, agi_cap=15 + tier * 5, vit_cap=15 + tier * 5,
            int_cap=10 + tier * 3, spi_cap=10 + tier * 3, wis_cap=10 + tier * 3,
            end_cap=15 + tier * 5, per_cap=10 + tier * 3, cha_cap=8 + tier * 2,
        )
        return self

    def with_race_attributes(
        self, attr_base: int, tier: int,
        r_str: int = 0, r_agi: int = 0, r_vit: int = 0,
        r_spi: int = 0, r_per: int = 0, r_cha: int = 0,
    ) -> EntityBuilder:
        """Generate race-specific attributes with racial modifiers."""
        eid = self._eid
        rng = self._rng
        tick = self._tick
        self._attrs = Attributes(
            str_=max(1, attr_base + r_str + rng.next_int(Domain.SPAWN, eid, tick + 20, 0, 3)),
            agi=max(1, attr_base + r_agi + rng.next_int(Domain.SPAWN, eid, tick + 21, 0, 3)),
            vit=max(1, attr_base + r_vit + rng.next_int(Domain.SPAWN, eid, tick + 22, 0, 3)),
            int_=max(1, attr_base - 2 + rng.next_int(Domain.SPAWN, eid, tick + 23, 0, 2)),
            spi=max(1, attr_base - 2 + r_spi + rng.next_int(Domain.SPAWN, eid, tick + 26, 0, 2)),
            wis=max(1, attr_base - 2 + rng.next_int(Domain.SPAWN, eid, tick + 24, 0, 2)),
            end=max(1, attr_base + rng.next_int(Domain.SPAWN, eid, tick + 25, 0, 3)),
            per=max(1, attr_base - 1 + r_per + rng.next_int(Domain.SPAWN, eid, tick + 27, 0, 2)),
            cha=max(1, attr_base - 3 + r_cha + rng.next_int(Domain.SPAWN, eid, tick + 28, 0, 2)),
        )
        self._caps = AttributeCaps(
            str_cap=15 + tier * 5, agi_cap=15 + tier * 5, vit_cap=15 + tier * 5,
            int_cap=10 + tier * 3, spi_cap=10 + tier * 3, wis_cap=10 + tier * 3,
            end_cap=15 + tier * 5, per_cap=10 + tier * 3, cha_cap=8 + tier * 2,
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
        """Add starting items to inventory (must call with_inventory first)."""
        if self._inventory:
            for item_id in item_ids:
                self._inventory.add_item(item_id)
        return self

    def with_existing_inventory(self, inv: Inventory) -> EntityBuilder:
        """Attach a pre-built Inventory (for complex inventory setups)."""
        self._inventory = inv
        return self

    def with_equipment(
        self, *,
        weapon: str | None = None,
        armor: str | None = None,
        accessory: str | None = None,
    ) -> EntityBuilder:
        """Set equipment slots on the current inventory."""
        if self._inventory:
            if weapon:
                self._inventory.weapon = weapon
            if armor:
                self._inventory.armor = armor
            if accessory:
                self._inventory.accessory = accessory
        return self

    # -------------------------------------------------------------------
    # Traits
    # -------------------------------------------------------------------

    def with_traits(self, race_prefix: str = "") -> EntityBuilder:
        """Assign personality traits using weighted random selection."""
        self._traits = assign_traits(
            self._rng, Domain.SPAWN, self._eid, self._tick,
            race_prefix=race_prefix,
        )
        return self

    # -------------------------------------------------------------------
    # Build
    # -------------------------------------------------------------------

    def build(self) -> Entity:
        """Construct and return the final Entity."""
        stamina = 30
        if self._attrs:
            stamina += self._attrs.end * 2
        if self._kind == "hero":
            stamina = max(stamina, 50 + (self._attrs.end * 2 if self._attrs else 0))

        return Entity(
            id=self._eid,
            kind=self._kind,
            pos=self._pos,
            stats=Stats(
                hp=self._base_hp,
                max_hp=self._base_hp,
                atk=self._base_atk,
                def_=self._base_def,
                spd=self._base_spd,
                luck=self._luck,
                crit_rate=self._crit_rate,
                crit_dmg=self._crit_dmg,
                evasion=self._evasion,
                level=self._level,
                xp=self._xp,
                xp_to_next=self._xp_to_next,
                gold=self._gold,
                stamina=stamina,
                max_stamina=stamina,
            ),
            ai_state=self._ai_state,
            faction=self._faction,
            next_act_at=float(self._tick),
            home_pos=self._home_pos,
            tier=self._tier,
            inventory=self._inventory,
            attributes=self._attrs,
            attribute_caps=self._caps,
            hero_class=self._hero_class or 0,
            skills=self._skills,
            traits=self._traits,
        )
