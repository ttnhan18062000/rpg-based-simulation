from __future__ import annotations
from src.ai.goals.base import GoalScorer, GoalScore
from src.core.state import EntityState, AuthoritativeState
from src.core.strategic import GoalKind

class HarvestScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        # Optimized v2: Early exit if entity is at capacity
        if len(entity.inventory.items) >= entity.inventory.max_slots:
            return GoalScore(kind=GoalKind.HARVESTING, utility=0.0)

        from src.core.strategic import ProjectStatus
        curr_proj_id = entity.strategic.current_project_id
        if curr_proj_id:
            proj = entity.strategic.projects.get(curr_proj_id)
            if proj and proj.status == ProjectStatus.ACTIVE and proj.kind == "harvesting" and proj.active_objective_id:
                try:
                    nid = int(proj.active_objective_id.split("_")[-1])
                    node = state.resource_nodes.get(nid)
                    if node and node.remaining_charges > 0 and node.cooldown_remaining <= 0:
                        px, py = entity.navigation.position
                        dist = max(1.0, abs(node.position[0] - px) + abs(node.position[1] - py))
                        return GoalScore(kind=GoalKind.HARVESTING, utility=50.0 / dist, target_id=str(nid), target_pos=node.position)
                except Exception:
                    pass

        from src.engine.spatial_query import SpatialQueryService
        best_node = SpatialQueryService.nearest_resource_node(state, entity.navigation.position)
        if best_node:
            dist = max(1.0, abs(best_node.position[0] - entity.navigation.position[0]) + abs(best_node.position[1] - entity.navigation.position[1]))
            best_score = 50.0 / dist
            return GoalScore(kind=GoalKind.HARVESTING, utility=best_score, target_id=str(best_node.id), target_pos=best_node.position)
        
        return GoalScore(kind=GoalKind.HARVESTING, utility=0.0)

class SleepScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        bio = entity.biological
        # Early exit: if sleep debt is low, don't bother searching
        if bio.sleep_debt < 20.0:
            return GoalScore(kind=GoalKind.FATIGUE, utility=bio.sleep_debt)

        utility = bio.sleep_debt
        
        # Night bias
        is_night = (state.world_time >= 1800 or state.world_time < 600)
        if is_night:
            utility += 30.0
            
        from src.engine.spatial_query import SpatialQueryService
        best_bldg = SpatialQueryService.nearest_building(state, entity.navigation.position, "inn")
        if best_bldg:
            return GoalScore(kind=GoalKind.FATIGUE, utility=utility, target_id=str(best_bldg.id), target_pos=best_bldg.position)
                    
        return GoalScore(kind=GoalKind.FATIGUE, utility=utility)

class EatScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        bio = entity.biological
        # Early exit: if hunger is low, don't bother searching
        if bio.hunger < 20.0:
            return GoalScore(kind=GoalKind.HUNGER, utility=bio.hunger)

        utility = bio.hunger
        
        from src.engine.spatial_query import SpatialQueryService
        best_bldg = SpatialQueryService.nearest_building(state, entity.navigation.position, "tavern")
        if best_bldg:
            return GoalScore(kind=GoalKind.HUNGER, utility=utility, target_id=str(best_bldg.id), target_pos=best_bldg.position)
                    
        return GoalScore(kind=GoalKind.HUNGER, utility=utility)


class SocialScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        # Placeholder for social interaction utility
        return GoalScore(kind=GoalKind.SOCIAL, utility=10.0)

class TownScorer(GoalScorer):
    """Scores the need to return to town for services."""
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        bio = entity.biological
        inv = entity.inventory
        
        # 1. Biological Needs
        utility = (bio.sleep_debt + bio.hunger) / 2.0
        
        # 2. Inventory Fullness
        inv_ratio = len(inv.items) / inv.max_slots if inv.max_slots > 0 else 1.0
        utility += inv_ratio * 40.0
        
        # 3. Low HP
        hp_ratio = entity.combat.hp / entity.combat.max_hp if entity.combat.max_hp > 0 else 1.0
        if hp_ratio < 0.5:
            utility += (1.0 - hp_ratio) * 60.0
            
        # Target is town center
        return GoalScore(kind=GoalKind.TOWN_RETURN, utility=utility, target_id="town_center", target_pos=state.town_center)


class CombatEngageScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        from src.engine.domain_logic import SimulationDomainLogic
        from src.engine.cognition import SensoryFilter
        
        raw_neighbors = SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0)
        neighbors = SensoryFilter.filter_saliency(entity, raw_neighbors, max_targets=5)
        hostiles = [n for n in neighbors if n.identity.faction != entity.identity.faction and n.combat.alive]
        
        if not hostiles:
            return GoalScore(kind=GoalKind.COMBAT_ENGAGE, utility=0.0)
            
        nearest_hostile = min(
            hostiles,
            key=lambda n: abs(n.navigation.position[0] - entity.navigation.position[0]) +
                          abs(n.navigation.position[1] - entity.navigation.position[1])
        )
        
        utility = 40.0
        utility += entity.identity.personality.bravery * 40.0
        
        # Stamina contribution
        if hasattr(entity, "stamina") and entity.stamina.max_stamina > 0:
            utility += (entity.stamina.current / entity.stamina.max_stamina) * 20.0
            
        utility = max(0.0, utility)
        return GoalScore(
            kind=GoalKind.COMBAT_ENGAGE,
            utility=utility,
            target_id=str(nearest_hostile.id),
            target_pos=nearest_hostile.navigation.position
        )


class CombatRetreatScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        from src.engine.domain_logic import SimulationDomainLogic
        from src.engine.cognition import SensoryFilter, AppraisalSystem
        
        raw_neighbors = SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0)
        neighbors = SensoryFilter.filter_saliency(entity, raw_neighbors, max_targets=5)
        region_trauma = SimulationDomainLogic.get_region_trauma(state, entity.navigation.position)
        
        emotion = AppraisalSystem.evaluate_emotional_state(
            entity,
            neighbors,
            region_trauma=region_trauma,
            social_context=entity.social
        )
        
        hp_ratio = entity.combat.hp / max(1, entity.combat.max_hp)
        if hp_ratio >= 0.5 and not emotion.is_fleeing:
            return GoalScore(kind=GoalKind.COMBAT_RETREAT, utility=0.0)
            
        utility = (1.0 - hp_ratio) * 100.0
        utility += emotion.panic_level * 50.0
        utility -= entity.identity.personality.bravery * 30.0
        
        utility = max(0.0, utility)
        return GoalScore(
            kind=GoalKind.COMBAT_RETREAT,
            utility=utility,
            target_id="town_center",
            target_pos=state.town_center
        )


class RecoverScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        hp_ratio = entity.combat.hp / max(1, entity.combat.max_hp)
        stamina_ratio = 1.0
        if hasattr(entity, "stamina") and entity.stamina.max_stamina > 0:
            stamina_ratio = entity.stamina.current / entity.stamina.max_stamina
            
        if hp_ratio >= 0.9 and stamina_ratio >= 0.9:
            return GoalScore(kind=GoalKind.RECOVER, utility=0.0)
            
        utility = (1.0 - hp_ratio) * 80.0
        utility += (1.0 - stamina_ratio) * 40.0
        
        from src.engine.spatial_query import SpatialQueryService
        best_bldg = SpatialQueryService.nearest_building(state, entity.navigation.position, "inn")
        if best_bldg:
            return GoalScore(kind=GoalKind.RECOVER, utility=utility, target_id=str(best_bldg.id), target_pos=best_bldg.position)
            
        return GoalScore(kind=GoalKind.RECOVER, utility=utility, target_id="town_center", target_pos=state.town_center)


class ResolveBlockerScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        # Blockers a timed-out resolve_blocker project already failed to resolve stay
        # suppressed for a while (BlockerState.suppression_until_tick) rather than
        # immediately re-winning at the same flat utility every tick -- without this, a
        # resolve_blocker project that can never actually complete (e.g. an "access"
        # blocker with no parseable coordinates) starves every other goal indefinitely.
        active_blockers = [
            b for b in entity.strategic.blockers.values()
            if not b.resolved and b.suppression_until_tick <= state.tick
        ]
        if not active_blockers:
            return GoalScore(kind=GoalKind.RESOLVE_BLOCKER, utility=0.0)
            
        blocker = active_blockers[0]
        target_pos = None
        target_id = str(blocker.id)
        
        if blocker.kind == "access":
            import ast
            try:
                coords = ast.literal_eval(blocker.subject)
                if isinstance(coords, tuple) and len(coords) == 2:
                    target_pos = (float(coords[0]), float(coords[1]))
            except:
                pass
                
        if blocker.kind == "material":
            match_lead = next((l for l in entity.strategic.leads.values() if l.subject == blocker.subject and l.kind == 'location'), None)
            if match_lead:
                try:
                    coords = tuple(map(float, match_lead.detail.split(',')))
                    target_pos = coords
                except:
                    pass
                    
        if target_pos is None:
            target_pos = state.town_center

        return GoalScore(
            kind=GoalKind.RESOLVE_BLOCKER,
            utility=80.0,
            target_id=target_id,
            target_pos=target_pos
        )


class GuildNeedScorer(GoalScorer):
    """Scores the need to visit the guild for quests/intel (TCK-20260807-QUEST-GUILDACTION-
    DEAD-WIRING). Gated behind ENABLE_GUILD_QUEST_GENERATION (default OFF) — a new gameplay
    behavior, not a validated replacement of existing behavior.

    Targets `town_hall` (not a dedicated "guild" building — no world in the real content corpus
    ever declares one; `town_hall` is present in every world) via
    `SpatialQueryService.nearest_building()`, the SAME pattern `EatScorer`/`SleepScorer` already
    use successfully — `target_id=str(building.id)` is a real int-castable building ID,
    correctly resolved by TacticalDecisionSystem._resolve_target_position() without any change
    to that shared function (unlike TownScorer's own broken "town_center" string convention,
    left untouched — a separate, disclosed, deferred bug).

    Utility signal mirrors GuildAction.visit()'s own existing precondition: spare project
    capacity. Moderate, non-urgent magnitude — Tier 4 (Economic) per
    docs/mechanics/04_strategic_cognition.md's own goal hierarchy, comparable to harvesting."""
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        flags = getattr(state, "feature_flags", None) or {}
        if flags.get("ENABLE_GUILD_QUEST_GENERATION", "OFF") != "ON":
            return GoalScore(kind=GoalKind.GUILD, utility=0.0)

        strat = entity.strategic
        if len(strat.projects) >= strat.profile.max_active_projects:
            return GoalScore(kind=GoalKind.GUILD, utility=0.0)

        from src.engine.spatial_query import SpatialQueryService
        best_bldg = SpatialQueryService.nearest_building(state, entity.navigation.position, "town_hall")
        if not best_bldg:
            return GoalScore(kind=GoalKind.GUILD, utility=0.0)

        return GoalScore(kind=GoalKind.GUILD, utility=25.0, target_id=str(best_bldg.id), target_pos=best_bldg.position)

