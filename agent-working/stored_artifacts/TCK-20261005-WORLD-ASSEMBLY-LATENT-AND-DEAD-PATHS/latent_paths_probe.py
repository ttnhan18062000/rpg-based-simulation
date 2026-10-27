"""Per-world counts for the latent checks of TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS (read-only).

Run from the repo root: python3 <this file> > latent_paths_results.jsonl
Checks per composition (data/worlds/*/world.yaml):
  duplicate_module_refs   module ids listed more than once in module_refs
  dangling_requires       an enabled module's `requires` id that is not an enabled module of the composition
                          (split: in the repository but not composed / absent from the repository)
  authored_order          refs whose YAML sets `order` (explicit) / sets a non-zero value
  order_disagrees         the authored-order sequence differs from the order the topological sort produces
  enabled_false           refs with enabled: false
"""
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, ".")
from src.worldassembly.resolve_io import load_composition_spec, load_content_repositories
from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
from src.worldmodules.utils import topological_sort_modules

_cat, repo = load_content_repositories()
rows = []
for yml in sorted(Path("data/worlds").glob("*/world.yaml")):
    raw = yaml.safe_load(yml.read_text(encoding="utf-8"))
    comp = load_composition_spec(yml)
    raw_refs = raw.get("module_refs", [])
    ids = [r.module_id for r in comp.module_refs]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    enabled = [r for r in comp.module_refs if r.enabled]
    enabled.sort(key=lambda r: r.order)
    graph = {}
    for r in enabled:
        graph[r.module_id] = WorldModuleAuthoringNormalizer.normalize(repo.get_module(r.module_id))
    dangling_in_repo, dangling_absent = [], []
    for mid, spec in graph.items():
        for req in spec.requires:
            if req not in graph:
                (dangling_in_repo if repo.get_module(req) else dangling_absent).append(f"{mid}->{req}")
    sorted_ids = topological_sort_modules(graph)
    rows.append({
        "world": comp.world_id,
        "module_refs": len(ids),
        "duplicate_module_refs": dup,
        "dangling_requires_in_repo_not_composed": dangling_in_repo,
        "dangling_requires_absent_from_repo": dangling_absent,
        "refs_with_explicit_order": sum(1 for r in raw_refs if "order" in r),
        "refs_with_nonzero_order": sum(1 for r in comp.module_refs if r.order != 0),
        "order_disagrees_with_executed_sequence": [r.module_id for r in enabled] != sorted_ids,
        "authored_sequence": [r.module_id for r in enabled],
        "executed_sequence": sorted_ids,
        "enabled_false": sum(1 for r in comp.module_refs if not r.enabled),
    })
for row in rows:
    print(json.dumps(row))
