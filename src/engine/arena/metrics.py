from __future__ import annotations
import math
from typing import Dict, List, Optional
from src.core.models.world_state import WorldState
from src.core.models.arena import ArenaResult, ScenarioReport

class MetricService:
    """Service for extracting and aggregating behavioral metrics from arena runs. [Milestone 6]"""

    @staticmethod
    def extract_final_metrics(world: WorldState, ticks: int) -> Dict[str, float]:
        """Extract high-level metrics from a finished simulation world."""
        metrics = {}
        
        # Calculate clumping / spatial entropy
        # We look at the average distance between all alive combatants
        alive = [e for e in world.entities.values() if e.combat.alive and e.kind != "generator"]
        if len(alive) > 1:
            total_dist = 0.0
            pairs = 0
            for i in range(len(alive)):
                for j in range(i + 1, len(alive)):
                    total_dist += alive[i].spatial.pos.manhattan(alive[j].spatial.pos)
                    pairs += 1
            metrics["clumping_factor"] = total_dist / pairs if pairs > 0 else 0.0
        else:
            metrics["clumping_factor"] = 0.0
            
        return metrics

    @staticmethod
    def detect_stall(world: WorldState, recent_hps: Dict[int, float], recent_positions: Dict[int, Any]) -> bool:
        """Returns True if no entity has meaningfully changed state."""
        for eid, ent in world.entities.items():
            if not ent.combat.alive:
                continue
            
            # HP check
            prev_hp = recent_hps.get(eid)
            if prev_hp is not None and ent.combat.hp != prev_hp:
                return False # Activity detected
            
            # Position check
            prev_pos = recent_positions.get(eid)
            if prev_pos is not None and ent.spatial.pos != prev_pos:
                return False # Activity detected
                
        return True # Every alive entity is stagnant
