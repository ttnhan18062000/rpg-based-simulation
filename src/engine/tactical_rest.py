"""
src/engine/tactical_rest.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07

World Rule SURV-06: every kind with a rest need can rest in place, sleeping rough (the `REST` action, which recovers sleep debt
without a building), wherever it is not in danger; a bed (an inn or a home) only makes rest better, and rest never requires a
building. The dispatch carries the reason `REST_IN_PLACE` so a rest in place stays distinguishable from rest at the inn. World Rule SURV-07: a pressing need is acted on
in time. So an entity whose fatigue project would reach the inn only after its sleep debt has crossed
`ESCALATION_FULL` of the consequence line, or whose fatigue project has no inn to walk to, rests where it stands, provided
no present threat to it holds (`present_threat_terms`, AGENCY-07's predicate, is the "in danger" test).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence, Tuple

from src.core.items import food_hunger_recovery
from src.core.movement_modes import MovementMode
from src.core.strategic import GoalKind, ProjectStatus
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.biological_needs import need_rates
from src.engine.need_pull import ESCALATION_FULL, SLEEP_LINE, arrival_fraction
from src.engine.service_reach import service_tile
from src.engine.tactical_threat import present_threat_terms

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

# The buildings whose service a REST uses (`town_resolution.SERVICE_KINDS["REST"]`): a bed.
BED_KINDS = frozenset({"inn", "home"})

# A fatigue project's goal only exists above this sleep debt (SleepScorer's own early exit), and a project completes below it.
REST_MIN_SLEEP_DEBT = 20.0


def _fatigue_target(state: AuthoritativeState, entity: EntityState) -> Tuple[bool, Optional[Tuple[float, float]]]:
    """(has an active fatigue project, the position its objective walks to, or None when it names no place)."""
    strat = entity.strategic
    project = strat.projects.get(strat.current_project_id) if strat.current_project_id else None
    if project is None or project.status != ProjectStatus.ACTIVE or project.kind != GoalKind.FATIGUE:
        return False, None
    obj = next((o for o in project.objectives if o.id == strat.current_objective_id), None)
    if obj is None:
        return True, None
    target_position = getattr(obj, "target_position", None)
    if target_position is not None:
        return True, (float(target_position[0]), float(target_position[1]))
    try:
        building = state.buildings.get(int(obj.target or ""))
    except (TypeError, ValueError):
        building = None
    if building is None:
        return True, None
    return True, (float(building.position[0]), float(building.position[1]))


def rest_in_place_update(
    state: AuthoritativeState, entity: EntityState, hostiles: Sequence[EntityState]
) -> Optional[EntityUpdate]:
    """A rest-where-you-stand update for a fatigue project that cannot reach a bed in time, or None to decide as usual."""
    has_project, target = _fatigue_target(state, entity)
    if not has_project or entity.biological.sleep_debt < REST_MIN_SLEEP_DEBT:
        return None
    if hostiles and present_threat_terms(entity, list(hostiles)):
        return None  # in danger (a perceived hostile makes a present threat); a wound alone, with no hostile in view, is not
    if target is not None:
        px, py = entity.navigation.position
        if service_tile(state, (int(px), int(py)), BED_KINDS) is not None:
            return None  # within reach of a bed: the building branch dispatches the rest
        travel = abs(px - target[0]) + abs(py - target[1])
        if arrival_fraction(entity.biological.sleep_debt, need_rates(entity)[1], travel, SLEEP_LINE) < ESCALATION_FULL:
            return None  # the bed is reachable in time: keep walking to it
    return EntityUpdate(
        entity_id=entity.id,
        navigation=NavigationUpdate(target_clear=True),
        task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "REST", "reason": "REST_IN_PLACE"}),
    )


# Hunger at or above which a subject carrying food eats it (SURV-06: carried food is a way to eat that needs no building).
# One meal removes a food item's `hunger_recovery`, so below this a carried meal would be wasted.
EAT_CARRIED_MIN_HUNGER = 40.0


def eat_carried_update(entity: EntityState, hostiles: Sequence[EntityState]) -> Optional[EntityUpdate]:
    """An eat-what-you-carry update for a hungry subject holding food, or None. No building is needed; a present threat outranks it."""
    if entity.biological.hunger < EAT_CARRIED_MIN_HUNGER:
        return None
    from src.engine.appraisal import can_eat_item
    if not any(food_hunger_recovery(stack.item_id) > 0.0 and stack.quantity > 0 and can_eat_item(entity, stack.item_id)
               for stack in entity.inventory.items):
        return None
    if hostiles and present_threat_terms(entity, list(hostiles)):
        return None
    return EntityUpdate(
        entity_id=entity.id,
        navigation=NavigationUpdate(target_clear=True),
        task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "EAT", "reason": "EAT_CARRIED"}),
    )


# How far (Manhattan tiles) a hungry animal will step back to a carcass it is standing near without a goal to go there: its own fresh kill is
# at most a step or two away when a held swing ends and the body has drifted a tile.
CARCASS_NEAR = 3.0


def eat_at_corpse_in_place_update(
    state: AuthoritativeState, entity: EntityState, hostiles: Sequence[EntityState]
) -> Optional[EntityUpdate]:
    """Decision 44: a hungry subject at, or just beside, a carcass whose food its diet allows eats it where it lies (stepping back to it first when
    it is a tile or two off), at the same hunger a carried meal would be eaten (one gate for the hunt and the meal). This is what makes a kill
    lead to the meal: the killer is beside its own fresh kill. A kind never eats a carcass of its own species; a present threat outranks it."""
    if entity.biological.hunger < EAT_CARRIED_MIN_HUNGER or not state.corpses:
        return None
    if hostiles and present_threat_terms(entity, list(hostiles)):
        return None
    from src.content_semantics.faction import get_species_id_str
    from src.engine.appraisal import can_eat_item
    from src.engine.domain.core_actions import EAT_AT_CORPSE_REACH
    own = get_species_id_str(entity)
    px, py = entity.navigation.position
    best, best_distance = None, 0.0
    for corpse_id in sorted(state.corpses):
        corpse = state.corpses[corpse_id]
        distance = abs(px - corpse.position[0]) + abs(py - corpse.position[1])
        if distance > CARCASS_NEAR or not any(i.quantity > 0 and can_eat_item(entity, i.item_id) for i in corpse.items):
            continue
        dead = state.entities.get(corpse.original_entity_id)
        if dead is not None and get_species_id_str(dead) == own:
            continue
        if best is None or distance < best_distance:
            best, best_distance = corpse, distance
    if best is None:
        return None
    if best_distance <= EAT_AT_CORPSE_REACH:
        return EntityUpdate(
            entity_id=entity.id,
            navigation=NavigationUpdate(target_clear=True),
            task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "EAT", "reason": "EAT_AT_CORPSE", "corpse_id": best.id}),
        )
    return EntityUpdate(
        entity_id=entity.id,
        navigation=NavigationUpdate(target_set=best.position, movement_mode_set=MovementMode.WANDER),
        task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": best.position, "reason": "TO_CARCASS"}),
    )


def in_place_survival_update(
    state: AuthoritativeState, entity: EntityState, hostiles: Sequence[EntityState]
) -> Optional[EntityUpdate]:
    """A survival action that needs no building: rest in place, else eat carried food; None to decide as usual."""
    return (rest_in_place_update(state, entity, hostiles) or eat_carried_update(entity, hostiles)
            or eat_at_corpse_in_place_update(state, entity, hostiles))
