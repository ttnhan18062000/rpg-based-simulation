#!/usr/bin/env python3
"""TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION — perf-benchmark a real SimQ corpus world.

Reuses tools/calibrate_simq.py's own world-loading (_load_world_state -> real WorldCompiler-built
AuthoritativeState) so a perf baseline shares real, authored world content with SimQ calibration —
no synthetic scenario needed. This IS a separate, dedicated engine execution from a normal
calibration run (BenchHarness runs its own warmup+sample tick loop) — see investigation.md for why
this isn't a truly free byproduct of an existing calibration run.

Prints the harness result dict; it writes nothing. A corpus baseline comes only from
``tools/perf/rerun_baselines.py record`` (a candidate) followed by ``tools/perf/baseline_lifecycle.py promote``
(TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS removed the old ``--commit`` raw-dict writer).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calibrate_simq import _load_world_state  # noqa: E402


def bench_corpus_world(world_name: str, seed: int, warmup_ticks: int, sample_ticks: int) -> dict:
    from src.perf.bench_harness import BenchHarness
    from src.perf.profiles import PERF_PROFILES

    state, compile_report = _load_world_state(world_name, seed)
    if state is None:
        raise ValueError(
            f"World {world_name!r} has no resolved world spec — cannot benchmark a "
            "non-existent corpus world (this tool is for real corpus worlds only, "
            "not the 'generic' synthetic fallback)."
        )

    # PERF_512MB_LOCAL — matches tests/perf/conftest.py's own perf_harness fixture default and
    # PERF_PROFILES registry, NOT src/config/profiles.py's PROD_SMALL (a different profile
    # namespace used by calibrate_simq.py's own Kernel construction, confirmed incompatible with
    # the real perf-test harness fixture during this ticket's own Test phase).
    profile_name = "PERF_512MB_LOCAL"
    scenario_id = f"simq_corpus_{world_name}"
    harness = BenchHarness(PERF_PROFILES[profile_name])
    result = harness.run_benchmark(
        scenario_id=scenario_id,
        initial_state=state,
        warmup_ticks=warmup_ticks,
        sample_ticks=sample_ticks,
    )
    result["profile"] = profile_name
    result["matrix_scenario"] = "simq_corpus"
    result["source_world"] = world_name
    result["source_entity_count"] = compile_report.get("entity_count")
    result["source_region_count"] = compile_report.get("region_count")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", required=True, help="Corpus world name under data/worlds/")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--warmup-ticks", type=int, default=100)
    parser.add_argument("--sample-ticks", type=int, default=1000)
    args = parser.parse_args()

    result = bench_corpus_world(args.world, args.seed, args.warmup_ticks, args.sample_ticks)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
