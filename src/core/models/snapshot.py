from __future__ import annotations

from collections import defaultdict
from typing import Mapping, TYPE_CHECKING, Any
from pydantic import Field, PrivateAttr

if TYPE_CHECKING:
    from src.core.gameplay.buildings import Building
    from src.core.world.grid import Grid
    from src.core.entities.entity import Entity
    from src.core.models.world_objects import TreasureChest
    from src.core.world.regions import Region
    from src.core.world.resource_nodes import ResourceNode
    from src.core.models.world_state import WorldState

from src.core.models.base import SimulationModel
from src.core.models.social import SocialRegistry

_SPATIAL_CELL = 8  # cell size aligned with SimulationConfig.spatial_cell_size

class Snapshot(SimulationModel):
    """Read-only view of the world, safe to share across threads.

    Enforces immutability at runtime through the SimulationModel base.
    """

    tick: int
    seed: int
    entities: Mapping[int, Entity]
    grid: Grid
    ground_items: Mapping[tuple[int, int], list[str]]
    camps: tuple[tuple[int, int], ...]
    buildings: tuple[Building, ...]
    resource_nodes: tuple[ResourceNode, ...]
    treasure_chests: tuple[TreasureChest, ...]
    regions: tuple[Region, ...]
    
    # Strategic State
    region_control: Mapping[str, float] = Field(default_factory=dict)
    war_status: Mapping[int, bool] = Field(default_factory=dict)
    faction_aggression: Mapping[int, float] = Field(default_factory=dict)
    
    # Phase 0: Social Registry
    social_registry: SocialRegistry = Field(default_factory=SocialRegistry)
    
    # Phase 3 Stage 4: Group Registry
    group_registry: Mapping[str, GroupRecord] = Field(default_factory=dict)

    # Phase 4 Stage 1-3: World State Registries
    world_history: "WorldHistoryRegistry" = Field(default_factory=lambda: WorldHistoryRegistry())
    household_registry: Mapping[str, "HouseholdRecord"] = Field(default_factory=dict)
    scar_registry: tuple["LocalScarRecord", ...] = Field(default_factory=tuple)
    region_consequence_registry: dict[str, RegionConsequenceRecord] = Field(default_factory=dict)
    successor_registry: dict[int, SuccessorRecord] = Field(default_factory=dict)
    strategic_registry: "WorldStrategicRegistry" = Field(default_factory=lambda: WorldStrategicRegistry()) # [PHASE 6]
    
    # Internal spatial caches (not serialized)
    _spatial: dict = PrivateAttr(default_factory=dict)
    _spatial_ground: dict = PrivateAttr(default_factory=dict)

    @property
    def world_day(self) -> int:
        return self.tick // 100

    @property
    def hour(self) -> int:
        """Current hour of the day (0-23). Assuming 100 ticks per day."""
        return (self.tick % 100) * 24 // 100

    @classmethod
    def from_world(cls, world: WorldState, shallow: bool = False) -> Snapshot:
        """Create a snapshot of the world state.
        
        If shallow=True, it skips deep-copying and freezing entities. 
        This is significantly faster but MUST be used with the DecisionPhase 
        mutation tripwire for safety. [Milestone 7 Optimization]
        """
        if shallow:
            # Optimized Path: Share references to live objects.
            # Mutation safety is enforced via DecisionPhase tripwire in SimulationModel.
            # Pillar 7: High-perf construction bypassing repetitive Pydantic tree validation.
            snap = cls.model_construct(
                tick=world.tick,
                seed=world.seed,
                entities=dict(world.entities),
                grid=world.grid, # Shared reference
                ground_items=world.ground_items,
                camps=tuple((c.x, c.y) for c in world.camps),
                buildings=tuple(world.buildings),
                resource_nodes=tuple(world.resource_nodes.values()),
                treasure_chests=tuple(world.treasure_chests.values()),
                regions=tuple(world.regions),
                region_control=world.region_control,
                war_status=world.war_status,
                faction_aggression=world.faction_aggression,
                social_registry=world.social_registry,
                group_registry=world.group_registry,
                world_history=world.world_history,
                household_registry=world.household_registry,
                scar_registry=tuple(world.scar_registry),
                region_consequence_registry=world.region_consequence_registry,
                successor_registry=world.successor_registry,
                strategic_registry=world.strategic_registry
            )
            
            # Tier 2 Optimization: Direct Spatial Sharing
            # If the cell size matches, we can share the spatial dictionary (dict of sets).
            # This is safe because sets of entity IDs are naturally immutable for the snapshot.
            world_cell_size = getattr(world.spatial_index, "_cell_size", 8)
            if world_cell_size == _SPATIAL_CELL:
                snap._spatial = dict(world.spatial_index._cells)
            else:
                # Fallback only if config changes mid-run (unlikely in production)
                spatial = defaultdict(list)
                for eid, e in copied_entities.items():
                    if e.combat.hp > 0 and e.kind != "generator":
                        spatial[(e.spatial.pos.x // _SPATIAL_CELL, e.spatial.pos.y // _SPATIAL_CELL)].append(eid)
                snap._spatial = dict(spatial)
                
            return snap

        # Original Authoritative Path (Deep Isolation)
        copied_entities = {}
        for eid, e in world.entities.items():
            # AOA Pillar 1: Isolation. Each entity in the snapshot must be 
            # a deep copy of the live state to ensure thread-safety and zero-mutation.
            ent = e.copy()
            ent.freeze()
            copied_entities[eid] = ent
        
        # Build spatial index
        spatial = defaultdict(list)
        for eid, e in copied_entities.items():
            if e.combat.hp > 0 and e.kind != "generator":
                spatial[(e.spatial.pos.x // _SPATIAL_CELL, e.spatial.pos.y // _SPATIAL_CELL)].append(eid)
                
        spatial_ground = defaultdict(list)
        for pos_key, items in world.ground_items.items():
            if items:
                spatial_ground[(pos_key[0] // _SPATIAL_CELL, pos_key[1] // _SPATIAL_CELL)].append(pos_key)
                
        snap = cls(
            tick=world.tick,
            seed=world.seed,
            entities=copied_entities,
            # CRITICAL: Must copy the grid! Otherwise snap.freeze() will freeze the live world grid.
            grid=world.grid.copy(),
            ground_items={k: list(v) for k, v in world.ground_items.items()},
            camps=tuple((c.x, c.y) for c in world.camps),
            buildings=tuple(b.copy() for b in world.buildings),
            resource_nodes=tuple(n.copy() for n in world.resource_nodes.values()),
            treasure_chests=tuple(c.copy() for c in world.treasure_chests.values()),
            regions=tuple(r.copy() for r in world.regions),
            region_control=dict(world.region_control),
            war_status=dict(world.war_status),
            faction_aggression=dict(world.faction_aggression),
            social_registry=world.social_registry.copy(),
            group_registry={k: v.model_copy(deep=True) for k, v in world.group_registry.items()},
            # Phase 4 Propagation
            world_history=world.world_history.copy(),
            household_registry={k: v.model_copy(deep=True) for k, v in world.household_registry.items()},
            scar_registry=tuple(s.model_copy(deep=True) for s in world.scar_registry),
            region_consequence_registry={k: v.model_copy(deep=True) for k, v in world.region_consequence_registry.items()},
            successor_registry={k: v.model_copy(deep=True) for k, v in world.successor_registry.items()},
            strategic_registry=world.strategic_registry.copy()
        )
        
        # Manually set private attrs
        snap._spatial = dict(spatial)
        snap._spatial_ground = dict(spatial_ground)
        
        # Recursive freeze
        snap.freeze()
        return snap

    def nearby_entity_ids(self, x: int, y: int, radius: int) -> list[int]:
        """Return entity IDs in cells overlapping the Manhattan-radius neighborhood."""
        # x/y can be raw ints or parts of a dict if called with keywords
        cx, cy = x // _SPATIAL_CELL, y // _SPATIAL_CELL
        r = (radius // _SPATIAL_CELL) + 1
        result: list[int] = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                bucket = self._spatial.get((cx + dx, cy + dy))
                if bucket:
                    result.extend(bucket)
        return result

    def nearby_ground_positions(self, x: int, y: int, radius: int) -> list[tuple[int, int]]:
        """Return ground item positions (gx, gy) in neighboring spatial cells."""
        cx, cy = x // _SPATIAL_CELL, y // _SPATIAL_CELL
        r = (radius // _SPATIAL_CELL) + 1
        result: list[tuple[int, int]] = []
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                bucket = self._spatial_ground.get((cx + dx, cy + dy))
                if bucket:
                    result.extend(bucket)
        return result


# --- AOA Stabilization: Pydantic Rebuild ---
# Resolve forward references for Snapshot once dependencies are defined.
# Restore eager rebuild now that circular dependency is broken.
from src.core.entities.entity import Entity
from src.core.world.grid import Grid
from src.core.gameplay.buildings import Building
from src.core.models.world_objects import TreasureChest
from src.core.world.resource_nodes import ResourceNode
from src.core.world.regions import Region
from src.core.models.vectors import Vector2, FloatVector2
from src.core.models.lived_structure import GroupRecord
from src.core.models.history import WorldHistoryRegistry
from src.core.models.households import HouseholdRecord
from src.core.models.local_scars import LocalScarRecord
from src.core.models.regions import RegionConsequenceRecord
from src.core.models.continuity import SuccessorRecord
from .world_strategy import WorldStrategicRegistry # [PHASE 6]
from src.core.models.enums import Faction, HeroClass, AIState, ActionType, EmotionType, GoalType

Snapshot.model_rebuild()
