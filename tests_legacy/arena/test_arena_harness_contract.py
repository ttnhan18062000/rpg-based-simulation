import os
import sys
import pytest
from src_legacy.config import SimulationConfig
from src_legacy.engine.arena.runner import ArenaRunner
from src_legacy.core.models.arena import Scenario, ParticipantProfile, StopCondition
from src_legacy.core.models.enums import AIState, ArenaStopCondition, EntityRole, Faction, HeroClass
from src_legacy.core.models.vectors import Vector2

@pytest.fixture
def base_config():
    return SimulationConfig(
        world_seed=42,
        num_workers=1,
        initial_entity_count=0,
        generator_spawn_interval=999999 # Disable background spawning
    )

@pytest.fixture
def arena_runner(base_config):
    return ArenaRunner(base_config)

def test_arena_structural_determinism(arena_runner):
    """Verify that the arena produced structurally identical ScenarioReports for the same seed.
    
    This validates that the simulation and its reporting layer use stable, 
    deterministic logic. Note: This checks structural equality via 
    Pydantic model_dump, not canonical byte-identical streams. [Milestone 7 Hardening]
    """
    scenario = Scenario(
        id="test-det",
        name="Determinism Test",
        participants=[
            ParticipantProfile(faction=Faction.HERO_GUILD, kind="hero", atk_over=50),
            ParticipantProfile(faction=Faction.GOBLIN_HORDE, kind="goblin", atk_over=50)
        ],
        initial_placements=[Vector2(x=31, y=32), Vector2(x=32, y=32)],
        max_ticks=100,
        iterations=3 # More iterations to increase confidence
    )
    
    report1 = arena_runner.run_scenario(scenario)
    report2 = arena_runner.run_scenario(scenario)
    
    # Pillar 6: Structural verification of the entire report tree
    d1 = report1.model_dump()
    d2 = report2.model_dump()
    
    # [Milestone 7] Ignore non-deterministic performance metrics
    perf_keys = ["avg_peak_rss", "peak_rss_high_water", "total_cpu_time"]
    for d in [d1, d2]:
         for k in perf_keys:
             d.pop(k, None)
             
    assert d1 == d2, f"Reports differ: {d1} vs {d2}"
    assert report1.avg_ticks > 0

def test_arena_stop_condition_wipe(arena_runner):
    """Verify that the arena correctly detects when one side is eliminated."""
    # HERO_GUILD participant is extremely overpowered to ensure a wipe
    scenario = Scenario(
        id="test-wipe",
        name="Wipe Test",
        participants=[
            ParticipantProfile(faction=Faction.HERO_GUILD, kind="hero", hp_over=2000, atk_over=10000), # Ultra-overpowered
            ParticipantProfile(faction=Faction.GOBLIN_HORDE, kind="goblin", hp_over=1)
        ],
        initial_placements=[Vector2(x=32, y=32), Vector2(x=33, y=32)],
        stop_conditions=[StopCondition(type=ArenaStopCondition.WIPE)],
        iterations=1
    )
    
    report = arena_runner.run_scenario(scenario)
    assert "HERO_GUILD" in report.win_rates
    assert report.win_rates["HERO_GUILD"] == 1.0
    assert report.stop_reason == ArenaStopCondition.WIPE # Explicit check

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
        max_ticks=50,
        iterations=1
    )
    
    report = arena_runner.run_scenario(scenario)
    assert report.avg_ticks == 50
    assert report.stop_reason == ArenaStopCondition.TIMEOUT

def test_arena_stop_condition_stall(arena_runner):
    """Verify that the arena correctly detects lack of activity (STALL) as a telemetry report."""
    scenario = Scenario(
        id="test-stall",
        name="Stall Test",
        participants=[
            ParticipantProfile(faction=Faction.HERO_GUILD, ai_state=AIState.GUARD_CAMP, spd_over=0, leash_over=0),
            ParticipantProfile(faction=Faction.HERO_GUILD, ai_state=AIState.GUARD_CAMP, spd_over=0, leash_over=0) # Non-hostile to each other
        ],
        initial_placements=[Vector2(x=32, y=32), Vector2(x=33, y=32)],
        max_ticks=200,
        iterations=1
    )
    
    report = arena_runner.run_scenario(scenario)
    # The runner breaks at ~100 ticks due to inactivity internal threshold
    assert report.stall_rate == 1.0
    assert report.stop_reason == ArenaStopCondition.STALL
    assert 100 <= report.avg_ticks < 120

def test_mutation_tripwire_during_decision(arena_runner):
    """Verify that any attempt to mutate entities during the decision phase raises a RuntimeError."""
    from src_legacy.core.models.base import DecisionPhase
    from src_legacy.core.entities.entity_builder import EntityBuilder
    from src_legacy.platform.rng import DeterministicRNG
    
    rng = DeterministicRNG(1)
    entity = EntityBuilder(rng, 1).kind("hero").build()
    
    # Normal mutation is fine
    entity.combat.hp -= 10
    
    # Mutation during DecisionPhase is FORBIDDEN
    with DecisionPhase():
        with pytest.raises(RuntimeError) as excinfo:
            entity.combat.hp -= 10
        assert "Cannot mutate" in str(excinfo.value)
        assert "Decision Phase" in str(excinfo.value)
