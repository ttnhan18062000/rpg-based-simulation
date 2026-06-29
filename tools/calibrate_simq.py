"""Simulation Quality Scoring Calibration Script.

Usage:
    python3 tools/calibrate_simq.py --ticks 100 --seed 42 --name sandbox_world
    python3 tools/calibrate_simq.py --ticks 500 --seed 137 --name urban_political

Runs the engine for N ticks, then replays simulation_events.jsonl through QualityHub.
Writes quality_report.json to data/calibration/{name}_seed{seed}_{ticks}t/.

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


def _load_weights():
    from src.simulation_quality.weights import ScoringWeights
    return ScoringWeights.load(
        weights_path="config/simulation_quality/scoring_weights.yaml",
        grade_path="config/simulation_quality/grade_thresholds.yaml",
        detection_path="config/simulation_quality/detection_params.yaml",
        profile="default",
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


def _run_engine(seed: int, ticks: int, entity_count: int = 10) -> tuple[str, float]:
    """Drive the kernel tick_once() N times; return (run_dir, elapsed_sec)."""
    from src.engine.kernel import Kernel
    from src.core.state import AuthoritativeState
    from src.platform.rng import DeterministicRNG
    from src.systems.world_systems.generator import EntityGenerator
    from src.config.profiles import PROD_SMALL

    rng = DeterministicRNG(seed)
    gen = EntityGenerator(seed)

    entities = {}
    hero = gen.spawn_hero((64.0, 64.0))
    entities[hero.id] = hero
    for i in range(entity_count - 1):
        monster = gen.spawn_goblin((60.0 + i, 60.0 + i))
        entities[monster.id] = monster

    state = AuthoritativeState(tick=0, seed=seed, entities=entities)
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
    args = parser.parse_args()

    run_tag = f"{args.name}_seed{args.seed}_{args.ticks}t"
    cal_dir = os.path.join("data", "calibration", run_tag)
    os.makedirs(cal_dir, exist_ok=True)

    print(f"[calibrate_simq] Running engine: {run_tag} entities={args.entities}")
    engine_run_dir, elapsed, run_id = _run_engine(args.seed, args.ticks, args.entities)
    print(f"[calibrate_simq] Engine done in {elapsed:.2f}s. JSONL at: {engine_run_dir}")

    weights = _load_weights()
    hub, persistence = _build_hub(weights, cal_dir, run_id or run_tag)

    event_count = _replay_jsonl_through_hub(engine_run_dir, hub)
    print(f"[calibrate_simq] Replayed {event_count} events through QualityHub.")

    report = hub.get_quality_report()
    persistence.write_report(report)
    persistence.shutdown()

    print(f"\n=== Quality Report: {run_tag} ===")
    print(f"  ticks={args.ticks} events={event_count} elapsed={elapsed:.2f}s")
    print(f"  overall_grade={report.overall_grade} overall_score={report.overall_score:.4f}")
    print("\n  Pillar breakdown:")
    for pillar_id, snap in sorted(report.pillars.items()):
        print(f"    {pillar_id:20s}  grade={snap.grade}  norm={snap.normalized_score:+.4f}  events={snap.event_count}")
    print(f"\n  Report written: {os.path.join(cal_dir, 'quality_report.json')}")
    return report


if __name__ == "__main__":
    main()
