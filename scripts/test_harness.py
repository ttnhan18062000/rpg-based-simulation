#!/usr/bin/env python3
"""
Test Harness for Strategic Implementation. [MILESTONE 7]
Provides a deterministic headless run path using the authoritative HeadlessRunner.
"""

import os
import sys
import argparse
import logging
from typing import Any

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.testing.headless_regression_runner import HeadlessRunner
from src.testing.assertions import load_json, assert_graph_integrity

def setup_harness_logging(log_level: str = "INFO"):
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def run_harness(seed: int, ticks: int, output_dir: str, verify: bool = False, max_runs: int = 10) -> Any:
    """Execute a deterministic simulation run using the HeadlessRunner."""
    runner = HeadlessRunner(output_root=output_dir, max_runs=max_runs)
    
    print(f"--- HARNESS RUN START (Seed: {seed}, Ticks: {ticks}) ---")
    
    result = runner.run(seed, ticks)
    
    if not result.success:
        print(f"ERROR: {result.error}")
        return
        
    print(f"Simulation finished: {result.ticks} ticks in {result.duration:.2f}s ({result.ticks/result.duration:.2f} TPS)")
    print(f"Replay saved to: {result.replay_path}")
    print(f"Cognition graphs saved for {len(result.cognition_paths)} entities.")
    
    # 5. Verification (Optional)
    if verify:
        print("--- VERIFICATION ---")
        errors = 0
        
        # Verify Replay
        if result.replay_path.exists() and result.replay_path.stat().st_size > 0:
            print(f"✓ Replay captured: {result.replay_path}")
        else:
            print(f"✗ Replay missing or empty: {result.replay_path}")
            errors += 1
            
        # Verify Graphs
        for eid, path in result.cognition_paths.items():
            if path.exists() and path.stat().st_size > 0:
                print(f"✓ Cognition export captured for E{eid}: {path}")
                try:
                    graph = load_json(path)
                    assert_graph_integrity(graph)
                    print(f"  ✓ Structural integrity verified for E{eid}")
                except Exception as e:
                    print(f"  ✗ Integrity check failed for E{eid}: {e}")
                    errors += 1
            else:
                print(f"✗ Cognition export missing or empty for E{eid}: {path}")
                errors += 1
        
        if errors == 0:
            print("--- ALL VERIFICATIONS PASSED ---")
        else:
            print(f"--- VERIFICATION FAILED ({errors} errors) ---")
            
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strategic Implementation Test Harness")
    parser.add_argument("--seed", type=int, default=111, help="Deterministic world seed")
    parser.add_argument("--ticks", type=int, default=50, help="Number of ticks to run")
    parser.add_argument("--outdir", type=str, default="logs/harness", help="Output directory")
    parser.add_argument("--verify", action="store_true", help="Verify output artifacts")
    parser.add_argument("--max-runs", type=int, default=10, help="Max run artifacts to keep in outdir")
    
    args = parser.parse_args()
    setup_harness_logging()
    run_harness(args.seed, args.ticks, args.outdir, args.verify, args.max_runs)
