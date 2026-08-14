from __future__ import annotations
from typing import Dict, Optional, Tuple

from src.ai.goals.base import GoalScorer, GoalScore
from src.core.state import EntityState, AuthoritativeState
from src.core.enums import EntityRole
from src.core.strategic import GoalKind
from src.domains.adventure.schema import RouteFamily
from src.engine.behavior_consumers import get_cognition_profile_definition, get_role_definition
from src.observability.cognition.decision_trace_writer import get_active_writer as _get_active_writer

# Per-process cache of cognition_profile_id -> supports_adventure_routing, shared across all
# entities and ticks. phase.py's own _supports_adventure_routing(entity, cache) expects a
# cache dict shared across one AdventureDecisionPhase.apply() call (phase.py:83-96, confirmed
# read directly: "cache is a per-apply()-call dict keyed by cognition_profile_id"). This scorer
# is invoked once per entity per tick via GoalRegistry.get_all_scores(entity, state)
# (base.py:46-50) -- there is no natural per-tick shared cache object at this call site
# (investigation.md Risk #3). Cognition profile definitions are static content for the run's
# duration, so a module-level dict persisting across ticks is a safe substitute, not a
# correctness risk.
_PROFILE_ELIGIBILITY_CACHE: Dict[str, bool] = {}

# Dedicated tier-5-competition normalization ceiling for AdventureGoalScorer.score(), decoupled
# from src.systems.strategic_systems.intelligence._ADVENTURE_ROUTE_SCORE_MAX (TCK-20260813-
# ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5). _ADVENTURE_ROUTE_SCORE_MAX stays 2.9 and
# continues to serve only _score_scale_max()'s Generalized Bypass gate purpose in
# evaluate_project_switch() -- do not reuse it here, and do not let a future scorer reuse THIS
# constant for an unrelated purpose either (that reuse pattern is what caused this ticket).
# Value derived in plan.md Step 1: max(empirical raw_score corpus maximum across
# simq_routing_test/hero_guild_routing x seeds{42,123,456}_500t, 2.4 theoretical safety floor
# derived from RECOVER's own real max-urgency ceiling (healing=CRITICAL + rest_inn benefit=1.0)
# -- see plan.md Step 1b for the full per-need-key urgency-tier table). Empirical max measured
# this session was 0.7439 (well below the theoretical floor), so the floor of 2.4 governs.
_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX: float = 2.4


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


class AdventureGoalScorer(GoalScorer):
    """
    GoalScorer wrapper around AdventureDecisionService.decide() (src/domains/adventure/
    service.py), registered under GoalKind.ADVENTURE_ROUTE as one candidate among many in tier 5
    of StrategicIntelligenceSystem.evaluate_strategic_intent()
    (src/systems/strategic_systems/intelligence.py:1355). See
    docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md.
    """

    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        if not _supports_adventure_routing(entity, _PROFILE_ELIGIBILITY_CACHE):
            return GoalScore(kind=GoalKind.ADVENTURE_ROUTE, utility=0.0, target_id=None)

        # MUST be a lazy (function-local) import, not top-level: intelligence.py's own
        # top-level `from src.ai.goals import GoalRegistry` (intelligence.py:77) means a
        # top-level import here of intelligence.py's constants would depend on which module
        # happens to be imported first process-wide -- a fragile, easy-to-silently-break
        # ordering dependency. Deferring to call time (after all modules have finished
        # loading at import time) removes the fragility entirely. Matches this codebase's own
        # established convention: every scorer in src/ai/goals/scorers.py already does
        # function-local imports for cross-module concerns (e.g. SpatialQueryService imported
        # inside RecoverScorer.score(), scorers.py:181).
        from src.systems.strategic_systems.intelligence import _GOAL_UTILITY_SCORE_MAX
        from src.domains.adventure.generator import AdventureRouteGenerator
        from src.domains.adventure.service import AdventureDecisionService
        from src.world.providers.resources import ResourceOpportunityProvider
        from src.world.providers.services import ServiceOpportunityProvider

        # Replicates the deleted AdventureDecisionPhase.apply()'s opportunities -> generate ->
        # decide sequence exactly, for this single entity (generator.py, service.py unchanged).
        # This IS the live, sole adventure-decision path today (TCK-20260811-DELETE-ADVENTURE-
        # DECISION-PHASE deleted AdventureDecisionPhase and cut over to this scorer). It is
        # reached unconditionally, every tick, for every entity eligible per
        # _supports_adventure_routing() above -- not gated behind ENABLE_ADVENTURE_ROUTING or
        # any other flag (see docs/parity_ledger/strategic_cognition.yaml STRAT-252).
        #
        # faction_directives is NOT threaded through here: unlike the deleted phase's apply(),
        # which received it as a pipeline-level artifact computed earlier in the same tick by
        # FactionDecisionPhase.execute() (pipeline.py:181), there is no `state.faction_directives`
        # attribute for this GoalScorer.score(entity, state) call signature to read.
        # decide()'s own faction_directives parameter already defaults to None (service.py:36),
        # so passing None here is a disclosed, intentional simplification -- live and current,
        # not a placeholder awaiting a follow-up wiring ticket. See
        # docs/mechanics/04_strategic_cognition.md §6.10 and docs/systems/faction_contract.md
        # for the full disclosure of what this means for faction-directive urgency scoring.
        opportunities = (
            ResourceOpportunityProvider.get_opportunities(entity, state)
            + ServiceOpportunityProvider.get_opportunities(entity, state)
        )
        candidates = AdventureRouteGenerator.generate(entity, state, opportunities=opportunities)
        result = AdventureDecisionService.decide(
            entity,
            candidates,
            tick=state.tick,
            resource_nodes=state.resource_nodes,
            faction_directives=None,
            factions=state.factions,
        )

        # Risk #1 resolution (plan.md Step 3 decision, PORT): mirrors phase.py's own
        # decision-trace-writer call (formerly phase.py:147-152), the only writer to
        # decision_trace.jsonl anywhere in the codebase. Written unconditionally for every
        # entity this scorer evaluates, before the DEFER_WITH_REASON/target resolution branches
        # below -- matching AdventureDecisionPhase.apply()'s old per-hero loop, which recorded
        # the trace before checking whether the result was DEFER_WITH_REASON.
        _writer = _get_active_writer()
        if _writer is not None:
            scored_candidates = result.trace.get("scored_candidates", [])
            if scored_candidates:
                _writer.write_trace(entity.id, state.tick, scored_candidates)

        selected = result.selected
        if selected is None or selected.family == RouteFamily.DEFER_WITH_REASON:
            # AC5: ineligible/DEFER_WITH_REASON never clear the 20.0 tier-5 floor.
            return GoalScore(
                kind=GoalKind.ADVENTURE_ROUTE,
                utility=0.0,
                target_id=None,
                metadata={
                    "route_family": RouteFamily.DEFER_WITH_REASON,
                    "raw_score": selected.score if selected else 0.0,
                },
            )

        raw_score = selected.score
        family = selected.family

        # Risk #1 resolution (plan.md decision, REVISED 2026-08-11 after an
        # architecture-reviewer pass -- fix belongs here, in the scorer's own target_id/
        # target_pos construction, NOT in the shared floor gate at intelligence.py:1373, per
        # investigation.md's Anti-Drift Hazards). RECOVER (forced, generator.py:98-109),
        # ASK_INFORMATION (forced, generator.py:111-123), and FORM_PARTY (always,
        # generator.py:125-163) never populate target_node_id/source_opportunity_ids
        # (confirmed by reading generator.py directly). decide() then leaves target=None
        # (service.py:134-140) and target_pos is never set at all, for any route
        # (service.py:135, confirmed unconditional). Left as-is, these three families would
        # always fail intelligence.py:1373's target-presence check regardless of utility.
        #
        # Synthesizing target_id ALONE is not sufficient (this was the plan's original,
        # reviewer-rejected version): it clears the target-presence check but leaves
        # target_pos=None, which RouteToProjectMapper.map_to_states() (mapper.py:88-95) commits
        # verbatim into ObjectiveState.target_position, and
        # TacticalDecisionSystem._resolve_target_position() (tactical.py:702-753) can never
        # recover from int()/ast.literal_eval() parsing since target_id is neither -- its only
        # remaining fallback IS target_position (tactical.py:751-752), which is also None. The
        # committed project then wins tier-5 arbitration and locks the slot, but tactical.py's
        # `if target_pos:` guard (tactical.py:221, and again at 275 for the non-REACH_LOCATION
        # branch) is False every tick, so the entity never even starts navigating -- it stalls
        # forever. This is the exact "wins but stalls" defect the reviewer traced end-to-end.
        #
        # Fix: pair the placeholder target_id with a REAL target_pos, sourced the same way the
        # codebase's own working precedent already does it -- TownScorer pairs
        # target_id="town_center" with target_pos=state.town_center (scorers.py:98);
        # RecoverScorer pairs a real building id (or "town_center") with
        # target_pos=best_bldg.position or state.town_center (scorers.py:181-186). With a real
        # target_pos, _resolve_target_position()'s node-3 fallback (tactical.py:751-752)
        # resolves it into real navigation -- node_id/building_id stay None, which is the SAME
        # documented, accepted limitation tactical_contract.md §7 already describes for
        # TownScorer's own "town_center" winners (arrival dispatches to a bare idle EntityUpdate,
        # not INTERACT/EAT/REST) -- not a new gap, an existing accepted one these 3 families now
        # share with TownScorer. This makes the candidate genuinely tactically actionable
        # (navigates, then reaches the same accepted idle-arrival state TownScorer winners already
        # reach) instead of a permanent dead lock.
        if selected.target_node_id is not None:
            target_id = str(selected.target_node_id)
            target_pos = None
        elif selected.source_opportunity_ids:
            target_id = selected.source_opportunity_ids[0]
            target_pos = None
        else:
            target_id = f"adventure:{family.value}"
            target_pos = AdventureGoalScorer._resolve_placeholder_target_pos(family, entity, state)

        utility = min(
            _GOAL_UTILITY_SCORE_MAX,
            (raw_score / _ADVENTURE_ROUTE_TIER5_COMPETITION_MAX) * _GOAL_UTILITY_SCORE_MAX,
        )

        return GoalScore(
            kind=GoalKind.ADVENTURE_ROUTE,
            utility=utility,
            target_id=target_id,
            target_pos=target_pos,
            metadata={"route_family": family, "raw_score": raw_score},
        )

    @staticmethod
    def _resolve_placeholder_target_pos(
        family: RouteFamily, entity: EntityState, state: AuthoritativeState
    ) -> Optional[Tuple[float, float]]:
        """
        Real target_pos source for the 3 route families that never carry a
        target_node_id/source_opportunity_ids (see the Risk #1 comment block in score() above).
        Mirrors the SAME real data sources RecoverScorer/TownScorer already use
        (src/ai/goals/scorers.py:98,163,186, confirmed read directly) -- deliberately not a
        synthetic placeholder position, per the architecture-reviewer's explicit instruction to
        "read RecoverScorer/TownScorer directly to see what real position data they pull from
        entity/state, and use the same kind of real, available field."
        """
        from src.domains.adventure.schema import RouteFamily as _RF

        if family == _RF.RECOVER:
            # Same source as RecoverScorer's own no-target_node_id path (scorers.py:181-186):
            # nearest inn if one exists, else town_center. "Recovering" plausibly means going to
            # a place of rest, not staying in place -- mirrors the existing scorer exactly rather
            # than inventing a new convention.
            from src.engine.spatial_query import SpatialQueryService
            best_bldg = SpatialQueryService.nearest_building(state, entity.navigation.position, "inn")
            return best_bldg.position if best_bldg else state.town_center

        if family == _RF.ASK_INFORMATION:
            # Same source as TownScorer's target_pos (scorers.py:98): information-gathering is a
            # town-centered activity in this codebase's existing convention (no dedicated
            # "information source" building exists in the real content corpus -- confirmed by
            # GuildNeedScorer's own docstring, scorers.py:233, noting no world ever declares a
            # dedicated "guild" building either, and using town_hall/town_center instead).
            return state.town_center

        if family == _RF.FORM_PARTY:
            # Real ally position, mirroring generator.py's OWN FORM_PARTY candidate-eligibility
            # filter exactly (generator.py:126-137, confirmed read directly: non-self,
            # non-MONSTER role, alive). generator.py only generates a FORM_PARTY route when this
            # candidate list is non-empty (generator.py:138 `if candidates:`), and score() reads
            # the same `state` snapshot generate() just ran against synchronously within the same
            # call -- so a non-empty candidate list is expected here too. Nearest by Manhattan
            # distance, matching this codebase's existing nearest-selection convention (e.g.
            # CombatEngageScorer's `min(hostiles, key=...)`, scorers.py:113-117). Defensive
            # fallback to the entity's own current position (organizing/waiting in place) if,
            # against expectation, no candidate remains -- never re-raises or returns None, since
            # a None here would silently reproduce the exact "stalls forever" defect being fixed.
            from src.core.enums import EntityRole
            candidates = [
                e for e in state.entities.values()
                if e.id != entity.id
                and getattr(e.identity, "role", EntityRole.MONSTER) != EntityRole.MONSTER
                and getattr(e, "is_alive", True)
            ]
            if candidates:
                nearest = min(
                    candidates,
                    key=lambda e: abs(e.navigation.position[0] - entity.navigation.position[0])
                    + abs(e.navigation.position[1] - entity.navigation.position[1]),
                )
                return nearest.navigation.position
            return entity.navigation.position

        return None
