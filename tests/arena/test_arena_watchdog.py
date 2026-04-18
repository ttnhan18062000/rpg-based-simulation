import pytest
import time
from unittest.mock import patch
from src.config import SimulationConfig
from src.engine.arena.runner import ArenaRunner
from src.core.models.arena import Scenario, ParticipantProfile, StopCondition
from src.core.models.enums import ArenaStopCondition, EntityRole, Faction, HeroClass
from src.core.models.vectors import Vector2

@pytest.fixture
def arena_runner():
    config = SimulationConfig(world_seed=42, watchdog_timeout=1.0) # 1s for fast testing
    return ArenaRunner(config)

def test_watchdog_aborts_on_hang(arena_runner):
    """Verify that a tick hanging for > watchdog_timeout is aborted."""
    scenario = Scenario(
        id="hang_test",
        name="Hang Test",
        participants=[
            ParticipantProfile(faction=Faction.HERO_GUILD, role=EntityRole.HERO, hero_class=HeroClass.WARRIOR)
        ],
        initial_placements=[Vector2(x=32, y=32)],
        stop_conditions=[],
        max_ticks=10,
        iterations=1
    )
    
    # Mock WorldLoop.tick_once to simulate a hang
    with patch("src.engine.arena.runner.WorldLoop.tick_once") as mock_tick:
        def slow_tick():
            time.sleep(2.0) # Longer than 1.0s timeout
            return True
        mock_tick.side_effect = slow_tick
        
        report = arena_runner.run_scenario(scenario)
        
        # Should have aborted the iteration
        assert report.total_iterations == 1
        # The result stop reason should be WATCHDOG_TIMEOUT (as set in our exception handler for hung ticks)
        assert report.stop_reason == ArenaStopCondition.WATCHDOG_TIMEOUT

def test_watchdog_allows_fast_ticks(arena_runner):
    """Verify that normal fast ticks are NOT aborted."""
    scenario = Scenario(
        id="fast_test",
        name="Fast Test",
        participants=[
            ParticipantProfile(faction=Faction.HERO_GUILD, role=EntityRole.HERO, hero_class=HeroClass.WARRIOR)
        ],
        initial_placements=[Vector2(x=32, y=32)],
        stop_conditions=[],
        max_ticks=5,
        iterations=1
    )
    
    report = arena_runner.run_scenario(scenario)
    assert report.total_iterations == 1
    assert report.avg_ticks == 5
    assert report.stop_reason == ArenaStopCondition.TIMEOUT
