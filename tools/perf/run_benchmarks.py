import sys
import os
import json
import logging
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.perf.bench_harness import BenchHarness
from src.perf.scenarios import SCENARIO_BUILDERS
from src.perf.profiles import PERF_MATRIX, PERF_PROFILES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_matrix(smoke=False):
    """
    Execute the standardized performance matrix.
    M5 Law: All benchmarks must use the explicit PERF_MATRIX and SCENARIO_BUILDERS.
    """
    output_dir = Path("reports/perf")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for scenario_name, scales in PERF_MATRIX.items():
        builder = SCENARIO_BUILDERS[scenario_name]
        
        for scale, modes in scales.items():
            # Smoke filter: Only smallest scale for each scenario/mode
            if smoke and scale != min(scales.keys()):
                continue
            
            for mode, profile_name in modes.items():
                profile = PERF_PROFILES[profile_name]
                
                # Setup state based on scenario signature
                if scenario_name == "combat":
                    state = builder(team_a_count=scale, team_b_count=scale)
                elif scenario_name == "resource":
                    state = builder(entity_count=scale, node_count=scale // 2)
                else:
                    state = builder(entity_count=scale)
                
                harness = BenchHarness(profile)
                
                # Reduce ticks for smoke tests to fit CI budgets
                warmup = 10 if smoke else 50
                sample = 20 if smoke else 200
                
                logger.info(f"Running {scenario_name} scale={scale} mode={mode} ({profile_name})...")
                try:
                    res = harness.run_benchmark(
                        f"{scenario_name}_{scale}_{mode}", 
                        state, 
                        warmup_ticks=warmup, 
                        sample_ticks=sample
                    )
                except Exception as e:
                    logger.error(f"Benchmark failed for {scenario_name}_{scale}_{mode}: {e}")
                    continue
                
                # Add matrix metadata for aggregator
                res["matrix_scenario"] = scenario_name
                res["matrix_scale"] = scale
                res["matrix_mode"] = mode
                
                # Save individual JSON for granular traceability
                filename = f"{scenario_name}_{scale}_{mode}.json"
                with open(output_dir / filename, "w") as f:
                    json.dump(res, f, indent=2)
                
                results.append(res)
    
    # Save full matrix result for summary report
    with open(output_dir / "matrix_full.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Benchmark run complete. Results in {output_dir}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Run only the smallest scale for CI/Smoke tests.")
    args = parser.parse_args()
    
    run_matrix(smoke=args.smoke)
