# Compliance IDs: WORLD-006
from __future__ import annotations
from dataclasses import replace
from typing import Dict, List, Optional, Tuple
from src.core.state import (
    AuthoritativeState, RegionState, LocalScarState
)

class RegionalConsequenceService:
    """World-tier service managing persistent world trauma and stability."""

    @staticmethod
    def process_recovery(state: AuthoritativeState) -> Tuple[Dict[str, RegionState], Dict[int, LocalScarState]]:
        """
        Process time-based recovery for regional danger and local scars.
        Logic ID: WORLD-006 (Regional trauma and stability recovery over time)
        """
        new_regions = {}
        new_scars = {}

        # 1. Local Scars Recovery
        for scar_id, scar in state.local_scars.items():
            if state.tick > scar.created_tick:
                new_severity = max(0.0, scar.severity - scar.recovery_rate)
                if new_severity > 0.01:
                    new_scars[scar_id] = replace(scar, severity=new_severity)
                # Scars below 0.01 are implicitly removed by not being added to new_scars
            else:
                new_scars[scar_id] = scar

        # 2. Regional Consequences Recovery
        for region_id, region in state.regions.items():
            new_trauma = region.trauma_score
            new_stability = region.stability

            if new_trauma > 0:
                # Decay towards zero
                new_trauma = max(0.0, new_trauma - 0.0005)
            
            # Stability slowly recovers towards 1.0
            new_stability = min(1.0, new_stability + 0.0001)

            if new_trauma != region.trauma_score or new_stability != region.stability:
                new_regions[region_id] = replace(region, trauma_score=new_trauma, stability=new_stability)
            else:
                new_regions[region_id] = region

        return new_regions, new_scars

    @staticmethod
    def create_battlefield_scar(
        state: AuthoritativeState, 
        pos: Tuple[float, float], 
        level: int,
        event_id: str
    ) -> LocalScarState:
        """Create a battlefield scar from a death event."""
        # Severity scales with level
        severity = min(1.0, 0.2 + (level * 0.02))
        scar_id = len(state.local_scars) + 1
        
        return LocalScarState(
            id=scar_id,
            position=pos,
            kind="BATTLE_FIELD",
            severity=severity,
            created_tick=state.tick,
            source_event_id=event_id,
            recovery_rate=0.0005
        )

    @staticmethod
    def create_raid_scar(
        state: AuthoritativeState, 
        pos: Tuple[float, float],
        event_id: str
    ) -> LocalScarState:
        """Create a raid damage scar from a town raid."""
        scar_id = len(state.local_scars) + 1
        return LocalScarState(
            id=scar_id,
            position=pos,
            kind="RAID_DAMAGE",
            severity=0.8,
            created_tick=state.tick,
            source_event_id=event_id,
            recovery_rate=0.0002
        )
