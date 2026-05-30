import pytest
import time
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState, EntityState, RegionState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.engine.checkpoint import CanonicalStateHasher
from src.core.enums import Faction, EntityRole

@pytest.mark.extra_slow
def test_long_run_stability():
    """
    Simulate 2,000 ticks and verify:
    1. Determinism (Identical hash on repeat)
    2. Memory Stability (No significant growth)
    3. Population Stability (Entities spawning/dying loop)
    VERIFIED v2: test_long_run_stability.py
    """
    TICKS = 2000
    SEED = 999
    
    def run_sim(ticks, seed):
        profile = RuntimeProfile(
            name="stability-test",
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=1024,
            max_cpu_percent=100.0,
            max_worker_count=1,
            max_queue_depth=1000,
            max_replay_buffer_kb=1024,
            max_observability_budget_percent=5.0,
            max_tick_budget_ms=100.0
        )

        
        from src.core.builder import V2EntityBuilder
        # Initial state with a few heroes and a monster region
        state = AuthoritativeState(
            tick=0, 
            seed=seed, 
            world_time=0,
            regions={
                "wilds": RegionState(
                    id="wilds", 
                    name="The Wilds", 
                    bounds=(0, 0, 20, 20),
                    hazard_level=0.4,
                    calamity_intensity=0.1
                )
            },
            entities={
                1: V2EntityBuilder(1).kind("hero").location(2, 2).combat(readiness=100.0).build(),
                2: V2EntityBuilder(2).kind("hero").location(3, 3).combat(readiness=100.0).build()
            }
        )
        
        rng = DeterministicRNG(seed)
        kernel = Kernel(profile, state, rng)
        
        mem_samples = []
        pop_samples = []
        
        for t in range(ticks):
            kernel.tick_once()
            
            # Sample status every 100 ticks
            if t % 100 == 0:
                status = kernel.status
                if status.signal_history:
                    mem_samples.append(status.signal_history[-1].memory_estimate_mb)
                pop_samples.append(len(kernel.state.entities))
                
        final_hash = CanonicalStateHasher.get_hash(kernel.state)
        return final_hash, mem_samples, pop_samples

    # 1. First Run
    print("\nStarting Long-Run Stability Test (Run 1)...")
    start_t = time.time()
    hash1, mem1, pop1 = run_sim(TICKS, SEED)
    duration1 = time.time() - start_t
    print(f"Run 1 Completed in {duration1:.2f}s. Final Hash: {hash1}")

    # 2. Second Run (Reproduction check)
    print("Starting Reproduction Test (Run 2)...")
    hash2, mem2, pop2 = run_sim(TICKS, SEED)
    print(f"Run 2 Completed. Final Hash: {hash2}")

    # VERIFIED v2: long_run_determinism
    assert hash1 == hash2, "DIVERGENCE: Long-run simulation is not deterministic!"

    # 3. Verify Memory Stability
    # We allow some initial growth (caching, etc.) but it should level off.
    # We check if the last 50% of the run has a significantly growing trend.
    if len(mem1) >= 10:
        halfway = len(mem1) // 2
        initial_mem = mem1[0]
        final_mem = mem1[-1]
        late_trend = mem1[-1] - mem1[halfway]
        
        print(f"Memory: Initial={initial_mem:.2f}MB, Final={final_mem:.2f}MB, Late Trend={late_trend:.2f}MB")
        print(f"Population: Initial={pop1[0]}, Mid={pop1[halfway]}, Final={pop1[-1]}")
        
        # Threshold: Adjusted for population growth. 
        # If population doubles, memory will naturally grow.
        assert late_trend < 25.0, f"POTENTIAL MEMORY LEAK: Late-stage growth {late_trend:.2f}MB is too high."


    # 4. Verify Population Stability
    # We expect some entities to be added (spawns) and removed (death/decay).
    # It should not explode to 1,000+ entities if the spawners are balanced.
    final_pop = pop1[-1]
    print(f"Population: Final={final_pop} entities")
    assert final_pop < 200, "POPULATION EXPLOSION: World entity count is too high."
    assert final_pop > 0, "WORLD EXTINCTION: All entities disappeared."

if __name__ == "__main__":
    test_long_run_stability()
