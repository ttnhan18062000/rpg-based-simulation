from __future__ import annotations

from typing import Optional

from src.content.resolver import ResolvedEntityArchetype
from src.core.enums import EntityRole, Faction
from src.entities.runtime_contract import ResolvedEntityRuntimeContract


def resolved_archetype_to_contract(
    arch: ResolvedEntityArchetype,
) -> ResolvedEntityRuntimeContract:
    """
    Map ResolvedEntityArchetype to ResolvedEntityRuntimeContract.

    This is the archetype-native construction path entry point. It extracts
    flat runtime-relevant fields from the resolved archetype and returns a
    typed contract that ArchetypeEntityFactory can consume.

    Three entity construction paths exist in the runtime:
      1. archetype-native: catalog → resolved archetype → contract → EntityState  [preferred]
      2. worldspec role/faction/count: existing world assembly population expansion
      3. legacy builder: V2EntityBuilder for arena/test/migration use cases

    Paths 2 and 3 remain valid. This function is the gateway for path 1.
    """
    stats = arch.stat_profile
    inventory = arch.inventory_profile

    legacy_role = _try_role(arch.legacy_engine_role)
    legacy_faction = _try_faction(arch.legacy_engine_bucket)

    trait_ids = tuple(t.id for t in arch.traits)
    theme_ids = tuple(t.id for t in arch.themes)

    return ResolvedEntityRuntimeContract(
        archetype_id=arch.archetype_id,
        species_id=arch.species_id,
        faction_id=arch.faction_id,
        role_id=arch.role_id,
        kind=arch.species_id,  # kind derives from species; may be overridden by spawn context
        legacy_role=legacy_role,
        legacy_faction=legacy_faction,
        hp=stats.hp,
        max_hp=stats.max_hp,
        atk=stats.atk,
        def_stat=stats.def_stat,
        attack_range=stats.attack_range,
        readiness=stats.readiness,
        inventory_items=dict(inventory.starting_items),
        starting_gold=inventory.starting_gold,
        traits=trait_ids,
        themes=theme_ids,
        cognition_profile_id=arch.cognition_profile.id,
        drive_profile_id=arch.drive_profile.id,
        need_profile_id=arch.need_profile.id,
        sense_profile_id=arch.sense_profile.id,
        skill_profile_id=arch.skill_profile.id if arch.skill_profile else None,
    )


def _try_role(name: str) -> Optional[EntityRole]:
    try:
        return EntityRole[name]
    except KeyError:
        return None


def _try_faction(name: str) -> Optional[Faction]:
    try:
        return Faction[name]
    except KeyError:
        return None
