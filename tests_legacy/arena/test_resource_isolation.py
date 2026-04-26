import pytest
import psutil
from src_legacy.config import SimulationConfig
from src_legacy.engine.arena.runner import ArenaRunner
from src_legacy.core.models.arena import Scenario, ParticipantProfile, StopCondition
from src_legacy.core.models.enums import ArenaStopCondition, EntityRole, Faction, HeroClass
from src_legacy.core.models.vectors import Vector2

def test_resource_isolation_bounded_growth():
    """Verify that memory does not show a strong linear leak over many iterations."""
    config = SimulationConfig(world_seed=42)
    runner = ArenaRunner(config)
    
    scenario = Scenario(
        id="isolation_test",
        name="Isolation Test",
        participants=[
            ParticipantProfile(faction=Faction.HERO_GUILD, role=EntityRole.HERO, hero_class=HeroClass.WARRIOR)
        ],
        initial_placements=[Vector2(x=32, y=32)],
        stop_conditions=[],
        max_ticks=20, # Short iterations
        iterations=50 # Run enough to see a trend
    )
    
    process = psutil.Process()
    start_rss = process.memory_info().rss / (1024 * 1024)
    
    report = runner.run_scenario(scenario)
    
    end_rss = process.memory_info().rss / (1024 * 1024)
    leak_mb = end_rss - start_rss
    
    # We allow some fragmentation/drift, but a linear leak would be massive for 50 iterations.
    # Given each iteration setup/teardown is heavy, >100MB would suggest a leak.
    # Bounded growth target: < 150MB total drift for 50 iterations. [AOA PHASE 5]
    print(f"Memory Drift: {leak_mb:.2f} MB (Start: {start_rss:.1f}, End: {end_rss:.1f})")
    
    assert report.total_iterations == 50
    assert leak_mb < 150 
