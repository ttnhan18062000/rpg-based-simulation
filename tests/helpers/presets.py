from __future__ import annotations

from typing import Any

from src.core.enums import EntityRole, Faction
from src.core.state import EntityState, ItemStack
from tests.helpers.entities import make_entity, make_hero, make_monster, stack


DEFAULT_CLASS_LOADOUTS: dict[str, list[ItemStack]] = {
    "warrior": [stack("iron_sword", 1)],
    "mage": [stack("staff", 1)],
    "rogue": [stack("dagger", 1)],
}


DEFAULT_CLASS_SKILLS: dict[str, set[str]] = {
    "warrior": {"power_strike"},
    "mage": {"firebolt"},
    "rogue": {"backstab"},
}


def make_class_entity(
    entity_id: int = 1,
    *,
    class_id: str,
    pos: tuple[float, float] = (0.0, 0.0),
    kind: str = "hero",
    role: EntityRole = EntityRole.HERO,
    faction: Faction = Faction.HERO_GUILD,
    include_default_loadout: bool = True,
    include_default_skills: bool = True,
    items: list[ItemStack] | None = None,
    learned_skills: set[str] | None = None,
    **kwargs: Any,
) -> EntityState:
    final_items = list(items or [])
    if include_default_loadout:
        final_items.extend(DEFAULT_CLASS_LOADOUTS.get(class_id, []))

    final_skills = set(learned_skills or set())
    if include_default_skills:
        final_skills.update(DEFAULT_CLASS_SKILLS.get(class_id, set()))

    return make_entity(
        entity_id,
        kind=kind,
        pos=pos,
        role=role,
        faction=faction,
        class_id=class_id,
        items=final_items if final_items else kwargs.pop("items", None),
        learned_skills=final_skills if final_skills else kwargs.pop("learned_skills", None),
        **kwargs,
    )


def make_warrior(entity_id: int = 1, *, pos=(0.0, 0.0), **kwargs) -> EntityState:
    return make_class_entity(entity_id, class_id="warrior", pos=pos, **kwargs)


def make_mage(entity_id: int = 1, *, pos=(0.0, 0.0), **kwargs) -> EntityState:
    return make_class_entity(entity_id, class_id="mage", pos=pos, **kwargs)


def make_rogue(entity_id: int = 1, *, pos=(0.0, 0.0), **kwargs) -> EntityState:
    return make_class_entity(entity_id, class_id="rogue", pos=pos, **kwargs)


def make_goblin(
    entity_id: int = 2,
    *,
    pos: tuple[float, float] = (1.0, 0.0),
    hp: int = 30,
    atk: int = 8,
    def_stat: int = 2,
    evolution_level: int = 1,
    **kwargs,
) -> EntityState:
    return make_monster(
        entity_id,
        pos=pos,
        kind=kwargs.pop("kind", "goblin"),
        hp=hp,
        max_hp=kwargs.pop("max_hp", hp),
        atk=atk,
        def_stat=def_stat,
        evolution_level=evolution_level,
        **kwargs,
    )


def make_world_boss(
    entity_id: int = 900,
    *,
    pos: tuple[float, float] = (10.0, 10.0),
    hp: int = 1000,
    atk: int = 100,
    def_stat: int = 50,
    evolution_level: int = 10,
    **kwargs,
) -> EntityState:
    return make_monster(
        entity_id,
        pos=pos,
        kind=kwargs.pop("kind", "world_boss"),
        hp=hp,
        max_hp=kwargs.pop("max_hp", hp),
        atk=atk,
        def_stat=def_stat,
        evolution_level=evolution_level,
        **kwargs,
    )


def make_reward_ready_hero(
    entity_id: int = 1,
    *,
    pos: tuple[float, float] = (0.0, 0.0),
    gold: int = 0,
    max_slots: int = 10,
    items: list[ItemStack] | None = None,
    **kwargs,
) -> EntityState:
    return make_hero(
        entity_id,
        pos=pos,
        gold=gold,
        max_slots=max_slots,
        items=items or [],
        hp=kwargs.pop("hp", 100),
        max_hp=kwargs.pop("max_hp", 100),
        readiness=kwargs.pop("readiness", 100.0),
        alive=kwargs.pop("alive", True),
        **kwargs,
    )