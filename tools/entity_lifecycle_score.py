#!/usr/bin/env python3
"""Per-entity lifecycle scoring tool (TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS).

Computes 7 named, never-blended-into-one per-entity metrics from a real recorded event stream
(path_length, path_density, phase_coverage, path_entropy, loop_score, growth_trajectory,
conclusion_coherence), then aggregates them population-wide and per group (role/faction/kind/
region) with mean AND spread, never mean alone -- see this ticket's own investigation.md for why
(a same-day investigation found a 67%-identical population masked by a healthy-looking mean).

Data source: either drives a fresh, short-lived simulation (`--world`/`--seed`/`--ticks`) via
`_run_for_analysis()`, or scores an existing `data/runs/{run_id}/simulation_events.jsonl`
directory (`--run-dir`), mirroring tools/calibrate_simq.py's own run/score separation.

`_run_for_analysis()` deliberately does NOT reuse `tools.calibrate_simq._run_engine()` -- that
function's own integrity guard requires `pressure_mode_final == "NORMAL"` (zero backpressure for
the entire run), a bar calibrated for SimQ-score CALIBRATION trustworthiness specifically. This
tool's own correctness bar is narrower: `dropped_count == 0` (no event actually lost). Real
investigation found `_run_engine()`'s stricter guard is non-deterministic under the higher event
volume `SIM_OBS_MODE=NORMAL` requires (real-time queue-timing sensitive, not a function of
world/seed/ticks) -- reusing it unmodified would make this tool flaky for reasons unrelated to
the simulation being analyzed. See investigation.md's own Item 4 for the full real-data trace.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Optional

import yaml

_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

DEFAULT_WEIGHTS_PATH = Path("config/simulation_quality/entity_lifecycle_weights.yaml")


def load_weights(path: Optional[str] = None) -> dict:
    resolved = DEFAULT_WEIGHTS_PATH if path is None else Path(path)
    return yaml.safe_load(resolved.read_text())


def _event_type_to_bucket(weights: dict) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for bucket, event_types in weights["lifecycle_phase_buckets"].items():
        for et in event_types:
            mapping[et] = bucket
    return mapping


# ---------------------------------------------------------------------------
# Data source: dedicated run driver (does not reuse calibrate_simq._run_engine's own guard)
# ---------------------------------------------------------------------------


def _run_for_analysis(
    world: str, seed: int, ticks: int, obs_mode: str, entity_count: int = 10
) -> tuple[str, dict]:
    """Drive a short-lived Kernel run at the given observability mode; return (run_dir, health).

    health = {"dropped_count": int, "pressure_mode_final": str, "survival_triggered": bool} --
    reported, not hard-failed on, per this module's own docstring.
    """
    os.environ["SIM_OBS_MODE"] = obs_mode

    from src.engine.kernel import Kernel
    from src.core.state import AuthoritativeState
    from src.platform.rng import DeterministicRNG
    from src.systems.world_systems.generator import EntityGenerator
    from src.config.profiles import PROD_SMALL
    from calibrate_simq import _load_world_state, _load_profile_feature_flags, _resolve_profile
    from src.domains.optimization.feature_flags import FeatureMode

    rng = DeterministicRNG(seed)
    state, _compile_report = _load_world_state(world, seed)

    if state is None:
        gen = EntityGenerator(seed)
        entities = {}
        hero = gen.spawn_hero((64.0, 64.0))
        entities[hero.id] = hero
        for i in range(entity_count - 1):
            gx, gy = 20.0 + (i % 5) * 8.0, 20.0 + (i // 5) * 8.0
            monster = gen.spawn_goblin((gx, gy))
            entities[monster.id] = monster
        state = AuthoritativeState(tick=0, seed=seed, entities=entities)

    profile = _resolve_profile(world)
    extra_flags = _load_profile_feature_flags(profile) or {}
    combined: dict = {}
    for flag, raw_val in extra_flags.items():
        val = raw_val.strip().upper()
        if val in ("ON", "TRUE", "1", "YES"):
            combined[flag] = FeatureMode.ON
    if combined:
        from dataclasses import replace as dc_replace
        existing = dict(getattr(state, "feature_flags", None) or {})
        existing.update(combined)
        state = dc_replace(state, feature_flags=existing)

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng, flags={"no_frame_pacing": True})
    run_id = getattr(kernel, "_run_id", None)
    for _ in range(ticks):
        kernel.tick_once()

    obs_status = kernel.event_recorder.observability_status()
    dropped_count = kernel.event_recorder.queue.dropped_count
    survival_triggered = any(obs_status["survival_counts"].values())

    try:
        kernel.shutdown()
    except Exception:
        pass
    time.sleep(0.3)

    health = {
        "dropped_count": dropped_count,
        "pressure_mode_final": obs_status["mode"],
        "survival_triggered": survival_triggered,
        "data_loss": dropped_count > 0,
    }
    run_dir = os.path.join("data", "runs", run_id) if run_id else ""
    return run_dir, health


# ---------------------------------------------------------------------------
# Entity metadata + path extraction
# ---------------------------------------------------------------------------


def _entity_metadata(world_state) -> dict[int, dict]:
    """role/faction/kind/region per entity, per investigation.md Item 1's corrected field paths.

    faction reads entity.identity.properties["faction_id"] (the real, content-driven faction
    string) -- NOT entity.identity.faction (the legacy 4-value IntEnum, confirmed via direct
    inspection to collapse all real per-world faction diversity into 4 buckets).
    region reads entity.identity.properties["spawn_region"] directly -- no
    LegalityServiceV2.get_region_for_position spatial lookup needed, confirmed always present.
    """
    from src.core.enums import EntityRole

    role_names = {int(r): r.name for r in EntityRole}
    metadata: dict[int, dict] = {}
    for eid, ent in world_state.entities.items():
        props = getattr(ent.identity, "properties", None) or {}
        metadata[eid] = {
            "role": role_names.get(int(ent.identity.role), str(int(ent.identity.role))),
            "faction": props.get("faction_id"),
            "kind": ent.kind,
            "region": props.get("spawn_region"),
        }
    return metadata


def extract_entity_paths(run_dir: str, world_state) -> dict[int, dict]:
    """Read simulation_events.jsonl, group by entity_id, join real metadata.

    Raw JSONL event_type values are the PRE-translation, engine-emitted names (e.g.
    "StrategicObjectiveChanged") -- QualityHub only translates to the SimQ contract vocabulary
    (e.g. "strategic_goal_changed") at scoring time, not at emission time. Reuses
    QualityHub._translate() directly (real reuse, not a hand-duplicated partial alias list) so
    this tool's bucket mapping -- built from the translated/snake_case entity.yaml catalog --
    actually matches what's really in the JSONL.
    """
    from src.simulation_quality.quality_hub import QualityHub
    from src.observability.events import ObservabilityEventEnvelope

    metadata = _entity_metadata(world_state)
    jsonl_path = os.path.join(run_dir, "simulation_events.jsonl")
    paths: dict[int, list] = {}
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            eid = d.get("entity_id")
            if eid is None:
                continue
            d = dict(d)
            d.pop("related_entity_ids", None)
            try:
                env = ObservabilityEventEnvelope(**d)
                event_type = QualityHub._translate(env).event_type
            except TypeError:
                event_type = d.get("event_type")
            paths.setdefault(eid, []).append((d.get("tick"), event_type, d.get("severity")))

    result: dict[int, dict] = {}
    for eid, events in paths.items():
        events_sorted = sorted(events, key=lambda x: (x[0] if x[0] is not None else 0))
        result[eid] = {
            "events": events_sorted,
            "metadata": metadata.get(eid, {"role": None, "faction": None, "kind": None, "region": None}),
        }
    return result


# ---------------------------------------------------------------------------
# Per-entity metrics
# ---------------------------------------------------------------------------


def _shannon_entropy_normalized(type_seq: list[str]) -> float:
    if len(type_seq) < 2:
        return 0.0
    counts = Counter(type_seq)
    total = len(type_seq)
    probs = [c / total for c in counts.values()]
    raw_entropy = -sum(p * math.log2(p) for p in probs)
    n_distinct = len(counts)
    max_entropy = math.log2(n_distinct) if n_distinct > 1 else 1.0
    return raw_entropy / max_entropy if max_entropy > 0 else 0.0


def dominant_cycle_coverage(type_seq: list[str], max_period: int = 12) -> tuple[int, float]:
    n = len(type_seq)
    if n < 6:
        return (0, 0.0)
    best = (0, 0.0)
    for p in range(1, min(max_period, n // 3) + 1):
        matches = sum(1 for i in range(n - p) if type_seq[i] == type_seq[i + p])
        coverage = matches / (n - p)
        if coverage > best[1]:
            best = (p, coverage)
    return best


def compute_entity_metrics(entity_path: dict, weights: dict, ticks_observed: int) -> dict:
    events = entity_path["events"]
    type_seq = [et for (_t, et, _sev) in events]
    bucket_map = _event_type_to_bucket(weights)
    min_sample = weights["minimum_sample_threshold"]

    path_length = len(events)
    path_density = path_length / ticks_observed if ticks_observed > 0 else 0.0

    buckets_touched = {bucket_map.get(et, "UNBUCKETED") for et in type_seq} - {"UNBUCKETED"}
    n_real_buckets = len(weights["lifecycle_phase_buckets"])
    phase_coverage = len(buckets_touched) / n_real_buckets if n_real_buckets else 0.0

    low_confidence = path_length < min_sample
    path_entropy = _shannon_entropy_normalized(type_seq)
    period, coverage = dominant_cycle_coverage(type_seq)
    loop_score = coverage

    growth_tags = set(weights["growth_trajectory_tags"]["positive"])
    stall_tags = set(weights["growth_trajectory_tags"]["negative"])
    growth_count = sum(1 for et in type_seq if et in growth_tags)
    stall_count = sum(1 for et in type_seq if et in stall_tags)
    growth_trajectory = (
        (growth_count - stall_count) / path_length if path_length > 0 else 0.0
    )

    incoherent_tags = set(weights["conclusion_incoherent_tags"])
    is_incoherent = any(et in incoherent_tags for et in type_seq)
    silent_from_spawn = path_length == 0
    conclusion_coherence = not is_incoherent

    return {
        "path_length": path_length,
        "path_density": round(path_density, 6),
        "phase_coverage": round(phase_coverage, 4),
        "buckets_touched": sorted(buckets_touched),
        "path_entropy": round(path_entropy, 4),
        "path_entropy_confidence": "low" if low_confidence else "normal",
        "loop_score": round(loop_score, 4),
        "loop_score_period": period,
        "loop_score_confidence": "low" if low_confidence else "normal",
        "growth_trajectory": round(growth_trajectory, 4),
        "conclusion_coherence": conclusion_coherence,
        "silent_from_spawn": silent_from_spawn,
        "metadata": entity_path["metadata"],
    }


# ---------------------------------------------------------------------------
# Population aggregation + grouping
# ---------------------------------------------------------------------------

_NUMERIC_METRICS = (
    "path_length", "path_density", "phase_coverage", "path_entropy", "loop_score",
    "growth_trajectory",
)


def _mean_stdev(values: list[float]) -> tuple[float, float]:
    n = len(values)
    if n == 0:
        return (0.0, 0.0)
    mean = sum(values) / n
    if n < 2:
        return (mean, 0.0)
    variance = sum((v - mean) ** 2 for v in values) / n
    return (mean, math.sqrt(variance))


def _aggregate_one_group(entity_metrics: list[dict]) -> dict:
    result: dict = {"entity_count": len(entity_metrics)}
    for metric in _NUMERIC_METRICS:
        values = [em[metric] for em in entity_metrics]
        mean, stdev = _mean_stdev(values)
        result[metric] = {"mean": round(mean, 4), "stdev": round(stdev, 4)}
    coherent_count = sum(1 for em in entity_metrics if em["conclusion_coherence"])
    result["conclusion_coherence_rate"] = round(
        coherent_count / len(entity_metrics), 4
    ) if entity_metrics else 0.0
    return result


def aggregate(entity_metrics: dict[int, dict], group_by: Optional[list[str]] = None) -> dict:
    all_metrics = list(entity_metrics.values())
    result: dict = {"global": _aggregate_one_group(all_metrics)}

    # within-run z-scores per entity, per metric, relative to the global population
    global_stats = {
        metric: _mean_stdev([em[metric] for em in all_metrics])
        for metric in _NUMERIC_METRICS
    }
    zscores: dict[int, dict] = {}
    for eid, em in entity_metrics.items():
        z: dict[str, float] = {}
        for metric in _NUMERIC_METRICS:
            mean, stdev = global_stats[metric]
            z[metric] = round((em[metric] - mean) / stdev, 4) if stdev > 0 else 0.0
        zscores[eid] = z
    result["zscores"] = zscores

    if group_by:
        groups: dict = {}
        for dim in group_by:
            by_value: dict[str, list[dict]] = {}
            for em in all_metrics:
                key = str(em["metadata"].get(dim))
                by_value.setdefault(key, []).append(em)
            groups[dim] = {value: _aggregate_one_group(members) for value, members in by_value.items()}
        result["groups"] = groups

    return result


def _bigrams(type_seq: list[str]) -> set:
    return set(zip(type_seq, type_seq[1:])) if len(type_seq) > 1 else set()


_DIVERSITY_CONTEXT_BY_ARCHETYPE = {
    "monster_only_gauntlet": (
        "monster-only gauntlet (TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS) -- low "
        "diversity is expected by design for this world's archetype, not a defect"
    ),
}


def _load_world_archetype(world_name: Optional[str]) -> Optional[str]:
    """Reads config/simulation_quality/corpus_registry.yaml's _worlds[world_name].archetype.
    Fails open (returns None) if the registry or the world entry doesn't exist -- this is an
    interpretive annotation, never a hard requirement to score a run."""
    if not world_name:
        return None
    registry_path = Path("config/simulation_quality/corpus_registry.yaml")
    if not registry_path.exists():
        return None
    registry = yaml.safe_load(registry_path.read_text())
    return (registry.get("_worlds", {}).get(world_name) or {}).get("archetype")


def cluster_paths(
    entity_paths: dict[int, dict],
    weights: dict,
    group_by: Optional[list[str]] = None,
    world_name: Optional[str] = None,
) -> dict:
    """Cluster entities by exact event-type-set; report distinct-shape count and dominant share."""
    def _cluster(eids: list[int]) -> dict:
        shape_to_entities: dict[tuple, list[int]] = {}
        for eid in eids:
            type_seq = [et for (_t, et, _sev) in entity_paths[eid]["events"]]
            shape = tuple(sorted(set(type_seq)))
            shape_to_entities.setdefault(shape, []).append(eid)
        n = len(eids)
        dominant_shape, dominant_members = max(
            shape_to_entities.items(), key=lambda kv: len(kv[1]), default=((), [])
        )
        return {
            "entity_count": n,
            "distinct_shapes": len(shape_to_entities),
            "dominant_shape": list(dominant_shape),
            "dominant_shape_count": len(dominant_members),
            "dominant_shape_share": round(len(dominant_members) / n, 4) if n else 0.0,
        }

    result: dict = {"global": _cluster(list(entity_paths.keys()))}

    archetype = _load_world_archetype(world_name)
    context = _DIVERSITY_CONTEXT_BY_ARCHETYPE.get(archetype)
    if context:
        result["global"]["diversity_context"] = context

    if group_by:
        groups: dict = {}
        for dim in group_by:
            by_value: dict[str, list[int]] = {}
            for eid, ep in entity_paths.items():
                key = str(ep["metadata"].get(dim))
                by_value.setdefault(key, []).append(eid)
            groups[dim] = {value: _cluster(members) for value, members in by_value.items()}
        result["groups"] = groups

    return result


def run_metadata(ticks: int, weights: dict) -> dict:
    return {
        "ticks": ticks,
        "stall_detector_reachable": ticks >= weights["stall_detector_window_ticks"],
        # life_arc_incoherent requires Hero's Journey generation >= 2, not a fixed tick window --
        # not derivable from tick count alone. Reported null rather than guessed; none of
        # TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION's own real runs reached generation 2
        # either, consistent with this being genuinely rare, not resolved by that ticket.
        "life_arc_detector_reachable": None,
        # TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION: dominant_shape_share/distinct_shapes
        # are real but unreliable below this many ticks -- empirically found artificially
        # inflated at short tick-lengths (paths too short to differentiate), stabilizing by
        # ~1000 ticks on real data. Read clustering results with this flag, not at face value
        # alone, when it's False.
        "clustering_reliable": ticks >= weights["clustering_reliable_tick_threshold"],
    }


# ---------------------------------------------------------------------------
# Orchestration + CLI
# ---------------------------------------------------------------------------


def score_run(
    run_dir: str,
    world_state,
    ticks: int,
    weights: dict,
    group_by: Optional[list[str]] = None,
    world_name: Optional[str] = None,
) -> dict:
    entity_paths = extract_entity_paths(run_dir, world_state)
    entity_metrics = {
        eid: compute_entity_metrics(ep, weights, ticks) for eid, ep in entity_paths.items()
    }
    return {
        "run_metadata": run_metadata(ticks, weights),
        "entity_metrics": entity_metrics,
        "aggregation": aggregate(entity_metrics, group_by=group_by),
        "clustering": cluster_paths(entity_paths, weights, group_by=group_by, world_name=world_name),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Per-entity lifecycle scoring tool")
    parser.add_argument("--world", default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ticks", type=int, default=800)
    parser.add_argument("--obs-mode", default=None)
    parser.add_argument("--run-dir", default=None, help="Score an existing run instead of driving a new one")
    parser.add_argument("--group-by", default="role,faction,kind,region")
    parser.add_argument("--weights", default=None)
    args = parser.parse_args()

    weights = load_weights(args.weights)
    group_by = [g.strip() for g in args.group_by.split(",") if g.strip()] if args.group_by else None

    sys.path.insert(0, str(_TOOLS_DIR))
    from calibrate_simq import _load_world_state

    if args.run_dir:
        run_dir = args.run_dir
        health = None
        if not args.world:
            print(json.dumps({"error": "--world is required (for entity metadata) when using --run-dir"}))
            return 1
        world_state, _report = _load_world_state(args.world, args.seed)
    else:
        if not args.world:
            print(json.dumps({"error": "--world is required"}))
            return 1
        obs_mode = args.obs_mode or weights["default_obs_mode"]
        run_dir, health = _run_for_analysis(args.world, args.seed, args.ticks, obs_mode)
        world_state, _report = _load_world_state(args.world, args.seed)

    result = score_run(run_dir, world_state, args.ticks, weights, group_by=group_by, world_name=args.world)
    if health is not None:
        result["run_health"] = health

    # clean up a self-driven run's own data/runs/ directory -- never leave scratch run data
    # behind, matching this repo's own data/runs/ cleanup convention.
    if not args.run_dir and run_dir and os.path.isdir(run_dir) and run_dir.startswith("data/runs/"):
        import shutil
        shutil.rmtree(run_dir)

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
