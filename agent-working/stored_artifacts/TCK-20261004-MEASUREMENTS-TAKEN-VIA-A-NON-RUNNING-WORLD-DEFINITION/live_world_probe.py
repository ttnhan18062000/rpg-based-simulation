"""Re-take the three closed tickets' compile-time measurements through the production path (read-only).

python3 live_world_probe.py > live_world_probe_results.jsonl   (repo root)
Loader: WorldRepository("data/worlds").load_world_with_context(world) -> WorldCompiler.compile(spec, seed=42, context=ctx),
i.e. what production loads (the `resolved/` redirect). Per world: modules composed, regions, regions with non-empty
population_cohorts, the largest cohort bracket, and the CampState entries.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

repo = WorldRepository("data/worlds")
for world in sorted(p.name for p in Path("data/worlds").iterdir() if p.is_dir()):
    spec, ctx = repo.load_world_with_context(world)
    state, _ = WorldCompiler.compile(spec, seed=42, context=ctx)
    regions = state.regions.values() if isinstance(state.regions, dict) else state.regions
    cohorts = {getattr(r, "id", i): dict(r.population_cohorts or {}) for i, r in enumerate(regions)}
    brackets = [c.count for per in cohorts.values() for c in per.values()]
    print(json.dumps({
        "world": world,
        "regions": len(spec.regions),
        "regions_with_nonempty_cohorts": sum(1 for v in cohorts.values() if v),
        "largest_bracket": max(brackets) if brackets else 0,
        "cohort_brackets_by_region": {k: {b: c.count for b, c in v.items()} for k, v in cohorts.items() if v},
        "camps": sorted(state.camps),
    }, default=str))
