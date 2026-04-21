import pytest
from dataclasses import replace
from src_v2.engine.kernel import Kernel
from src_v2.platform.rng import DeterministicRNG
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.certification.scenarios import build_scenario_state

@pytest.fixture
def profile():
    return RuntimeProfile(
        name="integrity_test",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=100,
        max_cpu_percent=100.0,
        max_worker_count=0,
        max_queue_depth=10,
        max_tick_budget_ms=100.0,
        max_replay_buffer_kb=100,
        max_observability_budget_percent=0.0
    )

def test_autonomous_loop_determinism(profile):
    """
    STRICT LAW: A 100-tick autonomous run must be bit-identical 
    across multiple executions of the same seed.
    """
    initial_state = build_scenario_state("INTEG_RESOURCE_LOOP")
    
    # Run 1
    rng1 = DeterministicRNG(42)
    kernel1 = Kernel(profile, initial_state, rng1)
    for _ in range(100):
        kernel1.tick_once()
    state1 = kernel1.state
    
    # Run 2
    rng2 = DeterministicRNG(42)
    kernel2 = Kernel(profile, initial_state, rng2)
    for _ in range(100):
        kernel2.tick_once()
    state2 = kernel2.state
    
    # Assert Bit-Identity (Hash of the entire state)
    # We can use a simple equality check because dataclasses handle nested equality
    assert state1 == state2, "NONDETERMINISM: Integrated progression loop drifted across identical runs."
    
    # Assert successful loop completion (Hero should have at least one sword after 100 ticks)
    hero = state1.entities[1]
    assert "steel_sword" in hero.inventory.items, "LOOP FAILURE: Hero failed to craft sword in 100 autonomous ticks."
    print("INTEGRITY GUARD PASSED: 100-tick loop is deterministic and productive.")

def test_kernel_phase_ordering_integrity(profile):
    """
    Guard against regressions in the Kernel resolution phase ordering. 
    Redirection MUST see the current tick's inventory additions.
    """
    initial_state = build_scenario_state("INTEG_RESOURCE_LOOP")
    rng = DeterministicRNG(42)
    kernel = Kernel(profile, initial_state, rng)
    
    # Tick 1: Fail craft -> Redirection
    kernel.tick_once()
    hero = kernel.state.entities[1]
    assert hero.identity.navigation_target == (1.0, 0.0)
    
    # Fast forward to the tick where harvest completes.
    # In our scenario, distance is 1 (1 tick to move) and required_ticks is 2.
    # Tick 2: Move. 
    # Tick 3: Start. 
    # Tick 4: Finish + Redirection (Immediate).
    for _ in range(3):
        kernel.tick_once()
    
    hero = kernel.state.entities[1]
    # If the ordering is correct, at the END of the tick where harvest finished, 
    # the hero should already have its navigation_target reset to (0,0).
    has_progression = ("iron_ore" in hero.inventory.items) or ("steel_sword" in hero.inventory.items)
    assert has_progression, f"LOOP FAILURE: Hero has neither ore nor sword. Inventory: {hero.inventory.items}"
    assert hero.identity.navigation_target == (0.0, 0.0), f"ORDERING REGRESSION: Redirection failed to react to same-tick harvest completion. Current target: {hero.identity.navigation_target}"
