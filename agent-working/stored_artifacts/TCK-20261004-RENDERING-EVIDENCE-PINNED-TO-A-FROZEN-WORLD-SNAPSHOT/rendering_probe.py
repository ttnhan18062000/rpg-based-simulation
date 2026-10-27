"""Re-measure the six rendering-evidence numbers on the frozen fixture and the live corpus (read-only).

python3 rendering_probe.py > rendering_probe_results.jsonl   (from the repo root)
Per world (frozen dungeon_crawl fixture + every data/worlds/* world, seed 42, tick 0): walkable count, connectivity components,
density CV, and the shape components (terrain type, size, fill ratio) so that "which live world carries a forest and a cave"
(UQ-2) is read from data, plus the terrain-histogram TVD of the live and frozen dungeon_crawl against sandbox_world.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from src.rendering.connectivity import analyze_connectivity
from src.rendering.density import compute_density_cv, compute_terrain_histogram
from src.rendering.shape import connected_components
from src.rendering.variants import normalize_histogram, total_variation_distance
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from tests.unit.rendering.frozen_dungeon_crawl import load_frozen_dungeon_crawl

repo = WorldRepository("data/worlds")


def measure(label, spec):
    state, _ = WorldCompiler.compile(spec, seed=42)
    conn = analyze_connectivity(state.terrain, state.blocked_tiles)
    comps = connected_components(state.terrain)
    shapes = sorted(((c.terrain_type, c.size, round(c.fill_ratio, 3)) for c in comps), key=lambda t: (t[0], -t[1]))
    return state, {
        "world": label,
        "entities": len(state.entities),
        "walkable": conn.walkable_count,
        "components": conn.component_count,
        "density_cv": round(compute_density_cv(state.entities).cv, 3),
        "forest_components": [s[1] for s in shapes if s[0] == "forest"],
        "cave_components": [s[1] for s in shapes if s[0] == "cave"],
        "shape_components": [list(s) for s in shapes],
    }, normalize_histogram(compute_terrain_histogram(state.terrain))


rows, hists = [], {}
for label, spec in [("frozen:dungeon_crawl", load_frozen_dungeon_crawl())] + [(w, repo.load_world(w)) for w in sorted(p.name for p in Path("data/worlds").iterdir() if p.is_dir())]:
    _s, row, hist = measure(label, spec)
    rows.append(row)
    hists[label] = hist
for row in rows:
    if row["world"] in ("frozen:dungeon_crawl", "dungeon_crawl"):
        row["tvd_vs_sandbox_world"] = round(total_variation_distance(hists["sandbox_world"], hists[row["world"]]), 4)
    print(json.dumps(row))
