"""Appraisal of one entity by another: the read-only questions behind hunting, wariness and threat (decisions 44-49).

A kind declares properties (diet, edibility, size, power, wits) and nothing else. Whether one entity can eat, can overcome or is
threatened by another is derived here, from those properties, the observer's own KNOW-04 prior and what is perceived. No function reads a
role, a trait list or a predator/prey label, and none mutates state. Constants live in one table with their fiction reason.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from src.cognition.common_knowledge import believed_danger_rank
from src.content.schema import PROPERTY_BANDS
from src.content_semantics.faction import get_species_id_str
from src.core.items import food_class
from src.engine.behavior_consumers import (
    get_entity_signals,
    get_kind_properties,
    get_perception_gate,
)
from src.engine.legality import LegalityServiceV2

if TYPE_CHECKING:
    from src.core.state import EntityState

# Fiction reasons for the constants (one table, never scattered).
THREAT_RANGE = 4  # tiles: close enough that a creature that can eat you and is coming for you has to be acted on now
WARY_DISTANCE = 5  # tiles: farther than THREAT_RANGE, so a wary creature starts keeping its distance before it is in danger
# A subject believes it can overcome a kind only when its own power band ranks STRICTLY above the danger it believes that kind poses; a tie
# is "cannot": wild creatures avoid a fight with an equal.
HUNT_HUNGER = 40.0  # hunger at which a subject will hunt: the line at which food on hand would be eaten (tactical_rest.EAT_CARRIED_MIN_HUNGER)


class Relation(str, Enum):
    """How one entity regards another, strongest first."""

    FACTION_HOSTILE = "FACTION_HOSTILE"  # the faction semantics rate it hostile (people and monster factions)
    PREDATION = "PREDATION"  # I am hungry, my diet can eat its body and I believe I can overcome it
    THREATENING = "THREATENING"  # it can eat me, is within THREAT_RANGE and is coming for me
    WARY = "WARY"  # it can eat me and I believe I cannot overcome it (what it IS; hunger is never read)
    NONE = "NONE"


def perceives(entity: "EntityState", other: "EntityState") -> bool:
    """True when ``entity`` perceives the living ``other`` through the perception gate."""
    if not other.combat.alive:
        return False
    dist = LegalityServiceV2.get_manhattan_dist(entity.navigation.position, other.navigation.position)
    try:
        return bool(get_perception_gate().can_perceive(entity, get_entity_signals(other), {"distance": float(dist)}).perceived)
    except (AttributeError, KeyError, TypeError, ValueError, RuntimeError):
        return True  # gate failure: permissive fallback, as the tactical pass has always done


def can_eat(eater: "EntityState", other: "EntityState") -> bool:
    """True when the living ``other``'s body feeds a food class the eater's body can eat (both read from content)."""
    if not other.combat.alive:
        return False
    _, eater_body = get_kind_properties(get_species_id_str(eater))
    _, other_body = get_kind_properties(get_species_id_str(other))
    if eater_body is None or other_body is None:
        return False
    return bool(set(eater_body.diet or ()) & set(other_body.edible_as or ()))


def can_eat_item(eater: "EntityState", item_id: str) -> bool:
    """True when ``item_id`` is food whose class the eater's body can eat (decision 44: the diet gate).

    A body whose diet is undeclared, or an entity with no known species, keeps the legacy "eats any food" behaviour: missing data gates
    nothing."""
    item_class = food_class(item_id)
    if item_class is None:
        return False
    _, body = get_kind_properties(get_species_id_str(eater))
    if body is None or body.diet is None:
        return True
    return item_class in body.diet


def can_use_inn_meal(eater: "EntityState") -> bool:
    """True when the inn's free meal (a prepared meal) is in the eater's diet; an undeclared diet keeps the legacy behaviour."""
    _, body = get_kind_properties(get_species_id_str(eater))
    return body is None or body.diet is None or "prepared" in body.diet


def can_overcome(entity: "EntityState", other: "EntityState") -> bool:
    """True when ``entity``'s own power band ranks strictly above the danger it believes ``other``'s kind poses (its KNOW-04 prior).

    M0 shortcut, closed by Milestone 1's one-appraisal child: the belief is about the kind, never this individual, so it cannot see the
    target's visible condition, the subject's own condition or a group. A coarse-band tie resolves to "cannot overcome"."""
    species, _ = get_kind_properties(get_species_id_str(entity))
    if species is None or species.power is None:
        return False
    return PROPERTY_BANDS.index(species.power) > believed_danger_rank(entity, other)


def _distance(entity: "EntityState", other: "EntityState") -> float:
    return float(LegalityServiceV2.get_manhattan_dist(entity.navigation.position, other.navigation.position))


def _coming_for(other: "EntityState", entity: "EntityState") -> bool:
    """True when ``other`` has committed to ``entity`` or its last step closed the distance to it."""
    if other.task.payload.get("target_id") == entity.id:
        return True
    previous = other.navigation.last_position
    if previous is None:
        return False
    before = LegalityServiceV2.get_manhattan_dist(previous, entity.navigation.position)
    return _distance(entity, other) < before


def appraise(entity: "EntityState", other: "EntityState") -> Relation:
    """The non-faction relation of ``entity`` toward the perceived ``other``: PREDATION, THREATENING, WARY or NONE."""
    if entity.id == other.id or not perceives(entity, other):
        return Relation.NONE
    # Cheapest gate first; the KNOW-04 capability estimate runs only when every cheaper gate has passed.
    if can_eat(entity, other) and entity.biological.hunger >= HUNT_HUNGER and can_overcome(entity, other):
        return Relation.PREDATION
    if can_eat(other, entity):
        if _distance(entity, other) <= THREAT_RANGE and _coming_for(other, entity):
            return Relation.THREATENING
        if not can_overcome(entity, other):
            return Relation.WARY
    return Relation.NONE
