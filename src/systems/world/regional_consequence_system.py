"""Regional Consequence System — Manages world-level spatial history (Scars) and region metrics. [PHASE 4]

This system listens for traumatic events in the simulation and generates localized 'scars' 
at the coordinates of the event, while aggregating regional danger and stability metrics.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from src.systems.infrastructure.base import System
from src.core.models.local_scars import LocalScarRecord, ScarKind
from src.core.models.regions import RegionConsequenceRecord
from src.core.models.history import EventKind

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext
    from src.core.models.world_state import WorldState
    from src.core.models.history import HistoricalEvent

logger = logging.getLogger(__name__)

class RegionalConsequenceSystem(System):
    """World-tier system managing long-term physical and emotional consequences of events. [PHASE 4]

    Pillar 5: Reactive World Consequence. This system monitors the WorldHistoryRegistry
    for significant events (like Hero deaths) and translates them into:
    1. Local Scars: Physical markers of trauma (e.g., battlefields) that AI can perceive.
    2. Regional Danger: Aggregated metrics that shift the safety profile of a whole region.
    3. Decay: Natural recovery of stability and fading of old scars over time.

    Responsibilities:
    - monitor_history: Scans recent ticks for fatalities and major raids.
    - create_scars: Spawns LocalScarRecords at event coordinates.
    - update_regions: Recalculates danger_level and stability for affected areas.
    - process_decay: Periodically reduces danger levels and removes expired scars.
    """

    def on_init(self, context: SystemContext) -> None:
        """Initialize regional records if they don't exist."""
        world = context.world
        for region in world.regions:
            if region.region_id not in world.region_consequence_registry:
                world.region_consequence_registry[region.region_id] = RegionConsequenceRecord(
                    region_id=region.region_id
                )

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Process time-based recovery for scars and regional consequences."""
        self._process_recovery(context, tick)
        self._process_new_events(context, tick)

    def _process_recovery(self, context: SystemContext, tick: int) -> None:
        """Slowly decay scar severity and reset regional danger levels."""
        world = context.world
        
        # 1. Local Scars Recovery
        remaining_scars = []
        for scar in world.scar_registry:
            if tick > scar.created_tick:
                scar.severity = max(0.0, scar.severity - scar.recovery_rate)
            
            if scar.severity > 0.01:
                remaining_scars.append(scar)
            else:
                logger.info("Tick %d: Local scar at %s (%s) has fully healed.", 
                            tick, scar.location_pos, scar.kind.value)
        
        world.scar_registry = remaining_scars
        
        # 2. Regional Consequences Recovery (Decay towards zero/stable)
        for record in world.region_consequence_registry.values():
            if record.danger_level > 0:
                record.danger_level = max(0.0, record.danger_level - 0.0005)
            elif record.danger_level < 0:
                record.danger_level = min(0.0, record.danger_level + 0.0002)
                
            record.stability = min(1.0, record.stability + 0.0001)

    def _process_new_events(self, context: SystemContext, tick: int) -> None:
        """Check for events added in the current tick and apply consequences.
        
        Uses the authoritative WorldHistoryRegistry.
        """
        world = context.world
        # Current tick events
        new_events = [e for e in world.world_history.events.values() if e.tick == tick]
        
        for event in new_events:
            if event.kind == EventKind.DEATH:
                self._apply_death_consequences(context, event)
            elif event.kind == EventKind.TOWN_RAIDED:
                self._apply_raid_consequences(context, event)

    def _apply_death_consequences(self, context: SystemContext, event: HistoricalEvent) -> None:
        """A hero's death leaves a 'Battlefield' scar and increases regional danger."""
        world = context.world
        pos = event.location
        if not pos:
            return
            
        # 1. Create Local Scar
        # Severity scales with level? (Assume Level is in metadata)
        level = event.metadata.get("level", 1)
        severity = min(1.0, 0.2 + (level * 0.02))
        
        scar = LocalScarRecord(
            location_pos=pos,
            kind=ScarKind.BATTLE_FIELD,
            severity=severity,
            created_tick=world.tick,
            source_event_id=event.event_id,
            recovery_rate=0.0005 # Slow decay
        )
        world.scar_registry.append(scar)
        
        # 2. Update Regional Consequence
        region_id = self._find_region_id(world, pos)
        if region_id:
            record = world.region_consequence_registry.get(region_id)
            if record:
                # Death increases danger and reduces stability
                record.danger_level = min(1.0, record.danger_level + 0.1)
                record.stability = max(0.0, record.stability - 0.05)
                record.last_major_change_tick = world.tick

    def _apply_raid_consequences(self, context: SystemContext, event: HistoricalEvent) -> None:
        """A town raid leaves 'Raid Damage' scars and spikes danger."""
        world = context.world
        pos = event.location
        if not pos:
            return
            
        # 1. Create Local Scar (Higher severity than single death)
        scar = LocalScarRecord(
            location_pos=pos,
            kind=ScarKind.RAID_DAMAGE,
            severity=0.8,
            created_tick=world.tick,
            source_event_id=event.event_id,
            recovery_rate=0.0002 # Very slow recovery
        )
        world.scar_registry.append(scar)
        
        # 2. Update Regional Consequence
        region_id = self._find_region_id(world, pos)
        if region_id:
            record = world.region_consequence_registry.get(region_id)
            if record:
                record.danger_level = min(1.0, record.danger_level + 0.2)
                record.stability = max(0.0, record.stability - 0.15)
                record.last_major_change_tick = world.tick

    def _find_region_id(self, world: WorldState, pos: Vector2) -> str | None:
        """Helper to find which region a position belongs to."""
        from src.core.world.regions import find_region_at
        region = find_region_at(pos, world.regions)
        return region.region_id if region else None
