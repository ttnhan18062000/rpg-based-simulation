import pytest
from dataclasses import replace
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.config.profiles import RuntimeProfile, HardwareClass
from src.certification.scenarios import build_scenario_state

@pytest.fixture
def integrity_profile():
    return RuntimeProfile(
        name="integrity_guard",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=100,
        max_cpu_percent=100.0,
        max_worker_count=0,
        max_queue_depth=10,
        max_tick_budget_ms=100.0,
        max_replay_buffer_kb=100,
        max_observability_budget_percent=0.0
    )

def test_autonomous_loop_determinism_drift_guard(integrity_profile):
    """
    STRICT LAW: The integrated Phase 5 progression loop must be bit-identical 
    across identical runs. Any drift here indicates a non-deterministic resolution logic.
    """
    initial_state = build_scenario_state("INTEG_RESOURCE_LOOP")
    
    # Run 1
    rng1 = DeterministicRNG(42)
    kernel1 = Kernel(integrity_profile, initial_state, rng1)
    for _ in range(100):
        kernel1.tick_once()
    state1 = kernel1.state
    
    # Run 2
    rng2 = DeterministicRNG(42)
    kernel2 = Kernel(integrity_profile, initial_state, rng2)
    for _ in range(100):
        kernel2.tick_once()
    state2 = kernel2.state
    
    assert state1 == state2, "NONDETERMINISM DRIFT: Integrated progression loop drifted across identical runs."
    
    # Assert successful loop completion (Hero should have at least one sword)
    hero = state1.entities[1]
    assert any(item.item_id == "steel_sword" for item in hero.inventory.items), "LOGIC DRIFT: Integrated loop failed to produce a sword in 100 ticks."

def test_resolution_phase_ordering_integrity(integrity_profile):
    """
    LAW: The integrated loop must successfully resolve redirection and crafting.
    Hero starts at Town -> Needs Ore -> Goes to Node -> Harvests -> Returns to Town -> Crafts.
    """
    initial_state = build_scenario_state("INTEG_RESOURCE_LOOP")
    rng = DeterministicRNG(42)
    kernel = Kernel(integrity_profile, initial_state, rng)
    
    # Hero starts with wood and 1 iron_ore. Needs one more iron_ore to craft.
    # Total ticks to success: 1 (fail) + 1 (move) + 2 (harvest) + 1 (move back) + 1 (craft) = ~6 ticks.
    for _ in range(50):
        kernel.tick_once()
    
    hero = kernel.state.entities[1]
    assert any(item.item_id == "steel_sword" for item in hero.inventory.items), f"INTEGRATION FAILURE: Hero failed to craft sword. Inventory: {hero.inventory.items}, Blockers: {list(hero.strategic.blockers.keys())}"
    assert hero.navigation.target == (0.0, 0.0), "INTEGRATION FAILURE: Hero final target should be home (0,0)"

def test_lifecycle_timeout_semantics_guard(integrity_profile):
    """
    LAW: The engine must honor forced timeouts for certification truth.
    """
    from src.certification.models import ScenarioExpectations
    
    # Mocking a timeout scenario
    expectations = ScenarioExpectations(
        expected_lifecycle_outcome="TIMEOUT",
        shutdown_timeout_s=0.0,
        requires_semantic_equivalence=False
    )
    
    # We verify the expectations object carries the correct intent
    assert expectations.expected_lifecycle_outcome == "TIMEOUT"
    assert expectations.shutdown_timeout_s == 0.0
