"""Step-1 calibration probe (plan section 6). Read-only: no src/ edit, no behaviour change.

Per measured tick it records the measured costs (tick total, locomotion, final_integrity, combat_engagement buckets) and the
PRE-POLICY demand counts, read from AuthoritativeState before the tick runs. The dirty-set size inside refine is read by
wrapping AuthoritativeApplyPipeline.refine from this script, so pipeline.py is not touched.

Usage: python3 calibrate_step1.py OUT.json [sizes comma list] [per-config wall budget seconds]
"""
import json
import sys
import time

sys.path.insert(0, ".")
from src.config.profiles import HardwareClass, RuntimeProfile  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.engine.pipeline import AuthoritativeApplyPipeline  # noqa: E402
from src.perf.scenarios import (  # noqa: E402
    build_idle_state, build_movement_state, build_resource_state, build_strategic_state)
from src.platform.rng import DeterministicRNG  # noqa: E402

DIRTY_FIELDS = ("movement_entities", "combat_entities", "inventory_entities", "strategic_entities", "social_entities",
                "lifecycle_entities", "biological_entities", "attribute_entities", "identity_entities", "town_entities")
_captured = {}
_orig_refine = AuthoritativeApplyPipeline.refine


def _wrapped_refine(state, update, *a, **kw):
    out = _orig_refine(state, update, *a, **kw)
    ds = getattr(out, "dirty_set", None)
    _captured["dirty_total"] = sum(len(getattr(ds, f, ()) or ()) for f in DIRTY_FIELDS) if ds is not None else 0
    _captured["dirty_move"] = len(ds.movement_entities) if ds is not None else 0
    _captured["dirty_strat"] = len(ds.strategic_entities) if ds is not None else 0
    return out


AuthoritativeApplyPipeline.refine = staticmethod(_wrapped_refine)


def profile(workers):
    return RuntimeProfile(name="calib", hardware_class=HardwareClass.CLASS_B, max_ram_mb=4096, max_cpu_percent=90.0,
                          max_worker_count=workers, max_queue_depth=500, max_replay_buffer_kb=4096,
                          max_observability_budget_percent=10.0, max_tick_budget_ms=100000.0)


SC = {
    "idle": lambda n: build_idle_state(entity_count=n),
    "movement": lambda n: build_movement_state(entity_count=n),
    "resource": lambda n: build_resource_state(entity_count=n, node_count=max(5, n // 10)),
    "strategic": lambda n: build_strategic_state(entity_count=n),
}


def neighbour_pairs(ents, radius=10.0):
    """Ordered pairs (a, b), a != b, of active entities within `radius` (Euclidean), via a one-pass tile hash. Deterministic, state only."""
    cell = {}
    for e in ents:
        x, y = e.navigation.position
        cell.setdefault((int(x // radius), int(y // radius)), []).append((x, y))
    r2 = radius * radius
    total = 0
    for (cx, cy), pts in cell.items():
        near = [q for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in cell.get((cx + dx, cy + dy), ())]
        for (x, y) in pts:
            total += sum(1 for (u, v) in near if (u - x) ** 2 + (v - y) ** 2 <= r2) - 1
    return total


def demand(state):
    ents = [e for e in state.entities.values() if e.lifecycle.active]
    t0 = time.perf_counter_ns()
    pairs = neighbour_pairs(ents)
    pair_ms = (time.perf_counter_ns() - t0) / 1e6
    return dict(neighbour_pairs=pairs, neighbour_pairs_ms=pair_ms,
        entities_active=len(ents),
        movers=sum(1 for e in ents if e.navigation.target is not None),
        leads=sum(len(getattr(e.strategic, "leads", None) or []) for e in ents) if hasattr(ents[0], "strategic") else 0,
    )


def main():
    out_path = sys.argv[1]
    sizes = [int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "100,250,500").split(",")]
    wall = float(sys.argv[3]) if len(sys.argv) > 3 else 90.0
    rows = []
    for ex, workers in (("sequential", 0), ("thread", 2)):
        for name, mk in SC.items():
            for n in sizes:
                k = Kernel(profile(workers), mk(n), DeterministicRNG(7), flags={"no_frame_pacing": True, "no_replay": True})
                t_cfg = time.monotonic()
                try:
                    for t in range(14):
                        d = demand(k._state)
                        _captured.clear()
                        k.tick_once()
                        if t < 3:
                            continue
                        pc = k._phase_costs
                        rows.append(dict(sc=name, n=n, ex=ex, tick=t, tick_ms=k._final_compute_ms,
                                         loco_ms=pc.get("locomotion", 0.0), integ_ms=pc.get("final_integrity", 0.0),
                                         combat_ms=pc.get("combat_engagement", 0.0), coop_ms=pc.get("cooperation", 0.0),
                                         results=len(k._final_results), move_cand=k._metrics.get("movement_candidates", 0),
                                         mode=str(k._current_policy.mode), **d, **_captured))
                        if time.monotonic() - t_cfg > wall:
                            break
                finally:
                    k.shutdown()
                print(f"{ex} {name} {n}: {sum(1 for r in rows if (r['ex'], r['sc'], r['n']) == (ex, name, n))} rows, "
                      f"{time.monotonic() - t_cfg:.0f}s", flush=True)
                json.dump(rows, open(out_path, "w"))


main()
