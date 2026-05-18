from __future__ import annotations
import unittest
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.history import HistoricalEvent, EventKind
from src_legacy.core.models.local_scars import ScarKind
from src_legacy.systems.world.regional_consequence_system import RegionalConsequenceSystem
from src_legacy.config import SimulationConfig
from src_legacy.core.world.grid import Grid
from src_legacy.systems.spatial_hash import SpatialHash
from src_legacy.systems.rng import DeterministicRNG
from src_legacy.systems.infrastructure.base import SystemContext

class TestRegionalConsequences(unittest.TestCase):
    def setUp(self):
        self.config = SimulationConfig()
        grid = Grid(self.config.grid_width, self.config.grid_height)
        spatial = SpatialHash(self.config.spatial_cell_size)
        self.world = WorldState(seed=42, grid=grid, spatial_index=spatial)
        self.rng = DeterministicRNG(42)
        self.system = RegionalConsequenceSystem(self.config, rng=self.rng)
        self.ctx = SystemContext(
            config=self.config,
            world=self.world,
            rng=self.rng,
            generator=None,
            faction_reg=None,
            emit=lambda *a, **k: None
        )

    def test_hero_death_creates_scar(self):
        # 1. Arrange: Create a hero death event
        event = HistoricalEvent(
            event_id="evt_1",
            tick=10,
            kind=EventKind.DEATH,
            location=Vector2(50, 50),
            involved_ids={1},
            tags=["hero_death"],
            description="Hero fell in battle",
            summary="Hero Death"
        )
        self.world.world_history.add_event(event)
        
        # 2. Act: Tick the system
        self.system.on_tick(self.ctx, 10)
        
        # 3. Assert: A scar should be created at (50, 50)
        self.assertEqual(len(self.world.scar_registry), 1)
        scar = self.world.scar_registry[0]
        self.assertEqual(scar.kind, ScarKind.BATTLE_FIELD)
        self.assertEqual(scar.location_pos, Vector2(50, 50))
        self.assertGreater(scar.severity, 0.0)

    def test_scar_decay(self):
        # 1. Arrange: Add an existing scar
        from src_legacy.core.models.local_scars import LocalScarRecord
        scar = LocalScarRecord(
            location_pos=Vector2(10, 10),
            kind=ScarKind.RAID_DAMAGE,
            severity=0.5,
            created_tick=1,
            recovery_rate=0.1,
            source_event_id="evt_1"
        )
        self.world.scar_registry.append(scar)
        
        # 2. Act: Tick the system
        # Since created_tick=1 and current tick is 2, it should decay
        self.system.on_tick(self.ctx, 2)
        
        # 3. Assert: Severity should be reduced
        self.assertLess(self.world.scar_registry[0].severity, 0.5)

    def test_ai_perception_of_scars(self):
        from src_legacy.core.entities.entity import Entity
        from src_legacy.core.aspects.spatial import SpatialAspect
        from src_legacy.ai.perception import Perception
        from src_legacy.core.models.local_scars import LocalScarRecord
        
        # Arrange
        actor = Entity(id=1, kind="hero")
        actor.spatial = SpatialAspect(pos=Vector2(5, 5))
        
        scar = LocalScarRecord(
            location_pos=Vector2(6, 6),
            kind=ScarKind.BATTLE_FIELD,
            severity=1.0,
            created_tick=1,
            source_event_id="evt_1"
        )
        self.world.scar_registry.append(scar)
        
        snapshot = Snapshot.from_world(self.world)
        
        # Act
        visible = Perception.visible_scars(actor, snapshot, scan_range=10)
        
        # Assert
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].location_pos, Vector2(6, 6))

    def test_ai_goal_bias_from_danger(self):
        from src_legacy.ai.goals.scorers import FleeGoal, ExploreGoal
        from src_legacy.core.models.regions import RegionConsequenceRecord
        from src_legacy.core.aspects.mind import PersonalityProfile
        from src_legacy.ai.states import AIContext
        from src_legacy.core.world.regions import Region
        from src_legacy.core.models.enums import Material
        
        # 1. Arrange: High danger region
        region_id = "danger_zone"
        self.world.region_consequence_registry[region_id] = RegionConsequenceRecord(
            region_id=region_id,
            danger_level=1.0, # Very high
            stability=0.2
        )
        
        # Create a region and assign actor to it
        region = Region(
            region_id=region_id, name="Danger", terrain=Material.MOUNTAIN,
            center=Vector2(50, 50), radius=100, difficulty=5
        )
        self.world.regions.append(region)
        
        from src_legacy.core.entities.entity import Entity
        from src_legacy.core.aspects.spatial import SpatialAspect
        from src_legacy.core.models.enums import TraitType
        actor = Entity(id=2, kind="hero")
        actor.spatial = SpatialAspect(pos=Vector2(50, 50))
        actor.combat.max_hp_base = 100
        actor.combat.hp = 40
        actor.spatial.current_region_id = region_id
        actor.identity.traits = [TraitType.CURIOUS] # Positive explore utility
        
        # [AOA STABILIZATION] Inject a visible high-threat enemy into memory
        # to trigger should_flee's panic logic, justifying the danger bias.
        from src_legacy.ai.beliefs import BeliefRecord
        from src_legacy.core.aspects.mind import ThreatEstimate
        actor.mind.perception.entity_memory[999] = BeliefRecord(
            entity_id=999,
            pos=Vector2(51, 51), # Right next to actor
            last_seen_tick=1,
            threat=ThreatEstimate(overall=0.9, confidence=1.0)
        )
        
        snapshot = Snapshot.from_world(self.world)
        ctx = AIContext(
            actor=actor,
            snapshot=snapshot,
            config=self.config,
            rng=self.rng,
            faction_reg=None
        )
        
        # 2. Act: Score goals
        flee_scorer = FleeGoal()
        explore_scorer = ExploreGoal()
        
        flee_score = flee_scorer.score(ctx)
        explore_score = explore_scorer.score(ctx)
        
        # 3. Assert: 
        # Flee should be high due to danger
        self.assertGreater(flee_score, 0.4) 
        # Explore should be penalized (original base is 0.5)
        self.assertLess(explore_score, 0.5)

if __name__ == "__main__":
    unittest.main()
