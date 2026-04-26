from __future__ import annotations
from typing import Dict, Any, List
from dataclasses import dataclass, field
from src_legacy.core.state import AuthoritativeState

@dataclass
class WorldMetrics:
    """Snapshot of simulation dynamics."""
    tick: int
    total_entities: int
    alive_entities: int
    total_gold: float
    total_trauma: float
    avg_influence: float
    project_counts: Dict[str, int] = field(default_factory=dict) # Kind -> Count
    faction_power: Dict[int, float] = field(default_factory=dict) # FactionID -> Influence

class MetricsService:
    """
    Extracts high-level behavioral and dynamical metrics from V2 state.
    Used for certification reports and strategy auditing.
    """

    @staticmethod
    def extract_metrics(state: AuthoritativeState) -> WorldMetrics:
        """Analyze current state and produce metrics snapshot."""
        alive = [e for e in state.entities.values() if e.combat.alive]
        
        # 1. Resource & Trauma
        total_gold = sum(e.inventory.gold for e in state.entities.values())
        total_trauma = sum(r.trauma_score for r in state.regions.values())
        
        # 2. Influence & Faction Power
        avg_influence = 0.0
        faction_power = {}
        if state.regions:
            avg_influence = sum(r.influence for r in state.regions.values()) / len(state.regions)
            for r in state.regions.values():
                if r.owner_faction_id is not None:
                    faction_power[r.owner_faction_id] = faction_power.get(r.owner_faction_id, 0.0) + r.influence

        # 3. Project Distribution
        project_counts = {}
        for e in alive:
            for p in e.strategic.projects.values():
                project_counts[p.kind] = project_counts.get(p.kind, 0) + 1

        return WorldMetrics(
            tick=state.tick,
            total_entities=len(state.entities),
            alive_entities=len(alive),
            total_gold=total_gold,
            total_trauma=total_trauma,
            avg_influence=avg_influence,
            project_counts=project_counts,
            faction_power=faction_power
        )

    @staticmethod
    def detect_strategy_shifts(prior_metrics: WorldMetrics, current_metrics: WorldMetrics) -> List[str]:
        """Detect significant shifts in global strategy or dynamics."""
        shifts = []
        # Example: Large trauma spike
        if current_metrics.total_trauma > prior_metrics.total_trauma + 10.0:
            shifts.append("HIGH_TRAUMA_SPIKE")
        
        # Example: Faction flip
        if current_metrics.faction_power.keys() != prior_metrics.faction_power.keys():
            shifts.append("FACTION_CONTROL_SHIFT")
            
        return shifts
