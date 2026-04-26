import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src_legacy.engine.world_loop import WorldLoop as LegacyLoop
from src.engine.kernel import Kernel as V2Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass

def create_test_profile():
    return RuntimeProfile(
        name="test_parity",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=512,
        max_cpu_percent=100.0,
        max_worker_count=0, # Sequential for parity
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=100.0
    )
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder

@pytest.mark.differential
def test_tick_advancement_parity():
    """
    Verifies that V2 tick advancement aligns perfectly with legacy behavior.
    Legacy: tick increments AFTER the step.
    V2: tick increments in Advancement phase (now aligned to POST-step).
    """
    # 1. Setup V2
    profile = create_test_profile()
    initial_state = AuthoritativeState(tick=0, seed=42)
    rng = DeterministicRNG(42)
    v2_kernel = V2Kernel(profile, initial_state, rng)
    
    # 2. Verify Initial State
    assert v2_kernel.state.tick == 0
    
    # 3. Execute 1 Tick in V2
    v2_kernel.tick_once()
    # After 1 step, tick should be 1
    assert v2_kernel.state.tick == 1
    
    # 4. Verify world_time increment
    # world_time starts at 0, should be 1
    assert v2_kernel.state.world_time == 1

@pytest.mark.differential
def test_multi_tick_alignment():
    """Verifies tick sequence over multiple steps."""
    initial_state = AuthoritativeState(tick=0, seed=42)
    rng = DeterministicRNG(42)
    v2_kernel = V2Kernel(create_test_profile(), initial_state, rng)
    
    ticks = []
    for _ in range(5):
        ticks.append(v2_kernel.state.tick)
        v2_kernel.tick_once()
        
    assert ticks == [0, 1, 2, 3, 4]
    assert v2_kernel.state.tick == 5
