"""Hostile lookup shared by the goal scorers (TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07)."""
from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.content_semantics.faction import are_entities_hostile
from src.content_semantics.relation import RelationContext
from src.engine.cognition import SensoryFilter
from src.engine.domain_logic import SimulationDomainLogic
from src.systems.strategic_systems.entity_target_objective import (
    ENTITY_TARGET_PERCEPTION_RADIUS,
)

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


def perceived_hostiles(entity: "EntityState", state: "AuthoritativeState") -> List["EntityState"]:
    """The live neighbours, within the target-perception radius and the saliency cap, that the catalog calls hostile to `entity`."""
    raw_neighbors = SimulationDomainLogic.get_neighbor_view(state, entity, radius=ENTITY_TARGET_PERCEPTION_RADIUS)
    neighbors = SensoryFilter.filter_saliency(entity, raw_neighbors, max_targets=5)
    ex, ey = entity.navigation.position
    return [
        n for n in neighbors
        if n.combat.alive and are_entities_hostile(entity, n, RelationContext(
            distance=abs(n.navigation.position[0] - ex) + abs(n.navigation.position[1] - ey),
            combat_engaged=True))
    ]
