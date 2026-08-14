from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from src.core.enums import EntityRole, Faction
from src.core.state import EntityState


# --- Compatibility projection maps (legacy enum → string ID) ---

_ROLE_COMPAT: dict[int, str] = {
    EntityRole.HERO: "hero",
    EntityRole.SHOPKEEPER: "shopkeeper",
    EntityRole.MONSTER: "creature",
    EntityRole.CITIZEN: "citizen",
    EntityRole.WORKER: "worker",
    EntityRole.GUARD: "guard",
}

_FACTION_COMPAT: dict[int, str] = {
    Faction.HERO_GUILD: "hero_guild",
    Faction.MONSTER_HORDE: "monster_horde",
    Faction.TOWN_COUNCIL: "town_council",
    Faction.NEUTRAL: "neutral",
}


class IdentityResolutionError(ValueError):
    """Raised when no usable identity can be resolved from an entity."""


class ResolvedEntityIdentity(BaseModel):
    """
    Resolved identity for a runtime entity, regardless of construction path.

    source indicates which path succeeded:
    - clean_metadata: explicit archetype/race/faction/role strings in identity.properties
    - runtime_identity_extension: runtime-set identity strings in a secondary properties key
    - compatibility_projection: legacy int enum projected to string ID via compat map
    - legacy_enum: raw legacy enum name used as string ID (lowest confidence)
    """

    model_config = ConfigDict(frozen=True)

    entity_id: int
    archetype_id: Optional[str] = None
    race_id: Optional[str] = None
    faction_id: str
    role_id: str
    profession_id: Optional[str] = None

    legacy_faction: Optional[Faction] = None
    legacy_role: Optional[EntityRole] = None

    source: Literal[
        "clean_metadata",
        "runtime_identity_extension",
        "compatibility_projection",
        "legacy_enum",
    ]


class EntityIdentityResolver:
    """
    Single identity access layer. Reads clean catalog identity first; falls
    back to legacy enum identity only when necessary.

    Does not load catalog files. Does not import CatalogRepository.
    """

    def resolve(self, entity: EntityState) -> ResolvedEntityIdentity:
        props = entity.identity.properties or {}

        # --- Path 1: clean_metadata ---
        # A real, content-driven faction_id is trusted on its own -- role_id is a real gap in
        # some spawn/compile paths (worldbuilding/compiler.py never sets it) but has zero real
        # consumers of its own (confirmed via grep: only .faction_id/.archetype_id are ever read,
        # in tactical.py/quests.py). Requiring role_id here previously discarded a correct
        # faction_id by falling through to Path 3's coarse legacy-enum projection, which collapses
        # any faction outside the old 4-value Faction enum to "neutral" -- silently defeating
        # hostility detection for the majority of a real content-driven roster
        # (TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE: 100% of dungeon_crawl's entities,
        # 43% of urban_political's, confirmed via live corpus instrumentation).
        faction_id = props.get("faction_id")
        role_id = props.get("role_id") or _ROLE_COMPAT.get(entity.identity.role)
        if faction_id:
            return ResolvedEntityIdentity(
                entity_id=entity.id,
                archetype_id=props.get("archetype_id"),
                race_id=props.get("race_id"),
                faction_id=faction_id,
                role_id=role_id or "unresolved",
                profession_id=props.get("profession_id"),
                legacy_faction=_try_faction(entity.identity.faction),
                legacy_role=_try_role(entity.identity.role),
                source="clean_metadata",
            )

        # --- Path 2: runtime_identity_extension ---
        rt_faction = props.get("runtime_faction_id")
        rt_role = props.get("runtime_role_id")
        if rt_faction and rt_role:
            return ResolvedEntityIdentity(
                entity_id=entity.id,
                archetype_id=props.get("archetype_id"),
                race_id=props.get("race_id"),
                faction_id=rt_faction,
                role_id=rt_role,
                profession_id=props.get("profession_id"),
                legacy_faction=_try_faction(entity.identity.faction),
                legacy_role=_try_role(entity.identity.role),
                source="runtime_identity_extension",
            )

        # --- Path 3: compatibility_projection ---
        compat_role = _ROLE_COMPAT.get(entity.identity.role)
        compat_faction = _FACTION_COMPAT.get(entity.identity.faction)
        if compat_role and compat_faction:
            return ResolvedEntityIdentity(
                entity_id=entity.id,
                faction_id=compat_faction,
                role_id=compat_role,
                legacy_faction=_try_faction(entity.identity.faction),
                legacy_role=_try_role(entity.identity.role),
                source="compatibility_projection",
            )

        # --- Path 4: legacy_enum ---
        legacy_role = _try_role(entity.identity.role)
        legacy_faction = _try_faction(entity.identity.faction)
        if legacy_role is not None and legacy_faction is not None:
            return ResolvedEntityIdentity(
                entity_id=entity.id,
                faction_id=legacy_faction.name.lower(),
                role_id=legacy_role.name.lower(),
                legacy_faction=legacy_faction,
                legacy_role=legacy_role,
                source="legacy_enum",
            )

        raise IdentityResolutionError(
            f"Entity {entity.id} has no resolvable faction or role identity. "
            f"Properties: {list(props.keys())} | role={entity.identity.role} faction={entity.identity.faction}"
        )


def _try_role(value: int) -> Optional[EntityRole]:
    try:
        return EntityRole(value)
    except ValueError:
        return None


def _try_faction(value: int) -> Optional[Faction]:
    try:
        return Faction(value)
    except ValueError:
        return None
