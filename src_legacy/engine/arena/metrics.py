from __future__ import annotations
import math
from typing import Dict, List, Optional
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.models.arena import ArenaResult, ScenarioReport

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
    def detect_stall(world: WorldState, recent_hps: Dict[int, float], recent_positions: Dict[int, tuple[int, int]]) -> bool:
        """Returns True if no entity has meaningfully changed state."""
        for eid, ent in world.entities.items():
            if not ent.combat.alive:
                continue
            
            # HP check: Only treat HP DECREASES (damage) as activity. 
            # Regeneration/Resting without movement or combat is still a stall.
            prev_hp = recent_hps.get(eid)
            if prev_hp is not None and ent.combat.hp < prev_hp:
                return False 
            
            # Position check
            prev_pos = recent_positions.get(eid)
            if prev_pos is not None:
                # Use from_any to normalize access
                from src_legacy.core.models.vectors import Vector2
                pos = Vector2.from_any(ent.spatial.pos)
                curr_pos = (pos.x, pos.y)
                if curr_pos != prev_pos:
                    return False 
        
        return True
                
    @staticmethod
    def record_usage_stats() -> Dict[str, float]:
        """Capture current resource utilization for stability auditing. [Milestone 6]"""
        try:
            import psutil
            process = psutil.Process()
            info = process.memory_info()
            cpu = process.cpu_times()
            return {
                "rss_mb": info.rss / (1024 * 1024),
                "cpu_user": cpu.user,
                "cpu_system": cpu.system,
                "cpu_total": cpu.user + cpu.system
            }
        except (ImportError, Exception):
            return {"rss_mb": 0.0, "cpu_user": 0.0, "cpu_system": 0.0, "cpu_total": 0.0}
