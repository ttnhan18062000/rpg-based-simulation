# tests/parity/test_strategic_persistence.py
import pytest
from dataclasses import replace
from src_legacy.core.state import AuthoritativeState, EntityState, ResourceNodeState
from src_legacy.core.enums import EntityRole, Faction
from src_legacy.core.builder import V2EntityBuilder
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.engine.kernel import Kernel
from src_legacy.core.strategic import ProjectStatus
from tests_legacy.parity.test_parity_rpg_recovery import create_test_profile

@pytest.mark.v2_contract
def test_strategic_harvesting_lifecycle():
    """Verifies project creation, persistence, and completion."""
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).readiness(100.0).build())
    node = ResourceNodeState(
        id=1, kind="TREE", position=(5, 5), 
        yields_item="WOOD", remaining_charges=1, 
        max_charges=5, required_ticks=1
    )
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero}, resource_nodes={1: node})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    # Tick 1: Strategic system should propose Harvesting project (Readiness 100)
    kernel.tick_once()
    h1 = kernel.state.entities[1]
    assert h1.strategic.current_project_id is not None
    proj_id = h1.strategic.current_project_id
    assert h1.strategic.projects[proj_id].kind == "harvesting"
    assert h1.strategic.projects[proj_id].status == ProjectStatus.ACTIVE
    
    # Tick 2: Hero should interact (Readiness is consumed in tick 1, but we wait)
    # Actually, readiness is consumed when BRAIN is resolved? No, BRAIN emits INTERACT.
    # The INTERACT action consumes 100 readiness in DomainLogic.
    
    # Wait for readiness to recover and brain to process completion
    for _ in range(30): kernel.tick_once()
    
    # Verify node depleted and project completed
    h1 = kernel.state.entities[1]
    n1 = kernel.state.resource_nodes[1]
    assert n1.remaining_charges == 0
    # Project should be COMPLETED now
    assert h1.strategic.projects[proj_id].status == ProjectStatus.COMPLETED
    assert h1.strategic.current_project_id == ""

@pytest.mark.v2_contract
def test_strategic_combat_interruption():
    """Verifies project suspension during combat and resumption after."""
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).readiness(100.0).build())
    node = ResourceNodeState(
        id=1, kind="TREE", position=(5, 5), 
        yields_item="WOOD", remaining_charges=5, 
        max_charges=5, required_ticks=1
    )
    # Goblin appears at distance
    goblin = (V2EntityBuilder(2).at((25, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).readiness(100.0).build())
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin}, resource_nodes={1: node})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    # Tick 1: Project created
    kernel.tick_once()
    h1 = kernel.state.entities[1]
    proj_id = h1.strategic.current_project_id
    assert h1.strategic.projects[proj_id].status == ProjectStatus.ACTIVE
    
    # Move Goblin closer to trigger interruption (Hero view radius is 10)
    # We'll just teleport him for the test
    kernel._state = replace(kernel.state, entities={
        1: kernel.state.entities[1],
        2: replace(kernel.state.entities[2], position=(6, 5))
    })
    
    # Hero reaches readiness (Wait 10 ticks)
    for _ in range(10): kernel.tick_once()
    
    # Tick 12: Tactical sees goblin, should SUSPEND project
    kernel.tick_once()
    h1 = kernel.state.entities[1]
    assert h1.strategic.projects[proj_id].status == ProjectStatus.SUSPENDED
    assert h1.strategic.current_project_id == ""
    
    # Kill Goblin (Give Hero enough strength to one-shot)
    kernel._state = replace(kernel.state, entities={
        1: replace(kernel.state.entities[1], 
                   readiness=100.0,
                   combat=replace(kernel.state.entities[1].combat, atk=5000)),
        2: replace(kernel.state.entities[2], readiness=0.0)
    })
    # Hero attacks Goblin
    kernel.tick_once()
    assert not kernel.state.entities[2].combat.alive
    
    # Tick 14+: No hostiles, Hero needs readiness to resume (Wait 11 ticks)
    for _ in range(11): kernel.tick_once()
    h1 = kernel.state.entities[1]
    assert h1.strategic.projects[proj_id].status == ProjectStatus.ACTIVE
    assert h1.strategic.current_project_id == proj_id
