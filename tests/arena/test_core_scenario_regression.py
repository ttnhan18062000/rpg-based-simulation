import pytest
import json
from pathlib import Path
from src.config import SimulationConfig
from src.engine.arena.runner import ArenaRunner
from src.core.models.arena import Scenario

@pytest.fixture
def base_config():
    return SimulationConfig(world_seed=42)

@pytest.fixture
def arena_runner(base_config):
    return ArenaRunner(base_config)

def load_scenario(path_str: str) -> Scenario:
    with open(path_str, "r") as f:
        data = json.load(f)
        return Scenario.model_validate(data)

# Calculate path relative to the tests/arena directory
SCENARIOS_DIR = Path(__file__).parent.parent.parent / "data" / "arena"

def test_regression_melee_mirror(arena_runner):
    """Scenario 1v1-01: Symmetry Check."""
    path = SCENARIOS_DIR / "1v1_melee_vs_melee.json"
    if not path.exists():
        pytest.skip(f"Scenario file not found: {path}")
        
    scenario = load_scenario(str(path))
    report = arena_runner.run_scenario(scenario)
    
    # Mirror match should be roughly balanced in terms of stability
    assert report.total_iterations == 10
    assert report.stall_rate == 0.0
    # Both sides should have some win rate (stochastically)
    total_win_rate = sum(report.win_rates.values())
    assert total_win_rate > 0.5 

def test_regression_kiting_open(arena_runner):
    """Scenario 1v1-02: Ranged vs Melee Open Field."""
    path = SCENARIOS_DIR / "1v1_ranged_vs_melee_open.json"
    if not path.exists():
        pytest.skip(f"Scenario file not found: {path}")

    scenario = load_scenario(str(path))
    report = arena_runner.run_scenario(scenario)
    
    # Ranger (HERO_GUILD) should win > 60% with current kiting logic
    # Note: Using 60% as a safe baseline for initial Milestone 6
    ranger_win_rate = report.win_rates.get("HERO_GUILD", 0)
    assert ranger_win_rate >= 0.6, f"Ranger win rate {ranger_win_rate} below 60%"

def test_regression_elite_vs_swarm(arena_runner):
    """Scenario 1vm-01: Elite vs Swarm."""
    path = SCENARIOS_DIR / "1vm_elite_vs_swarm.json"
    if not path.exists():
        pytest.skip(f"Scenario file not found: {path}")

    scenario = load_scenario(str(path))
    report = arena_runner.run_scenario(scenario)
    
    # Elite Warrior (HERO_GUILD) should be able to cleave/tank 5 goblins
    warrior_win_rate = report.win_rates.get("HERO_GUILD", 0)
    assert warrior_win_rate >= 0.8, f"Elite Warrior win rate {warrior_win_rate} below 80%"
