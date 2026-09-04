from __future__ import annotations
from typing import List
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate
from src.core.enums import EntityRole

# TCK-20260903-ECONOMIC-VACANCY-SIGNAL. Role set rationale: see plan.md's Occupancy Definition
# section -- SHOPKEEPER (routine.py:138, SHOPKEEPING) and WORKER (routine.py:142, HARVESTING) are
# production-relevant; GUARD (routine.py:144, PATROLLING) is not. Deliberately narrower than
# OccupationChangeGoalScorer's _CANDIDATE_ROLES (occupation_change_scorer.py:14), which also
# includes GUARD for retraining purposes unrelated to production.
_PRODUCTION_RELEVANT_ROLES = (EntityRole.SHOPKEEPER, EntityRole.WORKER)


class EconomicVacancyService:
    """
    Detects when a death leaves a region with zero living holders of a production-relevant role
    and emits a PRODUCTION_ROLE_VACATED WorldEvent. Mirrors FactionInfluenceService's shape
    (src/world/influence.py) -- called once per tick from LifecycleSystem.resolve_lifecycle's
    aggregate `if recent_deaths:` block, after the main per-entity death loop, over the same
    recent_deaths list FactionInfluenceService.process_influence_shift already consumes there.
    """

    @staticmethod
    def check_and_emit(state: AuthoritativeState, recent_deaths: List[EntityState]) -> StateUpdate:
        from src.engine.legality import LegalityServiceV2  # local import, mirrors
                                                             # occupation_change_scorer.py:36 and
                                                             # influence.py's own local import style
        from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

        events = []
        for entity in recent_deaths:
            if entity.identity.role not in _PRODUCTION_RELEVANT_ROLES:
                continue
            region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
            if region is None:
                continue

            still_occupied = False
            for other_id, other in state.entities.items():
                if other_id == entity.id:
                    continue
                # Deliberately stricter than OccupationChangeGoalScorer's combat.alive-only filter
                # (occupation_change_scorer.py:47-48). Verified: resolve_lifecycle's death-marking
                # block (lifecycle.py:109-121) sets lifecycle.active=False on every death regardless
                # of reason, but never writes combat.alive_set for OLD_AGE deaths -- alive_set is
                # only ever written in src/engine/combat.py (KILL) and
                # src/engine/world_dynamics.py:39 (HAZARD). An old-age-dead entity's combat.alive
                # therefore stays True forever. Filtering on combat.alive alone would count that
                # stale corpse as a permanent occupant and this check would never fire for a region
                # whose real occupants all died of old age. lifecycle.active is the reliable
                # liveness signal here.
                if not other.lifecycle.active or not other.combat.alive:
                    continue
                if other.identity.role != entity.identity.role:
                    continue
                other_region = LegalityServiceV2.get_region_for_position(
                    other.navigation.position, state
                )
                if other_region is not None and other_region.id == region.id:
                    still_occupied = True
                    break

            if not still_occupied:
                events.append(WorldEvent(
                    category=WorldEventCategory.PRODUCTION_ROLE_VACATED,
                    tick=state.tick,
                    region_id=region.id,
                    subject=str(entity.id),
                    severity=1.0,
                    payload={"vacated_role": float(int(entity.identity.role))},
                ))

        if not events:
            return StateUpdate()
        return StateUpdate(world_events_add=events)
