import sys, json, statistics, math
sys.path.insert(0, ".")
from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.perf.scenarios import build_idle_state, build_movement_state, build_resource_state, build_strategic_state

def profile():
    return RuntimeProfile(name="calib", hardware_class=HardwareClass.CLASS_B, max_ram_mb=4096, max_cpu_percent=90.0,
        max_worker_count=0, max_queue_depth=500, max_replay_buffer_kb=4096, max_observability_budget_percent=10.0,
        max_tick_budget_ms=100000.0)

SC = {
 "idle": lambda n: build_idle_state(entity_count=n),
 "movement": lambda n: build_movement_state(entity_count=n),
 "resource": lambda n: build_resource_state(entity_count=n, node_count=max(5, n // 10)),
 "strategic": lambda n: build_strategic_state(entity_count=n),
}
rows = []
for name, mk in SC.items():
    for n in (60, 150, 300):
        k = Kernel(profile(), mk(n), DeterministicRNG(7), flags={"no_frame_pacing": True, "no_replay": True})
        try:
            for t in range(18):
                k.tick_once()
                if t < 3:  # warm-up
                    continue
                pc = k._phase_costs; m = k._metrics
                rows.append(dict(sc=name, n=n,
                    tick_ms=k._final_compute_ms, loco_ms=pc.get("locomotion", 0.0), integ_ms=pc.get("final_integrity", 0.0),
                    results=len(k._final_results), items=len(k._current_work_items), entities=len(k._state.entities),
                    phase_runs=m.get("phase_runs", 0), raw_up=m.get("raw_entity_updates", 0), comp_up=m.get("compacted_entity_updates", 0),
                    move_cand=m.get("movement_candidates", 0),
                    dirty_total=sum(len(getattr(ds, f)) for ds in [k._current_update.dirty_set] if ds is not None for f in ("movement_entities","combat_entities","inventory_entities","strategic_entities","social_entities","lifecycle_entities","biological_entities","attribute_entities","identity_entities")) if k._current_update is not None else 0,
                    dirty_strat=len(k._current_update.dirty_set.strategic_entities) if k._current_update is not None and k._current_update.dirty_set is not None else 0,
                    leads=sum(len(getattr(e.strategic, "leads", []) or []) for e in k._state.entities.values()) if hasattr(next(iter(k._state.entities.values())), "strategic") else 0,
                    ent_updates=len(k._current_update.entity_updates) if k._current_update is not None else 0))
        finally:
            k.shutdown()
json.dump(rows, open("calibration_rows.json", "w"))
def corr(xs, ys):
    if len(set(xs)) < 2 or len(set(ys)) < 2: return float("nan")
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sx = math.sqrt(sum((x-mx)**2 for x in xs)); sy = math.sqrt(sum((y-my)**2 for y in ys))
    return sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / (sx*sy)
print("rows", len(rows))
for target in ("tick_ms", "loco_ms", "integ_ms"):
    print("==", target)
    for c in ("results", "entities", "raw_up", "comp_up", "move_cand", "dirty_total", "dirty_strat", "leads", "ent_updates"):
        xs = [r[c] for r in rows]; ys = [r[target] for r in rows]
        print(f"  {c:11s} r={corr(xs, ys):.3f}  range[{min(xs)}..{max(xs)}]")
print("per-scenario tick_ms vs results r:")
for name in SC:
    rr = [r for r in rows if r["sc"] == name]
    print(f"  {name:10s} r={corr([r['results'] for r in rr],[r['tick_ms'] for r in rr]):.3f}  r(entities)={corr([r['entities'] for r in rr],[r['tick_ms'] for r in rr]):.3f}  ms/result={statistics.fmean([r['tick_ms']/max(1,r['results']) for r in rr]):.3f}")
