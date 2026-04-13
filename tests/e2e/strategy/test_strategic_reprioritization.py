"""E2E Strategic Reprioritization Suite. [MILESTONE 5]

Verifies that major narrative events (e.g. Near Death) correctly trigger 
strategic updates, concern generation, and project pivots.
"""

import pytest
import os
from pathlib import Path

from src.config import SimulationConfig
from src.api.engine_manager import EngineManager
from src.core.models.enums import InterpretedLifeEventKind, ProjectKind, ConcernKind, StrategicStatus
from src.core.models.strategy import ProjectRecord
from src.core.aspects.mind import InterpretedEvent
from src.core.logic.cognition_graph_exporter import EntityCognitionExporter

@pytest.fixture
def simulation_env():
    """Setup a controlled engine environment for injection."""
    seed = 42
    config = SimulationConfig(
        world_seed=seed,
        hero_count=1,
        initial_entity_count=2,
        num_workers=1,
        grid_width=32,
        grid_height=32
    )
    mgr = EngineManager(config)
    yield mgr
    mgr.stop()

class TestStrategicReprioritizationE2E:
    
    def test_hero_near_death_pivot(self, simulation_env):
        """Verify that a hero pivots from Exploration to Recovery (Development) on Near Death."""
        mgr = simulation_env
        loop = mgr._loop
        assert loop is not None
        
        # 1. Settle the world for a few ticks
        for _ in range(2):
            loop.tick_once()
            
        # 2. Identify the Hero and FORCE initial state
        hero = next(e for e in loop.world.entities.values() if e.identity.role == 0)
        hero_id = hero.id
        
        # Force Exploration project
        initial_proj = ProjectRecord(
            project_id=f"project_explorer_{hero_id}",
            kind=ProjectKind.EXPLORATION,
            label="Initial Exploration",
            status=StrategicStatus.ACTIVE,
            priority=1.5
        )
        hero.mind.strategic.projects = [initial_proj]
        hero.mind.strategic.current_project_id = initial_proj.project_id
        
        # Force hero to be ready to think
        hero.next_act_at = 0.0
        
        # 3. Simulate "Near Death" incident
        hero.combat.hp = 1
        
        # Add to memory_log
        memory_entry = InterpretedEvent(
            tick=loop.world.tick,
            type="trauma",
            impact=9.0,
            life_event_kind=int(InterpretedLifeEventKind.NEAR_DEATH),
            details={"threat_id": -1, "type": "combat"}
        )
        hero.mind.narrative.memory_log.append(memory_entry)
        
        # 4. Tick several times
        for _ in range(15):
            hero.next_act_at = 0.0 # Keep him thinking every tick
            loop.tick_once()
            
        # 5. Verify StrategicState
        concerns = hero.mind.strategic.concerns
        survival_concerns = [c for c in concerns if "Survival" in c.label or c.kind == ConcernKind.THREAT]
        assert len(survival_concerns) >= 1, "Hero should have a Survival/Threat concern"
        
        current_proj = hero.mind.strategic.current_project
        assert current_proj is not None
        assert current_proj.kind == ProjectKind.DEVELOPMENT, f"Should have pivoted to DEVELOPMENT, got {current_proj.kind}"
        
        # 6. Verify Cognition Graph Export
        graph = EntityCognitionExporter.export(hero, loop.world.tick)
        nodes = graph.nodes
        project_nodes = [n for n in nodes if n.kind == "project"]
        
        # Check if any project node has kind DEVELOPMENT
        found_dev = False
        for n in project_nodes:
            if n.attributes.get("project_kind") == "DEVELOPMENT":
                found_dev = True
                break
        
        assert found_dev, f"Cognition graph must show DEVELOPMENT project node. Found kinds: {[n.attributes.get('project_kind') for n in project_nodes]}"
