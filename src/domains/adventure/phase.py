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
from src.core.enums import EntityRole
from src.core.updates import StateUpdate, EntityUpdate
from src.domains.adventure.generator import AdventureRouteGenerator
from src.domains.adventure.schema import RouteFamily
from src.domains.adventure.service import AdventureDecisionService
from src.engine.behavior_consumers import get_cognition_profile_definition, get_role_definition
from src.systems.strategic import StrategicIntelligenceSystem
from src.systems.strategic_systems.intelligence import _threat_resolved
from src.world.providers.resources import ResourceOpportunityProvider
from src.world.providers.services import ServiceOpportunityProvider
from src.observability.cognition.decision_trace_writer import get_active_writer as _get_active_writer


def _resolve_cognition_profile_id(entity: EntityState) -> Optional[str]:
    """
    Resolve the cognition profile governing this entity's adventure eligibility.

    Tier 1: explicit identity.properties["cognition_profile_id"] (archetype-native spawn path,
    ArchetypeEntityFactory.build_entity, src/entities/archetype_factory.py:56-57) always wins.
    Tier 2: identity.properties["role_id"] -> RoleDefinition.default_cognition_profile, mirroring
    EntityArchetypeResolver._resolve_from_definition's own archetype-or-role-default pattern
    (src/content/resolver.py:460-462).
    Tier 3: entities spawned via the hero_adventurers world module (WorldEntitySpawner
    ._spawn_legacy_guard, src/worldassembly/entity_spawner.py:101-141, fed by the no-archetype_id
    else-branch of ProfileResolutionEngine.resolve(), src/worldassembly/resolver.py:1020-1032)
    have BOTH cognition_profile_id and role_id absent/None in identity.properties -- confirmed by
    direct read this session (ResolvedEntityProfile.role_id defaults to None, and the else-branch
    never sets it). identity.role (the legacy EntityRole enum) is still reliably HERO for these
    entities (RoleSemanticsService.get_legacy_entity_role), so fall back through the enum for
    this one evidenced real-corpus gap only.
    """
    props = entity.identity.properties  # always a dict, never None: src/core/state.py:490
    explicit = props.get("cognition_profile_id")
    if explicit:
        return explicit
    role_id = props.get("role_id")
    if role_id:
        role_def = get_role_definition(role_id)
        if role_def and role_def.default_cognition_profile:
            return role_def.default_cognition_profile
    if entity.identity.role == EntityRole.HERO:
        role_def = get_role_definition("hero")
        if role_def and role_def.default_cognition_profile:
            return role_def.default_cognition_profile
    return None


def _supports_adventure_routing(entity: EntityState, cache: Dict[str, bool]) -> bool:
    """Eligibility predicate: does entity's resolved cognition profile allow adventure routing?

    `cache` is a per-apply()-call dict keyed by cognition_profile_id, so the catalog accessor is
    invoked at most once per distinct profile id encountered in a tick, not once per hero
    (see Step 5's call site and Step 9's caching test).
    """
    profile_id = _resolve_cognition_profile_id(entity)
    if not profile_id:
        return False
    if profile_id not in cache:
        profile_def = get_cognition_profile_definition(profile_id)
        cache[profile_id] = bool(profile_def and profile_def.supports_adventure_routing)
    return cache[profile_id]


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
            - Cognitively adventure-capable (resolved cognition_profile.supports_adventure_routing = True)
            - Alive (combat.alive = True)
            - Active (lifecycle.active = True)
            - Not active in a locked/unresolved project (unless project is stale or lock is expired)
        """
        update = StateUpdate()
        tick = state.tick

        # Avoid processing if no eligible entities exist
        _profile_eligibility_cache: Dict[str, bool] = {}
        heroes = [
            e for e in state.entities.values()
            if _supports_adventure_routing(e, _profile_eligibility_cache)
            and e.combat.alive and e.lifecycle.active
        ]
        if not heroes:
            return update

        entity_updates: Dict[int, EntityUpdate] = {}

        # Resolve the trace writer once before the entity loop — the lazy import
        # of observability.cognition triggers expensive Pydantic model construction
        # on first access, making it O(n) if left inside the loop.
        _resolved_writer = trace_writer if trace_writer is not None else _get_active_writer()

        for hero in heroes:
            # Check strategic plan lock status
            strat = hero.strategic
            if strat and strat.current_project_id:
                active_proj = strat.projects.get(strat.current_project_id)
                if active_proj:
                    # If project lock hasn't expired, skip evaluating routing decisions
                    # unless the triggering threat has been resolved (HP > 80%, no hostile
                    # in vicinity) — early-release prevents cascading dead time post-combat.
                    if tick < active_proj.lock_until_tick and not _threat_resolved(hero, state):
                        continue

            # 1. Generate candidate route options
            opportunities = (
                ResourceOpportunityProvider.get_opportunities(hero, state)
                + ServiceOpportunityProvider.get_opportunities(hero, state)
            )
            candidates = AdventureRouteGenerator.generate(hero, state, opportunities=opportunities)

            # 2. Decide using service ( personality-biased scoring + project mapping )
            result = AdventureDecisionService.decide(
                hero, candidates, tick=tick,
                resource_nodes=state.resource_nodes,
                faction_directives=faction_directives,
                factions=factions,
            )

            # 2a. Write decision trace if writer is available (LIGHT+ mode observability)
            _writer = _resolved_writer
            if _writer is not None:
                scored_candidates = result.trace.get("scored_candidates", [])
                if scored_candidates:
                    _writer.write_trace(hero.id, tick, scored_candidates)

            # If no selection or deferred, do not update project.
            # On explicit DEFER_WITH_REASON, write a minimal EntityUpdate so that
            # event_extractor.py can emit defer_with_reason (reads "last_defer_reason").
            if not result.selected or result.selected.family == RouteFamily.DEFER_WITH_REASON:
                if result.selected and result.selected.family == RouteFamily.DEFER_WITH_REASON:
                    entity_updates[hero.id] = EntityUpdate(
                        entity_id=hero.id,
                        property_updates={
                            "last_defer_reason": result.selected.reason or "unknown",
                            "last_defer_tick": tick,
                        },
                    )
                continue

            # 3. Create strategic updates for the committed choice
            if result.proposed_project and result.proposed_objective:
                strat_upd = StrategicIntelligenceSystem.evaluate_project_switch(
                    hero, result.proposed_project, tick, state=state
                )
                if strat_upd is None:
                    continue

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
