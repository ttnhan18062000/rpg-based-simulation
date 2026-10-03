---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE
artifact_type: plan
tags: [simulation-quality, world, corpus]
---

# Plan — TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE

## Steps

1. `tools/generate_corpus_registry.py`: add `compute_density(world_name, scale) -> dict` — reads
   the world's own `resolved/world.resolved.yaml` topology, computes the 6 metrics from
   investigation.md, and folds the result into `build_worlds_section()`'s per-world entry as a new
   `density` key (sibling to the existing `scale`/`tier`/`run_keys` keys — additive, no
   restructure, matching `TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW`'s own established
   backward-compat discipline).
2. Regenerate `config/simulation_quality/corpus_registry.yaml` via the tool (not hand-edited).
3. `tests/tools/test_corpus_registry.py`: the 4 new tests from test_plan.md (test 5 extends an
   existing test).
4. `docs/world/density_metrics.md` (new): formulas, derivations, the corpus-wide sanity-check
   numbers, cross-references to `spawn.py`'s runtime formula and `HighEntityDensityWarningRule`'s
   threshold, forward reference to `TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY`.
5. `docs/guides/world_density.md` (new): practical usage — how to compute density for a world
   you're authoring, how to read the registry's own figures, what the corpus's real observed
   range looks like per metric (so "dense"/"sparse" has a concrete anchor, not a vibe).
6. `docs/simulation_quality/corpus_tier_taxonomy.md`: one-line pointer to the two new docs.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md identifies real, distinct density metrics | Done |
| corpus_registry.yaml extended with density sub-object | Steps 1-2 |
| Technical doc | Step 4 |
| Guide doc | Step 5 |
| Scoped pytest passes | Step 3 |
