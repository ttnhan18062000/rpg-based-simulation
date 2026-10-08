"""The one test for "this neighbour is a perceived, hostile-compatible entity" (CONFLICT-04).

The tactical pass builds its ``hostiles`` list with it and the movement layer asks it for the engaged adjacent hostile that makes a
stored-target step a non-decision, so the decision layer and the movement layer cannot disagree about who is a hostile.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from src.content_semantics.faction import (
    get_faction_id_str,
    get_faction_semantics_service,
    get_species_id_str,
)
from src.content_semantics.relation import RelationContext
from src.engine.behavior_consumers import get_entity_signals, get_perception_gate
from src.engine.legality import LegalityServiceV2
from src.entities.identity_resolver import (
    EntityIdentityResolver,
    IdentityResolutionError,
)

if TYPE_CHECKING:
    from src.core.state import EntityState


def source_identity(entity: "EntityState") -> Tuple[str, str]:
    """(faction id, identity source) of ``entity`` as the hostility test reads them; legacy fallback when it cannot be resolved."""
    try:
        identity = EntityIdentityResolver().resolve(entity)
        return identity.faction_id, identity.source
    except IdentityResolutionError:
        return get_faction_id_str(entity), "legacy_fallback"


def is_engaged(entity: "EntityState", other: "EntityState") -> bool:
    """True when either names the other as its target (the combat-engaged state the relation context reads)."""
    return entity.task.payload.get("target_id") == other.id or other.task.payload.get("target_id") == entity.id


def perceived_hostile(entity: "EntityState", other: "EntityState", source: Optional[Tuple[str, str]] = None) -> bool:
    """True when ``entity`` perceives ``other`` (alive, passes the perception gate) and the faction semantics rate it hostile.

    ``source`` is ``source_identity(entity)`` when the caller tests many neighbours of one entity."""
    if not other.combat.alive:
        return False
    dist = LegalityServiceV2.get_manhattan_dist(entity.navigation.position, other.navigation.position)
    try:
        perceived = get_perception_gate().can_perceive(entity, get_entity_signals(other), {"distance": float(dist)}).perceived
    except (AttributeError, KeyError, TypeError, ValueError, RuntimeError):
        perceived = True  # gate failure: permissive fallback, as the tactical pass has always done
    if not perceived:
        return False
    # `intruding` is left unset (None): see the note in LegalityServiceV2.verify_attack_legality.
    context = RelationContext(
        distance=float(dist),
        combat_engaged=is_engaged(entity, other),
        source_species=get_species_id_str(entity),
        target_species=get_species_id_str(other),
    )
    source_faction = (source or source_identity(entity))[0]
    try:
        target_faction = EntityIdentityResolver().resolve(other).faction_id
    except IdentityResolutionError:
        target_faction = get_faction_id_str(other)
    return bool(get_faction_semantics_service().is_hostile_compat(source_faction, target_faction, context))
