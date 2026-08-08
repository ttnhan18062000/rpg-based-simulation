#!/usr/bin/env python3
"""Long-run (default 5000-tick) combined SimQ pillar + entity-lifecycle observation.

TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER: the real, calibration-corpus-wide default
(62.5% of grade_anchors.json run_keys) is 200 ticks — too short for several lifecycle/diversity
signals to be reliable (entity_lifecycle_score.py's own clustering_reliable_tick_threshold: 1000;
see this ticket's investigation.md for the full tick-gated-detector survey). This tool is an
additive, periodic observation tier, NOT a fast-tier regression fixture — it does not touch
grade_anchors.json or any SimQ pillar scoring formula; it drives one real Kernel run per world and
captures both the real SimQ pillar report and the real entity-lifecycle score from the SAME run,
writing durable, committed JSON snapshots to docs/simulation_quality/long_run_observations/.

Reuses entity_lifecycle_score.py's own lean _run_for_analysis() run-driver (not
calibrate_simq.py's _run_engine(), whose own integrity guard is confirmed non-deterministic under
higher event volume -- see entity_lifecycle_score.py's own module docstring) so the Kernel runs
exactly once per world; both the SimQ report and the lifecycle score are derived from that same
run_dir's simulation_events.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS_DIR))

DEFAULT_WORLDS = [
    "wilderness_survival",
    "resource_dense_basin",
    "crowded_frontier",
    "hero_guild_routing",
    "dungeon_crawl",
    "urban_political",
]

OUTPUT_DIR = Path("docs/simulation_quality/long_run_observations")


def observe_world(world: str, seed: int, ticks: int, obs_mode: str = "NORMAL") -> dict:
    """Drive one real Kernel run for `world` and return a combined SimQ + lifecycle observation.

    Cleans up its own data/runs/ scratch directory before returning -- never leaves scratch run
    data behind, matching this repo's own convention.
    """
    from entity_lifecycle_score import _run_for_analysis, load_weights, score_run
    from calibrate_simq import _build_hub, _load_weights, _load_world_state, _replay_jsonl_through_hub, _resolve_profile

    run_dir, health = _run_for_analysis(world, seed, ticks, obs_mode)
    try:
        profile = _resolve_profile(world)
        simq_weights = _load_weights(profile)
        run_id = os.path.basename(run_dir)
        hub, _persistence = _build_hub(simq_weights, run_dir, run_id)
        event_count = _replay_jsonl_through_hub(run_dir, hub)
        simq_report = hub.get_quality_report().to_dict()

        world_state, _compile_report = _load_world_state(world, seed)
        els_weights = load_weights()
        lifecycle_score = score_run(
            run_dir, world_state, ticks, els_weights,
            group_by=["role", "faction", "kind", "region"], world_name=world,
        )

        return {
            "world": world,
            "seed": seed,
            "ticks": ticks,
            "obs_mode": obs_mode,
            "health": health,
            "simq_event_count": event_count,
            "simq_report": simq_report,
            "lifecycle_score": lifecycle_score,
        }
    finally:
        if os.path.isdir(run_dir) and run_dir.startswith("data/runs/"):
            shutil.rmtree(run_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Long-run combined SimQ + entity-lifecycle observation")
    parser.add_argument("--ticks", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--worlds", type=str, default=None,
        help=f"Comma-separated world names (default: {','.join(DEFAULT_WORLDS)})",
    )
    parser.add_argument("--obs-mode", type=str, default="NORMAL", dest="obs_mode")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR), dest="output_dir")
    args = parser.parse_args()

    worlds = [w.strip() for w in args.worlds.split(",")] if args.worlds else DEFAULT_WORLDS
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for world in worlds:
        print(f"[simq_long_run_observation] Observing {world} at {args.ticks} ticks...", flush=True)
        result = observe_world(world, args.seed, args.ticks, args.obs_mode)
        out_path = output_dir / f"{world}_seed{args.seed}_{args.ticks}t.json"
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, default=str)
        report = result["simq_report"]
        clustering = result["lifecycle_score"]["clustering"]["global"]
        print(
            f"  overall_grade={report['overall_grade']} "
            f"dominant_shape_share={clustering['dominant_shape_share']} "
            f"dropped={result['health']['dropped_count']}"
        )
        print(f"  Written: {out_path}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
