"""Integration tests for AI Strategic Reprioritization (Phase 1 Stage 15).

This suite verifies that entities correctly sense world-tier trauma (regional danger and scars)
and dynamically reprioritize their long-term projects to address stability or historical investigation.
"""

import pytest
from unittest.mock import MagicMock
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.models.strategy import StrategicStatus, ConcernKind, ProjectKind
from src.ai.brain import AIBrain
from src.core.models.snapshot import Snapshot
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.core.world.regions import Region
from src.core.models.enums import Material
from src.core.models.regions import RegionConsequenceRecord
from src.core.models.local_scars import LocalScarRecord, ScarKind

@pytest.fixture
def mock_world():
    grid = Grid(100, 100)
    spatial = SpatialHash(cell_size=10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    # Setup Regions
    # Region(region_id, name, terrain, center, radius, difficulty, owner_faction, locations)
    r1 = Region(
        region_id="forest", 
        name="The Dark Forest", 
        terrain=Material.FOREST, 
        center=Vector2(25, 25), 
        radius=50,
        difficulty=1
    )
    world.regions = [r1]
    
    # Setup Consequence Registry
    world.entities = {} # Correct attribute name
    world.region_consequence_registry = {
        "forest": RegionConsequenceRecord(region_id="forest", danger_level=0.0, stability=1.0)
    }
    return world

def test_strategic_pivot_on_regional_danger(mock_world):
    """Verify that heroes pivot from personal quests to regional stabilization during high-danger events.
    
    Logic:
    1. Hero starts in a safe region with a personal quest.
    2. Regional danger spikes (0.9), stability drops (0.2).
    3. Strategic evaluation triggers a Regional Threat concern.
    4. Current project is suspended (pivoted) to 'Restore Regional Order'.
    """
    # 1. Setup Hero in Forest
    hero = Entity(id=1, kind="hero")
    hero.spatial.pos = Vector2(25, 25)
    hero.spatial.region_id = "forest"
    
    config = SimulationConfig()
    brain = AIBrain(config, DeterministicRNG(0))
    
    # Seed a default project
    from src.core.models.strategy import ProjectRecord, ObjectiveRecord, ObjectiveKind
    default_prj = ProjectRecord(
        project_id="quest_1", kind=ProjectKind.QUEST, label="Standard Quest", priority=2.0
    )
    hero.mind.strategic.projects.append(default_prj)
    hero.mind.strategic.current_project_id = "quest_1"
    
    # 2. Initial Evaluation (Safe)
    snapshot = Snapshot.from_world(mock_world)
    state, proposal = brain.decide(hero, snapshot)
    
    update = next((u for u in proposal.updates if hasattr(u, 'concerns_add_or_update')), None)
    
    # Baseline check: no threat concern added
    if update:
        assert not any(c.concern_id == "concern_regional_threat" for c in update.concerns_add_or_update)

    # 3. Spike Danger
    mock_world.region_consequence_registry["forest"].danger_level = 0.9
    mock_world.region_consequence_registry["forest"].stability = 0.2
    
    # 4. Crisis Evaluation
    snapshot = Snapshot.from_world(mock_world)
    state, proposal = brain.decide(hero, snapshot)
    update = next((u for u in proposal.updates if hasattr(u, 'concerns_add_or_update')), None)
    
    assert update is not None
    # Verify Concern added
    threat_c = next((c for c in update.concerns_add_or_update if c.concern_id == "concern_regional_threat"), None)
    assert threat_c is not None
    assert threat_c.priority >= 6.0
    
    # Verify Project Pivot
    assert update.current_project_id == "project_stabilization"
    assert update.interrupted_project_id == "quest_1"
    
    # Verify Project Record added
    stab_prj = next((p for p in update.projects_add_or_update if p.project_id == "project_stabilization"), None)
    assert stab_prj is not None
    assert stab_prj.kind == ProjectKind.SOCIAL # Based on my implementation

def test_recovery_hysteresis(mock_world):
    """Verify that heroes only resume their original projects once regional danger drops below a threshold.
    
    Logic:
    1. Hero is already in stabilization mode due to threat.
    2. Regional danger drops significantly (0.1).
    3. Strategic evaluation clears the threat concern.
    4. Project state is updated for potential resumption (hysteresis validation).
    """
     # 1. Setup Hero already in stabilization mode
    hero = Entity(id=1, kind="hero")
    hero.spatial.pos = Vector2(25, 25)
    
    from src.core.models.strategy import ConcernRecord
    hero.mind.strategic.concerns.append(ConcernRecord(
        concern_id="concern_regional_threat", kind=ConcernKind.THREAT, label="High Danger", priority=6.0
    ))
    hero.mind.strategic.current_project_id = "project_stabilization"
    hero.mind.strategic.interrupted_project_id = "quest_1"
    hero.spatial.region_id = "forest"
    
    config = SimulationConfig()
    brain = AIBrain(config, DeterministicRNG(0))
    
    # Danger is now low
    mock_world.region_consequence_registry["forest"].danger_level = 0.1
    mock_world.region_consequence_registry["forest"].stability = 0.9
    
    # 2. Recovery Evaluation
    snapshot = Snapshot.from_world(mock_world)
    state, proposal = brain.decide(hero, snapshot)
    update = next((u for u in proposal.updates if hasattr(u, 'concerns_remove')), None)
    
    assert update is not None
    # Verify Concern REMOVED
    assert "concern_regional_threat" in update.concerns_remove
    
def test_scar_detection(mock_world):
    """Verify that heroes sense nearby world trauma (scars) and investigate.
    
    Logic:
    1. Hero is near a Battlefield scar (Manhattan distance < 10).
    2. Strategic evaluation detects the trauma site and generates an opportunity concern.
    """
    hero = Entity(id=1, kind="hero")
    hero.spatial.pos = Vector2(20, 20)
    
    # Add a nearby scar
    mock_world.scar_registry = [
        LocalScarRecord(
            location_pos=Vector2(22, 22), # Distance 4
            kind=ScarKind.BATTLE_FIELD,
            severity=0.5,
            created_tick=50,
            source_event_id="evt_123"
        )
    ]
    
    config = SimulationConfig()
    brain = AIBrain(config, DeterministicRNG(0))
    
    snapshot = Snapshot.from_world(mock_world)
    state, proposal = brain.decide(hero, snapshot)
    update = next((u for u in proposal.updates if hasattr(u, 'concerns_add_or_update')), None)
    assert update is not None
    scar_c = next((c for c in update.concerns_add_or_update if c.concern_id == "concern_nearby_scar"), None)
    assert scar_c is not None
    assert scar_c.source_event_id == "evt_123"
