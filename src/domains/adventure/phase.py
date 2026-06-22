"""
src/domains/adventure/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 3 — AdventureDecisionPhase

Unified integration phase coordinating route generation, Personality-biased
scoring, target selection, and strategic alignment in the tick execution.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any

from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate
from src.domains.adventure.generator import AdventureRouteGenerator
from src.domains.adventure.schema import RouteFamily
from src.domains.adventure.service import AdventureDecisionService
from src.world.providers.resources import ResourceOpportunityProvider


class AdventureDecisionPhase:
    """
    Simulates subjective routing decisions for heroes, running at strategic cadence.
    """

    @staticmethod
    def apply(
        state: AuthoritativeState,
        context: Optional[dict] = None,
        trace_writer: Optional[Any] = None,
        faction_directives: Optional[list] = None,
        factions: Optional[Any] = None,
    ) -> StateUpdate:
        """
        Evaluate eligible heroes on the current tick, execute subjective routing,
        and generate strategic StateUpdates for state transition.
        
        Eligible entities are:
            - Heroes (EntityRole = 0)
            - Alive (combat.alive = True)
            - Active (lifecycle.active = True)
            - Not active in a locked/unresolved project (unless project is stale or lock is expired)
        """
        update = StateUpdate()
        tick = state.tick

        # Avoid processing if no heroes exist
        heroes = [e for e in state.entities.values() if e.combat.alive and e.lifecycle.active]
        if not heroes:
            return update

        entity_updates: Dict[int, EntityUpdate] = {}

        for hero in heroes:
            # Check strategic plan lock status
            strat = hero.strategic
            if strat and strat.current_project_id:
                active_proj = strat.projects.get(strat.current_project_id)
                if active_proj:
                    # If project lock hasn't expired, skip evaluating routing decisions
                    if tick < active_proj.lock_until_tick:
                        continue

            # 1. Generate candidate route options
            opportunities = ResourceOpportunityProvider.get_opportunities(hero, state)
            candidates = AdventureRouteGenerator.generate(hero, state, opportunities=opportunities)

            # 2. Decide using service ( personality-biased scoring + project mapping )
            result = AdventureDecisionService.decide(
                hero, candidates, tick=tick,
                resource_nodes=state.resource_nodes,
                faction_directives=faction_directives,
                factions=factions,
            )

            # 2a. Write decision trace if writer is available (LIGHT+ mode observability)
            _writer = trace_writer
            if _writer is None:
                from src.observability.cognition.decision_trace_writer import get_active_writer
                _writer = get_active_writer()
            if _writer is not None:
                scored_candidates = result.trace.get("scored_candidates", [])
                if scored_candidates:
                    _writer.write_trace(hero.id, tick, scored_candidates)

            # If no selection or deferred, do not update project
            if not result.selected or result.selected.family == RouteFamily.DEFER_WITH_REASON:
                continue

            # 3. Create strategic updates for the committed choice
            if result.proposed_project and result.proposed_objective:
                strat_upd = StrategicUpdate(
                    projects_add_or_update=[result.proposed_project],
                    current_project_id_set=result.proposed_project.id,
                    current_objective_id_set=result.proposed_objective.id,
                )
                
                # Retrieve existing property updates or create new
                prop_upd = {
                    "last_routing_tick": tick,
                    "last_routing_family": result.selected.family.value,
                }
                
                # Include rejected trace for debug visibility
                trace_records = {
                    "selected": result.selected.family.value,
                    "score": result.selected.score,
                    "candidate_count": len(candidates),
                }

                entity_updates[hero.id] = EntityUpdate(
                    entity_id=hero.id,
                    strategic=strat_upd,
                    property_updates=prop_upd,
                )

        if entity_updates:
            update = StateUpdate(entity_updates=entity_updates)

        return update
