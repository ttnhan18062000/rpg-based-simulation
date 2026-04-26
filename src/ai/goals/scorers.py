from __future__ import annotations
from src.ai.goals.base import GoalScorer, GoalScore
from src.core.state import EntityState, AuthoritativeState

class HarvestScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        best_node_id = None
        best_score = 0.0
        
        for node in state.resource_nodes.values():
            if node.remaining_charges > 0 and node.cooldown_remaining <= 0:
                # Proximity score
                dist = max(1.0, abs(node.position[0] - entity.position[0]) + abs(node.position[1] - entity.position[1]))
                node_score = 50.0 / dist
                if node_score > best_score:
                    best_score = node_score
                    best_node_id = str(node.id)
        
        return GoalScore(kind="harvesting", utility=best_score, target_id=best_node_id)

class SleepScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        bio = entity.biological
        utility = bio.sleep_debt # Base utility is sleep debt
        
        # Night bias
        is_night = (state.world_time >= 1800 or state.world_time < 600)
        if is_night:
            utility += 30.0
            
        # Find nearest inn
        best_building_id = None
        min_dist = 999.0
        for b in state.buildings.values():
            if b.kind == "inn":
                dist = abs(b.position[0] - entity.position[0]) + abs(b.position[1] - entity.position[1])
                if dist < min_dist:
                    min_dist = dist
                    best_building_id = str(b.id)
                    
        return GoalScore(kind="fatigue", utility=utility, target_id=best_building_id)

class EatScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        bio = entity.biological
        utility = bio.hunger
        
        # Find nearest tavern
        best_building_id = None
        min_dist = 999.0
        for b in state.buildings.values():
            if b.kind == "tavern":
                dist = abs(b.position[0] - entity.position[0]) + abs(b.position[1] - entity.position[1])
                if dist < min_dist:
                    min_dist = dist
                    best_building_id = str(b.id)
                    
        return GoalScore(kind="hunger", utility=utility, target_id=best_building_id)

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
        inv_ratio = len(inv.items) / inv.max_slots
        utility += inv_ratio * 40.0
        
        # 3. Low HP
        hp_ratio = entity.combat.hp / entity.combat.max_hp
        if hp_ratio < 0.5:
            utility += (1.0 - hp_ratio) * 60.0
            
        # Target is town center
        return GoalScore(kind="town_return", utility=utility, target_pos=state.town_center)
