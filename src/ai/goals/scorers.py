from __future__ import annotations
from src.ai.goals.base import GoalScorer, GoalScore
from src.core.state import EntityState, AuthoritativeState

class HarvestScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        # Optimized v2: Early exit if entity is at capacity
        if len(entity.inventory.items) >= entity.inventory.max_slots:
            return GoalScore(kind="harvesting", utility=0.0)

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
                        return GoalScore(kind="harvesting", utility=50.0 / dist, target_id=str(nid), target_pos=node.position)
                except Exception:
                    pass

        from src.engine.spatial_query import SpatialQueryService
        best_node = SpatialQueryService.nearest_resource_node(state, entity.navigation.position)
        if best_node:
            dist = max(1.0, abs(best_node.position[0] - entity.navigation.position[0]) + abs(best_node.position[1] - entity.navigation.position[1]))
            best_score = 50.0 / dist
            return GoalScore(kind="harvesting", utility=best_score, target_id=str(best_node.id), target_pos=best_node.position)
        
        return GoalScore(kind="harvesting", utility=0.0)

class SleepScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        bio = entity.biological
        # Early exit: if sleep debt is low, don't bother searching
        if bio.sleep_debt < 20.0:
            return GoalScore(kind="fatigue", utility=bio.sleep_debt)

        utility = bio.sleep_debt
        
        # Night bias
        is_night = (state.world_time >= 1800 or state.world_time < 600)
        if is_night:
            utility += 30.0
            
        from src.engine.spatial_query import SpatialQueryService
        best_bldg = SpatialQueryService.nearest_building(state, entity.navigation.position, "inn")
        if best_bldg:
            return GoalScore(kind="fatigue", utility=utility, target_id=str(best_bldg.id), target_pos=best_bldg.position)
                    
        return GoalScore(kind="fatigue", utility=utility)

class EatScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        bio = entity.biological
        # Early exit: if hunger is low, don't bother searching
        if bio.hunger < 20.0:
            return GoalScore(kind="hunger", utility=bio.hunger)

        utility = bio.hunger
        
        from src.engine.spatial_query import SpatialQueryService
        best_bldg = SpatialQueryService.nearest_building(state, entity.navigation.position, "tavern")
        if best_bldg:
            return GoalScore(kind="hunger", utility=utility, target_id=str(best_bldg.id), target_pos=best_bldg.position)
                    
        return GoalScore(kind="hunger", utility=utility)


class SocialScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        # Placeholder for social interaction utility
        return GoalScore(kind="social", utility=10.0)

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
        return GoalScore(kind="town_return", utility=utility, target_pos=state.town_center)
