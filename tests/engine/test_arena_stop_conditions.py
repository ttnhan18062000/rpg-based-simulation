import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, NavigationComponent, StrategicComponent
from src.certification.harness import CertificationHarness
from src.certification.models import ScenarioExpectations, ArenaStopCondition
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction

@pytest.fixture
def base_profile():
    return RuntimeProfile(
        name="ARENA_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=0, # Sequential
        max_tick_budget_ms=50.0, max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0
    )

def test_arena_stop_condition_wipe(base_profile):
    # 1. Team A (Strong)
    a1 = (V2EntityBuilder(1)
          .kind("hero")
          .location(0.0, 0.0)
          .identity(faction=Faction.HERO_GUILD)
          .with_base_stats(hp=100, atk=50)
          .build())
    
    # 2. Team B (Weak)
    b1 = (V2EntityBuilder(2)
          .kind("monster")
          .location(1.0, 0.0) # Adjacent
          .identity(faction=Faction.MONSTER_HORDE)
          .with_base_stats(hp=1, atk=10)
          .build())
    
    state = AuthoritativeState(tick=100, seed=42, entities={1: a1, 2: b1})
    
    harness = CertificationHarness(base_profile, output_dir="reports/test_wipe")
    expectations = ScenarioExpectations(reproducibility_required=False)
    
    # In a 1v1 adjacent, a1 will kill b1 in tick 1
    result = harness.run_scenario("WIPE_TEST", state, expectations, ticks=100)
    
    assert result.stop_condition == ArenaStopCondition.WIPE
    assert result.final_state.tick < 200 # Should stop way before 100 ticks + 100 initial
    print(f"\nSuccessfully verified Arena WIPE stop condition at tick {result.final_state.tick}.")

def test_arena_stop_condition_timeout(base_profile):
    # Far apart entities, won't interact
    a1 = (V2EntityBuilder(1)
          .kind("hero")
          .location(0.0, 0.0)
          .identity(faction=Faction.HERO_GUILD)
          .with_base_stats(hp=100)
          .build())
    
    b1 = (V2EntityBuilder(2)
          .kind("hero")
          .location(50.0, 50.0)
          .identity(faction=Faction.MONSTER_HORDE)
          .with_base_stats(hp=100)
          .build())
    
    state = AuthoritativeState(tick=100, seed=42, entities={1: a1, 2: b1})
    
    harness = CertificationHarness(base_profile, output_dir="reports/test_timeout")
    expectations = ScenarioExpectations(reproducibility_required=False)
    
    result = harness.run_scenario("TIMEOUT_TEST", state, expectations, ticks=10)
    
    assert result.stop_condition == ArenaStopCondition.TIMEOUT
    assert result.final_state.tick == 110 # 100 + 10
    print(f"\nSuccessfully verified Arena TIMEOUT stop condition at tick {result.final_state.tick}.")
