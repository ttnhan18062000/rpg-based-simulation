# src/world/threat.py
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING
from src.core.enums import Domain

from src.core.updates import WorldUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, RegionState

class ThreatService:
    """
    Manages regional threat (long-term) and retaliation pressure (short-term).
    """
    
    THREAT_DECAY_RATE = 0.01
    PRESSURE_COOLING_RATE = 0.1

    @staticmethod
    def process_threat_evolution(state: AuthoritativeState, region: RegionState) -> WorldUpdate | None:
        """
        Calculates threat decay and retaliation cooling for a region.
        """
        # Rule: Only decay during peaceful state
        # 1. No boss alive in region
        # 2. No active raid (tracked by high retaliation pressure)
        
        # Check if any boss exists in this region
        has_boss = any(e.kind == "world_boss" and e.active and e.combat.alive 
                       for e in state.entities.values())
        
        w_upd = WorldUpdate(region_id=region.id)
        changed = False
        
        # 1. Retaliation Pressure Cooling (Always cools unless active fighting)
        if region.retaliation_pressure > 0:
            w_upd = replace(w_upd, retaliation_pressure_delta=-ThreatService.PRESSURE_COOLING_RATE)
            changed = True
            
        # 2. Regional Threat Decay (Only during peaceful state)
        is_peaceful = not has_boss and region.retaliation_pressure < 5.0
        
        if is_peaceful and region.trauma_score > 0:
            w_upd = replace(w_upd, trauma_delta=-ThreatService.THREAT_DECAY_RATE)
            changed = True
            
        return w_upd if changed else None

    @staticmethod
    def record_kill(state: AuthoritativeState, region_id: str) -> WorldUpdate:
        """
        Increases retaliation pressure when a faction member is killed.
        """
        # Rule: monster killed -> short-term retaliation pressure increases
        return WorldUpdate(
            region_id=region_id,
            retaliation_pressure_delta=1.0 # 1.0 per kill
        )
