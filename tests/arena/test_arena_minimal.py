import pytest
from src.config import SimulationConfig
from src.engine.arena.runner import ArenaRunner
from src.core.models.arena import Scenario, ParticipantProfile, StopCondition
from src.core.models.enums import ArenaStopCondition, EntityRole, Faction, HeroClass
from src.core.models.vectors import Vector2

@pytest.fixture
def base_config():
    return SimulationConfig(world_seed=42)

@pytest.fixture
def arena_runner(base_config):
    return ArenaRunner(base_config)

def test_minimal_tick(arena_runner):
    """Verify that we can run even 1 tick without hanging."""
    scenario = Scenario(
        id="minimal",
        name="Minimal",
        participants=[
            ParticipantProfile(faction=Faction.HERO_GUILD, role=EntityRole.HERO, hero_class=HeroClass.WARRIOR)
        ],
        initial_placements=[Vector2(x=32, y=32)],
        stop_conditions=[StopCondition(type=ArenaStopCondition.WIPE)],
        max_ticks=1,
        iterations=1
    )
    
    print("DEBUG: Calling run_scenario...")
    report = arena_runner.run_scenario(scenario)
    print("DEBUG: run_scenario returned.")
    assert report.total_iterations == 1
    assert report.avg_ticks == 1
