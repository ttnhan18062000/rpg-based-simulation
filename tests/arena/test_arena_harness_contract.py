import os
import sys
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

def test_arena_determinism(arena_runner):
    """Verify that the arena harness produces byte-identical results for the same seed."""
    scenario = Scenario(
        id="test-det",
        name="Determinism Test",
        participants=[
            ParticipantProfile(faction=Faction.HERO_GUILD, atk_over=50),
            ParticipantProfile(faction=Faction.GOBLIN_HORDE, atk_over=50)
        ],
        initial_placements=[Vector2(x=31, y=32), Vector2(x=32, y=32)],
        stop_conditions=[StopCondition(type=ArenaStopCondition.WIPE)],
        max_ticks=100,
        iterations=2
    )
    
    report1 = arena_runner.run_scenario(scenario)
    report2 = arena_runner.run_scenario(scenario)
    
    # Reports should be identical across separate run_scenario calls
    assert report1.avg_ticks == report2.avg_ticks
    assert report1.win_rates == report2.win_rates
    assert report1.stall_rate == report2.stall_rate

def test_arena_stop_condition_wipe(arena_runner):
    """Verify that the arena correctly detects when one side is eliminated."""
    # HERO_GUILD participant is extremely overpowered to ensure a wipe
    scenario = Scenario(
        id="test-wipe",
        name="Wipe Test",
        participants=[
            ParticipantProfile(faction=Faction.HERO_GUILD, hp_over=2000, atk_over=1000),
            ParticipantProfile(faction=Faction.GOBLIN_HORDE, hp_over=1)
        ],
        initial_placements=[Vector2(x=32, y=32), Vector2(x=33, y=32)],
        stop_conditions=[StopCondition(type=ArenaStopCondition.WIPE)],
        iterations=1
    )
    
    report = arena_runner.run_scenario(scenario)
    assert "HERO_GUILD" in report.win_rates
    assert report.win_rates["HERO_GUILD"] == 1.0

def test_arena_stop_condition_timeout(arena_runner):
    """Verify that the arena respects the max_ticks limit."""
    # Entities far away, will never meet
    scenario = Scenario(
        id="test-timeout",
        name="Timeout Test",
        participants=[
            ParticipantProfile(faction=Faction.HERO_GUILD),
            ParticipantProfile(faction=Faction.GOBLIN_HORDE)
        ],
        initial_placements=[Vector2(x=0, y=0), Vector2(x=60, y=60)],
        stop_conditions=[StopCondition(type=ArenaStopCondition.WIPE)],
        max_ticks=50,
        iterations=1
    )
    
    report = arena_runner.run_scenario(scenario)
    assert report.avg_ticks == 50

def test_arena_stop_condition_stall(arena_runner):
    """Verify that the arena detects lack of activity (STALL)."""
    # Two entities that are not hostile or just standing still (but here we force it with same faction)
    # Actually, we'll use non-hostile factions and check for stall
    scenario = Scenario(
        id="test-stall",
        name="Stall Test",
        participants=[
            ParticipantProfile(faction=Faction.HERO_GUILD),
            ParticipantProfile(faction=Faction.HERO_GUILD) # Same faction, no fighting
        ],
        initial_placements=[Vector2(x=32, y=32), Vector2(x=33, y=32)],
        stop_conditions=[StopCondition(type=ArenaStopCondition.WIPE)],
        max_ticks=200,
        iterations=1
    )
    
    report = arena_runner.run_scenario(scenario)
    # 100 ticks of no activity (as configured in ArenaRunner)
    assert report.stall_rate == 1.0
