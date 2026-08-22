"""Rendering-quality metric-family threshold calibration script.

Usage:
    python3 tools/calibrate_rendering.py run --world dungeon_crawl --seed 42
    python3 tools/calibrate_rendering.py run --world dungeon_crawl --seed 137
    python3 tools/calibrate_rendering.py run --world dungeon_crawl --seed 999
    python3 tools/calibrate_rendering.py aggregate

Runs all four rendering metric families (connectivity, density, shape, and the
terrain-histogram half of variants) against one real, compiled world+seed pair and
writes a quality_report.json-equivalent JSON artifact to
data/calibration/rendering/{world}_seed{seed}/. Multi-seed/multi-world sweeping is an
external loop over repeated `run` invocations -- this script's own `--seed` flag accepts
exactly one integer per invocation, mirroring tools/calibrate_simq.py's CLI shape -- e.g.:

    for world in dungeon_crawl sandbox_world; do
      for seed in 42 137 999; do
        python3 tools/calibrate_rendering.py run --world "$world" --seed "$seed"
      done
    done
    python3 tools/calibrate_rendering.py aggregate

The `aggregate` subcommand then scans a directory of already-written per-run artifacts
and computes descriptive (min/max/mean, never asserted-against) healthy-band candidate
statistics per family, writing one provenance-headed JSON report to config/rendering/ --
a file separate from config/rendering/grade_thresholds.toml, never overwriting it (see
staging_artifacts/TCK-20260821-VISUAL-QUALITY-CALIBRATION/plan.md Decision 1).

compute_trail_activity (src/rendering/variants.py) is deliberately NOT implemented,
called, or calibrated anywhere in this script -- it structurally requires ticking a
Kernel forward N times and recording entity positions, a materially more expensive and
failure-prone operation than the single WorldCompiler.compile() call every other family
(and TVD's own per-run-histogram half) needs. That calibration is deferred to a future
ticket (plan.md Decision 2).

This script never imports src.simulation_quality.* or src.observability.events --
mirroring the four rendering metric modules' own independence-boundary discipline
(src/rendering/shape.py, src/rendering/variants.py) -- and never opens, parses, or
writes config/rendering/grade_thresholds.toml.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from src.rendering.connectivity import analyze_connectivity
from src.rendering.density import compute_density_cv, compute_terrain_histogram
from src.rendering.shape import connected_components
from src.rendering.variants import normalize_histogram, total_variation_distance


class CalibrationIntegrityError(Exception):
    """Raised when a calibration run's WorldCompiler.compile() produced a corrupted or
    degenerate compile_report -- mirrors tools/calibrate_simq.py's CalibrationIntegrityError
    (INFRA-320), adapted to this script's real single-compile-call architecture (no
    Kernel/EventRecorder queue exists here -- see plan.md Decision 2/8)."""


def _atomic_write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    os.rename(tmp_path, path)


def _load_and_compile(world_id: str, seed: int):
    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    return WorldCompiler.compile(spec, seed=seed)


def _check_compile_integrity(compile_report: dict, cal_dir: str) -> None:
    warnings = compile_report.get("warnings", [])
    entity_count = compile_report.get("entity_count", 0)
    region_count = compile_report.get("region_count", 0)
    guard_passed = (not warnings) and entity_count > 0 and region_count > 0
    _atomic_write_json(
        os.path.join(cal_dir, "compile_health.json"),
        {"warnings": warnings, "entity_count": entity_count,
         "region_count": region_count, "guard_passed": guard_passed},
    )
    if not guard_passed:
        raise CalibrationIntegrityError(
            f"compile integrity guard failed for world_id={compile_report.get('world_id')} "
            f"seed={compile_report.get('seed')}: warnings={warnings}, "
            f"entity_count={entity_count}, region_count={region_count}. Calibration data "
            f"for this run is unreliable and must not be written."
        )


@dataclass(frozen=True)
class RenderingCalibrationRunArtifact:
    world_id: str
    seed: int
    compile_report: dict
    connectivity: dict
    density: dict
    shape: dict
    variants: dict

    def to_dict(self) -> dict:
        return {
            "world_id": self.world_id, "seed": self.seed,
            "compile_report": self.compile_report, "connectivity": self.connectivity,
            "density": self.density, "shape": self.shape, "variants": self.variants,
        }


def _build_run_artifact(world_id: str, seed: int, state, compile_report: dict) -> RenderingCalibrationRunArtifact:
    conn = analyze_connectivity(state.terrain, state.blocked_tiles)
    dens = compute_density_cv(state.entities)
    shape_components = connected_components(state.terrain)
    raw_histogram = compute_terrain_histogram(state.terrain)
    normalized_histogram = normalize_histogram(raw_histogram)
    return RenderingCalibrationRunArtifact(
        world_id=world_id, seed=seed, compile_report=compile_report,
        connectivity={"walkable_count": conn.walkable_count,
                      "component_count": conn.component_count,
                      "component_sizes": conn.component_sizes,
                      "percent_reachable": conn.percent_reachable},
        density={"cv": dens.cv, "entity_count": dens.entity_count},
        shape={"components": [
            {"terrain_type": c.terrain_type, "size": c.size,
             "fill_ratio": c.fill_ratio, "bbox": list(c.bbox)}
            for c in shape_components
        ]},
        variants={"terrain_histogram_normalized": normalized_histogram},
    )


def _run_one(args) -> None:
    cal_dir = args.output or os.path.join(
        "data", "calibration", "rendering", f"{args.world}_seed{args.seed}"
    )
    state, compile_report = _load_and_compile(args.world, args.seed)
    _check_compile_integrity(compile_report, cal_dir)
    artifact = _build_run_artifact(args.world, args.seed, state, compile_report)
    output_path = os.path.join(cal_dir, "quality_report.json")
    _atomic_write_json(output_path, artifact.to_dict())
    print(f"[calibrate_rendering] world={args.world} seed={args.seed} -> {output_path}")


def _stats(values: list[float]) -> dict:
    return {
        "min": min(values),
        "max": max(values),
        "mean": statistics.mean(values),
        "n": len(values),
    }


def _aggregate(args) -> None:
    run_dirs = sorted(glob.glob(os.path.join(args.input_dir, "*")))
    loaded_runs: list[dict] = []
    for run_dir in run_dirs:
        report_path = os.path.join(run_dir, "quality_report.json")
        if not os.path.isfile(report_path):
            continue
        with open(report_path, "r", encoding="utf-8") as fh:
            loaded_runs.append(json.load(fh))

    percent_reachable_values = [r["connectivity"]["percent_reachable"] for r in loaded_runs]
    density_cv_values = [r["density"]["cv"] for r in loaded_runs]

    fill_ratio_by_terrain_type: dict[str, list[float]] = {}
    for r in loaded_runs:
        for component in r["shape"]["components"]:
            fill_ratio_by_terrain_type.setdefault(component["terrain_type"], []).append(
                component["fill_ratio"]
            )

    runs_by_world: dict[str, list[dict]] = {}
    for r in loaded_runs:
        runs_by_world.setdefault(r["world_id"], []).append(r)

    shape_variance_by_world: dict[str, object] = {}
    tvd_variance_by_world: dict[str, object] = {}
    for world_id, world_runs in runs_by_world.items():
        if len(world_runs) < 2:
            continue

        shape_signatures = [
            sorted(
                (c["terrain_type"], c["size"], c["fill_ratio"])
                for c in run["shape"]["components"]
            )
            for run in world_runs
        ]
        if all(sig == shape_signatures[0] for sig in shape_signatures):
            shape_variance_by_world[world_id] = "none (expected)"
        else:
            shape_variance_by_world[world_id] = "variance observed across seeds"

        histograms = [run["variants"]["terrain_histogram_normalized"] for run in world_runs]
        max_tvd = 0.0
        for i in range(len(histograms)):
            for j in range(i + 1, len(histograms)):
                tvd = total_variation_distance(histograms[i], histograms[j])
                max_tvd = max(max_tvd, tvd)
        if max_tvd == 0.0:
            tvd_variance_by_world[world_id] = "none (expected)"
        else:
            tvd_variance_by_world[world_id] = max_tvd

    provenance = {
        "calibration": f"{datetime.date.today().isoformat()} | TCK-20260821-VISUAL-QUALITY-CALIBRATION",
        "worlds": sorted({r["world_id"] for r in loaded_runs}),
        "seeds": sorted({r["seed"] for r in loaded_runs}),
        "ticks": 0,
        "scope_note": (
            "connectivity/density/shape/variants-TVD only (single WorldCompiler.compile() "
            "call per run); compute_trail_activity is deferred, see plan.md Decision 2"
        ),
    }

    observed = {
        "connectivity": {"percent_reachable": _stats(percent_reachable_values)} if percent_reachable_values else {},
        "density": {"cv": _stats(density_cv_values)} if density_cv_values else {},
        "shape": {
            "fill_ratio_by_terrain_type": {
                terrain_type: _stats(values)
                for terrain_type, values in fill_ratio_by_terrain_type.items()
            },
            "same_world_cross_seed_variance": shape_variance_by_world,
        },
        "variants": {
            "same_world_cross_seed_tvd": tvd_variance_by_world,
        },
    }

    report = {
        "provenance": provenance,
        "observed": observed,
        "validation_summary": (
            "Descriptive calibration statistics only -- no threshold value in this report "
            "is asserted, gated, or final. Not consumed by any pytest/CI gate or scoring "
            "pipeline."
        ),
        "runs_included": [
            {"world_id": r["world_id"], "seed": r["seed"]} for r in loaded_runs
        ],
    }
    _atomic_write_json(args.output, report)
    print(f"[calibrate_rendering] aggregated {len(loaded_runs)} runs -> {args.output}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rendering metric-family threshold calibration.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    run_parser = subparsers.add_parser("run", help="Run all four metric families for one (world, seed).")
    run_parser.add_argument("--world", type=str, required=True)
    run_parser.add_argument("--seed", type=int, required=True)
    run_parser.add_argument("--output", type=str, default=None)

    aggregate_parser = subparsers.add_parser("aggregate", help="Aggregate already-written per-run artifacts.")
    aggregate_parser.add_argument(
        "--input-dir", type=str, dest="input_dir",
        default=os.path.join("data", "calibration", "rendering"),
    )
    aggregate_parser.add_argument(
        "--output", type=str,
        default=os.path.join(
            "config", "rendering", "calibration_report_TCK-20260821-VISUAL-QUALITY-CALIBRATION.json"
        ),
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if args.mode == "run":
        _run_one(args)
    else:
        _aggregate(args)


if __name__ == "__main__":
    main()
