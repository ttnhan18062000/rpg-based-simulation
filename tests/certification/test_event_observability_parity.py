from __future__ import annotations
import pytest
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.engine.checkpoint import CanonicalStateHasher

def test_state_hash_parity_across_observability_modes(tmp_path):
    """
    Law: Event extraction, bounded queues, and timeline stores must operate
    without mutated side-effects or dynamic hash contamination in AuthoritativeState.
    Running under OFF, LIGHT, DEBUG, or CERTIFICATION modes must yield
    the EXACT same authoritative state hash.
    """
    modes = [
        ObservabilityMode.OFF,
        ObservabilityMode.LIGHT,
        ObservabilityMode.DEBUG,
        ObservabilityMode.CERTIFICATION
    ]
    
    final_hashes = {}

    for mode in modes:
        ObservabilityConfig.set_override_mode(mode)
        
        profile = RuntimeProfile(
            name=f"test-parity-{mode.value.lower()}",
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=1024,
            max_cpu_percent=100.0,
            max_worker_count=1,
            max_queue_depth=100,
            max_replay_buffer_kb=0,
            max_observability_budget_percent=0.0,
            max_tick_budget_ms=16.6
        )

        # Build fresh entity state
        e1 = V2EntityBuilder(1).combat(hp=100, alive=True).location(10.0, 10.0).build()
        
        state = AuthoritativeState(tick=0, seed=42, world_time=100, entities={1: e1})
        rng = DeterministicRNG(42)
        
        kernel = Kernel(profile, state, rng)
        
        # Advance simulation several ticks naturally
        for _ in range(5):
            kernel.tick_once()

        # Compute final hash
        final_hash = CanonicalStateHasher.get_hash(kernel.state)
        final_hashes[mode] = final_hash
        
        kernel.shutdown()

    # Reset override mode
    ObservabilityConfig.set_override_mode(None)

    # Assert that hashes for all modes are identical!
    reference_hash = final_hashes[ObservabilityMode.OFF]
    for mode, h in final_hashes.items():
        assert h == reference_hash, f"Hash mismatch under {mode.value}: expected {reference_hash}, got {h}"

    print("\nParity Verified! Hashes are 100% identical under all modes:")
    for mode, h in final_hashes.items():
        print(f" - {mode.value}: {h}")
