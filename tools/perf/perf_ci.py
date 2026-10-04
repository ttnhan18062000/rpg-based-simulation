#!/usr/bin/env python3
"""
V2 Engine Performance CI Gate.
Executes the smoke benchmark matrix and validates against committed baselines.
"""
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_ci_gate():
    # 1. Run Smoke Benchmarks
    logger.info("Step 1: Running smoke benchmark matrix...")
    try:
        subprocess.run([sys.executable, "tools/perf/run_benchmarks.py", "--smoke"], check=True)
    except subprocess.CalledProcessError:
        logger.error("Benchmark execution failed.")
        return False

    # 2. Run Regression Check
    logger.info("Step 2: Checking for performance regressions...")
    result = subprocess.run([sys.executable, "tools/perf/check_perf_regression.py"])
    if result.returncode == 2:
        logger.error("Performance regression check was not comparable: not every baseline was compared.")
        return False
    if result.returncode != 0:
        logger.error("Performance regression check failed.")
        return False

    logger.info("Performance CI Gate passed successfully.")
    return True

if __name__ == "__main__":
    if not run_ci_gate():
        sys.exit(1)
    sys.exit(0)
