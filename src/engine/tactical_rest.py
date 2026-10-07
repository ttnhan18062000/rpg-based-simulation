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

from src.ai.goals.need_pull import ESCALATION_FULL, SLEEP_LINE, arrival_fraction
from src.core.strategic import GoalKind, ProjectStatus
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.biological_needs import need_rates
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
    if getattr(obj, "target_position", None) is not None:
        return True, tuple(obj.target_position)
    try:
        building = state.buildings.get(int(obj.target))
    except (TypeError, ValueError):
        building = None
    return True, (tuple(building.position) if building is not None else None)


def rest_in_place_update(
    state: AuthoritativeState, entity: EntityState, hostiles: Sequence[EntityState]
) -> Optional[EntityUpdate]:
    """A rest-where-you-stand update for a fatigue project that cannot reach a bed in time, or None to decide as usual."""
    has_project, target = _fatigue_target(state, entity)
    if not has_project or entity.biological.sleep_debt < REST_MIN_SLEEP_DEBT:
        return None
    if present_threat_terms(entity, list(hostiles)):
        return None
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
