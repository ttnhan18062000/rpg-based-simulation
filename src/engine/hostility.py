"""The one test for "this neighbour is a perceived hostile or appraised as prey, threat or danger" (CONFLICT-04, decisions 44-49).

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
from src.engine.appraisal import Relation, appraise, perceives
from src.engine.legality import LegalityServiceV2
from src.entities.identity_resolver import (
    EntityIdentityResolver,
    IdentityResolutionError,
)

if TYPE_CHECKING:
    from src.core.state import EntityState


ATTACK_RELATIONS = frozenset({Relation.FACTION_HOSTILE, Relation.PREDATION})


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


def faction_hostile(entity: "EntityState", other: "EntityState", source: Optional[Tuple[str, str]] = None) -> bool:
    """True when ``entity`` perceives ``other`` (alive, passes the perception gate) and the faction semantics rate it hostile.

    ``source`` is ``source_identity(entity)`` when the caller tests many neighbours of one entity."""
    if not perceives(entity, other):
        return False
    dist = LegalityServiceV2.get_manhattan_dist(entity.navigation.position, other.navigation.position)
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


def relation(entity: "EntityState", other: "EntityState", source: Optional[Tuple[str, str]] = None) -> Relation:
    """How ``entity`` regards ``other`` (decisions 47 and 49): faction hostility first, then the appraisal from properties.

    "Appraisal for all, faction for people": a faction verdict wins; otherwise PREDATION, THREATENING, WARY or NONE."""
    if faction_hostile(entity, other, source):
        return Relation.FACTION_HOSTILE
    appraised = appraise(entity, other)
    if appraised is Relation.PREDATION and get_faction_id_str(entity) == get_faction_id_str(other):
        return Relation.NONE  # a faction does not hunt its own members
    return appraised


def perceived_hostile(entity: "EntityState", other: "EntityState", source: Optional[Tuple[str, str]] = None) -> bool:
    """True when ``other`` is an attack target of ``entity``: a faction hostile or prey it hunts. WARY and THREATENING are not (they are
    avoided, never engaged), so they never enter the hostile list."""
    return relation(entity, other, source) in ATTACK_RELATIONS
