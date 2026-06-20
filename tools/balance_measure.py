#!/usr/bin/env python3
"""
Balance measurement script — Epic 1.2A (TCK-20260619-E12A-BALANCE-MEASURE)

Runs urban_political world for N ticks (default 1000, seed 42) and
collects the D04 balance metrics that were previously blocked by hunger dominance.

Usage:
    python3 tools/balance_measure.py
    python3 tools/balance_measure.py --ticks 200 --seed 42

Outputs a JSON report to stdout and a human summary to stderr.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Blocker counter (patched into AdventureRouteScorer) ──────────────────────

_blocker_stats: Dict[str, int] = {"routes_total": 0, "routes_with_blockers": 0}
_blocker_samples: List[str] = []
_urgency_samples: List[float] = []
_family_counts: Dict[str, int] = {}
_SAMPLE_CAP = 20


def _patched_score(original_score):
    """Wraps AdventureRouteScorer.score() to count blocker and urgency stats."""
    def patched(entity, route):
        result = original_score(entity, route)
        _blocker_stats["routes_total"] += 1
        if result.blockers:
            _blocker_stats["routes_with_blockers"] += 1
            for b in result.blockers:
                if len(_blocker_samples) < _SAMPLE_CAP and b not in _blocker_samples:
                    _blocker_samples.append(b)
        # Track urgency and route family for calibration insight
        if len(_urgency_samples) < 200:
            _urgency_samples.append(route.urgency if hasattr(route, "urgency") else 0.0)
        fam = str(route.family) if hasattr(route, "family") else "unknown"
        _family_counts[fam] = _family_counts.get(fam, 0) + 1
        return result
    return patched


def _install_blocker_patch():
    from src.domains.adventure import scoring as scoring_mod
    # score is a staticmethod — access via the class dict
    original = scoring_mod.AdventureRouteScorer.__dict__["score"].__func__ \
        if hasattr(scoring_mod.AdventureRouteScorer.__dict__["score"], "__func__") \
        else scoring_mod.AdventureRouteScorer.__dict__["score"]
    scoring_mod.AdventureRouteScorer.score = staticmethod(_patched_score(original))


# ── Economic action counter (reads transaction_trace per tick) ────────────────

def _count_economic_actions(transaction_trace: List[str]) -> Dict[str, int]:
    """Count RESOURCE_NODE accepts (harvesting) and BUILDING accepts (crafting/trade)."""
    counts: Dict[str, int] = {"RESOURCE_NODE_accept": 0, "BUILDING_accept": 0, "other_accept": 0}
    for entry in transaction_trace:
        if "TRANSACTION ACCEPT:" not in entry:
            continue
        if "RESOURCE_NODE" in entry:
            counts["RESOURCE_NODE_accept"] += 1
        elif "BUILDING" in entry:
            counts["BUILDING_accept"] += 1
        else:
            counts["other_accept"] += 1
    return counts


# ── Main measurement run ──────────────────────────────────────────────────────

def run_measurement(ticks: int = 1000, seed: int = 42, world_id: str = "urban_political") -> Dict[str, Any]:
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler
    from src.engine.kernel import Kernel
    from src.engine.metrics import MetricsService
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.platform.rng import DeterministicRNG

    print(f"Loading world: {world_id} (seed={seed}, ticks={ticks})", file=sys.stderr)

    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    state, compile_report = WorldCompiler.compile(spec, seed=seed)
    rng = DeterministicRNG(seed)

    print(f"Compiled: {compile_report['entity_count']} entities, hash={compile_report['state_hash']}", file=sys.stderr)

    profile = RuntimeProfile(
        name="balance-measure",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=2048,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=2000,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=500.0,
    )

    # Enable adventure routing for measurement — it defaults to OFF in feature_flags.
    # This is the pipeline that uses blocker_penalty; without it, score() is never called.
    from dataclasses import replace
    enabled_flags = dict(state.feature_flags)
    enabled_flags["ENABLE_ADVENTURE_ROUTING"] = 1.0
    state = replace(state, feature_flags=enabled_flags)

    _install_blocker_patch()
    kernel = Kernel(profile=profile, state=state, rng=rng)

    # Per-tick tracking
    entity_count_start = len([e for e in kernel.state.entities.values() if e.combat.alive])
    gold_start = sum(e.inventory.gold for e in kernel.state.entities.values())
    initial_hp = {eid: e.combat.hp for eid, e in kernel.state.entities.items()}

    # Aggregate counters
    harvest_total = 0
    building_total = 0
    quest_completed_total = 0
    quest_completed_prev = 0

    # Per-100-tick window samples
    windows: List[Dict[str, Any]] = []
    window_harvest = 0
    window_building = 0
    window_quest_delta = 0

    start_time = time.time()

    for tick_idx in range(ticks):
        kernel.tick_once()
        st = kernel.state
        metrics = MetricsService.extract_metrics(st)

        # Count economic actions from transaction_trace
        eco = _count_economic_actions(list(st.transaction_trace))
        harvest_total += eco["RESOURCE_NODE_accept"]
        building_total += eco["BUILDING_accept"]
        window_harvest += eco["RESOURCE_NODE_accept"]
        window_building += eco["BUILDING_accept"]

        # Quest completions (delta from last tick)
        quest_done_now = metrics.quest_status_counts.get("COMPLETED", 0)
        delta_quests = max(0, quest_done_now - quest_completed_prev)
        quest_completed_total += delta_quests
        window_quest_delta += delta_quests
        quest_completed_prev = quest_done_now

        # Sample per window
        if (tick_idx + 1) % 100 == 0:
            alive_now = metrics.alive_entities
            gold_now = metrics.total_gold
            windows.append({
                "window_end_tick": tick_idx + 1,
                "alive_entities": alive_now,
                "total_gold": round(gold_now, 2),
                "harvest_actions_in_window": window_harvest,
                "building_actions_in_window": window_building,
                "quest_completions_in_window": window_quest_delta,
            })
            print(
                f"  tick={tick_idx+1:4d} | alive={alive_now:3d} | gold={gold_now:7.1f} "
                f"| harvest={window_harvest:3d} | building={window_building:3d} "
                f"| quests_done={window_quest_delta}",
                file=sys.stderr
            )
            window_harvest = 0
            window_building = 0
            window_quest_delta = 0

    elapsed = time.time() - start_time
    print(f"\nRun complete in {elapsed:.1f}s", file=sys.stderr)

    # Final state metrics
    final_state = kernel.state
    final_metrics = MetricsService.extract_metrics(final_state)
    alive_final = final_metrics.alive_entities
    gold_final = final_metrics.total_gold

    # Attrition: entities with <50% original HP
    attrition_count = sum(
        1 for eid, e in final_state.entities.items()
        if e.combat.alive and e.combat.hp < initial_hp.get(eid, e.combat.max_hp) * 0.5
    )
    dead_count = sum(1 for e in final_state.entities.values() if not e.combat.alive)
    attrition_rate = (dead_count + attrition_count) / max(1, entity_count_start)

    # Blocker stats
    routes_total = _blocker_stats["routes_total"]
    routes_blocked = _blocker_stats["routes_with_blockers"]
    blocker_freq = routes_blocked / max(1, routes_total)

    # Derived rates (per entity per 100 ticks)
    entity_100t_denom = max(1, entity_count_start) * (ticks / 100)
    harvest_rate = harvest_total / entity_100t_denom
    building_rate = building_total / entity_100t_denom
    quest_rate = quest_completed_total / entity_100t_denom
    gold_per_entity = (gold_final - gold_start) / max(1, entity_count_start)

    report = {
        "run": {
            "world_id": world_id,
            "seed": seed,
            "ticks": ticks,
            "elapsed_seconds": round(elapsed, 1),
            "entity_count_start": entity_count_start,
            "entity_count_final": len(final_state.entities),
            "alive_final": alive_final,
        },
        "metrics": {
            "gold_total_start": round(gold_start, 2),
            "gold_total_final": round(gold_final, 2),
            "gold_per_entity_net": round(gold_per_entity, 3),
            "harvest_total_actions": harvest_total,
            "harvest_rate_per_entity_per_100t": round(harvest_rate, 3),
            "building_total_actions": building_total,
            "building_rate_per_entity_per_100t": round(building_rate, 3),
            "quest_completions_total": quest_completed_total,
            "quest_completion_rate_per_entity_per_100t": round(quest_rate, 3),
            "combat_attrition_rate_at_final_tick": round(attrition_rate, 3),
            "dead_count_final": dead_count,
        },
        "blocker_stats": {
            "routes_total_scored": routes_total,
            "routes_with_blockers": routes_blocked,
            "blocker_frequency": round(blocker_freq, 4),
            "blocker_sample_strings": _blocker_samples[:_SAMPLE_CAP],
            "urgency_min": round(min(_urgency_samples), 4) if _urgency_samples else None,
            "urgency_max": round(max(_urgency_samples), 4) if _urgency_samples else None,
            "urgency_avg": round(sum(_urgency_samples) / len(_urgency_samples), 4) if _urgency_samples else None,
            "route_family_distribution": _family_counts,
        },
        "quest_status_final": final_metrics.quest_status_counts,
        "windows": windows,
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Balance measurement run")
    parser.add_argument("--ticks", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--world", default="urban_political")
    args = parser.parse_args()

    report = run_measurement(ticks=args.ticks, seed=args.seed, world_id=args.world)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
