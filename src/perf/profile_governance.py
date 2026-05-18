import cProfile
import pstats
from dataclasses import replace
from pstats import SortKey
import time
from src.perf.scenarios import build_metropolis_state
from src.perf.governance_scenarios import build_governance_state
from src.engine.kernel import Kernel
from src.config.profiles import PROD_DEFAULT
from src.platform.rng import DeterministicRNG
from src.engine.cadence import SystemCadence

def profile_governance():
    # Setup a heavy governance state
    # 1. Build Metropolis Scenario
    print("Building Metropolis Scenario (1000 entities, 50 regions, 1000 buildings)...")
    state = build_metropolis_state(entity_count=1000, region_count=50, buildings_per_region=20)
    
    # Custom cadence with high-frequency taxation for profiling
    cadence = SystemCadence(town_resolution=1)
    profile = PROD_DEFAULT.model_copy(update={"cadence": cadence})
    
    kernel = Kernel(
        profile,
        state,
        DeterministicRNG(42),
        flags={"audit_mode": False, "no_frame_pacing": True, "no_replay": True, "force_full_scan": True}
    )
    
    print("Starting profile...")
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run 5 ticks (each is a tax tick)
    for i in range(5):
        t0 = time.perf_counter()
        kernel.tick_once()
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"Tick {i} took {elapsed:.2f}ms")
        
    profiler.disable()
    
    stats = pstats.Stats(profiler)
    stats.sort_stats(SortKey.CUMULATIVE)
    print("\n--- Top 20 Cumulative Functions ---")
    stats.print_stats(20)
    
    print("\n--- TownResolutionSystem Breakdown ---")
    stats.print_stats("town_resolution.py")
    
    print("\n--- SpatialQueryService Breakdown ---")
    stats.print_stats("spatial_query.py")
    
    print("\n--- TownResolutionSystem Callees ---")
    stats.print_callees("/home/vboxuser/Work/rpg-based-simulation/src/engine/town_resolution.py:19(resolve)")

if __name__ == "__main__":
    profile_governance()
