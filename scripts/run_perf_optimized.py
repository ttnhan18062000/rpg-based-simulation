import os
import json
import time
import psutil
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.config.profiles import PROD_DEFAULT

SCENARIOS = {
    "IDLE_1000": {"entities": 1000, "ticks": 100},
    "IDLE_5000": {"entities": 5000, "ticks": 100},
    "STRATEGIC_500": {"entities": 500, "ticks": 50, "activity": "strategic"},
}

def run_scenario(name, config):
    print(f"[*] Running Scenario: {name} ({config['entities']} entities)")
    # Build entities
    from src.core.builder import V2EntityBuilder
    entities = {}
    for i in range(config["entities"]):
        builder = V2EntityBuilder(i)
        # Spread entities out: 1 per tile in a grid
        grid_size = int(config["entities"]**0.5) + 1
        x = i % grid_size
        y = i // grid_size
        builder.location(x, y)
        if config.get("activity") == "strategic":
             # Give them some gold and items to trigger strategic logic
             builder.inventory(gold=100)
        entities[i] = builder.build()
        
    # Initialize state
    state = AuthoritativeState(seed=42, tick=0, entities=entities, regions={})
        
    from src.platform.rng import DeterministicRNG
    rng = DeterministicRNG(42)
    kernel = Kernel(profile=PROD_DEFAULT, state=state, rng=rng)
    
    latencies = []
    process = psutil.Process(os.getpid())
    
    for t in range(config["ticks"]):
        start = time.perf_counter()
        kernel.tick_once()
        end = time.perf_counter()
        latencies.append((end - start) * 1000)
        
        if (t + 1) % 10 == 0:
            avg = sum(latencies[-10:]) / 10
            print(f"    Tick {t+1}/{config['ticks']} | Avg Latency: {avg:.2f}ms")
            costs = kernel._phase_costs
            print(f"      Costs: { {k: f'{v:.2f}ms' for k, v in costs.items()} }")

    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)]
    rss = process.memory_info().rss / (1024 * 1024)
    
    print(f"    p95: {p95:.2f}ms | RSS: {rss:.1f}MB\n")
    return {"p95": p95, "rss": rss}

if __name__ == "__main__":
    results = {}
    for name, config in SCENARIOS.items():
        results[name] = run_scenario(name, config)
        
    os.makedirs("reports/perf", exist_ok=True)
    with open("reports/perf/optimized.json", "w") as f:
        json.dump(results, f, indent=4)
    print("[+] Optimized results saved to reports/perf/optimized.json")
