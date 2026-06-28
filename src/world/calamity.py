# Compliance IDs: SUB-006, WORLD-023, WORLD-024, WORLD-025, WORLD-026, WORLD-027, WORLD-028, WORLD-063
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING, Dict
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, WorldUpdate
from src.core.enums import Domain

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.systems.world_systems.generator import EntityGenerator

class CalamityService:
    """
    Manages global world evolution, calamities, and macro threats.
    """
    
    MATURITY_INTERVAL = 1000
    CALAMITY_MIN_INTERVAL = 2000
    CALAMITY_RANDOM_CHANCE = 0.005
    CALAMITY_FORCE_INTERVAL = 5000
    
    @staticmethod
    def process_world_dynamics(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        """
        Processes maturity, calamity spawns, and regional intensity shifts.
        """
        updates = StateUpdate()
        
        # 1. Maturity Advancement
        if state.tick % CalamityService.MATURITY_INTERVAL == 0 and state.tick > 0:
            updates = updates.replace(maturity_set=state.maturity + 1)
            
        # 2. Calamity Spawn Check
        should_spawn = False
        if state.tick - state.last_calamity_tick >= CalamityService.CALAMITY_MIN_INTERVAL:
            if state.tick % CalamityService.CALAMITY_FORCE_INTERVAL == 0 and state.tick > 0:
                should_spawn = True
            
        if should_spawn:
            # Find high intensity region
            high_intensity_regions = [r for r in state.regions.values() if r.calamity_intensity > 0.3]
            if high_intensity_regions:
                # Sort by intensity
                target_region = max(high_intensity_regions, key=lambda r: r.calamity_intensity)
                
                # Spawn a boss
                boss = generator.spawn_monster(
                    state=state,
                    kind="world_boss",
                    pos=target_region.center,
                    difficulty_tier=4
                )
                
                updates = updates.replace(
                    entities_add=[boss],
                    last_calamity_tick_set=state.tick
                )
            
        return updates

    @staticmethod
    def apply_calamity_consequences(state: AuthoritativeState, recent_deaths: List[EntityState]) -> StateUpdate:
        """
        Increases regional calamity intensity when significant entities die.
        """
        world_updates = {}
        for entity in recent_deaths:
            from src.engine.legality import LegalityServiceV2
            region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
            if not region:
                continue
                
            # Calamity intensity increases on Hero death in high-hazard regions
            if entity.kind == "hero" and region.hazard_level > 0.5:
                intensity_delta = 0.05
                current_intensity = region.calamity_intensity
                world_updates[region.id] = WorldUpdate(
                    region_id=region.id,
                    calamity_intensity_set=min(1.0, current_intensity + intensity_delta)
                )
                
        return StateUpdate(world_updates=world_updates)


class CalamityPressurePropagator:
    """
    Seasonal propagation of calamity_intensity between adjacent regions (E52E).

    Every SEASONAL_PROPAGATION_INTERVAL ticks, each region with calamity_intensity
    above PROPAGATION_THRESHOLD spreads PROPAGATION_FACTOR * intensity to each
    adjacent neighbor (adjacency defined by RegionalPressureModel._are_adjacent,
    ADJACENCY_GAP=50 units).  The neighbor's intensity is capped at 1.0.
    """

    SEASONAL_PROPAGATION_INTERVAL: int = 500
    PROPAGATION_FACTOR: float = 0.15
    PROPAGATION_THRESHOLD: float = 0.10

    @staticmethod
    def propagate_seasonal(state: AuthoritativeState) -> StateUpdate:
        """Return a StateUpdate with calamity_intensity_set for affected neighbor regions.

        Returns a noop StateUpdate when tick % SEASONAL_PROPAGATION_INTERVAL != 0
        or when no regions meet the propagation threshold.
        """
        if state.tick == 0:
            return StateUpdate()
        if state.tick % CalamityPressurePropagator.SEASONAL_PROPAGATION_INTERVAL != 0:
            return StateUpdate()
        if not state.regions:
            return StateUpdate()

        from dataclasses import replace as dc_replace
        from src.domains.world_emergence.models import RegionalPressureModel

        factor = CalamityPressurePropagator.PROPAGATION_FACTOR
        threshold = CalamityPressurePropagator.PROPAGATION_THRESHOLD
        regions = list(state.regions.values())

        # Accumulate the maximum proposed intensity per neighbor across all sources.
        # Using max rather than sum prevents runaway amplification when multiple
        # high-intensity regions are adjacent to the same neighbor.
        proposed: dict[str, float] = {}
        for source in regions:
            if source.calamity_intensity < threshold:
                continue
            spread = source.calamity_intensity * factor
            for neighbor in regions:
                if neighbor.id == source.id:
                    continue
                if not RegionalPressureModel._are_adjacent(source, neighbor):
                    continue
                candidate = min(1.0, neighbor.calamity_intensity + spread)
                if candidate > proposed.get(neighbor.id, neighbor.calamity_intensity):
                    proposed[neighbor.id] = candidate

        if not proposed:
            return StateUpdate()

        world_updates: dict[str, WorldUpdate] = {}
        for r_id, new_intensity in proposed.items():
            world_updates[r_id] = WorldUpdate(
                region_id=r_id,
                calamity_intensity_set=new_intensity,
            )
        return StateUpdate(world_updates=world_updates)
