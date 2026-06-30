"""Simulation Quality Scoring Calibration Script.

Usage:
    python3 tools/calibrate_simq.py --ticks 100 --seed 42 --name sandbox_world
    python3 tools/calibrate_simq.py --ticks 500 --seed 137 --name urban_political
    python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name dungeon_crawl --profile dungeon_crawl

Runs the engine for N ticks, then replays simulation_events.jsonl through QualityHub.
Writes quality_report.json to data/calibration/{name}_seed{seed}_{ticks}t/.

When --name matches a compiled world under data/worlds/{name}/resolved/world.resolved.yaml,
that WorldSpec is loaded and compiled via WorldCompiler.compile() before the simulation run.
If no resolved spec exists, a generic hero + goblins scenario is used.

After running all 8 canonical scenarios, analyze normalized_score distributions and
update config/simulation_quality/grade_thresholds.yaml accordingly.
"""
from __future__ import annotations
import argparse
import json
import logging
import os
import sys
import time

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("calibrate_simq")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _resolve_profile(name: str) -> str:
    """Return the profile name to use for the given world name.

    Defaults to ``name`` if a matching profile file exists under
    ``config/simulation_quality/profiles/``, otherwise ``'default'``.
    """
    profile_path = os.path.join(
        "config", "simulation_quality", "profiles", f"{name}.yaml"
    )
    return name if os.path.exists(profile_path) else "default"


def _load_weights(profile: str = "default"):
    from src.simulation_quality.weights import ScoringWeights
    return ScoringWeights.load(
        weights_path="config/simulation_quality/scoring_weights.yaml",
        grade_path="config/simulation_quality/grade_thresholds.yaml",
        detection_path="config/simulation_quality/detection_params.yaml",
        profile=profile,
    )


def _build_hub(weights, run_dir: str, run_id: str):
    from src.simulation_quality.quality_hub import QualityHub
    from src.simulation_quality.persistence import QualityPersistence
    from src.simulation_quality.scorers.agency import AgencyScorer
    from src.simulation_quality.scorers.combat import CombatScorer
    from src.simulation_quality.scorers.cognition import CognitionScorer
    from src.simulation_quality.scorers.economy import EconomyScorer
    from src.simulation_quality.scorers.faction import FactionScorer
    from src.simulation_quality.scorers.information import InformationScorer
    from src.simulation_quality.scorers.narrative import NarrativeScorer
    from src.simulation_quality.scorers.progression import ProgressionScorer
    from src.simulation_quality.scorers.social import SocialScorer
    from src.simulation_quality.scorers.world_dynamics import WorldDynamicsScorer

    scorers = [
        AgencyScorer(weights),
        CombatScorer(weights),
        CognitionScorer(weights),
        EconomyScorer(weights),
        FactionScorer(weights),
        InformationScorer(weights),
        NarrativeScorer(weights),
        ProgressionScorer(weights),
        SocialScorer(weights),
        WorldDynamicsScorer(weights),
    ]
    persistence = QualityPersistence(run_dir)
    hub = QualityHub(scorers, weights, persistence, run_id=run_id)
    return hub, persistence


def _load_world_state(name: str, seed: int):
    """Load and compile a WorldSpec for the given world name.

    Looks for ``data/worlds/{name}/resolved/world.resolved.yaml``.
    Returns ``(AuthoritativeState, compile_report)`` on success, or
    ``(None, None)`` if the world is not found or compilation fails.
    """
    resolved_path = os.path.join("data", "worlds", name, "resolved", "world.resolved.yaml")
    if not os.path.exists(resolved_path):
        logger.info("No resolved world spec found for '%s' at %s — using generic simulation", name, resolved_path)
        return None, None

    try:
        import yaml
        from src.worldbuilding.schema import WorldSpec
        from src.worldbuilding.compiler import WorldCompiler

        with open(resolved_path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        spec = WorldSpec(**raw)
        state, report = WorldCompiler.compile(spec, seed)
        logger.info(
            "Loaded world '%s': %d entities, %d regions, %d resource nodes",
            name,
            report["entity_count"],
            report["region_count"],
            report["resource_node_count"],
        )
        return state, report
    except Exception as exc:
        logger.warning("Failed to load/compile world '%s': %s — falling back to generic simulation", name, exc)
        return None, None


def _run_engine(name: str, seed: int, ticks: int, entity_count: int = 10) -> tuple[str, float]:
    """Drive the kernel tick_once() N times; return (run_dir, elapsed_sec, run_id).

    If a compiled world spec exists for ``name``, loads it via WorldCompiler and
    injects the resulting AuthoritativeState into the Kernel.  Falls back to a
    generic hero + goblins scenario when no world is found.
    """
    from src.engine.kernel import Kernel
    from src.core.state import AuthoritativeState
    from src.platform.rng import DeterministicRNG
    from src.systems.world_systems.generator import EntityGenerator
    from src.config.profiles import PROD_SMALL

    rng = DeterministicRNG(seed)

    # Attempt to load a compiled world spec
    state, compile_report = _load_world_state(name, seed)

    if state is None:
        # Generic fallback: hero + staggered goblins
        # Goblins are placed in a 5-wide grid starting at (20, 20), well clear of
        # the hero at (64, 64) — avoids LAW-OCCUPANCY-COLLISION.
        gen = EntityGenerator(seed)
        entities = {}
        hero = gen.spawn_hero((64.0, 64.0))
        entities[hero.id] = hero
        for i in range(entity_count - 1):
            gx = 20.0 + (i % 5) * 8.0
            gy = 20.0 + (i // 5) * 8.0
            monster = gen.spawn_goblin((gx, gy))
            entities[monster.id] = monster
        state = AuthoritativeState(tick=0, seed=seed, entities=entities)

    # Inject feature-flag overrides from environment variables.
    # Recognized env vars: ENABLE_ADVENTURE_ROUTING, ENABLE_COMBAT_ENGAGEMENT,
    # ENABLE_SOCIAL_COOPERATION, ENABLE_WORLD_EMERGENCE, ENABLE_BELIEF_ASSIMILATION,
    # ENABLE_PROGRESSION_EVOLUTION, ENABLE_LIFE_ARC_CAMPAIGNS, etc.
    # Set to "ON", "SHADOW", "STRICT", or any truthy string to enable.
    # Example: ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py ...
    from src.domains.optimization.feature_flags import FeatureMode
    _KNOWN_FLAGS = [
        "ENABLE_WORLD_CAPABILITY_LAYER", "ENABLE_SELF_MODEL_COGNITION",
        "ENABLE_ADVENTURE_ROUTING", "ENABLE_COMBAT_ENGAGEMENT",
        "ENABLE_BELIEF_ASSIMILATION", "ENABLE_PROGRESSION_EVOLUTION",
        "ENABLE_SOCIAL_COOPERATION", "ENABLE_WORLD_EMERGENCE",
        "ENABLE_LIFE_ARC_CAMPAIGNS", "ENABLE_ENHANCED_TRACE_EVENTS",
    ]
    env_flag_overrides = {}
    for flag in _KNOWN_FLAGS:
        env_val = os.environ.get(flag, "").strip().upper()
        if env_val in ("ON", "TRUE", "1", "YES", "STRICT"):
            mode = FeatureMode.STRICT if env_val == "STRICT" else FeatureMode.ON
            env_flag_overrides[flag] = mode
            logger.info("Feature flag override from env: %s=%s", flag, mode)
        elif env_val == "SHADOW":
            env_flag_overrides[flag] = FeatureMode.SHADOW
            logger.info("Feature flag override from env: %s=SHADOW", flag)
    if env_flag_overrides:
        existing = dict(getattr(state, "feature_flags", None) or {})
        existing.update(env_flag_overrides)
        from dataclasses import replace as dc_replace
        state = dc_replace(state, feature_flags=existing)

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng)

    run_id = getattr(kernel, "_run_id", None)
    start = time.perf_counter()
    for _ in range(ticks):
        kernel.tick_once()
    elapsed = time.perf_counter() - start

    # Shutdown so drain worker flushes remaining JSONL events
    try:
        kernel.shutdown()
    except Exception:
        pass
    time.sleep(0.3)

    if run_id and os.path.isdir(os.path.join("data", "runs", run_id)):
        run_dir = os.path.join("data", "runs", run_id)
    else:
        import glob
        dirs = sorted(glob.glob("data/runs/run_*"), key=os.path.getmtime, reverse=True)
        run_dir = dirs[0] if dirs else ""

    return run_dir, elapsed, run_id or ""


def _replay_jsonl_through_hub(run_dir: str, hub) -> int:
    """Read simulation_events.jsonl from run_dir and replay each event through hub."""
    from src.observability.events import ObservabilityEventEnvelope

    jsonl_path = os.path.join(run_dir, "simulation_events.jsonl")
    if not os.path.exists(jsonl_path):
        logger.warning("No simulation_events.jsonl found in %s", run_dir)
        return 0

    event_count = 0
    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Remove fields not in ObservabilityEventEnvelope
                data.pop("related_entity_ids", None)
                env = ObservabilityEventEnvelope(**data)
                hub.on_envelope(env)
                event_count += 1
            except Exception as exc:
                logger.debug("Skipped JSONL event: %s", exc)
    return event_count


def main():
    parser = argparse.ArgumentParser(description="SimQ calibration runner")
    parser.add_argument("--ticks", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--name", type=str, default="generic")
    parser.add_argument("--entities", type=int, default=10)
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help=(
            "Quality scoring profile name (maps to "
            "config/simulation_quality/profiles/{profile}.yaml). "
            "Defaults to --name if a matching profile exists, else 'default'."
        ),
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Override the calibration output directory (default: data/calibration/{name}_seed{seed}_{ticks}t).",
    )
    args = parser.parse_args()

    # Resolve profile: explicit > name-based > default
    if args.profile is not None:
        profile = args.profile
    else:
        profile = _resolve_profile(args.name)

    run_tag = f"{args.name}_seed{args.seed}_{args.ticks}t"
    cal_dir = args.output if args.output else os.path.join("data", "calibration", run_tag)
    os.makedirs(cal_dir, exist_ok=True)

    print(f"[calibrate_simq] Running engine: {run_tag} entities={args.entities} profile={profile}")
    engine_run_dir, elapsed, run_id = _run_engine(args.name, args.seed, args.ticks, args.entities)
    print(f"[calibrate_simq] Engine done in {elapsed:.2f}s. JSONL at: {engine_run_dir}")

    weights = _load_weights(profile)
    hub, persistence = _build_hub(weights, cal_dir, run_id or run_tag)

    event_count = _replay_jsonl_through_hub(engine_run_dir, hub)
    print(f"[calibrate_simq] Replayed {event_count} events through QualityHub.")

    report = hub.get_quality_report()
    persistence.write_report(report)
    persistence.shutdown()

    print(f"\n=== Quality Report: {run_tag} ===")
    print(f"  ticks={args.ticks} events={event_count} elapsed={elapsed:.2f}s profile={profile}")
    print(f"  overall_grade={report.overall_grade} overall_score={report.overall_score:.4f}")
    print("\n  Pillar breakdown:")
    for pillar_id, snap in sorted(report.pillars.items()):
        print(f"    {pillar_id:20s}  grade={snap.grade}  norm={snap.normalized_score:+.4f}  events={snap.event_count}")
    print(f"\n  Report written: {os.path.join(cal_dir, 'quality_report.json')}")
    return report


if __name__ == "__main__":
    main()
