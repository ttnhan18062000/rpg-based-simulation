#!/usr/bin/env python3
"""
Generate (or refresh) the 5,000-tick behavioral regression baseline.

Usage:
    python3 tools/generate_regression_baseline.py
    make regression-baseline
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.regression.test_behavioral_5k import (
    collect_behavioral_metrics,
    BASELINE_PATH,
    SEED,
    TICKS,
    WORLD_ID,
)


def main() -> None:
    print(f"Generating {TICKS}-tick behavioral baseline (world={WORLD_ID}, seed={SEED})...")
    print("This takes ~2 minutes on Class-B hardware. Do not interrupt.")

    t0 = time.monotonic()
    metrics = collect_behavioral_metrics()
    elapsed = time.monotonic() - t0

    baseline = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "world_id": metrics["world_id"],
        "seed": metrics["seed"],
        "ticks": metrics["ticks"],
        "sample_interval": metrics["sample_interval"],
        "sample_count": metrics["sample_count"],
        "elapsed_s": round(elapsed, 1),
        "metrics": {
            "alive_avg":          metrics["alive_avg"],
            "gold_avg":           metrics["gold_avg"],
            "quest_active_count": metrics["quest_active_count"],
        },
    }

    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2) + "\n")

    print(f"\nBaseline written to {BASELINE_PATH}  ({elapsed:.0f}s)")
    print(json.dumps(baseline["metrics"], indent=2))
    print("\nCommit this file to lock the baseline.")


if __name__ == "__main__":
    main()
