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

        best_node_id = None
        best_node_pos = None
        best_score = 0.0
        
        grid = getattr(state, "_active_nodes_grid", None)
        if grid is None:
            grid = {}
            for n in state.resource_nodes.values():
                if n.remaining_charges > 0 and n.cooldown_remaining <= 0:
                    cx, cy = int(n.position[0] // 20), int(n.position[1] // 20)
                    grid.setdefault((cx, cy), []).append((n.position[0], n.position[1], str(n.id)))
            try: object.__setattr__(state, "_active_nodes_grid", grid)
            except: pass

        px, py = entity.navigation.position
        ecx, ecy = int(px // 20), int(py // 20)
        
        sorted_buckets = sorted(grid.keys(), key=lambda k: abs(k[0] - ecx) + abs(k[1] - ecy))
        for cx, cy in sorted_buckets:
            min_x, max_x = cx * 20, cx * 20 + 20
            min_y, max_y = cy * 20, cy * 20 + 20
            dx_box = max(0.0, min_x - px, px - max_x)
            dy_box = max(0.0, min_y - py, py - max_y)
            if best_score > 0 and (dx_box + dy_box) >= 50.0 / best_score:
                continue
                
            for nx, ny, nid in grid[(cx, cy)]:
                dx = abs(nx - px)
                if best_score > 0 and dx >= 50.0 / best_score:
                    continue
                dy = abs(ny - py)
                dist = max(1.0, dx + dy)
                node_score = 50.0 / dist
                if node_score > best_score:
                    best_score = node_score
                    best_node_id = nid
                    best_node_pos = (nx, ny)
        
        return GoalScore(kind="harvesting", utility=best_score, target_id=best_node_id, target_pos=best_node_pos)

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
            
        bldgs = getattr(state, "_inns_cache", None)
        if bldgs is None:
            bldgs = [(b.position[0], b.position[1], str(b.id)) for b in state.buildings.values() if b.kind == "inn"]
            try: object.__setattr__(state, "_inns_cache", bldgs)
            except: pass

        # Find nearest inn
        best_building_id = None
        best_building_pos = None
        min_dist = 999.0
        px, py = entity.navigation.position
        for bx, by, bid in bldgs:
            dist = abs(bx - px) + abs(by - py)
            if dist < min_dist:
                min_dist = dist
                best_building_id = bid
                best_building_pos = (bx, by)
                    
        return GoalScore(kind="fatigue", utility=utility, target_id=best_building_id, target_pos=best_building_pos)

class EatScorer(GoalScorer):
    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        bio = entity.biological
        # Early exit: if hunger is low, don't bother searching
        if bio.hunger < 20.0:
            return GoalScore(kind="hunger", utility=bio.hunger)

        utility = bio.hunger
        
        bldgs = getattr(state, "_taverns_cache", None)
        if bldgs is None:
            bldgs = [(b.position[0], b.position[1], str(b.id)) for b in state.buildings.values() if b.kind == "tavern"]
            try: object.__setattr__(state, "_taverns_cache", bldgs)
            except: pass

        # Find nearest tavern
        best_building_id = None
        best_building_pos = None
        min_dist = 999.0
        px, py = entity.navigation.position
        for bx, by, bid in bldgs:
            dist = abs(bx - px) + abs(by - py)
            if dist < min_dist:
                min_dist = dist
                best_building_id = bid
                best_building_pos = (bx, by)
                    
        return GoalScore(kind="hunger", utility=utility, target_id=best_building_id, target_pos=best_building_pos)

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
